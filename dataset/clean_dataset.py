from __future__ import annotations

import csv
import json
import re
import shutil
from collections import OrderedDict
from dataclasses import dataclass
from html import unescape
from pathlib import Path

from lxml import html

DATASET_DIR = Path(__file__).resolve().parent
RAW_JD_PATH = DATASET_DIR / "JD.md"
RAW_RESUME_PATH = DATASET_DIR / "Resume.csv"

JD_CLEANED_MD_PATH = DATASET_DIR / "JD.cleaned.md"
JD_CLEANED_CSV_PATH = DATASET_DIR / "JD.cleaned.csv"
JD_TEXT_DIR = DATASET_DIR / "jd_cleaned"

RESUME_CLEANED_CSV_PATH = DATASET_DIR / "Resume.cleaned.csv"
RESUME_TEXT_DIR = DATASET_DIR / "resume_cleaned"

REPORT_PATH = DATASET_DIR / "cleaning_report.json"


TITLE_ALIASES = {
    "summary": "summary",
    "professional summary": "summary",
    "career summary": "summary",
    "profile": "summary",
    "objective": "summary",
    "skills": "skills",
    "highlights": "skills",
    "core qualifications": "skills",
    "core competencies": "skills",
    "technical skills": "skills",
    "areas of expertise": "skills",
    "qualifications": "skills",
    "experience": "experience",
    "work history": "experience",
    "employment history": "experience",
    "professional experience": "experience",
    "career history": "experience",
    "education": "education",
    "education and training": "education",
    "education & certifications": "education",
    "education and certifications": "education",
    "certifications": "education",
    "projects": "projects",
    "selected projects": "projects",
    "project highlights": "projects",
}

SKIPPED_SECTION_TITLES = {
    "accomplishments",
    "activities and honors",
    "activities",
    "affiliations",
    "additional information",
    "awards",
    "languages",
    "interests",
    "references",
    "volunteer experience",
    "professional memberships",
}

PLACEHOLDER_VALUES = {
    "",
    "company name",
    "city",
    "state",
    "country",
    "name",
    "n/a",
}

MOJIBAKE_REPLACEMENTS = {
    "\u00a0": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2009": " ",
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2022": "-",
    "\u2023": "-",
    "\u2043": "-",
    "\u2219": "-",
    "\u25aa": "-",
    "\u25cf": "-",
    "\u25e6": "-",
    "\uff1a": ":",
    "\u2026": "...",
    "鈥檚": "'s",
    "鈥檝e": "'ve",
    "鈥檙e": "'re",
    "鈥檓": "'m",
    "鈥檒l": "'ll",
    "鈥擜": "-",
    "鈥攁": "-",
    "鈥�": '"',
    "鈥": "'",
    "â€¢": "-",
    "â€“": "-",
    "â€”": "-",
    "â€™": "'",
    "â€œ": '"',
    "â€\x9d": '"',
    "�": "",
}


@dataclass
class CleanedJD:
    category: str
    sample_number: int
    job_title: str
    company: str
    responsibilities: list[str]
    required: list[str]
    preferred: list[str]
    education: list[str]

    @property
    def slug(self) -> str:
        return f"{slugify(self.category)}_{self.sample_number:02d}_{slugify(self.job_title)}"

    def to_canonical_text(self) -> str:
        lines = [self.job_title, self.company, "", "Responsibilities"]
        lines.extend(f"- {item}" for item in self.responsibilities)
        lines.extend(["", "Required"])
        lines.extend(f"- {item}" for item in self.required)
        if self.preferred:
            lines.extend(["", "Preferred"])
            lines.extend(f"- {item}" for item in self.preferred)
        if self.education:
            lines.extend(["", "Education"])
            lines.extend(f"- {item}" for item in self.education)
        return "\n".join(lines).strip() + "\n"


@dataclass
class CleanedResume:
    resume_id: str
    category: str
    candidate_name: str
    cleaned_text: str
    summary_present: bool
    skills_present: bool
    experience_present: bool
    education_present: bool
    projects_present: bool

    @property
    def usable_for_parser(self) -> bool:
        return self.summary_present and self.skills_present and self.experience_present

    @property
    def slug(self) -> str:
        return f"{slugify(self.category)}_{slugify(self.resume_id)}"


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    text = unescape(value)
    for source, target in MOJIBAKE_REPLACEMENTS.items():
        text = text.replace(source, target)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\[[0-9]+\]", "", text)
    text = re.sub(r"\s*\(\[[^)]+\]\)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -\t\n")


