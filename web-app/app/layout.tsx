import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClinIQ | عيادتك أقرب",
  description: "إدارة المواعيد والبحث عن الأطباء في مكان واحد.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body className="antialiased">{children}</body>
    </html>
  );
}
