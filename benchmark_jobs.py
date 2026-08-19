import json
import shutil
from pathlib import Path


PARSED_DIR = Path("data/parsed")

BENCHMARK_DIR = Path(
    "data/benchmark/jobs"
)

MANIFEST_PATH = Path(
    "data/benchmark/manifest.json"
)


BENCHMARK_JOBS = [
    {
        "job_id": "1481754",
        "case": "clear_core",
        "note": "Clear Data Scientist role",
    },
    {
        "job_id": "1446383",
        "case": "clear_core",
        "note": "Clear Data Analyst role",
    },
    {
        "job_id": "1442050",
        "case": "clear_core",
        "note": "Clear Machine Learning Engineer role",
    },
    {
        "job_id": "1437674",
        "case": "clear_core",
        "note": "Junior AI Engineer role",
    },
    {
        "job_id": "1377995",
        "case": "clear_core",
        "note": "Senior Data Scientist role",
    },

    {
        "job_id": "1451105",
        "case": "persian_core",
        "note": "Persian AI Specialist advertisement",
    },
    {
        "job_id": "1483896",
        "case": "persian_core",
        "note": "Persian Data Analyst advertisement",
    },

    {
        "job_id": "1474897",
        "case": "borderline",
        "note": (
            "Business Analyst role that may or may not "
            "belong to the target Data Analyst market"
        ),
    },

    {
        "job_id": "1457574",
        "case": "irrelevant",
        "note": (
            "AI-related content role; should not be "
            "misclassified as technical AI engineering"
        ),
    },

    {
        "job_id": "1471834",
        "case": "complex",
        "note": (
            "Legal AI Specialist with substantial AI terminology "
            "but unusual professional requirements"
        ),
    },
]


def main():
    BENCHMARK_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = []

    print("=" * 70)
    print("BUILDING BENCHMARK SET")
    print("=" * 70)

    for item in BENCHMARK_JOBS:
        job_id = item["job_id"]

        source = (
            PARSED_DIR
            / f"job_{job_id}.json"
        )

        if not source.exists():
            print(
                f"✗ Missing job: {job_id}"
            )
            continue

        with source.open(
            "r",
            encoding="utf-8",
        ) as file:
            job = json.load(file)

        destination = (
            BENCHMARK_DIR
            / f"job_{job_id}.json"
        )

        shutil.copy2(
            source,
            destination,
        )

        manifest.append(
            {
                "job_id": job_id,
                "title": job.get("title"),
                "company_name": job.get(
                    "company_name"
                ),
                "case": item["case"],
                "note": item["note"],
            }
        )

        print(
            f"✓ {job_id}"
            f" | {item['case']:<12}"
            f" | {job.get('title')}"
        )

    MANIFEST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MANIFEST_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"Selected jobs: "
        f"{len(manifest)}/{len(BENCHMARK_JOBS)}"
    )

    print(
        f"Manifest: {MANIFEST_PATH}"
    )

    print(
        f"Jobs: {BENCHMARK_DIR}"
    )


if __name__ == "__main__":
    main()