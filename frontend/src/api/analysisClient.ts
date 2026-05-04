import { buildSampleAnalysisResult } from "../mocks/sampleAnalysisResult";
import type { AnalysisRequest, AnalysisResult } from "../types/analysis";
import { adaptMatchResponse, type BackendMatchResponse } from "./adapters";

const MOCK_LATENCY_MS = 850;
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || DEFAULT_API_BASE_URL
);

const useMockAnalysis = import.meta.env.VITE_USE_MOCK_ANALYSIS === "true";

interface BackendMatchRequest {
  resume_text: string;
  job_description_text: string;
}

export const runMockAnalysis = async (
  request: AnalysisRequest
): Promise<AnalysisResult> => {
  await new Promise((resolve) => window.setTimeout(resolve, MOCK_LATENCY_MS));
  return buildSampleAnalysisResult(request);
};

export const runMatchAnalysis = async (
  request: AnalysisRequest
): Promise<AnalysisResult> => {
  if (useMockAnalysis) {
    return runMockAnalysis(request);
  }

  const payload: BackendMatchRequest = {
    resume_text: request.resumeText,
    job_description_text: request.jobDescriptionText
  };

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/match`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
  } catch {
    throw new Error(
      `Backend unavailable at ${apiBaseUrl}. Start the FastAPI server or set VITE_USE_MOCK_ANALYSIS=true for demo mode.`
    );
  }

  if (!response.ok) {
    throw new Error(await backendErrorMessage(response));
  }

  const data = (await response.json()) as BackendMatchResponse;
  return adaptMatchResponse(data, request);
};

const backendErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through to the generic status message.
  }

  return `Backend request failed with HTTP ${response.status}.`;
};
