import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


RAW_JOBS_PATH = Path("data/raw_jobs.json")


GENERIC_QUERIES = {
    "Machine Learning",
    "یادگیری ماشین",
    "Artificial Intelligence",
    "هوش مصنوعی",
    "Data Analytics",
    "تحلیل داده",
}


TARGET_TITLE_TERMS = [
    # Data Science
    "data scientist",
    "data science",
    "دانشمند داده",
    "علم داده",

    # Data Analysis
    "data analyst",
    "data analytics",
    "تحلیلگر داده",
    "تحلیل داده",

    # ML
    "machine learning",
    "ml engineer",
    "یادگیری ماشین",

    # AI
    "ai engineer",
    "ai developer",
    "ai specialist",
    "artificial intelligence",
    "هوش مصنوعی",
]


def load_jobs():
    with RAW_JOBS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def extract_title_from_url(url):
    """
    Example:
    .../استخدام-senior-data-scientist
    ->
    senior data scientist
    """

    slug = url.rstrip("/").split("/")[-1]

    slug = unquote(slug)

    slug = re.sub(
        r"^استخدام[-\s]*",
        "",
        slug,
        flags=re.IGNORECASE,
    )

    slug = slug.replace("-", " ")

    slug = re.sub(
        r"\s+",
        " ",
        slug,
    )

    return slug.strip()


def normalize_text(text):
    return (
        text.lower()
        .replace("\u200c", " ")
        .strip()
    )


def title_looks_relevant(title):
    normalized_title = normalize_text(title)

    return any(
        normalize_text(term) in normalized_title
        for term in TARGET_TITLE_TERMS
    )


def main():
    jobs = load_jobs()

    category_counts = Counter()
    query_counts = Counter()
    match_count_distribution = Counter()

    generic_only_jobs = []
    weak_match_jobs = []
    suspicious_jobs = []

    for job_id, data in jobs.items():
        url = data["url"]

        matched_queries = data.get(
            "matched_queries",
            [],
        )

        matched_categories = data.get(
            "matched_categories",
            [],
        )

        title = extract_title_from_url(url)

        category_counts.update(
            matched_categories
        )

        query_counts.update(
            matched_queries
        )

        match_count_distribution[
            len(matched_queries)
        ] += 1

        # ----------------------------------------
        # Job found by only one query
        # ----------------------------------------

        if len(matched_queries) == 1:
            weak_match_jobs.append(
                {
                    "job_id": job_id,
                    "title": title,
                    "query": matched_queries[0],
                    "url": url,
                }
            )

        # ----------------------------------------
        # Job found only through generic queries
        # ----------------------------------------

        if (
            matched_queries
            and all(
                query in GENERIC_QUERIES
                for query in matched_queries
            )
        ):
            generic_only_jobs.append(
                {
                    "job_id": job_id,
                    "title": title,
                    "queries": matched_queries,
                    "url": url,
                }
            )

        # ----------------------------------------
        # Simple title-based noise heuristic
        # ----------------------------------------

        if not title_looks_relevant(title):
            suspicious_jobs.append(
                {
                    "job_id": job_id,
                    "title": title,
                    "queries": matched_queries,
                    "url": url,
                }
            )

    print("\n" + "=" * 70)
    print("RAW JOB AUDIT")
    print("=" * 70)

    print(
        f"Total unique candidates: {len(jobs)}"
    )

    # --------------------------------------------
    # Categories
    # --------------------------------------------

    print("\nCATEGORY COVERAGE")
    print("-" * 70)

    for category, count in category_counts.most_common():
        print(
            f"{category:<25} {count:>5}"
        )

    # --------------------------------------------
    # Query productivity
    # --------------------------------------------

    print("\nMOST PRODUCTIVE QUERIES")
    print("-" * 70)

    for query, count in query_counts.most_common():
        print(
            f"{query:<35} {count:>5}"
        )

    # --------------------------------------------
    # Number of matching queries per job
    # --------------------------------------------

    print("\nQUERY MATCH DISTRIBUTION")
    print("-" * 70)

    for match_count in sorted(
        match_count_distribution
    ):
        job_count = (
            match_count_distribution[
                match_count
            ]
        )

        print(
            f"{match_count:>2} queries -> "
            f"{job_count:>4} jobs"
        )

    print("\nMATCH STRENGTH")
    print("-" * 70)

    print(
        "Found by only 1 query:",
        len(weak_match_jobs),
    )

    print(
        "Found only via generic queries:",
        len(generic_only_jobs),
    )

    print(
        "Title does not contain obvious "
        "target terms:",
        len(suspicious_jobs),
    )

    # --------------------------------------------
    # Suspicious samples
    # --------------------------------------------

    print("\nPOTENTIALLY NOISY TITLES")
    print("-" * 70)

    for item in suspicious_jobs[:30]:
        print(
            f"\n[{item['job_id']}] "
            f"{item['title']}"
        )

        print(
            "Queries:",
            item["queries"],
        )

    # --------------------------------------------
    # Generic-only samples
    # --------------------------------------------

    print("\nGENERIC-QUERY-ONLY JOBS")
    print("-" * 70)

    for item in generic_only_jobs[:20]:
        print(
            f"\n[{item['job_id']}] "
            f"{item['title']}"
        )

        print(
            "Queries:",
            item["queries"],
        )


if __name__ == "__main__":
    main()