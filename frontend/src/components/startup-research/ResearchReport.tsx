"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Users,
  LayoutGrid,
  DollarSign,
  Target,
  AlertTriangle,
  Lightbulb,
  Shield,
  MessageSquare,
  Link as LinkIcon,
  Send,
  CheckCircle2,
  ChevronDown,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { startupResearchService } from "@/services/startupResearch";
import type { StartupResearchReport, ResearchCompetitor } from "@/lib/types";

interface Props {
  report: StartupResearchReport;
}

const SECTION_TABS = [
  { id: "summary", label: "Summary", icon: FileText },
  { id: "competitors", label: "Competitors", icon: Users },
  { id: "features", label: "Features", icon: LayoutGrid },
  { id: "pricing", label: "Pricing", icon: DollarSign },
  { id: "positioning", label: "Positioning", icon: Target },
  { id: "gaps", label: "Market Gaps", icon: AlertTriangle },
  { id: "differentiation", label: "Differentiation", icon: Lightbulb },
  { id: "swot", label: "SWOT", icon: Shield },
  { id: "recommendations", label: "Recommendations", icon: MessageSquare },
  { id: "sources", label: "Sources", icon: LinkIcon },
] as const;

type SectionId = (typeof SECTION_TABS)[number]["id"];

export function ResearchReport({ report }: Props) {
  const [activeSection, setActiveSection] = useState<SectionId>("summary");
  const [slackSending, setSlackSending] = useState(false);
  const [slackSent, setSlackSent] = useState(report.sent_to_slack);

  const handleSendToSlack = async () => {
    setSlackSending(true);
    try {
      await startupResearchService.sendToSlack(report.id);
      setSlackSent(true);
    } catch {
      // silently ignore
    } finally {
      setSlackSending(false);
    }
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 50) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <motion.div
      key={report.id}
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass rounded-2xl border border-zinc-800/60 overflow-hidden"
    >
      {/* Report header */}
      <div className="px-6 py-5 border-b border-zinc-800/60">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/25">
                {report.industry}
              </span>
              <span className="text-xs text-zinc-600">
                {new Date(report.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>
            <h2 className="text-base font-semibold text-zinc-100 mt-2 leading-snug">
              {report.startup_name ? (
                <>
                  <span className="text-purple-400">{report.startup_name}</span>
                  {" — "}
                </>
              ) : null}
              {report.startup_idea}
            </h2>
            <div className="flex items-center gap-4 mt-2 text-xs text-zinc-500">
              <span>
                <span className="text-zinc-300 font-medium">{report.competitors_found}</span> competitors found
              </span>
              <span>
                <span className="text-zinc-300 font-medium">{report.sources_analyzed}</span> sources analyzed
              </span>
              <span>
                Research score{" "}
                <span className={cn("font-semibold", scoreColor(report.research_score))}>
                  {report.research_score}/100
                </span>
              </span>
            </div>
          </div>

          {/* Slack button */}
          <button
            onClick={handleSendToSlack}
            disabled={slackSending || slackSent}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all flex-shrink-0",
              slackSent
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 cursor-default"
                : "bg-zinc-800/60 text-zinc-400 border-zinc-700/50 hover:text-zinc-200 hover:border-zinc-600"
            )}
          >
            {slackSending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : slackSent ? (
              <CheckCircle2 className="w-3 h-3" />
            ) : (
              <Send className="w-3 h-3" />
            )}
            {slackSent ? "Sent to Slack" : "Send to Slack"}
          </button>
        </div>

        {/* Keywords */}
        {report.keywords?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {report.keywords.map((kw) => (
              <span
                key={kw}
                className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800/60 border border-zinc-700/50 text-zinc-500"
              >
                {kw}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Section tabs */}
      <div className="flex overflow-x-auto border-b border-zinc-800/60 scrollbar-hide">
        {SECTION_TABS.map((tab) => {
          const Icon = tab.icon;
          const active = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-3 text-xs font-medium whitespace-nowrap border-b-2 transition-all flex-shrink-0",
                active
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-zinc-500 hover:text-zinc-300"
              )}
            >
              <Icon className="w-3 h-3" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Section content */}
      <div className="p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
          >
            {activeSection === "summary" && <SectionSummary report={report} />}
            {activeSection === "competitors" && <SectionCompetitors competitors={report.competitors} />}
            {activeSection === "features" && (
              <SectionFeatures rows={report.feature_comparison} competitors={report.competitors} />
            )}
            {activeSection === "pricing" && (
              <SectionPricing pricing={report.pricing_analysis} competitors={report.competitors} />
            )}
            {activeSection === "positioning" && (
              <SectionPositioning text={report.positioning_analysis} competitors={report.competitors} />
            )}
            {activeSection === "gaps" && <SectionGaps gaps={report.market_gaps} />}
            {activeSection === "differentiation" && (
              <SectionDifferentiation items={report.differentiation} />
            )}
            {activeSection === "swot" && <SectionSwot swot={report.swot} />}
            {activeSection === "recommendations" && (
              <SectionRecommendations items={report.founder_recommendations} />
            )}
            {activeSection === "sources" && <SectionSources sources={report.sources} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Section: Executive Summary
// ---------------------------------------------------------------------------
function SectionSummary({ report }: { report: StartupResearchReport }) {
  return (
    <div className="space-y-4">
      <SectionHeading>Executive Summary</SectionHeading>
      <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-xl p-4">
        <p className="text-sm text-zinc-300 leading-relaxed">
          {report.executive_summary || "No summary generated."}
        </p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <MetaTile label="Industry" value={report.industry} color="text-purple-400" />
        <MetaTile label="Business Model" value={report.business_model} color="text-brand-400" />
        <MetaTile label="ICP" value={report.icp} color="text-amber-400" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Competitor Landscape
// ---------------------------------------------------------------------------
function SectionCompetitors({ competitors }: { competitors: ResearchCompetitor[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!competitors?.length) {
    return <EmptySection message="No competitors analyzed yet." />;
  }

  return (
    <div className="space-y-4">
      <SectionHeading>Competitor Landscape ({competitors.length} found)</SectionHeading>
      <div className="space-y-2">
        {competitors.map((comp, i) => {
          const isOpen = expanded === comp.domain;
          return (
            <motion.div
              key={comp.domain || i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-zinc-900/40 border border-zinc-800/50 rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setExpanded(isOpen ? null : (comp.domain || String(i)))}
                className="w-full flex items-center gap-3 px-4 py-3.5 text-left hover:bg-zinc-800/30 transition-all"
              >
                {/* Favicon */}
                <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700/50 flex items-center justify-center flex-shrink-0 text-xs font-bold text-zinc-400">
                  {(comp.name || comp.domain || "?")[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-zinc-200">{comp.name || comp.domain}</p>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700/40">
                      {comp.market_positioning || "—"}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 truncate mt-0.5">{comp.description}</p>
                </div>
                <ChevronDown
                  className={cn("w-4 h-4 text-zinc-600 flex-shrink-0 transition-transform", isOpen && "rotate-180")}
                />
              </button>

              {isOpen && (
                <div className="px-4 pb-4 pt-1 border-t border-zinc-800/40 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <InfoBlock label="Target Audience" value={comp.target_audience} />
                    <InfoBlock label="Business Focus" value={comp.business_focus} />
                    <InfoBlock label="Pricing Model" value={comp.pricing_model} />
                  </div>
                  {comp.key_features?.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider mb-1.5">Key Features</p>
                      <div className="flex flex-wrap gap-1.5">
                        {comp.key_features.map((f) => (
                          <span key={f} className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 border border-zinc-700/40 text-zinc-400">
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {comp.strengths?.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider mb-1.5">Strengths</p>
                      <ul className="space-y-1">
                        {comp.strengths.map((s) => (
                          <li key={s} className="text-xs text-zinc-400 flex items-start gap-1.5">
                            <span className="text-emerald-400 mt-0.5">+</span> {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {comp.source_url && (
                    <a
                      href={comp.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-[10px] text-brand-400 hover:text-brand-300 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" /> {comp.source_url.substring(0, 60)}
                    </a>
                  )}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Feature Comparison
// ---------------------------------------------------------------------------
function SectionFeatures({
  rows,
  competitors,
}: {
  rows: StartupResearchReport["feature_comparison"];
  competitors: ResearchCompetitor[];
}) {
  if (!rows?.length) return <EmptySection message="No feature data extracted." />;

  const competitorNames = competitors.map((c) => c.name || c.domain || "").filter(Boolean);

  return (
    <div className="space-y-4">
      <SectionHeading>Feature Comparison</SectionHeading>
      <div className="overflow-x-auto rounded-xl border border-zinc-800/50">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-zinc-900/60 border-b border-zinc-800/50">
              <th className="text-left px-4 py-2.5 text-zinc-500 font-semibold uppercase tracking-wider">Feature</th>
              <th className="px-4 py-2.5 text-purple-400 font-semibold text-center">Your Idea</th>
              {competitorNames.slice(0, 5).map((name) => (
                <th key={name} className="px-4 py-2.5 text-zinc-400 font-semibold text-center truncate max-w-[80px]">
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.feature}
                className={cn(
                  "border-b border-zinc-800/30 transition-colors hover:bg-zinc-800/20",
                  i % 2 === 0 && "bg-zinc-900/20"
                )}
              >
                <td className="px-4 py-2.5 text-zinc-300 font-medium">{row.feature}</td>
                <td className="px-4 py-2.5 text-center text-purple-400 font-semibold">{row.your_idea || "✓"}</td>
                {competitorNames.slice(0, 5).map((name) => (
                  <td key={name} className="px-4 py-2.5 text-center">
                    <span className={row[name] === "✓" ? "text-emerald-400" : "text-zinc-700"}>
                      {row[name] || "—"}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Pricing Analysis
// ---------------------------------------------------------------------------
function SectionPricing({
  pricing,
  competitors,
}: {
  pricing: StartupResearchReport["pricing_analysis"];
  competitors: ResearchCompetitor[];
}) {
  if (!pricing?.length) return <EmptySection message="No pricing data found." />;

  return (
    <div className="space-y-4">
      <SectionHeading>Pricing Intelligence</SectionHeading>
      <div className="space-y-4">
        {pricing.map((entry, i) => {
          const comp = competitors.find(
            (c) => c.name === entry.competitor || c.domain === entry.competitor
          );
          return (
            <div key={i} className="bg-zinc-900/40 border border-zinc-800/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <p className="text-sm font-semibold text-zinc-200">{entry.competitor}</p>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700/40">
                  {entry.model}
                </span>
              </div>
              {entry.tiers?.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {entry.tiers.map((tier, j) => (
                    <div
                      key={j}
                      className="bg-zinc-800/50 border border-zinc-700/40 rounded-lg p-3 space-y-1.5"
                    >
                      <p className="text-xs font-semibold text-zinc-300">{tier.tier}</p>
                      <p className="text-sm font-bold text-brand-400">{tier.price}</p>
                      <ul className="space-y-0.5">
                        {(tier.features || []).slice(0, 3).map((f) => (
                          <li key={f} className="text-[10px] text-zinc-500 flex items-start gap-1">
                            <span className="text-zinc-600 mt-0.5">·</span> {f}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-zinc-600 italic">Pricing not publicly available.</p>
              )}
              {comp?.source_url && (
                <a
                  href={comp.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] text-zinc-600 hover:text-brand-400 mt-2 transition-colors"
                >
                  <ExternalLink className="w-2.5 h-2.5" /> Source
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Positioning Analysis
// ---------------------------------------------------------------------------
function SectionPositioning({
  text,
  competitors,
}: {
  text: string;
  competitors: ResearchCompetitor[];
}) {
  return (
    <div className="space-y-4">
      <SectionHeading>Positioning Analysis</SectionHeading>
      {text ? (
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-xl p-4">
          <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">{text}</p>
        </div>
      ) : (
        <EmptySection message="No positioning analysis generated." />
      )}
      {competitors?.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {competitors.map((c, i) => (
            <div key={i} className="bg-zinc-900/30 border border-zinc-800/40 rounded-lg px-3 py-2.5">
              <p className="text-xs font-semibold text-zinc-300">{c.name || c.domain}</p>
              <p className="text-[10px] text-zinc-500 mt-0.5">{c.market_positioning || "—"}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Market Gaps
// ---------------------------------------------------------------------------
function SectionGaps({ gaps }: { gaps: string[] }) {
  if (!gaps?.length) return <EmptySection message="No market gaps identified." />;

  return (
    <div className="space-y-4">
      <SectionHeading>Market Gaps — Opportunities</SectionHeading>
      <p className="text-xs text-zinc-500">
        These are areas where existing competitors fall short. Each gap is a direct opportunity for differentiation.
      </p>
      <div className="space-y-2">
        {gaps.map((gap, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-start gap-3 bg-amber-500/5 border border-amber-500/15 rounded-xl px-4 py-3"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-zinc-300 leading-snug">{gap}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Differentiation Opportunities
// ---------------------------------------------------------------------------
function SectionDifferentiation({ items }: { items: string[] }) {
  if (!items?.length) return <EmptySection message="No differentiation opportunities identified." />;

  return (
    <div className="space-y-4">
      <SectionHeading>Differentiation Opportunities</SectionHeading>
      <p className="text-xs text-zinc-500">
        Actionable ways to position your startup differently from the competition — based on evidence.
      </p>
      <div className="space-y-2">
        {items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-start gap-3 bg-emerald-500/5 border border-emerald-500/15 rounded-xl px-4 py-3"
          >
            <Lightbulb className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-zinc-300 leading-snug">{item}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: SWOT
// ---------------------------------------------------------------------------
function SectionSwot({ swot }: { swot: StartupResearchReport["swot"] }) {
  if (!swot) return <EmptySection message="No SWOT analysis generated." />;

  const quadrants = [
    { label: "Strengths", items: swot.strengths || [], color: "emerald", icon: "+" },
    { label: "Weaknesses", items: swot.weaknesses || [], color: "rose", icon: "−" },
    { label: "Opportunities", items: swot.opportunities || [], color: "brand", icon: "→" },
    { label: "Threats", items: swot.threats || [], color: "amber", icon: "!" },
  ];

  const colorMap: Record<string, string> = {
    emerald: "border-emerald-500/20 bg-emerald-500/5",
    rose: "border-rose-500/20 bg-rose-500/5",
    brand: "border-brand-500/20 bg-brand-500/5",
    amber: "border-amber-500/20 bg-amber-500/5",
  };
  const textMap: Record<string, string> = {
    emerald: "text-emerald-400",
    rose: "text-rose-400",
    brand: "text-brand-400",
    amber: "text-amber-400",
  };

  return (
    <div className="space-y-4">
      <SectionHeading>SWOT Analysis</SectionHeading>
      <div className="grid grid-cols-2 gap-3">
        {quadrants.map((q) => (
          <div
            key={q.label}
            className={cn("rounded-xl border p-4 space-y-2", colorMap[q.color])}
          >
            <div className="flex items-center gap-2">
              <span className={cn("text-sm font-bold", textMap[q.color])}>{q.icon}</span>
              <p className={cn("text-xs font-semibold uppercase tracking-wider", textMap[q.color])}>
                {q.label}
              </p>
            </div>
            {q.items.length > 0 ? (
              <ul className="space-y-1.5">
                {q.items.map((item, i) => (
                  <li key={i} className="text-xs text-zinc-400 flex items-start gap-1.5 leading-snug">
                    <span className={cn("flex-shrink-0 mt-0.5", textMap[q.color])}>·</span>
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-zinc-600 italic">None identified</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Founder Recommendations
// ---------------------------------------------------------------------------
function SectionRecommendations({ items }: { items: string[] }) {
  if (!items?.length) return <EmptySection message="No recommendations generated." />;

  return (
    <div className="space-y-4">
      <SectionHeading>Founder Recommendations</SectionHeading>
      <p className="text-xs text-zinc-500">
        Practical, evidence-based advice derived from the research — not generic startup guidance.
      </p>
      <div className="space-y-3">
        {items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex items-start gap-3 bg-purple-500/5 border border-purple-500/15 rounded-xl px-4 py-3.5"
          >
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-purple-500/15 border border-purple-500/25 text-purple-400 text-[10px] font-bold flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <p className="text-sm text-zinc-300 leading-snug">{item}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Sources
// ---------------------------------------------------------------------------
function SectionSources({ sources }: { sources: StartupResearchReport["sources"] }) {
  if (!sources?.length) return <EmptySection message="No sources recorded." />;

  const typeColor: Record<string, string> = {
    "Competitor website": "text-brand-400 border-brand-500/20 bg-brand-500/5",
    "Pricing page": "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    "Blog": "text-purple-400 border-purple-500/20 bg-purple-500/5",
    "Documentation": "text-amber-400 border-amber-500/20 bg-amber-500/5",
  };

  return (
    <div className="space-y-4">
      <SectionHeading>Verified Sources ({sources.length})</SectionHeading>
      <p className="text-xs text-zinc-500">
        All information in this report is derived from the following sources. Every major claim is traceable.
      </p>
      <div className="space-y-2">
        {sources.map((src, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="flex items-center gap-3 bg-zinc-900/40 border border-zinc-800/50 rounded-xl px-4 py-3"
          >
            <ExternalLink className="w-3.5 h-3.5 text-zinc-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-zinc-300 truncate">{src.name}</p>
              <a
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] text-zinc-600 hover:text-brand-400 transition-colors truncate block"
              >
                {src.url}
              </a>
            </div>
            <span
              className={cn(
                "text-[10px] px-2 py-0.5 rounded-full border flex-shrink-0",
                typeColor[src.type] || "text-zinc-500 border-zinc-700/40 bg-zinc-800/50"
              )}
            >
              {src.type}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared small components
// ---------------------------------------------------------------------------
function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
      {children}
    </h3>
  );
}

function MetaTile({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-lg px-3 py-2.5">
      <p className="text-[10px] text-zinc-600 uppercase tracking-wider font-semibold">{label}</p>
      <p className={cn("text-xs font-medium mt-0.5", color)}>{value || "—"}</p>
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider">{label}</p>
      <p className="text-xs text-zinc-400 mt-0.5">{value || "—"}</p>
    </div>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-12 text-zinc-600 text-sm">
      {message}
    </div>
  );
}
