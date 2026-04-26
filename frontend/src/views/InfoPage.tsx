import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

interface InfoPageProps {
  eyebrow: { tr: string; en: string };
  title: { tr: string; en: string };
  intro: { tr: string; en: string };
  sections: Array<{
    heading: { tr: string; en: string };
    body: { tr: string; en: string };
  }>;
}

const InfoPage: React.FC<InfoPageProps> = ({ eyebrow, title, intro, sections }) => {
  const { isEnglish } = useLanguage();

  return (
    <div className="space-y-8">
      <section className="shell page-hero px-6 py-8 md:px-10 md:py-12">
        <div className="relative z-10 max-w-4xl space-y-5 text-white">
          <p className="eyebrow text-white/65">{isEnglish ? eyebrow.en : eyebrow.tr}</p>
          <h1 className="font-heading text-5xl leading-tight md:text-6xl">{isEnglish ? title.en : title.tr}</h1>
          <p className="max-w-3xl text-base leading-8 text-white/72 md:text-lg">{isEnglish ? intro.en : intro.tr}</p>
        </div>
      </section>

      <section className="shell">
        <div className="section-card p-6 md:p-8">
          <div className="grid gap-6">
            {sections.map((section) => (
              <div key={section.heading.tr} className="rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-alt)] p-5">
                <h2 className="font-heading text-3xl text-[var(--text-strong)]">{isEnglish ? section.heading.en : section.heading.tr}</h2>
                <p className="mt-3 text-sm leading-8 text-[var(--text-primary)]">{isEnglish ? section.body.en : section.body.tr}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default InfoPage;
