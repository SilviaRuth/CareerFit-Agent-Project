export type MatchStatus = "matched" | "partial" | "gap";

export type RecommendationLevel = "strong" | "review" | "risk";

export type Severity = "high" | "medium" | "low";

export interface AnalysisRequest {
  resumeText: string;
  jobDescriptionText: string;
  targetRole: string;
  resumeFileName?: string;
  jobDescriptionFileName?: string;
}

export interface Recommendation {
  level: RecommendationLevel;
  label: string;
  summary: string;
}

export interface DimensionScore {
  id: string;
  label: string;
  score: number;
  summary: string;
  evidenceCount: number;
}

export interface EvidenceComparisonRow {
  id: string;
  requirement: string;
  resumeEvidence: string;
  status: MatchStatus;
  confidence: number;
  notes: string;
}

export interface GapAnalysisItem {
  id: string;
  missingRequirement: string;
  severity: Severity;
  whyItMatters: string;
  suggestedImprovement: string;
}

export interface AnalysisResult {
  id: string;
  source: "backend" | "mock";
  targetRole: string;
  generatedAt: string;
  overallScore: number;
  recommendation: Recommendation;
  dimensionScores: DimensionScore[];
  strengths: string[];
  gaps: string[];
  nextActions: string[];
  evidence: EvidenceComparisonRow[];
  gapAnalysis: GapAnalysisItem[];
  summaryMarkdown: string;
}
