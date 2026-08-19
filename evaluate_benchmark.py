import json
import shutil
from pathlib import Path


MODEL_SLUG = "qwen3_4b_instruct"

MANIFEST_PATH = Path(
    "data/benchmark/manifest.json"
)

JOBS_DIR = Path(
    "data/benchmark/jobs"
)

LOCAL_RESULTS_DIR = Path(
    f"data/benchmark/results/{MODEL_SLUG}"
)

DRIVE_RESULTS_DIR = Path(
    f"/content/drive/MyDrive/"
    f"job-market-analyzer-results/{MODEL_SLUG}"
)

REPORT_PATH = (
    LOCAL_RESULTS_DIR
    / "benchmark_review.md"
)

SUMMARY_PATH = (
    LOCAL_RESULTS_DIR
    / "benchmark_review_summary.json"
)

SOURCE_TEXT_LIMIT = 3500


CORE_ROLES = {
    "data_scientist",
    "data_analyst",
    "machine_learning_engineer",
    "ai_engineer",
}

ADJACENT_ROLES = {
    "data_engineer",
    "bi_analyst",
    "nlp_engineer",
    "computer_vision_engineer",
    "llm_engineer",
}


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def find_processed_path(job_id):
    candidates = [
        (
            LOCAL_RESULTS_DIR
            / "processed"
            / f"job_{job_id}.json"
        ),
        (
            DRIVE_RESULTS_DIR
            / "processed"
            / f"job_{job_id}.json"
        ),
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"Processed result not found "
        f"for job {job_id}"
    )


def get_benchmark_label(item):
    candidate_keys = [
        "benchmark_type",
        "case_type",
        "case",
        "group",
        "label",
        "category",
        "type",
    ]

    for key in candidate_keys:
        value = item.get(key)

        if value:
            return str(value)

    return "unspecified"


def format_experience(value):
    if value is None:
        return "-"

    if isinstance(value, dict):
        parts = []

        for key, item in value.items():
            if item not in (
                None,
                "",
                [],
            ):
                parts.append(
                    f"{key}={item}"
                )

        return "; ".join(parts) or "-"

    return str(value)


def format_software(items):
    if not items:
        return "-"

    output = []

    for item in items:
        if isinstance(item, dict):
            name = (
                item.get("name")
                or item.get("software")
                or item.get("raw_name")
                or "unknown"
            )

            level = (
                item.get("level")
                or item.get("raw_level")
                or "unspecified"
            )

            output.append(
                f"{name} ({level})"
            )
        else:
            output.append(str(item))

    return ", ".join(output)


def build_source_excerpt(job):
    sections = []

    for key in [
        "key_requirements",
        "job_description",
        "job_requirements",
    ]:
        value = job.get(key)

        if not value:
            continue

        if isinstance(value, list):
            value = "\n".join(
                str(x)
                for x in value
            )

        sections.append(
            f"[{key}]\n{value}"
        )

    text = "\n\n".join(sections)

    if len(text) > SOURCE_TEXT_LIMIT:
        text = (
            text[:SOURCE_TEXT_LIMIT]
            + "\n...[truncated]"
        )

    return text or "-"


def expected_group_for_role(role):
    if role in CORE_ROLES:
        return "core"

    if role in ADJACENT_ROLES:
        return "adjacent"

    if role == "other":
        return "irrelevant"

    return None


def find_structural_flags(analysis):
    flags = []

    role = (
        analysis
        .get("role_classification", {})
        .get("primary_role")
    )

    target_group = (
        analysis
        .get("role_classification", {})
        .get("target_group")
    )

    relevance = (
        analysis
        .get("role_classification", {})
        .get("relevance_score")
    )

    skills = analysis.get(
        "skills",
        [],
    )

    responsibilities = analysis.get(
        "responsibilities",
        [],
    )

    engineering = analysis.get(
        "engineering_expectations",
        [],
    )

    expected_group = (
        expected_group_for_role(role)
    )

    if (
        expected_group
        and target_group != expected_group
    ):
        flags.append(
            "role/target_group mismatch"
        )

    if not skills:
        flags.append(
            "no skills extracted"
        )

    canonical_names = [
        str(
            skill.get(
                "canonical_name",
                ""
            )
        ).casefold()
        for skill in skills
    ]

    if len(canonical_names) != len(
        set(canonical_names)
    ):
        flags.append(
            "duplicate canonical skills"
        )

    for skill in skills:
        name = str(
            skill.get(
                "canonical_name",
                ""
            )
        )

        if "_" in name:
            flags.append(
                "non-normalized skill name"
            )
            break

    if (
        target_group == "core"
        and relevance is not None
        and relevance < 50
    ):
        flags.append(
            "core role with low relevance"
        )

    if (
        target_group == "irrelevant"
        and relevance is not None
        and relevance > 50
    ):
        flags.append(
            "irrelevant role with high relevance"
        )

    if not responsibilities:
        flags.append(
            "no responsibilities extracted"
        )

    if not engineering:
        flags.append(
            "no engineering expectations"
        )

    return flags


