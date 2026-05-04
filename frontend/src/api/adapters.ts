import type {
  AnalysisRequest,
  AnalysisResult,
  DimensionScore,
  EvidenceComparisonRow,
  GapAnalysisItem,
  MatchStatus,
  Recommendation,
  Severity
} from "../types/analysis";

interface BackendEvidenceSpan {
  source_document: string;
  section: string;
  text: string;
  start_char?: number | null;
  end_char?: number | null;
  normalized_value?: string | null;
  explanation: string;
}

interface BackendRequirementMatch {
  requirement_id: string;
  requirement_label: string;
  normalized_label: string;
  requirement_priority: string;
  requirement_type: string;
  status: string;
  explanation: string;
  resume_evidence: BackendEvidenceSpan[];
  jd_evidence: BackendEvidenceSpan[];
}

interface BackendGapItem {
  requirement_id: string;
  requirement_label: string;
  requirement_priority: string;
  gap_type: string;
  explanation: string;
  resume_evidence: BackendEvidenceSpan[];
  jd_evidence: BackendEvidenceSpan[];
}

interface BackendDimensionScores {
  skills: number;
  experience: number;
  projects: number;
  domain_fit: number;
  education: number;
}

interface BackendBlockerFlags {
  missing_required_skills: boolean;
  seniority_mismatch: boolean;
  unsupported_claims: boolean;
}

interface BackendEvidenceSummary {
  total_evidence_spans: number;
  resume_evidence_spans: number;
  jd_evidence_spans: number;
  required_match_count: number;
  preferred_match_count: number;
  gap_count: number;
}

interface BackendAdaptationSummary {
  role_focus: string;
  company_signals: string[];
  emphasized_requirements: string[];
  prioritized_strengths: string[];
  prioritized_gaps: string[];
  explanation: string;
}

export interface BackendMatchResponse {
  overall_score: number;
  dimension_scores: BackendDimensionScores;
  required_matches: BackendRequirementMatch[];
  preferred_matches: BackendRequirementMatch[];
  gaps: BackendGapItem[];
  blocker_flags: BackendBlockerFlags;
  strengths?: string[];
  explanations?: string[];
  evidence_summary: BackendEvidenceSummary;
  adaptation_summary: BackendAdaptationSummary;
}

const dimensionLabels: Array<{
  key: keyof BackendDimensionScores;
  label: string;
}> = [
  { key: "skills", label: "Core skills" },
  { key: "experience", label: "Experience" },
  { key: "projects", label: "Projects" },
  { key: "domain_fit", label: "Domain fit" },
  { key: "education", label: "Education" }
];

export function adaptMatchResponse(
  response: BackendMatchResponse,
  request: AnalysisRequest
): AnalysisResult {
  const allMatches = [...response.required_matches, ...response.preferred_matches];
  const recommendation = buildRecommendation(response);
  const strengths = buildStrengths(response, allMatches);
  const gapSummaries = buildGapSummaries(response);
  const nextActions = buildNextActions(response);

  return {
    id: `backend-analysis-${Date.now()}`,
    source: "backend",
    targetRole: request.targetRole.trim() || response.adaptation_summary.role_focus || "Target role",
    generatedAt: new Date().toISOString(),
    overallScore: response.overall_score,
    recommendation,
    dimensionScores: adaptDimensionScores(response, allMatches),
    strengths,
    gaps: gapSummaries,
    nextActions,
    evidence: allMatches.map((match) => adaptEvidenceRow(match)),
    gapAnalysis: response.gaps.map((gap) => adaptGapItem(gap)),
    summaryMarkdown: buildSummaryMarkdown(response, request, recommendation, gapSummaries)
  };
}

function adaptDimensionScores(
  response: BackendMatchResponse,
  allMatches: BackendRequirementMatch[]
): DimensionScore[] {
  return dimensionLabels.map(({ key, label }) => ({
    id: key,
    label,
    score: response.dimension_scores[key],
    summary: summarizeDimension(key, response.dimension_scores[key]),
    evidenceCount: countEvidenceForDimension(key, allMatches)
  }));
}

function summarizeDimension(key: keyof BackendDimensionScores, score: number): string {
  const label = dimensionLabels.find((item) => item.key === key)?.label ?? key;

  if (score >= 80) {
    return `${label} is strongly supported by backend evidence.`;
  }

  if (score >= 50) {
    return `${label} is partially supported and should be reviewed.`;
  }

  return `${label} has limited supporting evidence in the current resume.`;
}

function countEvidenceForDimension(
  key: keyof BackendDimensionScores,
  allMatches: BackendRequirementMatch[]
): number {
  const typesByDimension: Record<keyof BackendDimensionScores, string[]> = {
    skills: ["skill"],
    experience: ["experience", "seniority"],
    projects: ["project"],
    domain_fit: ["domain"],
    education: ["education"]
  };

  return allMatches.filter((match) =>
    typesByDimension[key].includes(match.requirement_type)
  ).length;
}

