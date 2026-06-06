import React, { useEffect, useMemo, useState } from "react";
import { ExternalLink } from "lucide-react";
import api, { absUrl } from "../lib/api";
import { useLang } from "../contexts/LangContext";

const MARKETS = ["all", "arab", "foreign"];
const CATEGORIES = ["all", "websites", "stores", "other"];

export default function Portfolio() {
  const { t } = useLang();
  const [items, setItems] = useState([]);
  const [market, setMarket] = useState("all");
  const [category, setCategory] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.get("/projects").then(({ data }) => {
      if (mounted) setItems(data || []);
    }).finally(() => mounted && setLoading(false));
    return () => { mounted = false; };
  }, []);

  const filtered = useMemo(() => {
    return items.filter((p) => {
      const m = market === "all" || p.market === market;
      const c = category === "all" || p.category === category;
      return m && c;
    });
  }, [items, market, category]);

  return (
    <section id="work" data-testid="portfolio-section" className="relative bg-white text-[#112325] py-20 md:py-32">
      <div className="mx-auto max-w-7xl px-5 md:px-10">
        <div className="text-center max-w-3xl mx-auto">
          <h2 data-testid="portfolio-title" className="font-display text-4xl sm:text-5xl lg:text-6xl text-[#0A3D42]">{t.portfolio.title}</h2>
          <p data-testid="portfolio-sub" className="mt-4 text-[#3a5358] text-base md:text-lg leading-relaxed">{t.portfolio.sub}</p>
        </div>

        {/* Filters */}
        <div className="mt-10 flex flex-col items-center gap-4">
          <div className="seg-track" data-testid="market-filter">
            {MARKETS.map((m) => (
              <button
                key={m}
                data-testid={`market-${m}`}
                className="seg-btn"
                data-active={market === m}
                onClick={() => setMarket(m)}
              >
                {t.portfolio.market[m]}
              </button>
            ))}
          </div>
          <div className="seg-track" data-testid="category-filter">
            {CATEGORIES.map((c) => (
              <button
                key={c}
                data-testid={`category-${c}`}
                className="seg-btn"
                data-active={category === c}
                onClick={() => setCategory(c)}
              >
                {t.portfolio.category[c]}
              </button>
            ))}
          </div>
        </div>

        {/* Grid */}
        <div className="mt-12 md:mt-16">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="proj-card h-72 animate-pulse bg-[#F1F6F7]" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div data-testid="portfolio-empty" className="py-20 text-center text-[#3a5358] text-lg">
              {t.portfolio.empty}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
              {filtered.map((p) => (
                <a
                  key={p.id}
                  href={p.live_url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid={`project-card-${p.id}`}
                  className="proj-card group block"
                >
                  <div className="aspect-[16/10] overflow-hidden bg-[#EAF1F2]">
                    {p.image_url ? (
                      <img
                        src={p.image_url.startsWith("http") ? p.image_url : absUrl(p.image_url)}
                        alt={p.title}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full grid place-items-center text-[#3a5358] font-display text-3xl">{p.title.slice(0, 1)}</div>
                    )}
                  </div>
                  <div className="p-5">
                    <div className="flex items-center gap-2 text-xs text-[#3a5358] mb-2">
                      <span className="px-2 py-1 rounded-md bg-[#E6F2F5] text-[#0A3D42] font-medium">{t.portfolio.market[p.market] || p.market}</span>
                      <span className="px-2 py-1 rounded-md bg-[#F1F6F7] text-[#3a5358] font-medium">{t.portfolio.category[p.category] || p.category}</span>
                    </div>
                    <h3 className="font-display text-xl text-[#112325] leading-snug">{p.title}</h3>
                    <div className="mt-3 inline-flex items-center gap-2 text-[#0A3D42] font-semibold text-sm">
                      <span>{t.portfolio.visit}</span>
                      <ExternalLink className="w-4 h-4" />
                    </div>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
