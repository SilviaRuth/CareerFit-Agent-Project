import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { AnalysisResult, RecommendationLevel } from "../../types/analysis";

interface AnalysisDashboardProps {
  result: AnalysisResult;
}

const recommendationStyles: Record<RecommendationLevel, string> = {
  strong: "border-teal-200 bg-teal-50 text-teal-800",
  review: "border-amber-200 bg-amber-50 text-amber-800",
  risk: "border-rose-200 bg-rose-50 text-rose-800"
};

export function AnalysisDashboard({ result }: AnalysisDashboardProps) {
  return (
    <section className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-slate-500">Overall match</p>
            <div className="mt-3 flex items-end gap-2">
              <span className="text-6xl font-semibold leading-none text-slate-950">
                {result.overallScore}
              </span>
              <span className="pb-2 text-lg font-semibold text-slate-500">/ 100</span>
            </div>
          </div>
          <span
            className={`rounded-full border px-3 py-1 text-sm font-semibold ${recommendationStyles[result.recommendation.level]}`}
          >
            {result.recommendation.label}
          </span>
        </div>
        <p className="mt-5 text-sm leading-6 text-slate-600">{result.recommendation.summary}</p>
        <dl className="mt-6 grid grid-cols-2 gap-3">
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Evidence rows
            </dt>
            <dd className="mt-2 text-2xl font-semibold text-slate-950">{result.evidence.length}</dd>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Gap items
            </dt>
            <dd className="mt-2 text-2xl font-semibold text-slate-950">
              {result.gapAnalysis.length}
            </dd>
          </div>
        </dl>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold text-slate-950">Dimension scores</h2>
          <span className="text-sm text-slate-500">{result.targetRole}</span>
        </div>
        <div className="mt-5 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={result.dimensionScores}
              margin={{ top: 8, right: 12, bottom: 8, left: -18 }}
            >
              <CartesianGrid stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: "#475569", fontSize: 12 }} tickLine={false} />
              <Tooltip
                cursor={{ fill: "#f1f5f9" }}
                contentStyle={{
                  border: "1px solid #cbd5e1",
                  borderRadius: 8,
                  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.12)"
                }}
              />
              <Bar dataKey="score" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid gap-4 xl:col-span-2 md:grid-cols-2 xl:grid-cols-5">
        {result.dimensionScores.map((dimension) => (
          <article
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-panel"
            key={dimension.id}
          >
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-slate-950">{dimension.label}</h3>
              <span className="text-lg font-semibold text-slate-950">{dimension.score}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">{dimension.summary}</p>
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-slate-500">
              {dimension.evidenceCount} evidence signals
            </p>
          </article>
        ))}
      </div>

      <div className="grid gap-6 xl:col-span-2 lg:grid-cols-3">
        <InsightList title="Strengths" items={result.strengths} tone="teal" />
        <InsightList title="Gaps" items={result.gaps} tone="amber" />
        <InsightList title="Next actions" items={result.nextActions} tone="slate" />
      </div>
    </section>
  );
}

interface InsightListProps {
  title: string;
  items: string[];
  tone: "teal" | "amber" | "slate";
}

const listDotStyles: Record<InsightListProps["tone"], string> = {
  teal: "bg-teal-600",
  amber: "bg-amber-500",
  slate: "bg-slate-600"
};

function InsightList({ title, items, tone }: InsightListProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <h2 className="text-base font-semibold text-slate-950">{title}</h2>
      <ul className="mt-4 space-y-3">
        {items.map((item) => (
          <li className="flex gap-3 text-sm leading-6 text-slate-700" key={item}>
            <span className={`mt-2 h-2 w-2 shrink-0 rounded-full ${listDotStyles[tone]}`} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
