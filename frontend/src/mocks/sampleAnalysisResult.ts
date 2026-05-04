import type { AnalysisRequest, AnalysisResult } from "../types/analysis";

export const buildSampleAnalysisResult = (
  request: AnalysisRequest
): AnalysisResult => {
  const role = request.targetRole.trim() || "Senior Backend Engineer";

  return {
    id: "mock-analysis-001",
    source: "mock",
    targetRole: role,
    generatedAt: new Date().toISOString(),
    overallScore: 84,
    recommendation: {
      level: "strong",
      label: "Strong match",
      summary:
        "The resume shows direct backend API, Python, FastAPI, testing, and deployment evidence for the target role."
    },
    dimensionScores: [
      {
        id: "skills",
        label: "Core skills",
        score: 92,
        summary: "Python, FastAPI, REST APIs, PostgreSQL, Docker, and pytest are supported by resume evidence.",
        evidenceCount: 6
      },
      {
        id: "experience",
        label: "Experience",
        score: 88,
        summary: "Six years of backend engineering experience satisfies the seniority requirement.",
        evidenceCount: 3
      },
      {
        id: "domain",
        label: "Domain fit",
        score: 82,
        summary: "Healthcare workflow projects align with the JD domain.",
        evidenceCount: 2
      },
      {
        id: "delivery",
        label: "Delivery readiness",
        score: 76,
        summary: "Deployment and testing evidence is present, but ownership outcomes could be more explicit.",
        evidenceCount: 3
      },
      {
        id: "education",
        label: "Education",
        score: 80,
        summary: "Computer science education aligns with the preferred education signal.",
        evidenceCount: 1
      }
    ],
    strengths: [
      "Direct FastAPI and REST API evidence maps to required platform engineering work.",
      "pytest, Docker, AWS, and PostgreSQL appear in work or skills evidence.",
      "Healthcare workflow context supports domain fit for regulated product teams."
    ],
    gaps: [
      "Impact metrics are limited, so delivery scope is harder to judge.",
      "Leadership and cross-team ownership evidence is implied but not explicit."
    ],
    nextActions: [
      "Add quantified production outcomes for API latency, reliability, or adoption.",
      "Clarify ownership of architecture decisions and stakeholder coordination.",
      "Keep healthcare workflow examples near the top of the resume for this role."
    ],
    evidence: [
      {
        id: "ev-001",
        requirement: "4+ years of backend engineering experience",
        resumeEvidence:
          "Backend engineer with 6 years of experience building Python APIs for healthcare workflow products.",
        status: "matched",
        confidence: 0.96,
        notes: "Duration and backend scope are explicit."
      },
      {
        id: "ev-002",
        requirement: "Strong Python experience",
        resumeEvidence: "Skills include Python and experience deploying Python services.",
        status: "matched",
        confidence: 0.93,
        notes: "Skill and work-history evidence reinforce each other."
      },
      {
        id: "ev-003",
        requirement: "FastAPI or similar modern Python API framework",
        resumeEvidence: "Built FastAPI services for patient scheduling and claims workflows.",
        status: "matched",
        confidence: 0.95,
        notes: "Direct framework match."
      },
      {
        id: "ev-004",
        requirement: "REST API design experience",
        resumeEvidence: "Designed REST APIs used by web and mobile clients.",
        status: "matched",
        confidence: 0.91,
        notes: "Client usage gives useful context."
      },
      {
        id: "ev-005",
        requirement: "Experience writing automated tests with pytest",
        resumeEvidence: "Wrote pytest coverage for service and integration layers.",
        status: "matched",
        confidence: 0.9,
        notes: "Testing tool and layer coverage are both stated."
      },
      {
        id: "ev-006",
        requirement: "Production ownership and measurable impact",
        resumeEvidence: "Deployed Python services to AWS with Docker-based builds.",
        status: "partial",
        confidence: 0.68,
        notes: "Deployment signal exists, but impact metrics are missing."
      },
      {
        id: "ev-007",
        requirement: "Architecture leadership",
        resumeEvidence: "Created a clinic intake automation API using FastAPI and PostgreSQL.",
        status: "gap",
        confidence: 0.42,
        notes: "Project evidence exists, but leadership scope is not stated."
      }
    ],
    gapAnalysis: [
      {
        id: "gap-001",
        missingRequirement: "Quantified production impact",
        severity: "medium",
        whyItMatters:
          "Senior backend roles often evaluate whether the candidate can connect engineering work to product or reliability outcomes.",
        suggestedImprovement:
          "Add metrics such as request volume, latency reduction, deployment frequency, error-rate improvement, or user adoption."
      },
      {
        id: "gap-002",
        missingRequirement: "Architecture decision ownership",
        severity: "high",
        whyItMatters:
          "The JD implies senior-level design judgment, but the resume does not clearly separate implementation from ownership.",
        suggestedImprovement:
          "Add one bullet naming a system design decision, the tradeoff considered, and the result."
      },
      {
        id: "gap-003",
        missingRequirement: "Cross-functional collaboration evidence",
        severity: "low",
        whyItMatters:
          "Healthcare workflow systems usually require coordination with product, compliance, or operations stakeholders.",
        suggestedImprovement:
          "Mention collaboration with product, clinical operations, or compliance teams where accurate."
      }
    ],
    summaryMarkdown: [
      `## CareerFit Summary: ${role}`,
      "",
      "- Overall match score: 84",
      "- Recommendation: Strong match",
      "- Strongest evidence: Python, FastAPI, REST API design, pytest, Docker, AWS, healthcare workflows",
      "- Primary gaps: quantified impact, architecture ownership, cross-functional collaboration",
      "- Next action: add measurable production outcomes and senior ownership evidence"
    ].join("\n")
  };
};
