import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BUILDLoop",
  description: "Digital material passports for circular construction.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-surface antialiased">
      <body className="flex min-h-full flex-col bg-surface font-sans">
        {children}
      </body>
    </html>
  );
}
