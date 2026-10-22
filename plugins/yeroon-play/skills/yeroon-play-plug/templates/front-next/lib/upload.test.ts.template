import { describe, expect, test } from "vitest";
import { UploadRejectedError, uploadVideo } from "./upload";

type Call = { method: string; url: string; body?: unknown };

function memoryStorage(initial: Record<string, string> = {}): Storage {
  const data = new Map(Object.entries(initial));
  return {
    get length() {
      return data.size;
    },
    clear: () => data.clear(),
    getItem: (k: string) => data.get(k) ?? null,
    key: (i: number) => [...data.keys()][i] ?? null,
    removeItem: (k: string) => void data.delete(k),
    setItem: (k: string, v: string) => void data.set(k, v),
  };
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

function fakeApi(opts: {
  existingParts?: number[];
  partsStatus?: number;
  initResponse?: Response;
  putHook?: (partNumber: number, attempt: number) => Response | void;
}) {
  const calls: Call[] = [];
  const putAttempts = new Map<number, number>();
  const fetchImpl = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body =
      typeof init?.body === "string" ? JSON.parse(init.body) : init?.body;
    calls.push({ method, url, body });
    if (method === "POST" && url === "/api/videos/uploads") {
      if (opts.initResponse) return opts.initResponse;
      return json({ videoId: "v1", partSizeBytes: 10, partCount: 3 }, 201);
    }
    if (method === "GET" && url === "/api/videos/v1/upload/parts") {
      if (opts.partsStatus) return json({ title: "x" }, opts.partsStatus);
      return json({
        parts: (opts.existingParts ?? []).map((n) => ({
          partNumber: n,
          etag: `"e${n}"`,
          sizeBytes: 10,
        })),
      });
    }
    if (method === "POST" && url === "/api/videos/v1/upload/part-urls") {
      return json({
        urls: body.partNumbers.map((n: number) => ({
          partNumber: n,
          url: `http://minio/put/${n}`,
        })),
      });
    }
    if (method === "PUT") {
      const n = Number(url.split("/").pop());
      const attempt = (putAttempts.get(n) ?? 0) + 1;
      putAttempts.set(n, attempt);
      const custom = opts.putHook?.(n, attempt);
      if (custom) return custom;
      return new Response(null, { status: 200, headers: { ETag: `"e${n}"` } });
    }
    if (method === "POST" && url === "/api/videos/v1/upload/complete") {
      return json({ videoId: "v1", status: "ENVIADO" });
    }
    if (method === "DELETE" && url === "/api/videos/v1/upload") {
      return new Response(null, { status: 204 });
    }
    throw new Error(`chamada inesperada ${method} ${url}`);
  }) as typeof fetch;
  return { calls, fetchImpl };
}

const file = new File(["x".repeat(25)], "a.mp4", {
  type: "video/mp4",
  lastModified: 1,
});
const key = "upload:a.mp4:25:1";

describe("uploadVideo", () => {
  test("enviaTodasAsPartesECompletaComOsETags", async () => {
    const { calls, fetchImpl } = fakeApi({});
    const storage = memoryStorage();
    const progress: number[] = [];
    const r = await uploadVideo(file, {
      fetchImpl,
      storage,
      onProgress: (sent) => progress.push(sent),
    });
    expect(r).toEqual({ videoId: "v1" });
    expect(calls.filter((c) => c.method === "PUT")).toHaveLength(3);
    const complete = calls.find((c) => c.url.endsWith("/upload/complete"));
    expect(complete?.body).toEqual({
      parts: [
        { partNumber: 1, etag: '"e1"' },
        { partNumber: 2, etag: '"e2"' },
        { partNumber: 3, etag: '"e3"' },
      ],
    });
    expect(storage.getItem(key)).toBeNull();
    expect(progress.at(-1)).toBe(3);
  });

  test("retomaEnviandoSoAsPartesQueFaltam", async () => {
    const { calls, fetchImpl } = fakeApi({ existingParts: [1, 2] });
    const storage = memoryStorage({ [key]: "v1" });
    await uploadVideo(file, { fetchImpl, storage });
    expect(calls.some((c) => c.url === "/api/videos/uploads")).toBe(false);
    const puts = calls.filter((c) => c.method === "PUT");
    expect(puts.map((c) => c.url)).toEqual(["http://minio/put/3"]);
    const complete = calls.find((c) => c.url.endsWith("/upload/complete"));
    expect(
      (complete?.body as { parts: { partNumber: number }[] }).parts.map(
        (p) => p.partNumber,
      ),
    ).toEqual([1, 2, 3]);
  });

  test("videoNaoMaisPendenteApagaAChaveEComecaDoZero", async () => {
    const { calls, fetchImpl } = fakeApi({ partsStatus: 422 });
    const storage = memoryStorage({ [key]: "v1" });
    await uploadVideo(file, { fetchImpl, storage });
    expect(calls.some((c) => c.url === "/api/videos/uploads")).toBe(true);
  });

  test("inicioRecusadoCom422TrazAsMensagensDoServidor", async () => {
    const { calls, fetchImpl } = fakeApi({
      initResponse: json(
        {
          title: "Regra de negocio violada",
          errors: [{ id: "video.content-type", message: "Só vídeos são aceitos." }],
        },
        422,
      ),
    });
    const err = await uploadVideo(file, { fetchImpl, storage: memoryStorage() }).catch((e) => e);
    expect(err).toBeInstanceOf(UploadRejectedError);
    expect((err as Error).message).toBe("Só vídeos são aceitos.");
    expect(calls.some((c) => c.url.endsWith("/part-urls"))).toBe(false);
  });

  test("arquivoComTamanhoDiferenteComecaUploadNovo", async () => {
    const { calls, fetchImpl } = fakeApi({});
    const storage = memoryStorage({ "upload:a.mp4:99:1": "v1" });
    await uploadVideo(file, { fetchImpl, storage });
    expect(calls.some((c) => c.url === "/api/videos/uploads")).toBe(true);
    expect(calls.some((c) => c.url.endsWith("/upload/parts"))).toBe(false);
  });

  test("tentaDeNovoUmaParteQueFalhou", async () => {
    const { calls, fetchImpl } = fakeApi({
      putHook: (n, attempt) =>
        n === 2 && attempt === 1 ? new Response(null, { status: 500 }) : undefined,
    });
    await uploadVideo(file, { fetchImpl, storage: memoryStorage() });
    expect(
      calls.filter((c) => c.method === "PUT" && c.url.endsWith("/2")),
    ).toHaveLength(2);
    expect(calls.some((c) => c.url.endsWith("/upload/complete"))).toBe(true);
  });

  test("cancelarAbortaNoBackend", async () => {
    const controller = new AbortController();
    const { calls, fetchImpl } = fakeApi({
      putHook: () => {
        controller.abort();
      },
    });
    const storage = memoryStorage();
    await expect(
      uploadVideo(file, { fetchImpl, storage, signal: controller.signal }),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(
      calls.some((c) => c.method === "DELETE" && c.url === "/api/videos/v1/upload"),
    ).toBe(true);
    expect(calls.some((c) => c.url.endsWith("/upload/complete"))).toBe(false);
    expect(storage.getItem(key)).toBeNull();
  });
});
