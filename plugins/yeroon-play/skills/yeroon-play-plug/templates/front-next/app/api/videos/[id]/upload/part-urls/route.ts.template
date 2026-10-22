import { repasse } from "@/lib/repasse";

export async function POST(
  request: Request,
  ctx: RouteContext<"/api/videos/[id]/upload/part-urls">,
) {
  const { id } = await ctx.params;
  return repasse(request, `/videos/${encodeURIComponent(id)}/upload/part-urls`);
}
