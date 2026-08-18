import re
import asyncio
from urllib.parse import quote

from playwright.async_api import async_playwright


async def collect_job_links(keyword="Data Scientist", scrolls=4):
    search_url = f"https://jobvision.ir/jobs/keyword/{quote(keyword)}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome"
        )

        page = await browser.new_page(
            viewport={"width": 1400, "height": 1000}
        )

        print(f"\nOpening: {search_url}")

        await page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        await page.wait_for_timeout(5000)

        for i in range(scrolls):
            print(f"Scroll {i + 1}/{scrolls}")

            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            await page.wait_for_timeout(2000)

        links = await page.locator("a").evaluate_all(
            """
            elements => elements
                .map(a => a.href)
                .filter(Boolean)
            """
        )

        pattern = re.compile(
            r"^https://jobvision\.ir/jobs/(\d+)(?:/|$)"
        )

        jobs = {}

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

        await browser.close()

    return jobs


async def main():

    jobs = await collect_job_links(
        keyword="Data Scientist",
        scrolls=4
    )

    print("\n" + "=" * 60)
    print(f"FOUND JOBS: {len(jobs)}")
    print("=" * 60)

    for job_id, url in jobs.items():
        print(f"{job_id} -> {url}")


if __name__ == "__main__":
    asyncio.run(main())