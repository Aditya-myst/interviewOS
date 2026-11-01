import IosButton from "@/components/primitives/IosButton";

export default function WhyNotChatGPT() {
  return (
    <section className="bg-[var(--canvas)] py-24" id="why-not-chatgpt">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 flex flex-col lg:flex-row items-center gap-12">
        {/* Image placeholder */}
        <div className="flex-1 w-full max-w-sm h-64 bg-[var(--surface-2)] rounded-[20px] border border-[var(--border)] shadow-[0_1px_2px_rgba(0,0,0,.06),_0_10px_28px_-14px_rgba(0,0,0,.20)] flex items-center justify-center text-[var(--text-dim)]">
          Illustration
        </div>
        {/* Text side */}
        <div className="flex-1">
          <p className="text-micro text-[var(--text-dim)] mb-2">WHY NOT CHATGPT</p>
          <h2 className="text-display-2 text-[var(--text)] mb-4">Because you need focused, verifiable interview prep</h2>
          <p className="text-[var(--text-dim)] mb-6 max-w-[60ch]">
            ChatGPT gives generic answers, not evidence‑based skill assessments. InterviewOS gives you concrete proof of competence directly tied to job requirements.
          </p>
          <IosButton variant="primary" size="lg" arrow>
            Try InterviewOS now
          </IosButton>
        </div>
      </div>
    </section>
  );
}
