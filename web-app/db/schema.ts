import { index, integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull(),
  name: text("name").notNull(),
  createdAt: text("created_at").notNull(),
}, (t) => [uniqueIndex("idx_users_email").on(t.email)]);

export const doctors = sqliteTable("doctors", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  email: text("email").notNull(),
  name: text("name").notNull(),
  specialty: text("specialty").notNull(),
  location: text("location").notNull(),
  price: integer("price").notNull(),
  qualification: text("qualification").notNull().default(""),
  status: text("status").notNull().default("verified"),
  createdAt: text("created_at").notNull(),
}, (t) => [uniqueIndex("idx_doctors_email").on(t.email), index("idx_doctors_specialty").on(t.specialty)]);

export const slots = sqliteTable("slots", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  doctorId: integer("doctor_id").notNull().references(() => doctors.id),
  startsAt: text("starts_at").notNull(),
  bookedBy: text("booked_by").references(() => users.id),
}, (t) => [uniqueIndex("idx_slots_doctor_starts_at").on(t.doctorId, t.startsAt), index("idx_slots_booked_by").on(t.bookedBy)]);
