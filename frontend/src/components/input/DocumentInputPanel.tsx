import { ChangeEvent } from "react";

interface DocumentInputPanelProps {
  title: string;
  label: string;
  value: string;
  fileName?: string;
  error?: string;
  disabled?: boolean;
  onTextChange: (value: string) => void;
  onFileLoaded: (fileName: string, text: string) => void;
}

const readTextFile = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });

export function DocumentInputPanel({
  title,
  label,
  value,
  fileName,
  error,
  disabled,
  onTextChange,
  onFileLoaded
}: DocumentInputPanelProps) {
  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const text = await readTextFile(file);
    onFileLoaded(file.name, text);
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">{title}</h2>
          {fileName ? (
            <p className="mt-1 text-sm text-slate-500">Loaded file: {fileName}</p>
          ) : null}
        </div>
        <label className="inline-flex cursor-pointer items-center justify-center rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
          Upload text
          <input
            className="sr-only"
            type="file"
            accept=".txt,.md,.csv"
            disabled={disabled}
            onChange={handleFileChange}
          />
        </label>
      </div>

      <label className="mt-5 block text-sm font-medium text-slate-700" htmlFor={label}>
        {label}
      </label>
      <textarea
        id={label}
        className="mt-2 min-h-72 w-full resize-y rounded-md border border-slate-300 bg-white px-3 py-3 text-sm leading-6 text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:border-teal-700 focus:ring-0 disabled:bg-slate-100"
        value={value}
        disabled={disabled}
        placeholder="Paste content here."
        onChange={(event) => onTextChange(event.target.value)}
      />
      <div className="mt-2 flex items-center justify-between gap-3 text-xs">
        <span className={error ? "font-medium text-rose-700" : "text-slate-500"}>
          {error ?? `${value.trim().length.toLocaleString()} characters`}
        </span>
        <span className="text-slate-400">TXT and pasted text supported in this mock UI</span>
      </div>
    </section>
  );
}
