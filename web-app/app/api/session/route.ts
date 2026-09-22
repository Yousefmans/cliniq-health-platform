import { session } from "../../../lib/authz";

export async function GET() {
  try {
    return Response.json({ user: await session() });
  } catch (error) {
    console.error("session failed", error);
    return Response.json({ error: "تعذر تحميل الحساب الآن" }, { status: 503 });
  }
}
