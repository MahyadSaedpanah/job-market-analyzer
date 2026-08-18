import re
import asyncio
from urllib.parse import quote

from playwright.async_api import async_playwright


async def collect_job_links(
    keyword="Data Scientist",
    max_scrolls=30,
    stable_rounds=3,
):
    search_url = f"https://jobvision.ir/jobs/keyword/{quote(keyword)}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
        )

        page = await browser.new_page(
            viewport={"width": 1400, "height": 1000}
        )

        print(f"\nOpening: {search_url}")

        await page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(5000)

        pattern = re.compile(
            r"^https://jobvision\.ir/jobs/(\d+)(?:/|$)"
        )

        jobs = {}
        unchanged_count = 0

        for scroll_number in range(1, max_scrolls + 1):

            links = await page.locator("a").evaluate_all(
                """
                elements => elements
                    .map(a => a.href)
                    .filter(Boolean)
                """
            )

            previous_count = len(jobs)

            for url in links:
                match = pattern.match(url)

                if not match:
                    continue

                job_id = match.group(1)

                clean_url = (
                    url.split("?")[0]
                    .split("#")[0]
                )

                jobs[job_id] = clean_url

            current_count = len(jobs)

            print(
                f"Scroll {scroll_number}: "
                f"{current_count} unique jobs"
            )

            if current_count == previous_count:
                unchanged_count += 1
            else:
                unchanged_count = 0

            if unchanged_count >= stable_rounds:
                print(
                    f"No new jobs found for "
                    f"{stable_rounds} consecutive scrolls."
                )
                print("Stopping automatically.")
                break

            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            await page.wait_for_timeout(2000)

        else:
            print(
                f"Reached maximum scroll limit: {max_scrolls}"
            )

        await browser.close()

    return jobs


async def main():

    jobs = await collect_job_links(
        keyword="Data Scientist"
    )

    print("\n" + "=" * 60)
    print(f"FOUND JOBS: {len(jobs)}")
    print("=" * 60)

    for job_id, url in jobs.items():
        print(f"{job_id} -> {url}")


if __name__ == "__main__":
    asyncio.run(main())