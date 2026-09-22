import { and, eq, gt, isNull } from "drizzle-orm";
import { getDb } from "../../../db";
import { doctors, slots } from "../../../db/schema";
import { requireRole, sameOrigin } from "../../../lib/authz";

export async function GET() {
  const user = await requireRole("patient");
  if (user instanceof Response) return user;
  const list = await getDb().select({ id: slots.id, startsAt: slots.startsAt, doctorName: doctors.name,
    specialty: doctors.specialty, location: doctors.location }).from(slots)
    .innerJoin(doctors, eq(slots.doctorId, doctors.id)).where(eq(slots.bookedBy, user.id))
    .orderBy(slots.startsAt);
  return Response.json({ bookings: list });
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ error: "طلب غير مسموح" }, { status: 403 });
  const user = await requireRole("patient");
  if (user instanceof Response) return user;
  let body: { slotId?: number };
  try { body = await request.json() as { slotId?: number }; }
  catch { return Response.json({ error: "بيانات غير صالحة" }, { status: 400 }); }
  const id = Number(body.slotId);
  if (!Number.isSafeInteger(id) || id < 1) return Response.json({ error: "موعد غير صالح" }, { status: 400 });
  const result = await getDb().update(slots).set({ bookedBy: user.id })
    .where(and(eq(slots.id, id), isNull(slots.bookedBy), gt(slots.startsAt, new Date().toISOString())))
    .returning({ id: slots.id, startsAt: slots.startsAt });
  if (!result.length) return Response.json({ error: "الموعد لم يعد متاحًا" }, { status: 409 });
  return Response.json({ booking: result[0] }, { status: 201 });
}