def slugify(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "item"


def clean_bullet(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"^[*-]\s*", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text.strip()


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = clean_bullet(item)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def unique_text_blocks(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if not item or not item.strip():
            continue
        key = normalize_text(item).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def cleaned_non_placeholder(value: str | None) -> str:
    text = normalize_text(value)
    return "" if text.lower() in PLACEHOLDER_VALUES else text


def reset_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def parse_jd_markdown(path: Path) -> list[CleanedJD]:
    lines = path.read_text(encoding="utf-8").splitlines()
    category = ""
    current: dict[str, object] | None = None
    section: str | None = None
    results: list[CleanedJD] = []

    def finalize(sample: dict[str, object] | None) -> None:
        if not sample:
            return
        responsibilities = unique_preserve_order(sample.get("responsibilities", []))  # type: ignore[arg-type]
        raw_requirements = unique_preserve_order(sample.get("requirements", []))  # type: ignore[arg-type]
        required: list[str] = []
        preferred: list[str] = []
        education: list[str] = []
        for requirement in raw_requirements:
            lower_value = requirement.lower()
            if looks_like_education_requirement(lower_value):
                education.append(strip_preferred_marker(requirement))
            elif "preferred" in lower_value or "nice to have" in lower_value:
                preferred.append(strip_preferred_marker(requirement))
            else:
                required.append(requirement)
        cleaned_jd = CleanedJD(
            category=normalize_text(sample["category"]),  # type: ignore[index]
            sample_number=int(sample["sample_number"]),  # type: ignore[arg-type]
            job_title=normalize_text(sample["job_title"]),  # type: ignore[index]
            company=f"Sample {title_case_category(normalize_text(sample['category']))} Company",  # type: ignore[index]
            responsibilities=responsibilities,
            required=required,
            preferred=preferred,
            education=education,
        )
        if cleaned_jd.job_title and cleaned_jd.required:
            results.append(cleaned_jd)

    for raw_line in lines:
        line = normalize_text(raw_line)
        if not line:
            continue
        if line.startswith("## "):
            finalize(current)
            category = line[3:].strip()
            current = None
            section = None
            continue
        if line.startswith("### JD Sample"):
            finalize(current)
            sample_number_match = re.search(r"(\d+)", line)
            current = {
                "category": category,
                "sample_number": int(sample_number_match.group(1)) if sample_number_match else 0,
                "job_title": "",
                "responsibilities": [],
                "requirements": [],
            }
            section = None
            continue
        if current is None:
            continue
        if line.startswith("**Position:**"):
            current["job_title"] = re.sub(r"^\*\*Position:\*\*\s*", "", line).strip()
            continue
        if line.startswith("**Responsibilities:**"):
            section = "responsibilities"
            continue
        if line.startswith("**Requirements:**"):
            section = "requirements"
            continue
        if line.startswith("**Preferred"):
            section = "requirements"
            continue
        if line == "---":
            finalize(current)
            current = None
            section = None
            continue
        if line.startswith("*") and section in {"responsibilities", "requirements"}:
            bullet = clean_bullet(line)
            if bullet:
                current[section].append(bullet)  # type: ignore[index]

    finalize(current)
    return results


def looks_like_education_requirement(value: str) -> bool:
    return any(
        token in value
        for token in (
            "bachelor",
            "master",
            "phd",
            "degree",
            "diploma",
            "associate",
            "high school",
            "llb",
            "juris doctor",
            "md",
            "computer science",
        )
    )


def strip_preferred_marker(value: str) -> str:
    cleaned = re.sub(r"\((preferred|optional)\)", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bpreferred\b", "", cleaned, flags=re.IGNORECASE)
    return clean_bullet(cleaned)


def title_case_category(value: str) -> str:
    lower = normalize_text(value).replace("(", "").replace(")", "")
    parts = re.split(r"[-/ ]+", lower)
    return " ".join(part.capitalize() for part in parts if part)


def write_cleaned_jds(jds: list[CleanedJD]) -> None:
    reset_output_dir(JD_TEXT_DIR)
    markdown_lines = ["# Cleaned JD Dataset", ""]
    with JD_CLEANED_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "category",
                "sample_number",
                "job_title",
                "company",
                "required_count",
                "preferred_count",
                "education_count",
                "responsibility_count",
                "txt_path",
            ],
        )
        writer.writeheader()
        for jd in jds:
            category_dir = JD_TEXT_DIR / slugify(jd.category)
            category_dir.mkdir(parents=True, exist_ok=True)
            txt_path = category_dir / f"{jd.slug}.txt"
            txt_path.write_text(jd.to_canonical_text(), encoding="utf-8")

            writer.writerow(
                {
                    "category": jd.category,
                    "sample_number": jd.sample_number,
                    "job_title": jd.job_title,
                    "company": jd.company,
                    "required_count": len(jd.required),
                    "preferred_count": len(jd.preferred),
                    "education_count": len(jd.education),
                    "responsibility_count": len(jd.responsibilities),
                    "txt_path": str(txt_path.relative_to(DATASET_DIR)),
                }
            )

            markdown_lines.extend(
                [
                    f"## {jd.category}",
                    "",
                    f"### JD Sample {jd.sample_number}",
                    "",
                    f"Position: {jd.job_title}",
                    f"Company: {jd.company}",
                    "",
                    "Responsibilities:",
                ]
            )
            markdown_lines.extend(f"- {item}" for item in jd.responsibilities)
            markdown_lines.extend(["", "Required:"])
            markdown_lines.extend(f"- {item}" for item in jd.required)
            if jd.preferred:
                markdown_lines.extend(["", "Preferred:"])
                markdown_lines.extend(f"- {item}" for item in jd.preferred)
            if jd.education:
                markdown_lines.extend(["", "Education:"])
                markdown_lines.extend(f"- {item}" for item in jd.education)
            markdown_lines.extend(["", "---", ""])

    JD_CLEANED_MD_PATH.write_text("\n".join(markdown_lines).strip() + "\n", encoding="utf-8")


def parse_resume_html(raw_html: str, resume_id: str) -> CleanedResume:
    document = html.fromstring(raw_html or "<div></div>")
    section_store: OrderedDict[str, list[str]] = OrderedDict(
        (
            ("summary", []),
            ("skills", []),
            ("experience", []),
            ("projects", []),
            ("education", []),
        )
    )

    for section in document.xpath("//div[contains(@class, 'section')]"):
        title_nodes = section.xpath(".//div[contains(@class, 'sectiontitle')]")
        if not title_nodes:
            continue
        raw_title = normalize_text(title_nodes[0].text_content()).lower()
        if raw_title in SKIPPED_SECTION_TITLES:
            continue
        canonical_title = TITLE_ALIASES.get(raw_title)
        if canonical_title is None:
            continue
        if canonical_title == "summary":
            summary = extract_summary_section(section)
            if summary:
                section_store["summary"].append(summary)
        elif canonical_title == "skills":
            section_store["skills"].extend(extract_skills_section(section))
        elif canonical_title == "experience":
            section_store["experience"].extend(extract_experience_section(section))
        elif canonical_title == "education":
            section_store["education"].extend(extract_education_section(section))
        elif canonical_title == "projects":
            section_store["projects"].extend(extract_project_section(section))

    summary_text = " ".join(unique_text_blocks(section_store["summary"]))
    skills = unique_preserve_order(section_store["skills"])
    experience = unique_text_blocks(section_store["experience"])
    projects = unique_text_blocks(section_store["projects"])
    education = unique_text_blocks(section_store["education"])

    lines = [f"Candidate {resume_id}"]
    if summary_text:
        lines.extend(["", "Summary", summary_text])
    if skills:
        lines.extend(["", "Skills", ", ".join(skills)])
    if experience:
        lines.extend(["", "Experience"])
        for block in experience:
            lines.extend(block.split("\n"))
            lines.append("")
        if lines[-1] == "":
            lines.pop()
    if projects:
        lines.extend(["", "Projects"])
        lines.extend(f"- {item}" for item in projects)
    if education:
        lines.extend(["", "Education"])
        for block in education:
            lines.extend(block.split("\n"))
            lines.append("")
        if lines[-1] == "":
            lines.pop()

    cleaned_text = "\n".join(lines).strip() + "\n"
    return CleanedResume(
        resume_id=resume_id,
        category="",
        candidate_name=f"Candidate {resume_id}",
        cleaned_text=cleaned_text,
        summary_present=bool(summary_text),
        skills_present=bool(skills),
        experience_present=bool(experience),
        education_present=bool(education),
        projects_present=bool(projects),
    )


def extract_summary_section(section) -> str:
    parts: list[str] = []
    nodes = section.xpath(".//p | .//li")
    if not nodes:
        nodes = section.xpath(
            ".//div[contains(@class, 'field')] | .//span[contains(@class, 'field')]"
        )
    for node in nodes:
        text = normalize_text(node.text_content())
        if not text or text.lower() == "summary":
            continue
        parts.append(text)
    return " ".join(unique_text_blocks(parts))


def extract_skills_section(section) -> list[str]:
    collected: list[str] = []
    nodes = section.xpath(".//li | .//p")
    if not nodes:
        nodes = section.xpath(
            ".//div[contains(@class, 'field')] | .//td[contains(@class, 'field')]"
        )
    for node in nodes:
        text = normalize_text(node.text_content())
        if not text or text.lower() == "skills":
            continue
        collected.extend(split_skill_like_text(text))
    return unique_preserve_order(collected)


def split_skill_like_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    normalized = normalized.replace("  ", "\n")
    pieces = re.split(r",|\n|[;|]+", normalized)
    return [clean_bullet(piece) for piece in pieces if clean_bullet(piece)]


def extract_experience_section(section) -> list[str]:
    blocks: list[str] = []
    paragraphs = section.xpath(".//div[contains(@class, 'paragraph')]")
    for paragraph in paragraphs:
        title = cleaned_non_placeholder(
            extract_role_title(paragraph.xpath(".//span[contains(@class, 'jobtitle')]"))
        )
        if not title:
            continue
        company = cleaned_non_placeholder(
            first_text(
                paragraph.xpath(
                    ".//span[contains(@class, 'companyname') and not(contains(@class, 'educ'))]"
                )
            )
        )
        if not company:
            company = "Redacted Company"
        heading_parts = [title, company]
        date_values = [
            normalize_text(value)
            for value in paragraph.xpath(".//span[contains(@class, 'jobdates')]/text()")
        ]
        year_range = build_year_range(date_values)
        if year_range:
            heading_parts.append(year_range)
        heading = ", ".join(part for part in heading_parts if part)

        details = [
            clean_bullet(item.text_content())
            for item in paragraph.xpath(".//span[contains(@class, 'jobline')]//li")
        ]
        if not details:
            fallback = cleaned_non_placeholder(
                first_text(paragraph.xpath(".//span[contains(@class, 'jobline')]"))
            )
            if fallback:
                details = split_sentences(fallback)

        detail_lines = [f"- {item}" for item in unique_preserve_order(details)]
        block_lines = [heading]
        block_lines.extend(detail_lines)
        blocks.append("\n".join(block_lines))
    return unique_text_blocks(blocks)


def build_year_range(date_values: list[str]) -> str:
    years: list[str] = []
    current = False
    for value in date_values:
        if not value:
            continue
        if "current" in value.lower() or "present" in value.lower():
            current = True
        match = re.search(r"(19|20)\d{2}", value)
        if match:
            years.append(match.group(0))
    if len(years) >= 2:
        return f"{years[0]}-{years[1]}"
    if len(years) == 1 and current:
        return f"{years[0]}-Present"
    if len(years) == 1:
        return years[0]
    return "Present" if current else ""


def extract_education_section(section) -> list[str]:
    blocks: list[str] = []
    paragraphs = section.xpath(".//div[contains(@class, 'paragraph')]")
    for paragraph in paragraphs:
        degree = cleaned_non_placeholder(
            first_text(paragraph.xpath(".//span[contains(@class, 'degree')]"))
        )
        program = cleaned_non_placeholder(
            first_text(paragraph.xpath(".//span[contains(@class, 'programline')]"))
        )
        school = cleaned_non_placeholder(
            first_text(
                paragraph.xpath(
                    ".//span[contains(@class, 'companyname') and contains(@class, 'educ')]"
                )
            )
        )
        year = cleaned_non_placeholder(
            first_text(paragraph.xpath(".//span[contains(@class, 'jobdates')]"))
        )
        field = cleaned_non_placeholder(
            first_text(paragraph.xpath(".//span[contains(@class, 'field')]"))
        )

        summary_parts = []
        if degree and program:
            summary_parts.append(f"{degree} in {program}")
        elif degree:
            summary_parts.append(degree)
        elif program:
            summary_parts.append(program)
        if school:
            summary_parts.append(school)
        if year:
            summary_parts.append(year)
        if field and field.lower() not in {
            degree.lower() if degree else "",
            program.lower() if program else "",
        }:
            summary_parts.append(field)
        summary = ", ".join(part for part in summary_parts if part)
        if summary:
            blocks.append(summary)
    return unique_text_blocks(blocks)


def extract_project_section(section) -> list[str]:
    items: list[str] = []
    for node in section.xpath(".//li | .//p | .//div[contains(@class, 'field')]"):
        text = normalize_text(node.text_content())
        if text:
            items.append(text)
    return unique_text_blocks(items)


def extract_role_title(nodes: list) -> str:
    for node in nodes:
        raw_text = unescape(node.text_content() or "")
        parts = [
            normalize_text(part) for part in re.split(r"\n+", raw_text) if normalize_text(part)
        ]
        if not parts:
            continue
        if len(parts) == 1:
            return parts[0]
        first_part = parts[0]
        if all(part.lower() in first_part.lower() for part in parts[1:]):
            return first_part
        return " / ".join(unique_text_blocks(parts))
    return ""


def first_text(nodes: list) -> str:
    for node in nodes:
        text = normalize_text(node.text_content())
        if text:
            return text
    return ""


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", normalize_text(text))
    return [part.strip() for part in parts if part.strip()]


def write_cleaned_resumes(path: Path) -> list[CleanedResume]:
    reset_output_dir(RESUME_TEXT_DIR)
    cleaned_rows: list[CleanedResume] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cleaned = parse_resume_html(row.get("Resume_html", ""), row.get("ID", "").strip())
            cleaned.category = normalize_text(row.get("Category", ""))
            cleaned_rows.append(cleaned)

            category_dir = RESUME_TEXT_DIR / slugify(cleaned.category or "uncategorized")
            category_dir.mkdir(parents=True, exist_ok=True)
            txt_path = category_dir / f"{cleaned.slug}.txt"
            txt_path.write_text(cleaned.cleaned_text, encoding="utf-8")

    with RESUME_CLEANED_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "ID",
                "Category",
                "Candidate_name",
                "summary_present",
                "skills_present",
                "experience_present",
                "education_present",
                "projects_present",
                "usable_for_parser",
                "txt_path",
                "cleaned_resume_text",
            ],
        )
        writer.writeheader()
        for cleaned in cleaned_rows:
            writer.writerow(
                {
                    "ID": cleaned.resume_id,
                    "Category": cleaned.category,
                    "Candidate_name": cleaned.candidate_name,
                    "summary_present": cleaned.summary_present,
                    "skills_present": cleaned.skills_present,
                    "experience_present": cleaned.experience_present,
                    "education_present": cleaned.education_present,
                    "projects_present": cleaned.projects_present,
                    "usable_for_parser": cleaned.usable_for_parser,
                    "txt_path": str(
                        (
                            RESUME_TEXT_DIR
                            / slugify(cleaned.category or "uncategorized")
                            / f"{cleaned.slug}.txt"
                        ).relative_to(DATASET_DIR)
                    ),
                    "cleaned_resume_text": cleaned.cleaned_text.strip(),
                }
            )
    return cleaned_rows


