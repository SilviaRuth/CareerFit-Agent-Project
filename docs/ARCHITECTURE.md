# ARCHITECTURE.md

## 1. Overview

JD Matching Agent is an AI-first system that evaluates the fit between a candidate resume and a job description (JD), then produces:

- structured match scores
- evidence-backed gap analysis
- resume improvement suggestions
- interview preparation points
- optional rewritten resume bullets aligned to the JD

The system is designed as a modular pipeline rather than a single prompt wrapper.  
Core principle: **retrieval + structured analysis + controllable generation + transparent evidence**.

---

## 2. Product Goals

### Primary Goals
1. Parse resume and JD into structured representations.
2. Compare candidate signals against job requirements.
3. Produce interpretable fit analysis with evidence.
4. Identify skill gaps and priority improvements.
5. Generate actionable outputs for job application workflows.

### Secondary Goals
1. Support multiple resume versions for different roles.
2. Track changes across JD variants.
3. Allow recruiter-style and candidate-style views.
4. Provide reusable evaluation data for future tuning.

---

## 3. Non-Goals

At the current stage, this project does **not** aim to:
- replace ATS systems
- guarantee hiring outcomes
- fully automate final resume submission
- scrape job sites at scale
- make legal claims about discrimination or fairness compliance

---

## 4. High-Level Architecture

```text
User Input
 ├─ Resume (PDF/DOCX/TXT)
 ├─ Job Description (URL/TXT/PDF)
 └─ Optional metadata (target role, seniority, location)

        ↓

[Ingestion Layer]
 ├─ Resume parser
 ├─ JD parser
 ├─ Text cleaner
 └─ Document normalizer

        ↓

[Structuring Layer]
 ├─ Resume schema extraction
 ├─ JD schema extraction
 ├─ Skill/entity extraction
 ├─ Experience normalization
 └─ Requirement classification

        ↓

[Matching Engine]
 ├─ Lexical matching
 ├─ Semantic matching
 ├─ Rule-based scoring
 ├─ Evidence linking
 └─ Gap detection

        ↓

[Reasoning / Agent Layer]
 ├─ Orchestrator
 ├─ Analysis prompts
 ├─ Resume rewrite module
 ├─ Interview prep module
 └─ Learning recommendation module

        ↓

[Output Layer]
 ├─ Match score summary
 ├─ Strengths
 ├─ Gaps
 ├─ Resume rewrite suggestions
 ├─ Interview question suggestions
 └─ Traceable evidence / citations

````

---

## 5. Core Modules

### 5.1 Ingestion Layer

Responsible for collecting and normalizing raw inputs.

#### Inputs

* resume files
* JD text or URLs
* optional portfolio/project links

#### Responsibilities

* parse PDF/DOCX/TXT safely
* preserve section boundaries where possible
* normalize whitespace, bullets, headers
* detect likely resume sections:

  * summary
  * education
  * skills
  * experience
  * projects
  * certifications

#### Design Notes

* keep raw text and cleaned text separately
* record parser confidence / parsing warnings
* do not over-compress formatting too early

---

### 5.2 Structuring Layer

Transforms unstructured text into a canonical schema.

#### Resume schema example

```json
{
  "candidate_name": "",
  "target_roles": [],
  "skills": [],
  "experience_items": [],
  "project_items": [],
  "education_items": [],
  "certifications": []
}
```

#### JD schema example

```json
{
  "job_title": "",
  "company": "",
  "required_skills": [],
  "preferred_skills": [],
  "responsibilities": [],
  "experience_requirements": [],
  "education_requirements": [],
  "keywords": []
}
```

#### Responsibilities

* extract technical skills
* identify role level and domain
* classify requirements into:

  * required
  * preferred
  * implied
* normalize synonyms:

  * NLP ↔ Natural Language Processing
  * IR ↔ Information Retrieval
  * LLM apps ↔ GenAI applications

#### Design Notes

* use deterministic normalization before LLM inference
* maintain both original span and normalized label
* make extraction auditable

---

### 5.3 Matching Engine

The analytical core of the system.

#### Subcomponents

1. **Lexical matcher**

   * keyword overlap
   * exact phrase detection
   * section-aware scoring

2. **Semantic matcher**

   * embedding-based similarity
   * project-to-requirement relevance
   * experience-to-responsibility alignment

3. **Rule-based scorer**

   * required skill missing penalties
   * preferred skill soft bonuses
   * seniority mismatch adjustments
   * domain-specific weighting

4. **Evidence linker**

   * map each claim to a resume span
   * avoid unsupported praise or criticism

5. **Gap detector**

   * identify absent, weak, or unclear qualifications
   * separate “missing skill” from “missing evidence”

#### Output

```json
{
  "overall_score": 0,
  "dimension_scores": {
    "skills": 0,
    "experience": 0,
    "projects": 0,
    "education": 0,
    "domain_fit": 0
  },
  "matched_evidence": [],
  "gaps": [],
  "risk_flags": []
}
```

---

### 5.4 Reasoning / Agent Layer

Coordinates multi-step analysis and generation.

#### Responsibilities

* decide which tools/modules to invoke
* produce final fit narrative
* rewrite resume bullets aligned to JD
* generate interview prep content
* suggest learning priorities

#### Agent Design Principles

* evidence first, generation second
* no generated claim without source span
* keep chain modular:

  1. extract
  2. score
  3. diagnose
  4. improve
  5. present

#### Recommended Agent Pattern

Use a lightweight orchestrator, not an over-engineered multi-agent swarm in v1.

Suggested internal agents/modules:

* Parser Agent
* Schema Extraction Agent
* Match Analysis Agent
* Resume Rewrite Agent
* Interview Prep Agent

But implementation-wise, keep them as callable modules/functions first.

---

## 6. Data Flow

### Step 1: Input normalization

Resume and JD are parsed into normalized text artifacts.

### Step 2: Schema extraction

The system converts both documents into structured JSON representations.

### Step 3: Candidate-JD alignment

Requirements are matched against:

* skills
* work experience
* projects
* education
* other signals

### Step 4: Scoring and evidence generation

Each score dimension is backed by evidence spans.

### Step 5: Actionable output generation

The system produces:

* fit summary
* strong matches
* weak matches
* missing signals
* resume bullet improvements
* interview prep focus areas

---

## 7. Recommended Tech Stack

### Core Application

* Python
* FastAPI
* Pydantic
* Uvicorn

### Parsing

* PyMuPDF / pdfplumber
* python-docx
* BeautifulSoup (if JD URLs are supported)

### NLP / ML

* sentence-transformers
* scikit-learn
* optional transformers
* optional spaCy for NER / phrase extraction

### Storage

* local JSON for v1
* SQLite or Postgres later
* vector store optional in v1, useful in v2

### Frontend

* Streamlit for fast prototype
  or
* Next.js + FastAPI for portfolio-grade build

### Evaluation / Experimentation

* pandas
* pytest
* custom evaluation JSONL datasets
* optional MLflow / Weights & Biases later

---

## 8. Suggested Folder Structure

```text
project-root/
├─ app/
│  ├─ api/
│  ├─ core/
│  ├─ schemas/
│  ├─ services/
│  ├─ agents/
│  └─ utils/
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ CODE_REVIEW.md
│  ├─ ROADMAP.md
│  └─ DECISIONS.md
├─ data/
│  ├─ samples/
│  ├─ eval/
│  └─ outputs/
├─ tests/
├─ scripts/
├─ notebooks/
├─ README.md
├─ requirements.txt
└─ pyproject.toml
```

More detailed application split:

```text
app/
├─ api/
│  └─ routes/
├─ schemas/
│  ├─ resume.py
│  ├─ jd.py
│  └─ match_result.py
├─ services/
│  ├─ parser_service.py
│  ├─ extraction_service.py
│  ├─ matching_service.py
│  └─ rewrite_service.py
├─ agents/
│  └─ orchestrator.py
├─ core/
│  ├─ config.py
│  └─ logging.py
└─ utils/
   └─ text_cleaning.py
