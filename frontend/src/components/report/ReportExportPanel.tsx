interface ReportExportPanelProps {
  summaryMarkdown: string;
}

export function ReportExportPanel({ summaryMarkdown }: ReportExportPanelProps) {
  const handleCopySummary = async () => {
    await navigator.clipboard.writeText(summaryMarkdown);
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">Report export</h2>
          <p className="mt-1 text-sm text-slate-500">Generated from the current mock analysis.</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            className="inline-flex h-10 items-center justify-center rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800"
            type="button"
            onClick={handleCopySummary}
          >
            Copy summary
          </button>
          <button
            className="inline-flex h-10 items-center justify-center rounded-md border border-slate-300 px-4 text-sm font-semibold text-slate-500"
            type="button"
            disabled
          >
            Export markdown
          </button>
          <button
            className="inline-flex h-10 items-center justify-center rounded-md border border-slate-300 px-4 text-sm font-semibold text-slate-500"
            type="button"
            disabled
          >
            Export PDF
          </button>
        </div>
      </div>
      <pre className="mt-5 max-h-48 overflow-auto rounded-md border border-slate-200 bg-slate-50 p-4 text-xs leading-6 text-slate-700">
        {summaryMarkdown}
      </pre>
    </section>
  );
}
