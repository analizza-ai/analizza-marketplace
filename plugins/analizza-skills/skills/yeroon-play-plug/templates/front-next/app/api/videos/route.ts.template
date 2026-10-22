import { connection } from "next/server";
import { repasse } from "@/lib/repasse";

export async function GET(request: Request) {
  // Com cacheComponents o GET seria pré-renderizado no build; a lista muda a
  // cada upload, então força a execução por requisição.
  await connection();
  return repasse(request, "/videos");
}
