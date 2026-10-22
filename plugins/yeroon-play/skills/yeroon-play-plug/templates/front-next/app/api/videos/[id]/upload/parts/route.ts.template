import { repasse } from "@/lib/repasse";

export async function GET(
  request: Request,
  ctx: RouteContext<"/api/videos/[id]/upload/parts">,
) {
  const { id } = await ctx.params;
  return repasse(request, `/videos/${encodeURIComponent(id)}/upload/parts`);
}