def write_report(jds: list[CleanedJD], resumes: list[CleanedResume]) -> None:
    categories = sorted({jd.category for jd in jds})
    report = {
        "jd_samples": len(jds),
        "jd_categories": len(categories),
        "resume_rows": len(resumes),
        "usable_resume_rows": sum(item.usable_for_parser for item in resumes),
        "resume_with_summary": sum(item.summary_present for item in resumes),
        "resume_with_skills": sum(item.skills_present for item in resumes),
        "resume_with_experience": sum(item.experience_present for item in resumes),
        "resume_with_education": sum(item.education_present for item in resumes),
        "outputs": {
            "jd_cleaned_md": str(JD_CLEANED_MD_PATH.relative_to(DATASET_DIR)),
            "jd_cleaned_csv": str(JD_CLEANED_CSV_PATH.relative_to(DATASET_DIR)),
            "jd_text_dir": str(JD_TEXT_DIR.relative_to(DATASET_DIR)),
            "resume_cleaned_csv": str(RESUME_CLEANED_CSV_PATH.relative_to(DATASET_DIR)),
            "resume_text_dir": str(RESUME_TEXT_DIR.relative_to(DATASET_DIR)),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> None:
    cleaned_jds = parse_jd_markdown(RAW_JD_PATH)
    write_cleaned_jds(cleaned_jds)
    cleaned_resumes = write_cleaned_resumes(RAW_RESUME_PATH)
    write_report(cleaned_jds, cleaned_resumes)


if __name__ == "__main__":
    main()
