# CODE_REVIEW.md

## 1. Purpose

This document defines the code review standard for the JD Matching Agent project.

Goals:
- maintain clean architecture
- reduce hidden technical debt
- keep logic explainable
- ensure generated outputs are grounded
- make the repo collaboration-friendly for both humans and coding agents

---

## 2. Review Priorities

Review in this order:

1. Correctness
2. Evidence / grounding
3. Maintainability
4. Architectural fit
5. Testability
6. Performance
7. Style / naming

A clean-looking PR that breaks evidence traceability is not acceptable.

---

## 3. General Review Rules

### Must-have qualities
- single responsibility per module
- clear function boundaries
- typed interfaces where practical
- minimal hidden side effects
- explicit error handling
- deterministic behavior for critical paths

### Avoid
- giant files
- giant functions
- business logic inside route handlers
- prompt strings scattered everywhere
- magic numbers without explanation
- duplicated parsing / matching logic
- silent fallback behavior

---

## 4. PR Size Guideline

Preferred PR size:
- small to medium
- one concern per PR

Avoid PRs that combine:
- parser refactor
- API changes
- prompt redesign
- scoring changes
- UI updates

in a single merge request.

---

## 5. Architecture Review Checklist

### Reviewer should ask:
- Does this change fit the intended module boundary?
- Is domain logic placed in `services/` rather than API routes?
- Are schemas updated if the contract changed?
- Does the change preserve evidence traceability?
- Does this introduce coupling that will slow future iteration?

### Red flags
- route handler doing extraction + scoring + formatting directly
- one service depending on internals of another service
- output schema changing without documentation
- LLM call added without validation guardrails

---

## 6. Python Code Standards

### Functions
Prefer:
- short functions
- clear inputs/outputs
- explicit return types for core logic

Bad sign:
- one function doing parse + normalize + score + generate text

### Classes
Use classes only when they improve state organization or extensibility.  
Do not introduce classes just to look “enterprise”.

### Naming
Use names that reflect domain meaning:
- `extract_resume_schema`
- `match_requirements`
- `build_gap_report`

Avoid vague names:
- `process_data`
- `handle_all`
- `do_match`

---

## 7. Schema and Contract Review

All structured outputs must be contract-driven.

### Review questions
- Is the schema documented?
- Are optional fields truly optional?
- Are field names stable and unambiguous?
- Is downstream compatibility preserved?

### Rule
If JSON output changes, update:
- schema definition
- tests
- docs if public-facing behavior changed

---

## 8. LLM / Prompt Review

This project is not allowed to become prompt-chaos.

### Requirements
- prompts must live in dedicated files or prompt modules
- prompt inputs must be structured and explicit
- outputs should be validated
- critical reasoning outputs must be grounded in evidence spans

### Review questions
- Is the prompt too vague?
- Does it encourage unsupported claims?
- Is there a deterministic post-check?
- Can the output be validated against schema or rules?

### Red flags
- “just ask the model to score fit”
- no extraction layer before generation
- no source evidence attached to claims
- prompt logic embedded directly in API route code

---

## 9. Matching Logic Review

Since matching is the product core, changes here need extra scrutiny.

### Reviewer should verify:
- required vs preferred requirements are handled differently
- missing evidence is not confused with missing skill
- score dimensions are interpretable
- weights are documented
- rule changes are justified

### Mandatory for scoring changes
Any change to scoring logic should include:
- rationale
- sample before/after behavior
- updated tests or fixtures

---

## 10. Testing Expectations

### Minimum expectations by change type

#### Parser changes
- test on at least one clean input
- test on at least one messy input
- verify section extraction does not regress badly

#### Schema extraction changes
- test field presence
- test normalization behavior
- test edge cases for missing sections

#### Matching changes
- test required skill match
- test preferred skill match
- test missing evidence case
- test blocker flag behavior

#### Generation changes
- test schema validity
- test evidence presence
- manually inspect at least 3 outputs before merge

---

## 11. Error Handling Review

Errors must be informative and bounded.

### Good
- explicit parsing failure message
- structured validation errors
- logging with context
- graceful failure for partial parsing

### Bad
- blanket `except Exception`
- silent return of empty results
- fallback values that hide actual failures

---

## 12. Logging and Observability

Review whether the code:
- logs important stage transitions
- logs parse failures and validation failures
- avoids leaking secrets
- makes debugging easy

Useful log events:
- file parsed
- schema extraction complete
- match scoring complete
- generation validation failed
- fallback path triggered

---

## 13. Performance Review

Performance matters, but not before correctness.

### Reviewer should check
- unnecessary repeated embedding calls
- duplicate parsing
- large model calls where rules would suffice
- wasteful full-document reprocessing

### Rule
Do not prematurely optimize away readability in v1.

---

## 14. Security / Safety Review

Check for:
- unsafe file handling
- unbounded file uploads
- prompt injection from JD URLs or malformed text
- unsanitized HTML rendering
- secrets committed into code or config

### Rule
Never trust raw job posting text or uploaded documents.

---

## 15. Documentation Review

A code change is not complete if future-you cannot understand it.

Update docs when relevant:
- README
- ARCHITECTURE.md
- DECISIONS.md
- API examples
- test fixtures / sample outputs

---

## 16. Review Comments Style

Comments should be:
- specific
- actionable
- tied to risk or maintainability
- respectful but direct

Prefer:
- “Move this scoring rule into `matching_service.py` so route handlers stay thin.”
- “This output field needs schema validation because downstream logic assumes it exists.”

Avoid:
- “This feels weird.”
- “Can you clean this up?”
- “Maybe improve structure.”

---

## 17. Merge Criteria

A PR is mergeable when:
- functionality is correct
- architecture remains coherent
- tests are adequate for the change
- docs/contracts are updated if needed
- no major grounding or evidence issues remain

A PR should not merge if:
- scoring logic changed without tests
- LLM output is unvalidated
- output contract changed silently
- business logic was pushed into the wrong layer
- reviewer cannot trace why the system reached its conclusion

---

## 18. Project-Specific Golden Rules

1. Evidence before polish.
2. Parsing and matching are core assets; protect them.
3. Do not hide uncertainty behind confident wording.
4. Keep the system modular enough for future agentization.
5. Favor explicitness over cleverness.
6. Every “AI” behavior should be reviewable by a human.