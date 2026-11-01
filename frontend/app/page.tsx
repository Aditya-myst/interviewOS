import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import Hero from "@/components/marketing/Hero";
import LogoStrip from "@/components/marketing/LogoStrip";
import ProblemSlab from "@/components/marketing/ProblemSlab";
import HowItWorks from "@/components/marketing/HowItWorks";
import SampleReport from "@/components/marketing/SampleReport";
import WhyNotChatGPT from "@/components/marketing/WhyNotChatGPT";
import FAQ from "@/components/marketing/FAQ";
import FinalCTA from "@/components/marketing/FinalCTA";
import MarketingFooter from "@/components/marketing/MarketingFooter";

export const metadata: Metadata = {
  title: "InterviewOS – AI Career Preparation",
  description: "Free AI interview preparation platform – get a report in minutes.",
};

export default function HomePage() {
  return (
    <>
      <MarketingNav />
      <main className="bg-[var(--canvas)] text-[var(--text)]">
        <Hero />
        <LogoStrip />
        <ProblemSlab />
        <HowItWorks />
        <SampleReport />
        <WhyNotChatGPT />
        <FAQ />
        <FinalCTA />
        <MarketingFooter />
      </main>
    </>
  );
}

