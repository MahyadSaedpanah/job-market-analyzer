import asyncio
import re
from urllib.parse import quote
import json
from pathlib import Path    

from playwright.async_api import async_playwright

from config import SEARCH_QUERIES


JOB_PATTERN = re.compile(
    r"^https://jobvision\.ir/jobs/(\d+)(?:/|$)"
)


async def extract_jobs_from_page(page):
    links = await page.locator("a").evaluate_all(
        """
        elements => elements
            .map(a => a.href)
            .filter(Boolean)
        """
    )

    jobs = {}

    for url in links:
        match = JOB_PATTERN.match(url)

        if not match:
            continue

        job_id = match.group(1)

        clean_url = (
            url.split("?")[0]
            .split("#")[0]
        )

        jobs[job_id] = clean_url

    return jobs


async def collect_single_query(
    page,
    keyword,
    max_scrolls=30,
    stable_rounds=3,
):
    search_url = (
        f"https://jobvision.ir/jobs/keyword/{quote(keyword)}"
    )

    print(f"\nSearching: {keyword}")
    print(f"URL: {search_url}")

    await page.goto(
        search_url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    await page.wait_for_timeout(4000)

    jobs = {}
    unchanged_count = 0

    for scroll_number in range(1, max_scrolls + 1):
        page_jobs = await extract_jobs_from_page(page)

        previous_count = len(jobs)

        jobs.update(page_jobs)

        current_count = len(jobs)

        if current_count == previous_count:
            unchanged_count += 1
        else:
            unchanged_count = 0

        if unchanged_count >= stable_rounds:
            break

        await page.evaluate(
            "window.scrollTo(0, document.body.scrollHeight)"
        )

        await page.wait_for_timeout(1500)

    print(f"Found: {len(jobs)} jobs")

    return jobs


def flatten_queries():
    queries = []

    for category, keywords in SEARCH_QUERIES.items():
        for keyword in keywords:
            queries.append(
                {
                    "category": category,
                    "keyword": keyword,
                }
            )

    return queries


async def collect_multiple_queries(test_limit=None):
    queries = flatten_queries()

    if test_limit is not None:
        queries = queries[:test_limit]

    all_jobs = load_jobs_from_json()

    completed_queries = load_completed_queries(
        all_jobs
    )

    starting_job_count = len(all_jobs)

    executed_queries = 0
    skipped_queries = 0
    total_raw_results = 0

    print(
        f"\nLoaded {len(all_jobs)} existing jobs"
    )

    print(
        f"Completed queries: "
        f"{len(completed_queries)}"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
        )

        page = await browser.new_page(
            viewport={
                "width": 1400,
                "height": 1000,
            }
        )

        for index, query in enumerate(queries, start=1):
            category = query["category"]
            keyword = query["keyword"]

            if keyword in completed_queries:
                skipped_queries += 1

                print("\n" + "=" * 60)
                print(
                    f"SKIPPING COMPLETED QUERY: {keyword}"
                )
                print("=" * 60)

                continue

            print("\n" + "=" * 60)
            print(
                f"QUERY {index}/{len(queries)} "
                f"[{category}]"
            )
            print("=" * 60)

            jobs = await collect_single_query(
                page=page,
                keyword=keyword,
            )

            executed_queries += 1
            total_raw_results += len(jobs)

            # -------------------------------
            # Merge all results of this query
            # -------------------------------

            for job_id, url in jobs.items():

                if job_id not in all_jobs:
                    all_jobs[job_id] = {
                        "url": url,
                        "matched_queries": [],
                        "matched_categories": [],
                    }

                if (
                    keyword
                    not in all_jobs[job_id]["matched_queries"]
                ):
                    all_jobs[job_id]["matched_queries"].append(
                        keyword
                    )

                if (
                    category
                    not in all_jobs[job_id]["matched_categories"]
                ):
                    all_jobs[job_id]["matched_categories"].append(
                        category
                    )

            # -------------------------------
            # Save ONCE after the whole query
            # -------------------------------

            completed_queries.add(keyword)

            save_jobs_to_json(
                all_jobs
            )

            save_collection_state(
                completed_queries
            )

            print(
                f"Progress saved after: {keyword}"
            )

            await page.wait_for_timeout(1500)

        await browser.close()

    new_unique_jobs = (
        len(all_jobs) - starting_job_count
    )

    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    print(
        f"Queries selected: {len(queries)}"
    )

    print(
        f"Queries executed: {executed_queries}"
    )

    print(
        f"Queries skipped: {skipped_queries}"
    )

    print(
        f"Raw results this run: {total_raw_results}"
    )

    print(
        f"Existing jobs before run: {starting_job_count}"
    )

    print(
        f"New unique jobs this run: {new_unique_jobs}"
    )

    print(
        f"Total unique jobs: {len(all_jobs)}"
    )

    print("\nSAMPLE JOBS")
    print("-" * 60)

    for job_id, data in list(all_jobs.items())[:10]:
        print(f"\nJob ID: {job_id}")
        print(f"URL: {data['url']}")

        print(
            "Matched queries:",
            data["matched_queries"],
        )

        print(
            "Categories:",
            data["matched_categories"],
        )

    return all_jobs

def save_jobs_to_json(
    jobs,
    output_path="data/raw_jobs.json",
):
    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            jobs,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved {len(jobs)} unique jobs "
        f"to: {output_file}"
    )

def load_jobs_from_json(
    input_path="data/raw_jobs.json",
):
    input_file = Path(input_path)

    if not input_file.exists():
        return {}

    with input_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_completed_queries(
    jobs,
    state_path="data/collection_state.json",
):
    state_file = Path(state_path)

    if state_file.exists():
        with state_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            state = json.load(file)

        return set(
            state.get("completed_queries", [])
        )

    completed_queries = set()

    for job in jobs.values():
        completed_queries.update(
            job.get("matched_queries", [])
        )

    return completed_queries


def save_collection_state(
    completed_queries,
    state_path="data/collection_state.json",
):
    state_file = Path(state_path)

    state_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    state = {
        "completed_queries": sorted(
            completed_queries
        )
    }

    with state_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )

async def main():
    jobs = await collect_multiple_queries(
        test_limit=5
    )

    save_jobs_to_json(jobs)


if __name__ == "__main__":
    asyncio.run(main())