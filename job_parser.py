import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


RAW_JOBS_PATH = Path("data/raw_jobs.json")
PARSED_DIR = Path("data/parsed")


TEST_JOB_IDS = [
    "1481754",  # Data Scientist
    "1446383",  # Data Analyst
    "1442050",  # Machine Learning Engineer
    "1451105",  # کارشناس هوش مصنوعی
    "1437674",  # Junior AI Engineer
]


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

    if start_index is None:
        return []

    end_index = find_index(
        lines,
        end_label,
    )

    start_index += 1

    if (
        end_index is None
        or end_index <= start_index
    ):
        return lines[start_index:]

    return lines[
        start_index:end_index
    ]


def extract_software_from_key_requirements(lines):
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

        software.append(
            {
                "name": match.group(1).strip(),
                "level": match.group(2).strip(),
            }
        )

    return software


def extract_experience(lines):
    keywords = [
        "experience",
        "سابقه",
    ]

    for line in lines:
        normalized = line.lower()

        if any(
            keyword in normalized
            for keyword in keywords
        ):
            return line

    return None


def extract_top_metadata(
    lines,
    title,
):
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
        title_index + 1:
        title_index + 5
    ]

    while len(values) < 4:
        values.append(None)

    return {
        "posted": values[0],
        "company_name": values[1],
        "location": values[2],
        "employment_type": values[3],
    }


async def get_job_title(page):
    title_locator = page.locator(
        "h1.yn_title"
    )

    if await title_locator.count() > 0:
        return (
            await title_locator
            .first
            .inner_text()
        ).strip()

    # fallback
    h1 = page.locator("h1")

    if await h1.count() > 0:
        return (
            await h1.first.inner_text()
        ).strip()

    return None


async def parse_job(
    page,
    job_id,
    url,
):
    print(
        f"\nParsing job {job_id}..."
    )

    await page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    await page.wait_for_timeout(3000)

    title = await get_job_title(page)

    body_text = await page.locator(
        "body"
    ).inner_text()

    lines = clean_lines(
        body_text
    )

    top_metadata = extract_top_metadata(
        lines,
        title,
    )

    key_requirements = extract_section(
        lines,
        "key Requirements",
        "Job Description",
    )

    software = (
        extract_software_from_key_requirements(
            key_requirements
        )
    )

    experience = extract_experience(
        key_requirements
    )

    job_description_lines = extract_section(
        lines,
        "Job Description",
        "Job Requirements",
    )

    job_description = "\n".join(
        job_description_lines
    )

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

    job = {
        "job_id": job_id,
        "url": page.url,

        "title": title,

        "company_name": (
            top_metadata["company_name"]
        ),

        "location": (
            top_metadata["location"]
        ),

        "employment_type": (
            top_metadata["employment_type"]
        ),

        "posted": (
            top_metadata["posted"]
        ),

        "working_days_and_hours": (
            get_value_after_label(
                lines,
                "Working days and hours",
            )
        ),

        "business_trips": (
            get_value_after_label(
                lines,
                "Business trips",
            )
        ),

        "facilities_and_benefits": (
            get_value_after_label(
                lines,
                "Facilities and Benefits",
            )
        ),

        "experience": experience,

        "gender": (
            get_value_after_label(
                lines,
                "Gender",
            )
        ),

        "software": software,

        "company_info": company_info,

        "key_requirements_raw": (
            key_requirements
        ),

        "job_description": (
            job_description
        ),
    }

    return job


def save_parsed_job(job):
    PARSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PARSED_DIR
        / f"job_{job['job_id']}.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            job,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


def load_raw_jobs():
    with RAW_JOBS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


async def main():
    raw_jobs = load_raw_jobs()

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

        for job_id in TEST_JOB_IDS:
            raw_job = raw_jobs.get(
                job_id
            )

            if raw_job is None:
                print(
                    f"\nJob not found "
                    f"in raw_jobs.json: {job_id}"
                )
                continue

            try:
                job = await parse_job(
                    page=page,
                    job_id=job_id,
                    url=raw_job["url"],
                )

                output_path = (
                    save_parsed_job(job)
                )

                print(
                    f"✓ {job_id}"
                    f" | {job['title']}"
                    f" | {job['company_name']}"
                )

                print(
                    f"  Experience: "
                    f"{job['experience']}"
                )

                print(
                    f"  Software: "
                    f"{len(job['software'])}"
                )

                print(
                    f"  Description chars: "
                    f"{len(job['job_description'])}"
                )

                print(
                    f"  Saved: {output_path}"
                )

            except Exception as error:
                print(
                    f"✗ Failed: {job_id}"
                )

                print(
                    f"  {type(error).__name__}: "
                    f"{error}"
                )

            await page.wait_for_timeout(
                1500
            )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())