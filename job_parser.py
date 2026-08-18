import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


JOB_ID = "1481754"

JOB_URL = (
    "https://jobvision.ir/jobs/1481754/"
    "%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-data-scientist"
)

OUTPUT_PATH = Path(
    f"data/parsed/job_{JOB_ID}.json"
)


SOFTWARE_LEVELS = {
    "basic",
    "intermediate",
    "advanced",
    "expert",
}


def clean_lines(text):
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def find_index(lines, value):
    value = value.lower()

    for index, line in enumerate(lines):
        if line.lower() == value:
            return index

    return None


def get_value_after_label(lines, label):
    index = find_index(lines, label)

    if index is None:
        return None

    if index + 1 >= len(lines):
        return None

    return lines[index + 1]


def extract_section(
    lines,
    start_label,
    end_label,
):
    start_index = find_index(
        lines,
        start_label,
    )

    end_index = find_index(
        lines,
        end_label,
    )

    if start_index is None:
        return []

    start_index += 1

    if end_index is None:
        return lines[start_index:]

    return lines[
        start_index:end_index
    ]


def extract_software_from_key_requirements(
    lines,
):
    software = []

    pattern = re.compile(
        r"^(.*?)\s*-\s*"
        r"(Basic|Intermediate|Advanced|Expert)$",
        re.IGNORECASE,
    )

    for line in lines:
        match = pattern.match(line)

        if not match:
            continue

        name = match.group(1).strip()
        level = match.group(2).strip()

        software.append(
            {
                "name": name,
                "level": level,
            }
        )

    return software


def extract_experience(
    key_requirement_lines,
):
    for line in key_requirement_lines:
        if "experience" in line.lower():
            return line

        if "سابقه" in line:
            return line

    return None


def extract_top_metadata(lines, title):
    """
    Based on JobVision's current layout:

    Title
    Posted time
    Company
    Location
    Employment type
    """

    try:
        title_index = lines.index(title)
    except ValueError:
        return {
            "posted": None,
            "company_name": None,
            "location": None,
            "employment_type": None,
        }

    values = lines[
        title_index + 1:title_index + 5
    ]

    while len(values) < 4:
        values.append(None)

    return {
        "posted": values[0],
        "company_name": values[1],
        "location": values[2],
        "employment_type": values[3],
    }


async def parse_job():
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

        print(f"Opening job {JOB_ID}...")

        await page.goto(
            JOB_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(4000)

        # ----------------------------------------
        # Page title
        # ----------------------------------------

        title_locator = page.locator(
            "h1.yn_title"
        )

        title = (
            await title_locator
            .first
            .inner_text()
        ).strip()

        # ----------------------------------------
        # Full visible text
        # ----------------------------------------

        body_text = await page.locator(
            "body"
        ).inner_text()

        lines = clean_lines(
            body_text
        )

        # ----------------------------------------
        # Basic metadata
        # ----------------------------------------

        top_metadata = (
            extract_top_metadata(
                lines,
                title,
            )
        )

        # ----------------------------------------
        # Key Requirements
        # ----------------------------------------

        key_requirements = extract_section(
            lines,
            "key Requirements",
            "Job Description",
        )

        experience = extract_experience(
            key_requirements
        )

        software = (
            extract_software_from_key_requirements(
                key_requirements
            )
        )

        # ----------------------------------------
        # Job Description
        # ----------------------------------------

        job_description_lines = (
            extract_section(
                lines,
                "Job Description",
                "Job Requirements",
            )
        )

        job_description = "\n".join(
            job_description_lines
        )

        # ----------------------------------------
        # Company information
        # ----------------------------------------

        company_info = {
            "size": get_value_after_label(
                lines,
                "Company Size",
            ),
            "industry": get_value_after_label(
                lines,
                "Industry",
            ),
            "type": get_value_after_label(
                lines,
                "Company Type",
            ),
            "establishment_year": (
                get_value_after_label(
                    lines,
                    "Establishment year",
                )
            ),
            "ownership_type": (
                get_value_after_label(
                    lines,
                    "Ownership type",
                )
            ),
        }

        # ----------------------------------------
        # Other job metadata
        # ----------------------------------------

        working_days = (
            get_value_after_label(
                lines,
                "Working days and hours",
            )
        )

        business_trips = (
            get_value_after_label(
                lines,
                "Business trips",
            )
        )

        facilities = (
            get_value_after_label(
                lines,
                "Facilities and Benefits",
            )
        )

        gender = get_value_after_label(
            lines,
            "Gender",
        )

        # ----------------------------------------
        # Final structured object
        # ----------------------------------------

        job = {
            "job_id": JOB_ID,
            "url": page.url,

            "title": title,

            "company_name": (
                top_metadata[
                    "company_name"
                ]
            ),

            "location": (
                top_metadata[
                    "location"
                ]
            ),

            "employment_type": (
                top_metadata[
                    "employment_type"
                ]
            ),

            "posted": (
                top_metadata[
                    "posted"
                ]
            ),

            "working_days_and_hours": (
                working_days
            ),

            "business_trips": (
                business_trips
            ),

            "facilities_and_benefits": (
                facilities
            ),

            "experience": experience,

            "gender": gender,

            "software": software,

            "company_info": company_info,

            "key_requirements_raw": (
                key_requirements
            ),

            "job_description": (
                job_description
            ),
        }

        # ----------------------------------------
        # Save
        # ----------------------------------------

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with OUTPUT_PATH.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                job,
                file,
                ensure_ascii=False,
                indent=2,
            )

        await browser.close()

        return job


async def main():
    job = await parse_job()

    print("\n" + "=" * 70)
    print("PARSED JOB")
    print("=" * 70)

    print(
        json.dumps(
            job,
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n" + "=" * 70)

    print(
        f"Saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    asyncio.run(main())