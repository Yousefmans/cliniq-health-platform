import { and, eq, gt, isNull } from "drizzle-orm";
import { getDb } from "../../../db";
import { doctors, slots } from "../../../db/schema";
import { requireRole, sameOrigin } from "../../../lib/authz";

export async function GET(request: Request) {
  const doctorId = Number(new URL(request.url).searchParams.get("doctorId"));
  if (!Number.isSafeInteger(doctorId) || doctorId < 1) return Response.json({ slots: [] });
  const list = await getDb().select({ id: slots.id, doctorId: slots.doctorId, startsAt: slots.startsAt })
    .from(slots).where(and(eq(slots.doctorId, doctorId), isNull(slots.bookedBy), gt(slots.startsAt, new Date().toISOString())))
    .orderBy(slots.startsAt).limit(40);
  return Response.json({ slots: list });
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ error: "طلب غير مسموح" }, { status: 403 });
  const user = await requireRole("doctor");
  if (user instanceof Response) return user;
  const [doctor] = await getDb().select({ id: doctors.id }).from(doctors).where(eq(doctors.email, user.email)).limit(1);
  if (!doctor) return Response.json({ error: "ملف الطبيب غير موجود" }, { status: 404 });
  let body: { startsAt?: string };
  try { body = await request.json() as { startsAt?: string }; }
  catch { return Response.json({ error: "موعد غير صالح" }, { status: 400 }); }
  const dt = new Date(body.startsAt || "");
  if (Number.isNaN(dt.getTime()) || dt.getTime() <= Date.now() || dt.getTime() > Date.now() + 365 * 86400000)
    return Response.json({ error: "اختر موعدًا مستقبليًا خلال سنة" }, { status: 400 });
  try {
    const [slot] = await getDb().insert(slots).values({ doctorId: doctor.id, startsAt: dt.toISOString() }).returning();
    return Response.json({ slot }, { status: 201 });
  } catch (error) {
    if (String(error).includes("UNIQUE")) return Response.json({ error: "الموعد موجود بالفعل" }, { status: 409 });
    console.error("slot create failed", error);
    return Response.json({ error: "تعذر إضافة الموعد" }, { status: 503 });
  }
}
