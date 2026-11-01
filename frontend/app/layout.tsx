import type { Metadata } from "next";
import { Archivo_Black, Inter_Tight, JetBrains_Mono } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

const archivoBlack = Archivo_Black({
  weight: "400",
  variable: "--font-archivo-black",
  subsets: ["latin"],
  display: "swap",
});

const interTight = Inter_Tight({
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-inter-tight",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  weight: ["400", "500"],
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://interviewos.app"),
  title: {
    default: "InterviewOS — prove what you actually know",
    template: "%s | InterviewOS",
  },
  description:
    "InterviewOS tests what your resume claims against what the job requires, then builds a roadmap from the gaps that will actually be asked.",
  keywords: ["interview preparation", "skill gap analysis", "AI interview practice", "career"],
  openGraph: {
    title: "InterviewOS — prove what you actually know",
    description:
      "Evidence-based interview preparation: claims, verification, gaps, roadmap.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${archivoBlack.variable} ${interTight.variable} ${jetbrainsMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-[var(--canvas)] text-[var(--text)]">
        <TooltipProvider delay={300}>{children}</TooltipProvider>
      </body>
    </html>
  );
}
