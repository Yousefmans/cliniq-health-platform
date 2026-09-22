import { env } from "cloudflare:workers";
import { eq } from "drizzle-orm";
import { getChatGPTUser } from "../app/chatgpt-auth";
import { getDb } from "../db";
import { doctors, users } from "../db/schema";

export type Session = { id: string; email: string; name: string; role: "admin" | "doctor" | "patient" };

export async function session(): Promise<Session | null> {
  const identity = await getChatGPTUser();
  if (!identity) return null;
  const db = getDb();
  const email = identity.email.trim().toLowerCase();
  const name = identity.fullName || identity.email;
  // The identity headers are set by the Site dispatcher, never by client JSON.
  await db.insert(users).values({ id: identity.userId, email, name, createdAt: new Date().toISOString() })
    .onConflictDoUpdate({ target: users.id, set: { email, name } });
  const admin = identity.userId === env.ADMIN_USER_ID;
  const [doctor] = await db.select({ id: doctors.id }).from(doctors).where(eq(doctors.email, email)).limit(1);
  return { id: identity.userId, email, name, role: admin ? "admin" : doctor ? "doctor" : "patient" };
}

export async function requireRole(role: Session["role"]): Promise<Session | Response> {
  const who = await session();
  if (!who) return Response.json({ error: "يرجى تسجيل الدخول" }, { status: 401 });
  if (who.role !== role) return Response.json({ error: "ليس لديك صلاحية لهذه العملية" }, { status: 403 });
  return who;
}

export function sameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  return !origin || origin === new URL(request.url).origin;
}
