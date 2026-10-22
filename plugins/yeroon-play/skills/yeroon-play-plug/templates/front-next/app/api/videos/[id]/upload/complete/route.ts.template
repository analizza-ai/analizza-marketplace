import { repasse } from "@/lib/repasse";

export async function POST(
  request: Request,
  ctx: RouteContext<"/api/videos/[id]/upload/complete">,
) {
  const { id } = await ctx.params;
  return repasse(request, `/videos/${encodeURIComponent(id)}/upload/complete`);
}
