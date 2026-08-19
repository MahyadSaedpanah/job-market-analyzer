import json
from collections import Counter
from pathlib import Path


PARSED_DIR = Path("data/parsed")


LEAKAGE_TERMS = [
    "موقعیت های شغلی مشابه",
    "موقعیت‌های شغلی مشابه",
    "ثبت مشکل و تخلف آگهی",
    "ارسال رزومه برای",
    "Similar Jobs",
    "Report Job",
]


def load_parsed_jobs():
    jobs = []

    for file_path in sorted(
        PARSED_DIR.glob("job_*.json")
    ):
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            jobs.append(
                json.load(file)
            )

    return jobs


def is_empty(value):
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, list):
        return len(value) == 0

    if isinstance(value, dict):
        return len(value) == 0

    return False


def contains_leakage(job):
    fields_to_check = [
        job.get("job_description", ""),
        "\n".join(
            job.get(
                "job_requirements_raw",
                [],
            )
        ),
        "\n".join(
            job.get(
                "key_requirements_raw",
                [],
            )
        ),
    ]

    combined_text = "\n".join(
        fields_to_check
    )

    found_terms = [
        term
        for term in LEAKAGE_TERMS
        if term in combined_text
    ]

    return found_terms


def detect_language(text):
    if not text:
        return "unknown"

    persian_chars = sum(
        1
        for char in text
        if "\u0600" <= char <= "\u06FF"
    )

    latin_chars = sum(
        1
        for char in text
        if (
            "a" <= char.lower() <= "z"
        )
    )

    if persian_chars > latin_chars:
        return "persian"

    if latin_chars > persian_chars:
        return "english"

    return "mixed"


def main():
    jobs = load_parsed_jobs()

    missing_fields = Counter()

    language_counts = Counter()

    description_lengths = []

    no_software_jobs = []

    no_experience_jobs = []

    empty_description_jobs = []

    leakage_jobs = []

    suspicious_short_descriptions = []

    suspicious_long_descriptions = []

    software_count_distribution = Counter()

    for job in jobs:
        job_id = job.get("job_id")
        title = job.get("title")

        # --------------------------------------
        # Missing important fields
        # --------------------------------------

        important_fields = [
            "title",
            "company_name",
            "location",
            "employment_type",
            "posted",
            "job_description",
        ]

        for field in important_fields:
            if is_empty(
                job.get(field)
            ):
                missing_fields[field] += 1

        # --------------------------------------
        # Description
        # --------------------------------------

        description = (
            job.get(
                "job_description",
                ""
            )
            or ""
        )

        description_length = len(
            description
        )

        description_lengths.append(
            description_length
        )

        if description_length == 0:
            empty_description_jobs.append(
                (job_id, title)
            )

        elif description_length < 100:
            suspicious_short_descriptions.append(
                (
                    job_id,
                    title,
                    description_length,
                )
            )

        elif description_length > 10000:
            suspicious_long_descriptions.append(
                (
                    job_id,
                    title,
                    description_length,
                )
            )

        # --------------------------------------
        # Language
        # --------------------------------------

        language = detect_language(
            description
        )

        language_counts[
            language
        ] += 1

        # --------------------------------------
        # Software
        # --------------------------------------

        software = job.get(
            "software",
            [],
        )

        software_count_distribution[
            len(software)
        ] += 1

        if not software:
            no_software_jobs.append(
                (job_id, title)
            )

        # --------------------------------------
        # Experience
        # --------------------------------------

        if is_empty(
            job.get("experience")
        ):
            no_experience_jobs.append(
                (job_id, title)
            )

        # --------------------------------------
        # Leakage
        # --------------------------------------

        leakage_terms = (
            contains_leakage(job)
        )

        if leakage_terms:
            leakage_jobs.append(
                {
                    "job_id": job_id,
                    "title": title,
                    "terms": leakage_terms,
                }
            )

    # ------------------------------------------
    # Summary
    # ------------------------------------------

    print("\n" + "=" * 70)
    print("PARSED JOBS AUDIT")
    print("=" * 70)

    print(
        f"Total parsed jobs: "
        f"{len(jobs)}"
    )

    print("\nMISSING FIELDS")
    print("-" * 70)

    for field in [
        "title",
        "company_name",
        "location",
        "employment_type",
        "posted",
        "job_description",
    ]:
        print(
            f"{field:<25} "
            f"{missing_fields[field]:>5}"
        )

    print("\nLANGUAGE DISTRIBUTION")
    print("-" * 70)

    for language, count in (
        language_counts.most_common()
    ):
        print(
            f"{language:<15} "
            f"{count:>5}"
        )

    print("\nSTRUCTURED FIELD COVERAGE")
    print("-" * 70)

    print(
        "No structured software:",
        len(no_software_jobs),
    )

    print(
        "No structured experience:",
        len(no_experience_jobs),
    )

    print("\nSOFTWARE COUNT DISTRIBUTION")
    print("-" * 70)

    for count in sorted(
        software_count_distribution
    ):
        print(
            f"{count:>2} software -> "
            f"{software_count_distribution[count]:>4} jobs"
        )

    print("\nDESCRIPTION QUALITY")
    print("-" * 70)

    if description_lengths:
        print(
            "Shortest:",
            min(description_lengths),
        )

        print(
            "Longest:",
            max(description_lengths),
        )

        print(
            "Average:",
            round(
                sum(description_lengths)
                / len(description_lengths),
                1,
            ),
        )

    print(
        "Empty descriptions:",
        len(empty_description_jobs),
    )

    print(
        "Very short descriptions (<100):",
        len(
            suspicious_short_descriptions
        ),
    )

    print(
        "Very long descriptions (>10000):",
        len(
            suspicious_long_descriptions
        ),
    )

    print("\nCONTENT LEAKAGE")
    print("-" * 70)

    print(
        "Jobs with possible leakage:",
        len(leakage_jobs),
    )

    for item in leakage_jobs[:20]:
        print(
            f"\n[{item['job_id']}] "
            f"{item['title']}"
        )

        print(
            "Terms:",
            item["terms"],
        )

    print("\nEMPTY DESCRIPTION JOBS")
    print("-" * 70)

    for job_id, title in (
        empty_description_jobs[:20]
    ):
        print(
            f"{job_id} | {title}"
        )

    print("\nVERY SHORT DESCRIPTION JOBS")
    print("-" * 70)

    for (
        job_id,
        title,
        length,
    ) in suspicious_short_descriptions[:20]:
        print(
            f"{job_id} | "
            f"{length} chars | "
            f"{title}"
        )

    print("\nVERY LONG DESCRIPTION JOBS")
    print("-" * 70)

    for (
        job_id,
        title,
        length,
    ) in suspicious_long_descriptions[:20]:
        print(
            f"{job_id} | "
            f"{length} chars | "
            f"{title}"
        )

    


if __name__ == "__main__":
    main()