CREATE TABLE `doctors` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`email` text NOT NULL,
	`name` text NOT NULL,
	`specialty` text NOT NULL,
	`location` text NOT NULL,
	`price` integer NOT NULL,
	`qualification` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'verified' NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_doctors_email` ON `doctors` (`email`);--> statement-breakpoint
CREATE INDEX `idx_doctors_specialty` ON `doctors` (`specialty`);--> statement-breakpoint
CREATE TABLE `slots` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`doctor_id` integer NOT NULL,
	`starts_at` text NOT NULL,
	`booked_by` text,
	FOREIGN KEY (`doctor_id`) REFERENCES `doctors`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`booked_by`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_slots_doctor_starts_at` ON `slots` (`doctor_id`,`starts_at`);--> statement-breakpoint
CREATE INDEX `idx_slots_booked_by` ON `slots` (`booked_by`);--> statement-breakpoint
CREATE TABLE `users` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`name` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_users_email` ON `users` (`email`);