def build_job_summary(
    manifest_item,
    job,
    analysis,
):
    classification = analysis.get(
        "role_classification",
        {},
    )

    experience = analysis.get(
        "experience",
        {},
    )

    confidence = analysis.get(
        "confidence",
        {},
    )

    return {
        "job_id": job["job_id"],
        "title": job.get("title"),
        "benchmark_label": (
            get_benchmark_label(
                manifest_item
            )
        ),
        "primary_role": (
            classification.get(
                "primary_role"
            )
        ),
        "secondary_roles": (
            classification.get(
                "secondary_roles",
                [],
            )
        ),
        "target_group": (
            classification.get(
                "target_group"
            )
        ),
        "relevance_score": (
            classification.get(
                "relevance_score"
            )
        ),
        "seniority": analysis.get(
            "seniority"
        ),
        "min_experience": (
            experience.get(
                "min_years"
            )
        ),
        "max_experience": (
            experience.get(
                "max_years"
            )
        ),
        "skills_count": len(
            analysis.get(
                "skills",
                [],
            )
        ),
        "responsibilities_count": len(
            analysis.get(
                "responsibilities",
                [],
            )
        ),
        "engineering_count": len(
            analysis.get(
                "engineering_expectations",
                [],
            )
        ),
        "role_confidence": (
            confidence.get(
                "role_classification"
            )
        ),
        "seniority_confidence": (
            confidence.get(
                "seniority"
            )
        ),
        "flags": (
            find_structural_flags(
                analysis
            )
        ),
    }