```

---

## 9. API Surface (Proposed)

### `POST /parse/resume`

Parse and structure a resume.

### `POST /parse/jd`

Parse and structure a JD.

### `POST /match`

Return score, evidence, and gaps.

### `POST /rewrite`

Generate JD-aligned resume bullet improvements.

### `POST /interview-prep`

Generate likely interview topics and preparation points.

### `GET /health`

Health check.

---

## 10. Scoring Strategy

The overall score should not be a black box.

### Example weighted dimensions

* skill match: 30%
* experience relevance: 30%
* project relevance: 20%
* domain alignment: 10%
* education / credentials: 10%

### Important rule

A high overall score must still show critical blockers, for example:

* required skill missing
* years of experience gap
* domain mismatch
* no evidence for claimed skill

### Output style

Instead of only giving:

* “82/100”

Return:

* score
* explanation
* confidence
* blocker flags
* evidence spans

---

## 11. Evaluation Plan

### Offline evaluation dataset

Create a small benchmark set:

* 10 resumes
* 10 JDs
* annotated expected fit levels
* annotated required-skill matches
* annotated top gap reasons

### Metrics

* extraction accuracy
* skill match precision/recall
* score consistency
* explanation usefulness
* rewrite quality
* hallucination rate

### Manual review questions

* Is each criticism grounded?
* Is each suggestion actionable?
* Does the score roughly match human judgment?
* Are important missing requirements surfaced early?

---

## 12. Risks

### Product Risks

* oversimplified scoring
* misleading confidence
* ATS-style keyword gaming

### Technical Risks

* poor PDF parsing
* brittle skill extraction
* semantic overmatching
* hallucinated rewrite outputs

### Mitigations

* span-based evidence
* deterministic pre-processing
* rule-based checks around LLM outputs
* evaluation set before feature expansion

---

## 13. Roadmap

### Phase 1: Foundation

* project skeleton
* parsing
* schemas
* basic matching
* JSON outputs

### Phase 2: Usable MVP

* API endpoints
* scoring explanation
* resume rewrite
* simple UI

### Phase 3: Strong Portfolio Version

* evaluation benchmark
* richer evidence tracing
* multiple resume version support
* company / role adaptation
* analytics dashboard

### Phase 4: Advanced Agent Features

* learning plan generation
* interview simulation alignment
* cross-JD comparison
* profile memory and recommendation loop

---

## 14. Key Design Decisions

1. Build a pipeline first, not a prompt soup.
2. Keep extraction and scoring separable.
3. Prefer explainability over flashy output.
4. Use LLMs where they add leverage, not where rules are enough.
5. Make every recommendation traceable to source evidence.

