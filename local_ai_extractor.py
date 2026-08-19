import json
from pathlib import Path

from ollama import chat, ResponseError
from pydantic import ValidationError

from ai_prompt import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from ai_schema import AIJobAnalysis


MODEL_NAME = "qwen3:4b-instruct"

JOB_ID = "1481754"

BENCHMARK_JOBS_DIR = Path(
    "data/benchmark/jobs"
)

RESULTS_DIR = Path(
    "data/benchmark/results/qwen3_4b_instruct"
)


def load_benchmark_job(job_id):
    path = (
        BENCHMARK_JOBS_DIR
        / f"job_{job_id}.json"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_raw_response(
    job_id,
    content,
):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        RESULTS_DIR
        / f"job_{job_id}_raw.txt"
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def save_validated_result(
    job_id,
    analysis,
):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        RESULTS_DIR
        / f"job_{job_id}.json"
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            analysis.model_dump(
                mode="json"
            ),
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path


def extract_job(job):
    user_prompt = build_user_prompt(
        job
    )

    print("=" * 70)
    print("LOCAL AI EXTRACTION")
    print("=" * 70)

    print(
        f"Model: {MODEL_NAME}"
    )

    print(
        f"Job ID: {job['job_id']}"
    )

    print(
        f"Title: {job['title']}"
    )

    print("\nSending job to local model...")

    response = chat(
        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        format=(
            AIJobAnalysis
            .model_json_schema()
        ),

        think=False,

        options={
            "temperature": 0,
            "num_ctx": 16384,
            "num_predict": 4096,
        },
    )

    return response


def fix_empty_responsibilities(data, job):
    if data.get("responsibilities"):
        return data

    description = job.get(
        "job_description",
        ""
    )

    if not description:
        return data

    lines = [
        line.strip("-• \n")
        for line in description.splitlines()
        if len(line.strip()) > 20
    ]

    action_keywords = [
        "develop",
        "design",
        "build",
        "create",
        "evaluate",
        "analyze",
        "implement",
        "developing",
        "طراحی",
        "تحلیل",
        "ایجاد",
        "پیاده",
        "آموزش",
        "بررسی",
    ]

    extracted = []

    for line in lines:
        if any(
            key.lower() in line.lower()
            for key in action_keywords
        ):
            extracted.append(
                {
                    "text": line,
                    "category": "other"
                }
            )

    data["responsibilities"] = extracted[:8]

    return data

def main():
    job = load_benchmark_job(
        JOB_ID
    )

    try:
        response = extract_job(
            job
        )

    except ResponseError as error:
        print("\n" + "=" * 70)
        print("OLLAMA ERROR")
        print("=" * 70)

        print(error)

        return

    raw_content = (
        response.message.content
    )

    raw_path = save_raw_response(
        JOB_ID,
        raw_content,
    )

    print(
        f"\nRaw response saved to: "
        f"{raw_path}"
    )

    try:
        data = json.loads(raw_content)

        data = fix_role_grouping(data)

        data = fix_empty_responsibilities(
            data,
            job
        )

        analysis = AIJobAnalysis.model_validate(data)

    except ValidationError as error:
        print("\n" + "=" * 70)
        print("VALIDATION FAILED")
        print("=" * 70)

        print(error)

        return

    result_path = (
        save_validated_result(
            JOB_ID,
            analysis,
        )
    )

    print("\n" + "=" * 70)
    print("VALIDATION SUCCESS")
    print("=" * 70)

    print(
        "Primary role:",
        analysis
        .role_classification
        .primary_role
        .value,
    )

    print(
        "Target group:",
        analysis
        .role_classification
        .target_group
        .value,
    )

    print(
        "Relevance:",
        analysis
        .role_classification
        .relevance_score,
    )

    print(
        "Seniority:",
        analysis.seniority.value,
    )

    print(
        "Experience:",
        analysis.experience.min_years,
        "-",
        analysis.experience.max_years,
    )

    print(
        "Skills:",
        len(analysis.skills),
    )

    print(
        "Responsibilities:",
        len(
            analysis.responsibilities
        ),
    )

    print(
        "Soft skills:",
        len(
            analysis.soft_skills
        ),
    )

    print(
        "Engineering expectations:",
        len(
            analysis
            .engineering_expectations
        ),
    )

    print(
        f"\nValidated result saved to: "
        f"{result_path}"
    )

    print("\nSKILLS")
    print("-" * 70)

    for skill in analysis.skills:
        print(
            f"{skill.canonical_name:<30}"
            f" | {skill.category.value:<25}"
            f" | {skill.requirement.value:<12}"
            f" | {skill.proficiency.value}"
        )


if __name__ == "__main__":
    main()