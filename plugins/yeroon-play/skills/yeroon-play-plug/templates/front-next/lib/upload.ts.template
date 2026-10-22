export type UploadOptions = {
  onProgress?: (sentParts: number, totalParts: number) => void;
  signal?: AbortSignal;
  fetchImpl?: typeof fetch;
  storage?: Storage;
};

/** O início do upload foi recusado por regra de negócio (422): reenviar o mesmo arquivo não adianta. */
export class UploadRejectedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UploadRejectedError";
  }
}

type Part = { partNumber: number; etag: string };

const CONCURRENCY = 4;
const URL_BATCH = 20;
const BACKOFF_MS = [500, 1000, 2000];

function abortError(): DOMException {
  return new DOMException("Upload cancelado", "AbortError");
}

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

export async function uploadVideo(
  file: File,
  opts: UploadOptions = {},
): Promise<{ videoId: string }> {
  const doFetch = opts.fetchImpl ?? ((...a: Parameters<typeof fetch>) => fetch(...a));
  const storage = opts.storage ?? localStorage;
  const { signal } = opts;
  const key = `upload:${file.name}:${file.size}:${file.lastModified}`;

  const api = async (path: string, init?: RequestInit) => {
    const res = await doFetch(path, { ...init, signal });
    return res;
  };
  const jsonInit = (method: string, body: unknown): RequestInit => ({
    method,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const mustOk = async (res: Response, what: string) => {
    if (!res.ok) throw new Error(`${what} falhou (${res.status})`);
    return res;
  };

  const planKey = `${key}:plan`;
  const clearKeys = () => {
    storage.removeItem(key);
    storage.removeItem(planKey);
  };

  const startNew = async () => {
    const initRes = await api(
      "/api/videos/uploads",
      jsonInit("POST", {
        fileName: file.name,
        contentType: file.type || "application/octet-stream",
        sizeBytes: file.size,
      }),
    );
    if (initRes.status === 422) {
      let messages: string[] = [];
      try {
        const problem = (await initRes.json()) as { errors?: { message?: string }[] };
        messages = (problem.errors ?? []).flatMap((e) => (e.message ? [e.message] : []));
      } catch {
        // corpo fora do padrão: cai na mensagem genérica abaixo
      }
      throw new UploadRejectedError(
        messages.join(" ") || "O servidor recusou o arquivo.",
      );
    }
    const res = await mustOk(initRes, "Início do upload");
    const body = (await res.json()) as {
      videoId: string;
      partSizeBytes: number;
      partCount: number;
    };
    storage.setItem(key, body.videoId);
    storage.setItem(
      planKey,
      JSON.stringify({ partSize: body.partSizeBytes, partCount: body.partCount }),
    );
    return {
      videoId: body.videoId,
      partSize: body.partSizeBytes,
      partCount: body.partCount,
      done: [] as Part[],
    };
  };

  const resume = async (savedId: string) => {
    const res = await api(`/api/videos/${savedId}/upload/parts`);
    if (res.status === 404 || res.status === 422) {
      clearKeys();
      return null;
    }
    await mustOk(res, "Consulta das partes");
    const body = (await res.json()) as {
      parts: { partNumber: number; etag: string; sizeBytes: number }[];
    };
    // O GET /parts não informa o tamanho da parte: usa o plano guardado
    // ou, na falta dele, o maior tamanho já enviado.
    let partSize = 0;
    try {
      partSize = JSON.parse(storage.getItem(planKey) ?? "null")?.partSize ?? 0;
    } catch {
      partSize = 0;
    }
    if (!partSize) partSize = Math.max(0, ...body.parts.map((p) => p.sizeBytes));
    if (!partSize) {
      // Nada enviado e plano desconhecido: descarta e recomeça.
      await api(`/api/videos/${savedId}/upload`, { method: "DELETE" });
      clearKeys();
      return null;
    }
    return {
      videoId: savedId,
      partSize,
      partCount: Math.ceil(file.size / partSize),
      done: body.parts.map((p) => ({ partNumber: p.partNumber, etag: p.etag })),
    };
  };

  const saved = storage.getItem(key);
  const plan = (saved ? await resume(saved) : null) ?? (await startNew());
  const { videoId, partSize, partCount } = plan;
  const parts = new Map<number, string>(
    plan.done.map((p) => [p.partNumber, p.etag]),
  );
  opts.onProgress?.(parts.size, partCount);

  const cancel = async () => {
    try {
      await doFetch(`/api/videos/${videoId}/upload`, { method: "DELETE" });
    } finally {
      clearKeys();
    }
    throw abortError();
  };

  const putPart = async (n: number, url: string) => {
    const blob = file.slice((n - 1) * partSize, n * partSize);
    for (let attempt = 0; ; attempt++) {
      if (signal?.aborted) throw abortError();
      try {
        const res = await doFetch(url, {
          method: "PUT",
          headers: { "content-type": "application/octet-stream" },
          body: blob,
          signal,
        });
        if (!res.ok) throw new Error(`PUT da parte ${n} falhou (${res.status})`);
        const etag = res.headers.get("ETag");
        if (!etag) throw new Error(`Parte ${n} sem ETag na resposta`);
        parts.set(n, etag);
        opts.onProgress?.(parts.size, partCount);
        return;
      } catch (e) {
        if (signal?.aborted || (e as Error).name === "AbortError") throw abortError();
        if (attempt >= BACKOFF_MS.length) throw e;
        await sleep(BACKOFF_MS[attempt]);
      }
    }
  };

  const missing: number[] = [];
  for (let n = 1; n <= partCount; n++) if (!parts.has(n)) missing.push(n);

  try {
    for (let i = 0; i < missing.length; i += URL_BATCH) {
      const batch = missing.slice(i, i + URL_BATCH);
      const res = await mustOk(
        await api(
          `/api/videos/${videoId}/upload/part-urls`,
          jsonInit("POST", { partNumbers: batch }),
        ),
        "URLs das partes",
      );
      const { urls } = (await res.json()) as {
        urls: { partNumber: number; url: string }[];
      };
      const queue = [...urls];
      const worker = async () => {
        for (let next = queue.shift(); next; next = queue.shift()) {
          await putPart(next.partNumber, next.url);
        }
      };
      await Promise.all(
        Array.from({ length: Math.min(CONCURRENCY, queue.length) }, worker),
      );
    }
    if (signal?.aborted) throw abortError();
    await mustOk(
      await api(
        `/api/videos/${videoId}/upload/complete`,
        jsonInit("POST", {
          parts: [...parts.entries()]
            .sort(([a], [b]) => a - b)
            .map(([partNumber, etag]) => ({ partNumber, etag })),
        }),
      ),
      "Conclusão do upload",
    );
  } catch (e) {
    if (signal?.aborted || (e as Error).name === "AbortError") return cancel();
    throw e;
  }
  clearKeys();
  return { videoId };
}
