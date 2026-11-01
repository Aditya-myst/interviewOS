import { cn } from "@/lib/utils";
import { ArrowRight } from "lucide-react";

export default function ProblemSlab() {
  return (
    <section className="bg-[var(--ink-900)] py-24">
      <div className="max-w-5xl mx-auto px-6 lg:px-12">
        <p className="text-micro text-[var(--on-ink-dim)] mb-6">THE ACTUAL PROBLEM</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-[var(--on-ink)]">
          {/* Item 1 */}
          <div className="flex flex-col gap-2">
            <span className="text-[var(--green-400)] text-2xl font-mono">01</span>
            <h3 className="text-lg font-semibold">Resumes are marketing</h3>
            <p className="text-[var(--on-ink-dim)]">
              A listed skill and a demonstrated skill look identical on paper. Interviewers find out which one you have.
            </p>
          </div>
          {/* Item 2 */}
          <div className="flex flex-col gap-2">
            <span className="text-[var(--green-400)] text-2xl font-mono">02</span>
            <h3 className="text-lg font-semibold">Generic prep is wasted prep</h3>
            <p className="text-[var(--on-ink-dim)]">
              You don't need all of Docker. You need the four Docker questions this role will ask.
            </p>
          </div>
          {/* Item 3 */}
          <div className="flex flex-col gap-2">
            <span className="text-[var(--green-400)] text-2xl font-mono">03</span>
            <h3 className="text-lg font-semibold">Advice without evidence</h3>
            <p className="text-[var(--on-ink-dim)]">
              Every priority InterviewOS shows you points back at the answer, the project or the job line it came from.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
