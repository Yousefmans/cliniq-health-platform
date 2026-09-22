import { eq } from "drizzle-orm";
import { getDb } from "../../../../db";
import { doctors, slots, users } from "../../../../db/schema";
import { requireRole } from "../../../../lib/authz";

export async function GET() {
  const user = await requireRole("doctor");
  if (user instanceof Response) return user;
  const [doctor] = await getDb().select().from(doctors).where(eq(doctors.email, user.email)).limit(1);
  if (!doctor) return Response.json({ error: "ملف الطبيب غير موجود" }, { status: 404 });
  const list = await getDb().select({ id: slots.id, startsAt: slots.startsAt, patientName: users.name })
    .from(slots).innerJoin(users, eq(slots.bookedBy, users.id)).where(eq(slots.doctorId, doctor.id))
    .orderBy(slots.startsAt);
  return Response.json({ doctor, appointments: list });
}
