import React from "react";
import { Sparkles, ArrowRight, ArrowLeft } from "lucide-react";
import { useLang } from "../contexts/LangContext";
import ParticleField from "./ParticleField";

export default function Hero() {
  const { t, dir } = useLang();
  const ArrowIcon = dir === "rtl" ? ArrowLeft : ArrowRight;

  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section id="home" data-testid="hero-section" className="relative overflow-hidden bg-[#0A3D42] text-white pt-24 md:pt-28">
      <div className="absolute inset-0 hero-glow" aria-hidden="true" />
      <ParticleField />
      <div className="relative mx-auto max-w-7xl px-5 md:px-10 pb-24 md:pb-32 pt-10 md:pt-14">
        {/* AI Pill Badge ~ 2cm below header */}
        <div className="flex justify-center" style={{ marginTop: "1.5cm" }}>
          <div data-testid="ai-pill-badge" className="glass-pill inline-flex items-center gap-2 px-4 py-2 text-sm text-white/90">
            <Sparkles className="w-4 h-4 text-[#5EEAD4] ai-star" />
            <span className="font-medium">{t.hero.badge}</span>
          </div>
        </div>

        {/* Massive headline container */}
        <div className="headline-frame mt-10 md:mt-14 px-6 md:px-12 py-10 md:py-16 text-center">
          <h1
            data-testid="hero-headline"
            className="font-display font-black tracking-tight leading-[0.95] text-white text-6xl sm:text-7xl md:text-8xl lg:text-9xl"
          >
            {t.hero.title}
          </h1>
          <p data-testid="hero-sub" className="mt-6 md:mt-8 max-w-3xl mx-auto text-base md:text-lg text-white/80 leading-relaxed">
            {t.hero.sub}
          </p>
        </div>

        {/* Stacked CTAs */}
        <div className="mt-10 md:mt-12 flex flex-col items-center gap-4">
          <button
            data-testid="cta-work-btn"
            onClick={() => scrollTo("work")}
            className="btn-3d btn-3d-light bg-white text-[#112325] px-7 h-14 rounded-xl font-bold inline-flex items-center gap-3 min-w-[260px] justify-between"
          >
            <span>{t.hero.cta1}</span>
            <ArrowIcon className="w-5 h-5" />
          </button>
          <button
            data-testid="cta-consult-btn"
            onClick={() => scrollTo("consult")}
            className="btn-3d bg-transparent text-white border-2 border-white/85 hover:bg-white/10 px-7 h-14 rounded-xl font-bold inline-flex items-center gap-3 min-w-[260px] justify-between"
          >
            <span>{t.hero.cta2}</span>
            <ArrowIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </section>
  );
}
