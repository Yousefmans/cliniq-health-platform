import { and, eq, gt } from "drizzle-orm";
import { getDb } from "../../../../db";
import { slots } from "../../../../db/schema";
import { requireRole, sameOrigin } from "../../../../lib/authz";

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ error: "طلب غير مسموح" }, { status: 403 });
  const user = await requireRole("patient");
  if (user instanceof Response) return user;
  let slotId: number | undefined;
  try { ({ slotId } = await request.json() as { slotId?: number }); }
  catch { return Response.json({ error: "بيانات غير صالحة" }, { status: 400 }); }
  const id = Number(slotId);
  if (!Number.isSafeInteger(id) || id < 1) return Response.json({ error: "موعد غير صالح" }, { status: 400 });
  const result = await getDb().update(slots).set({ bookedBy: null })
    .where(and(eq(slots.id, id), eq(slots.bookedBy, user.id), gt(slots.startsAt, new Date().toISOString())))
    .returning({ id: slots.id });
  if (!result.length) return Response.json({ error: "لا يمكن إلغاء هذا الموعد" }, { status: 409 });
  return Response.json({ cancelled: true });
}