function adaptEvidenceRow(match: BackendRequirementMatch): EvidenceComparisonRow {
  return {
    id: match.requirement_id,
    requirement: evidenceText(match.jd_evidence) || match.requirement_label,
    resumeEvidence: evidenceText(match.resume_evidence) || "No resume evidence found.",
    status: adaptMatchStatus(match.status),
    confidence: displayConfidence(match),
    notes: match.explanation
  };
}

function adaptGapItem(gap: BackendGapItem): GapAnalysisItem {
  return {
    id: gap.requirement_id,
    missingRequirement: gap.requirement_label,
    severity: severityForGap(gap),
    whyItMatters: gap.explanation,
    suggestedImprovement: suggestedImprovement(gap)
  };
}

function adaptMatchStatus(status: string): MatchStatus {
  if (status === "matched") {
    return "matched";
  }

  if (status === "partial") {
    return "partial";
  }

  return "gap";
}

function displayConfidence(match: BackendRequirementMatch): number {
  if (match.status === "matched") {
    return 0.92;
  }

  if (match.status === "partial") {
    return 0.64;
  }

  return match.resume_evidence.length > 0 ? 0.42 : 0.28;
}

function evidenceText(spans: BackendEvidenceSpan[]): string {
  return spans
    .map((span) => span.text.trim())
    .filter(Boolean)
    .join(" ");
}

function severityForGap(gap: BackendGapItem): Severity {
  if (gap.requirement_priority === "required") {
    return "high";
  }

  if (gap.gap_type === "missing_evidence" || gap.gap_type === "seniority_mismatch") {
    return "medium";
  }

  return "low";
}

function suggestedImprovement(gap: BackendGapItem): string {
  if (gap.resume_evidence.length > 0) {
    return `Clarify the existing ${gap.requirement_label} evidence with specific scope, tools, and outcomes.`;
  }

  return `Add accurate resume evidence for ${gap.requirement_label}, or leave it out if the experience is not present.`;
}

function buildRecommendation(response: BackendMatchResponse): Recommendation {
  const hasBlocker = Object.values(response.blocker_flags).some(Boolean);

  if (response.overall_score >= 80 && !hasBlocker) {
    return {
      level: "strong",
      label: "Strong match",
      summary: "Backend scoring found a strong fit with no active blocker flags."
    };
  }

  if (response.overall_score >= 50 && !response.blocker_flags.missing_required_skills) {
    return {
      level: "review",
      label: "Review recommended",
      summary: "Backend scoring found a partial fit. Review gaps and weaker evidence before submission."
    };
  }

  return {
    level: "risk",
    label: "High-risk match",
    summary: "Backend scoring found material gaps or blocker flags that should be addressed first."
  };
}

function buildStrengths(
  response: BackendMatchResponse,
  allMatches: BackendRequirementMatch[]
): string[] {
  if (response.strengths?.length) {
    return response.strengths;
  }

  if (response.adaptation_summary.prioritized_strengths.length) {
    return response.adaptation_summary.prioritized_strengths;
  }

  return allMatches
    .filter((match) => match.status === "matched")
    .slice(0, 3)
    .map((match) => match.explanation);
}

function buildGapSummaries(response: BackendMatchResponse): string[] {
  if (response.gaps.length > 0) {
    return response.gaps.slice(0, 3).map((gap) => gap.explanation);
  }

  return ["No major required gaps were returned by the backend."];
}

function buildNextActions(response: BackendMatchResponse): string[] {
  const prioritizedGaps = response.adaptation_summary.prioritized_gaps;

  if (prioritizedGaps.length > 0) {
    return prioritizedGaps.map(
      (gap) => `Strengthen resume evidence for ${gap} with accurate examples and outcomes.`
    );
  }

  if (response.gaps.length > 0) {
    return response.gaps
      .slice(0, 3)
      .map((gap) => suggestedImprovement(gap));
  }

  return ["Use the evidence table to keep the strongest matched requirements prominent."];
}

function buildSummaryMarkdown(
  response: BackendMatchResponse,
  request: AnalysisRequest,
  recommendation: Recommendation,
  gaps: string[]
): string {
  return [
    `## CareerFit Summary: ${request.targetRole.trim() || "Target role"}`,
    "",
    `- Overall match score: ${response.overall_score}`,
    `- Recommendation: ${recommendation.label}`,
    `- Required matches: ${response.evidence_summary.required_match_count}`,
    `- Preferred matches: ${response.evidence_summary.preferred_match_count}`,
    `- Gap count: ${response.evidence_summary.gap_count}`,
    `- Primary gaps: ${gaps.join(" ")}`
  ].join("\n");
}