def build_markdown_report(
    records,
):
    lines = []

    lines.append(
        "# Benchmark Review"
    )
    lines.append("")
    lines.append(
        f"Model: `{MODEL_SLUG}`"
    )
    lines.append("")

    lines.append(
        "## Compact Summary"
    )
    lines.append("")

    lines.append(
        "| ID | Title | Benchmark | "
        "Role | Group | Rel. | "
        "Senior | Skills | Resp. | "
        "Eng. | Flags |"
    )

    lines.append(
        "|---|---|---|---|---|---:|"
        "---|---:|---:|---:|---|"
    )

    for record in records:
        summary = record["summary"]

        flags = ", ".join(
            summary["flags"]
        ) or "-"

        title = (
            summary["title"]
            or "-"
        ).replace(
            "|",
            "/",
        )

        lines.append(
            f"| {summary['job_id']} "
            f"| {title} "
            f"| {summary['benchmark_label']} "
            f"| {summary['primary_role']} "
            f"| {summary['target_group']} "
            f"| {summary['relevance_score']} "
            f"| {summary['seniority']} "
            f"| {summary['skills_count']} "
            f"| {summary['responsibilities_count']} "
            f"| {summary['engineering_count']} "
            f"| {flags} |"
        )

    for record in records:
        summary = record["summary"]
        job = record["job"]
        analysis = record["analysis"]
        manifest_item = record[
            "manifest_item"
        ]

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(
            f"## {summary['job_id']} — "
            f"{summary['title']}"
        )
        lines.append("")

        lines.append(
            "### Benchmark metadata"
        )
        lines.append("")

        metadata = {
            key: value
            for key, value
            in manifest_item.items()
            if key != "job_id"
        }

        lines.append("```json")
        lines.append(
            json.dumps(
                metadata,
                ensure_ascii=False,
                indent=2,
            )
        )
        lines.append("```")
        lines.append("")

        lines.append(
            "### Source signals"
        )
        lines.append("")

        lines.append(
            f"- Company: "
            f"{job.get('company_name', '-')}"
        )

        lines.append(
            f"- Structured experience: "
            f"{format_experience(job.get('structured_experience'))}"
        )

        lines.append(
            f"- Structured software: "
            f"{format_software(job.get('structured_software'))}"
        )

        lines.append("")

        lines.append(
            "### AI classification"
        )
        lines.append("")

        rc = analysis.get(
            "role_classification",
            {},
        )

        exp = analysis.get(
            "experience",
            {},
        )

        lines.append(
            f"- Primary role: "
            f"`{rc.get('primary_role')}`"
        )

        lines.append(
            f"- Secondary roles: "
            f"`{rc.get('secondary_roles', [])}`"
        )

        lines.append(
            f"- Target group: "
            f"`{rc.get('target_group')}`"
        )

        lines.append(
            f"- Relevance: "
            f"`{rc.get('relevance_score')}`"
        )

        lines.append(
            f"- Reason: "
            f"{rc.get('reason', '-')}"
        )

        lines.append(
            f"- Seniority: "
            f"`{analysis.get('seniority')}`"
        )

        lines.append(
            f"- Experience: "
            f"`{exp.get('min_years')} - "
            f"{exp.get('max_years')}`"
        )

        lines.append("")

        lines.append(
            "### Skills"
        )
        lines.append("")

        skills = analysis.get(
            "skills",
            [],
        )

        if not skills:
            lines.append("- None")

        for skill in skills:
            lines.append(
                f"- **{skill.get('canonical_name')}** "
                f"— `{skill.get('category')}` "
                f"/ `{skill.get('requirement')}` "
                f"/ `{skill.get('proficiency')}`"
            )

        lines.append("")

        lines.append(
            "### Responsibilities"
        )
        lines.append("")

        responsibilities = analysis.get(
            "responsibilities",
            [],
        )

        if not responsibilities:
            lines.append("- None")

        for item in responsibilities:
            lines.append(
                f"- `{item.get('category')}` — "
                f"{item.get('text')}"
            )

        lines.append("")

        lines.append(
            "### Engineering expectations"
        )
        lines.append("")

        engineering = analysis.get(
            "engineering_expectations",
            [],
        )

        if not engineering:
            lines.append("- None")

        for item in engineering:
            lines.append(
                f"- `{item.get('type')}` "
                f"/ `{item.get('requirement')}` "
                f"— {item.get('evidence')}"
            )

        lines.append("")

        lines.append(
            "### Structural flags"
        )
        lines.append("")

        flags = summary["flags"]

        if flags:
            for flag in flags:
                lines.append(
                    f"- ⚠️ {flag}"
                )
        else:
            lines.append(
                "- No automatic structural flags."
            )

        lines.append("")

        lines.append(
            "### Source text excerpt"
        )
        lines.append("")
        lines.append("```text")
        lines.append(
            build_source_excerpt(job)
        )
        lines.append("```")

    return "\n".join(lines)


def main():
    manifest = load_json(
        MANIFEST_PATH
    )

    records = []
    summaries = []

    print("=" * 100)
    print("BENCHMARK QUALITY REVIEW")
    print("=" * 100)

    for manifest_item in manifest:
        job_id = str(
            manifest_item["job_id"]
        )

        job = load_json(
            JOBS_DIR
            / f"job_{job_id}.json"
        )

        analysis = load_json(
            find_processed_path(
                job_id
            )
        )

        summary = build_job_summary(
            manifest_item,
            job,
            analysis,
        )

        summaries.append(summary)

        records.append(
            {
                "manifest_item": (
                    manifest_item
                ),
                "job": job,
                "analysis": analysis,
                "summary": summary,
            }
        )

        flags = (
            ", ".join(
                summary["flags"]
            )
            or "-"
        )

        print(
            f"{job_id:<10} "
            f"| {summary['primary_role']:<28} "
            f"| {summary['target_group']:<10} "
            f"| rel={summary['relevance_score']:<3} "
            f"| senior={summary['seniority']:<11} "
            f"| skills={summary['skills_count']:<2} "
            f"| resp={summary['responsibilities_count']:<2} "
            f"| eng={summary['engineering_count']:<2} "
            f"| {flags}"
        )

    save_json(
        SUMMARY_PATH,
        summaries,
    )

    report = build_markdown_report(
        records
    )

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    if DRIVE_RESULTS_DIR.exists():
        shutil.copy2(
            SUMMARY_PATH,
            DRIVE_RESULTS_DIR
            / SUMMARY_PATH.name,
        )

        shutil.copy2(
            REPORT_PATH,
            DRIVE_RESULTS_DIR
            / REPORT_PATH.name,
        )

    print("\n" + "=" * 100)
    print("REVIEW FILES")
    print("=" * 100)

    print(
        f"Summary: {SUMMARY_PATH}"
    )

    print(
        f"Detailed report: {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()