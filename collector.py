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

    all_jobs = {}
    total_raw_results = 0

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

            total_raw_results += len(jobs)

            for job_id, url in jobs.items():

                if job_id not in all_jobs:
                    all_jobs[job_id] = {
                        "url": url,
                        "matched_queries": [],
                        "matched_categories": [],
                    }

                if keyword not in all_jobs[job_id]["matched_queries"]:
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

            await page.wait_for_timeout(1500)

        await browser.close()

    duplicates = total_raw_results - len(all_jobs)

    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    print(f"Queries executed: {len(queries)}")
    print(f"Raw results: {total_raw_results}")
    print(f"Duplicates removed: {duplicates}")
    print(f"Unique jobs: {len(all_jobs)}")

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

async def main():
    jobs = await collect_multiple_queries(
        test_limit=3
    )

    save_jobs_to_json(jobs)


if __name__ == "__main__":
    asyncio.run(main())