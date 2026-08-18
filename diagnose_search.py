import asyncio
import re
from urllib.parse import quote

from playwright.async_api import async_playwright


async def diagnose_search(keyword="Data Scientist"):
    search_url = f"https://jobvision.ir/jobs/keyword/{quote(keyword)}"

    job_pattern = re.compile(
        r"^https://jobvision\.ir/jobs/(\d+)(?:/|$)"
    )

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

        async def get_status():
            links = await page.locator("a").evaluate_all(
                """
                elements => elements
                    .map(a => a.href)
                    .filter(Boolean)
                """
            )

            job_ids = set()

            for url in links:
                match = job_pattern.match(url)

                if match:
                    job_ids.add(match.group(1))

            height = await page.evaluate(
                "document.body.scrollHeight"
            )

            return len(job_ids), height

        # وضعیت اولیه
        count, height = await get_status()

        print("\nINITIAL STATE")
        print("-" * 50)
        print("Jobs:", count)
        print("Page height:", height)

        # چند scroll آزمایشی
        print("\nSCROLL TEST")
        print("-" * 50)

        for i in range(1, 9):
            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            await page.wait_for_timeout(2000)

            count, height = await get_status()

            print(
                f"Scroll {i}: "
                f"jobs={count}, "
                f"height={height}, "
                f"url={page.url}"
            )

        # متن تمام buttonها
        button_texts = await page.locator(
            "button"
        ).all_inner_texts()

        interesting_buttons = []

        keywords = [
            "بعد",
            "بیشتر",
            "نمایش",
            "ادامه",
            "next",
            "more",
            "load",
        ]

        for text in button_texts:
            clean_text = " ".join(text.split())

            if any(
                word.lower() in clean_text.lower()
                for word in keywords
            ):
                interesting_buttons.append(clean_text)

        print("\nPOSSIBLE PAGINATION BUTTONS")
        print("-" * 50)

        if interesting_buttons:
            for text in sorted(set(interesting_buttons)):
                print(text)
        else:
            print("None found")

        # لینک‌هایی که احتمالاً مربوط به pagination هستند
        links = await page.locator("a").evaluate_all(
            """
            elements => elements.map(a => ({
                text: (a.innerText || "").trim(),
                href: a.href || ""
            }))
            """
        )

        possible_pagination_links = []

        for link in links:
            text = link["text"]
            href = link["href"]

            lower_href = href.lower()
            lower_text = text.lower()

            if (
                "page=" in lower_href
                or "/page/" in lower_href
                or "offset=" in lower_href
                or "next" in lower_text
                or "بعدی" in text
            ):
                possible_pagination_links.append(
                    (text, href)
                )

        print("\nPOSSIBLE PAGINATION LINKS")
        print("-" * 50)

        if possible_pagination_links:
            for text, href in possible_pagination_links:
                print(f"{text!r} -> {href}")
        else:
            print("None found")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(
        diagnose_search("Data Scientist")
    )