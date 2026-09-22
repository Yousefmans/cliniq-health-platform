import { eq } from "drizzle-orm";
import { getDb } from "../../../db";
import { doctors } from "../../../db/schema";

export async function GET() {
  try {
    const list = await getDb().select({ id: doctors.id, name: doctors.name, specialty: doctors.specialty,
      location: doctors.location, price: doctors.price, qualification: doctors.qualification })
      .from(doctors).where(eq(doctors.status, "verified")).orderBy(doctors.id);
    return Response.json({ doctors: list });
  } catch (error) {
    console.error("doctors failed", error);
    return Response.json({ error: "تعذر تحميل الأطباء" }, { status: 503 });
  }
}
