import { defineCloudflareConfig } from "@opennextjs/cloudflare";

// Sem cache incremental: ligue um (R2, KV) so quando houver pagina pre-renderizada
// com dados que precise de revalidacao.
export default defineCloudflareConfig();
