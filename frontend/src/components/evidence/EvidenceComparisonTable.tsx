import type { EvidenceComparisonRow, MatchStatus } from "../../types/analysis";

interface EvidenceComparisonTableProps {
  rows: EvidenceComparisonRow[];
}

const statusStyles: Record<MatchStatus, string> = {
  matched: "border-teal-200 bg-teal-50 text-teal-800",
  partial: "border-amber-200 bg-amber-50 text-amber-800",
  gap: "border-rose-200 bg-rose-50 text-rose-800"
};

const statusLabels: Record<MatchStatus, string> = {
  matched: "Matched",
  partial: "Partial",
  gap: "Gap"
};

export function EvidenceComparisonTable({ rows }: EvidenceComparisonTableProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-950">Evidence comparison</h2>
      </div>

      {rows.length === 0 ? (
        <div className="px-5 py-12 text-center text-sm text-slate-500">
          No evidence rows are available.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-[960px] divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">JD requirement</th>
                <th className="px-5 py-3">Resume evidence</th>
                <th className="px-5 py-3">Match status</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {rows.map((row) => (
                <tr className="align-top" key={row.id}>
                  <td className="max-w-xs px-5 py-4 font-medium leading-6 text-slate-950">
                    {row.requirement}
                  </td>
                  <td className="max-w-md px-5 py-4 leading-6 text-slate-700">
                    {row.resumeEvidence}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusStyles[row.status]}`}
                    >
                      {statusLabels[row.status]}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex min-w-28 items-center gap-2">
                      <div className="h-2 flex-1 rounded-full bg-slate-100">
                        <div
                          className="h-2 rounded-full bg-teal-700"
                          style={{ width: `${Math.round(row.confidence * 100)}%` }}
                        />
                      </div>
                      <span className="w-10 text-right font-medium text-slate-700">
                        {Math.round(row.confidence * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="max-w-sm px-5 py-4 leading-6 text-slate-600">{row.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
