import { buildSampleAnalysisResult } from "../mocks/sampleAnalysisResult";
import type { AnalysisRequest, AnalysisResult } from "../types/analysis";

const MOCK_LATENCY_MS = 850;

export const runMockAnalysis = async (
  request: AnalysisRequest
): Promise<AnalysisResult> => {
  await new Promise((resolve) => window.setTimeout(resolve, MOCK_LATENCY_MS));
  return buildSampleAnalysisResult(request);
};
