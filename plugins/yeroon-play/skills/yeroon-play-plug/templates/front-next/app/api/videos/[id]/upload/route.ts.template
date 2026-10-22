import { repasse } from "@/lib/repasse";

export async function DELETE(
  request: Request,
  ctx: RouteContext<"/api/videos/[id]/upload">,
) {
  const { id } = await ctx.params;
  return repasse(request, `/videos/${encodeURIComponent(id)}/upload`);
}
