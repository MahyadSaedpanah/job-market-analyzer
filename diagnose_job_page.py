import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


JOB_URL = (
    "https://jobvision.ir/jobs/1481754/"
    "%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-data-scientist"
)

OUTPUT_DIR = Path("data/diagnostics")


async def diagnose_job_page():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
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

        print(f"Opening:\n{JOB_URL}\n")

        await page.goto(
            JOB_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(5000)

        # ----------------------------------------
        # Basic page information
        # ----------------------------------------

        print("=" * 70)
        print("PAGE INFO")
        print("=" * 70)

        print("URL:", page.url)
        print("Browser title:", await page.title())

        # ----------------------------------------
        # Headings
        # ----------------------------------------

        print("\n" + "=" * 70)
        print("HEADINGS")
        print("=" * 70)

        headings = await page.locator(
            "h1, h2, h3, h4, h5, h6"
        ).evaluate_all(
            """
            elements => elements.map(element => ({
                tag: element.tagName,
                text: (element.innerText || "").trim(),
                className: element.className || ""
            }))
            """
        )

        for index, heading in enumerate(
            headings,
            start=1,
        ):
            if not heading["text"]:
                continue

            print(
                f"{index:02d}. "
                f"<{heading['tag']}> "
                f"{heading['text']}"
            )

            print(
                f"    class={heading['className']}"
            )

        # ----------------------------------------
        # Full visible body text
        # ----------------------------------------

        body_text = await page.locator(
            "body"
        ).inner_text()

        body_file = (
            OUTPUT_DIR
            / "job_1481754_body.txt"
        )

        body_file.write_text(
            body_text,
            encoding="utf-8",
        )

        print("\n" + "=" * 70)
        print("BODY TEXT")
        print("=" * 70)

        print(
            f"Saved to: {body_file}"
        )

        # ----------------------------------------
        # Print numbered non-empty lines
        # ----------------------------------------

        lines = [
            line.strip()
            for line in body_text.splitlines()
            if line.strip()
        ]

        print(
            f"Non-empty text lines: {len(lines)}"
        )

        print("\n" + "=" * 70)
        print("IMPORTANT TEXT CONTEXT")
        print("=" * 70)

        target_terms = [
            "key requirements",
            "job description",
            "job requirements",
            "software",
            "gender",
            "experience",
            "python",
            "sql",
        ]

        interesting_indexes = set()

        for index, line in enumerate(lines):
            normalized = line.lower()

            if any(
                term in normalized
                for term in target_terms
            ):
                for nearby_index in range(
                    max(0, index - 2),
                    min(len(lines), index + 5),
                ):
                    interesting_indexes.add(
                        nearby_index
                    )

        previous_index = None

        for index in sorted(interesting_indexes):
            if (
                previous_index is not None
                and index > previous_index + 1
            ):
                print("...")

            print(
                f"{index + 1:03d}: "
                f"{lines[index]}"
            )

            previous_index = index

        print("\n" + "=" * 70)
        print("TOP PAGE CONTENT")
        print("=" * 70)

        for index, line in enumerate(lines[:35], start=1):
            print(
                f"{index:03d}: {line}"
            )

        # ----------------------------------------
        # Save rendered HTML too
        # ----------------------------------------

        html = await page.content()

        html_file = (
            OUTPUT_DIR
            / "job_1481754.html"
        )

        html_file.write_text(
            html,
            encoding="utf-8",
        )

        print("\n" + "=" * 70)
        print("FILES")
        print("=" * 70)

        print("Body:", body_file)
        print("HTML:", html_file)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(
        diagnose_job_page()
    )