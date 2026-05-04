import { FormEvent, useMemo, useState } from "react";
import { runMatchAnalysis } from "../api/analysisClient";
import { DocumentInputPanel } from "../components/input/DocumentInputPanel";
import type { AnalysisRequest, AnalysisResult } from "../types/analysis";

interface InputPageProps {
  onAnalysisComplete: (result: AnalysisResult) => void;
}

interface ValidationErrors {
  resumeText?: string;
  jobDescriptionText?: string;
  targetRole?: string;
}

const MIN_TEXT_LENGTH = 80;

export function InputPage({ onAnalysisComplete }: InputPageProps) {
  const [resumeText, setResumeText] = useState("");
  const [jobDescriptionText, setJobDescriptionText] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [resumeFileName, setResumeFileName] = useState<string | undefined>();
  const [jobDescriptionFileName, setJobDescriptionFileName] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | undefined>();

  const validationErrors = useMemo<ValidationErrors>(() => {
    const errors: ValidationErrors = {};

    if (resumeText.trim().length > 0 && resumeText.trim().length < MIN_TEXT_LENGTH) {
      errors.resumeText = "Resume content is too short for analysis.";
    }

    if (
      jobDescriptionText.trim().length > 0 &&
      jobDescriptionText.trim().length < MIN_TEXT_LENGTH
    ) {
      errors.jobDescriptionText = "Job description content is too short for analysis.";
    }

    if (targetRole.trim().length > 0 && targetRole.trim().length < 3) {
      errors.targetRole = "Target role needs at least 3 characters.";
    }

    return errors;
  }, [jobDescriptionText, resumeText, targetRole]);

  const canSubmit =
    resumeText.trim().length >= MIN_TEXT_LENGTH &&
    jobDescriptionText.trim().length >= MIN_TEXT_LENGTH &&
    targetRole.trim().length >= 3 &&
    Object.keys(validationErrors).length === 0 &&
    !isLoading;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError(undefined);

    if (!canSubmit) {
      setSubmitError("Add a resume, job description, and target role before running analysis.");
      return;
    }

    const request: AnalysisRequest = {
      resumeText,
      jobDescriptionText,
      targetRole,
      resumeFileName,
      jobDescriptionFileName
    };

    setIsLoading(true);
    try {
      const result = await runMatchAnalysis(request);
      onAnalysisComplete(result);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Analysis failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <form className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8" onSubmit={handleSubmit}>
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">CareerFit Agent</p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-950 sm:text-3xl">
              Resume to JD analysis
            </h1>
          </div>

          <div className="grid gap-2 sm:min-w-96">
            <label className="text-sm font-medium text-slate-700" htmlFor="target-role">
              Target role
            </label>
            <input
              id="target-role"
              className="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-950 shadow-sm placeholder:text-slate-400 focus:border-teal-700 disabled:bg-slate-100"
              value={targetRole}
              disabled={isLoading}
              placeholder="Senior Backend Engineer"
              onChange={(event) => setTargetRole(event.target.value)}
            />
            {validationErrors.targetRole ? (
              <p className="text-xs font-medium text-rose-700">{validationErrors.targetRole}</p>
            ) : null}
          </div>
        </header>

        {submitError ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
            {submitError}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-2">
          <DocumentInputPanel
            title="Resume"
            label="Resume content"
            value={resumeText}
            fileName={resumeFileName}
            error={validationErrors.resumeText}
            disabled={isLoading}
            onTextChange={setResumeText}
            onFileLoaded={(fileName, text) => {
              setResumeFileName(fileName);
              setResumeText(text);
            }}
          />
          <DocumentInputPanel
            title="Job description"
            label="Job description content"
            value={jobDescriptionText}
            fileName={jobDescriptionFileName}
            error={validationErrors.jobDescriptionText}
            disabled={isLoading}
            onTextChange={setJobDescriptionText}
            onFileLoaded={(fileName, text) => {
              setJobDescriptionFileName(fileName);
              setJobDescriptionText(text);
            }}
          />
        </div>

        <footer className="sticky bottom-0 z-10 -mx-4 border-t border-slate-200 bg-white/95 px-4 py-4 shadow-panel backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-slate-600">
              {isLoading
                ? "Running backend analysis..."
                : canSubmit
                  ? "Ready to analyze with the backend API."
                  : "Complete the required fields to continue."}
            </div>
            <button
              className="inline-flex h-11 items-center justify-center rounded-md bg-slate-950 px-5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
              type="submit"
              disabled={!canSubmit}
            >
              {isLoading ? "Analyzing..." : "Run Analysis"}
            </button>
          </div>
        </footer>
      </form>
    </main>
  );
}
