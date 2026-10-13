import type { Metadata } from "next";
import { Geist_Mono, Nunito } from "next/font/google";
import Image from "next/image";
import Link from "next/link";

import "./globals.css";

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Breaking Bread",
  description: "Turn a cooking video into a meal you can shop for, afford, and cook.",
};

// Pages set their own width: the (flow) screens are a narrow column, and cook
// mode uses the full width for the step and the video side by side.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${nunito.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <header className="bg-accent shadow-[0_4px_16px_-6px_rgb(11_37_19/0.5)]">
          <div className="mx-auto flex max-w-6xl items-center px-4 py-3">
            <Link href="/" aria-label="Breaking Bread home">
              <Image src="/logo-light.png" alt="Breaking Bread" width={939} height={772} preload className="h-16 w-auto sm:h-20" />
            </Link>
          </div>
        </header>
        <main className="flex w-full flex-1 flex-col pt-6">{children}</main>
      </body>
    </html>
  );
}
