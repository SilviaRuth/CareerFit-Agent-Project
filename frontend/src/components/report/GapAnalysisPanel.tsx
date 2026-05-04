import type { GapAnalysisItem, Severity } from "../../types/analysis";

interface GapAnalysisPanelProps {
  gaps: GapAnalysisItem[];
}

const severityStyles: Record<Severity, string> = {
  high: "border-rose-200 bg-rose-50 text-rose-800",
  medium: "border-amber-200 bg-amber-50 text-amber-800",
  low: "border-slate-200 bg-slate-50 text-slate-700"
};

export function GapAnalysisPanel({ gaps }: GapAnalysisPanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-base font-semibold text-slate-950">Gap analysis</h2>
        <span className="text-sm text-slate-500">{gaps.length} prioritized items</span>
      </div>

      {gaps.length === 0 ? (
        <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
          No missing requirements were found.
        </div>
      ) : (
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {gaps.map((gap) => (
            <article className="rounded-lg border border-slate-200 p-4" key={gap.id}>
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-sm font-semibold leading-6 text-slate-950">
                  {gap.missingRequirement}
                </h3>
                <span
                  className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize ${severityStyles[gap.severity]}`}
                >
                  {gap.severity}
                </span>
              </div>
              <div className="mt-4 space-y-4 text-sm leading-6 text-slate-600">
                <div>
                  <p className="font-semibold text-slate-800">Why it matters</p>
                  <p className="mt-1">{gap.whyItMatters}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-800">Suggested improvement</p>
                  <p className="mt-1">{gap.suggestedImprovement}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
