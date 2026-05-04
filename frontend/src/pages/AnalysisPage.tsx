import { AnalysisDashboard } from "../components/dashboard/AnalysisDashboard";
import { EvidenceComparisonTable } from "../components/evidence/EvidenceComparisonTable";
import { GapAnalysisPanel } from "../components/report/GapAnalysisPanel";
import { ReportExportPanel } from "../components/report/ReportExportPanel";
import type { AnalysisResult } from "../types/analysis";

interface AnalysisPageProps {
  result: AnalysisResult;
  onStartOver: () => void;
}

export function AnalysisPage({ result, onStartOver }: AnalysisPageProps) {
  const generated = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(result.generatedAt));

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
              Mock analysis report
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-950 sm:text-3xl">
              {result.targetRole}
            </h1>
            <p className="mt-2 text-sm text-slate-500">Generated {generated}</p>
          </div>
          <button
            className="inline-flex h-10 items-center justify-center rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            type="button"
            onClick={onStartOver}
          >
            New analysis
          </button>
        </header>

        <AnalysisDashboard result={result} />
        <EvidenceComparisonTable rows={result.evidence} />
        <GapAnalysisPanel gaps={result.gapAnalysis} />
        <ReportExportPanel summaryMarkdown={result.summaryMarkdown} />
      </div>
    </main>
  );
}
