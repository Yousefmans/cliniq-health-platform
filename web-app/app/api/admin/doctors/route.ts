import { getDb } from "../../../../db";
import { doctors } from "../../../../db/schema";
import { requireRole, sameOrigin } from "../../../../lib/authz";

export async function GET() {
  const user = await requireRole("admin");
  if (user instanceof Response) return user;
  const list = await getDb().select().from(doctors).orderBy(doctors.id);
  return Response.json({ doctors: list });
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ error: "طلب غير مسموح" }, { status: 403 });
  const user = await requireRole("admin");
  if (user instanceof Response) return user;
  let data: Record<string, unknown>;
  try { data = await request.json() as Record<string, unknown>; }
  catch { return Response.json({ error: "بيانات غير صالحة" }, { status: 400 }); }
  const email = String(data.email || "").trim().toLowerCase();
  const name = String(data.name || "").trim();
  const specialty = String(data.specialty || "").trim();
  const location = String(data.location || "").trim();
  const qualification = String(data.qualification || "").trim();
  const price = Number(data.price);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !name || !specialty || !location ||
      name.length > 150 || specialty.length > 100 || location.length > 200 || qualification.length > 500 ||
      !Number.isSafeInteger(price) || price < 0 || price > 100000) {
    return Response.json({ error: "راجع اسم الطبيب والبريد والتخصص والمكان والسعر" }, { status: 400 });
  }
  try {
    const [doctor] = await getDb().insert(doctors).values({ email, name, specialty, location, qualification,
      price, createdAt: new Date().toISOString() }).returning();
    return Response.json({ doctor }, { status: 201 });
  } catch (error) {
    if (String(error).includes("UNIQUE")) return Response.json({ error: "البريد مسجل لطبيب آخر" }, { status: 409 });
    console.error("doctor create failed", error);
    return Response.json({ error: "تعذر إضافة الطبيب" }, { status: 503 });
  }
}
