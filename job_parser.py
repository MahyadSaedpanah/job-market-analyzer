import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

RAW_JOBS_PATH = Path("data/raw_jobs.json")
PARSED_DIR = Path("data/parsed")

FAILURES_PATH = Path("data/parse_failures.json")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3
REQUEST_DELAY_MS = 1500


TEST_JOB_IDS = [
    "1481754",  # Data Scientist
    "1446383",  # Data Analyst
    "1442050",  # Machine Learning Engineer
    "1451105",  # کارشناس هوش مصنوعی
    "1437674",  # Junior AI Engineer
]


# --------------------------------------------------
# Bilingual labels
# --------------------------------------------------

SECTION_LABELS = {
    "key_requirements": [
        "key Requirements",
        "Key Requirements",
        "شاخص های کلیدی از نظر کارفرما",
        "شاخص‌های کلیدی از نظر کارفرما",
    ],

    "job_description": [
        "Job Description",
        "شرح شغل و وظایف",
    ],

    "job_requirements": [
        "Job Requirements",
        "شرایط احراز شغل",
    ],
}

JOB_REQUIREMENTS_END_LABELS = [
    # Persian
    "ثبت مشکل و تخلف آگهی",
    "موقعیت های شغلی مشابه",
    "موقعیت‌های شغلی مشابه",
    "ارسال رزومه",

    # English fallbacks
    "Report Job",
    "Similar Jobs",
    "Apply",
]


FIELD_LABELS = {
    "company_size": [
        "Company Size",
        "اندازه سازمان",
    ],

    "industry": [
        "Industry",
        "صنعت",
    ],

    "company_type": [
        "Company Type",
        "نوع فعالیت",
    ],

    "establishment_year": [
        "Establishment year",
        "سال تاسیس",
        "سال تأسیس",
    ],

    "ownership_type": [
        "Ownership type",
        "نوع مالکیت",
        "مالکیت",
    ],

    "working_days": [
        "Working days and hours",
        "روز و ساعت کاری",
        "روزها و ساعات کاری",
    ],

    "business_trips": [
        "Business trips",
        "سفرهای کاری",
    ],

    "facilities": [
        "Facilities and Benefits",
        "مزایا و تسهیلات",
    ],

    "gender": [
        "Gender",
        "جنسیت",
    ],

    "education": [
        "Education",
        "تحصیلات",
    ],

    "military_service": [
        "Military Service",
        "Military service",
        "وضعیت نظام وظیفه",
        "خدمت سربازی",
    ],
}


SOFTWARE_LEVEL_MAP = {
    # English
    "basic": "Basic",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "expert": "Expert",

    # Persian
    "مقدماتی": "Basic",
    "متوسط": "Intermediate",
    "پیشرفته": "Advanced",
    "حرفه ای": "Expert",
    "حرفه‌ای": "Expert",
}


# --------------------------------------------------
# Text helpers
# --------------------------------------------------

def normalize_text(text):
    if text is None:
        return ""

    return (
        text
        .replace("\u200c", " ")
        .replace("ي", "ی")
        .replace("ك", "ک")
        .strip()
        .lower()
    )


def clean_lines(text):
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def find_index_any(lines, labels):
    normalized_labels = {
        normalize_text(label)
        for label in labels
    }

    for index, line in enumerate(lines):
        if normalize_text(line) in normalized_labels:
            return index

    return None


def get_value_after_labels(
    lines,
    labels,
):
    index = find_index_any(
        lines,
        labels,
    )

    if index is None:
        return None

    if index + 1 >= len(lines):
        return None

    return lines[index + 1]


def extract_section(
    lines,
    start_labels,
    end_labels,
):
    start_index = find_index_any(
        lines,
        start_labels,
    )

    if start_index is None:
        return []

    content_start = start_index + 1

    normalized_end_labels = {
        normalize_text(label)
        for label in end_labels
    }

    end_index = None

    # فقط بعد از start دنبال پایان section بگرد
    for index in range(
        content_start,
        len(lines),
    ):
        if (
            normalize_text(lines[index])
            in normalized_end_labels
        ):
            end_index = index
            break

    if end_index is None:
        return lines[content_start:]

    return lines[
        content_start:end_index
    ]


# --------------------------------------------------
# Structured extraction
# --------------------------------------------------

def extract_software_from_key_requirements(
    lines,
):
    software = []

    pattern = re.compile(
        r"^(.*?)\s*-\s*(.*?)$"
    )

    for line in lines:
        match = pattern.match(line)

        if not match:
            continue

        name = match.group(1).strip()
        raw_level = match.group(2).strip()

        normalized_level = normalize_text(
            raw_level
        )

        if (
            normalized_level
            not in SOFTWARE_LEVEL_MAP
        ):
            continue

        software.append(
            {
                "name": name,
                "level": (
                    SOFTWARE_LEVEL_MAP[
                        normalized_level
                    ]
                ),
                "raw_level": raw_level,
            }
        )

    return software


def extract_experience(lines):
    experience_keywords = [
        "experience",
        "سابقه",
    ]

    for line in lines:
        normalized = normalize_text(line)

        if any(
            keyword in normalized
            for keyword in experience_keywords
        ):
            return line

    return None


def extract_top_metadata(
    lines,
    title,
):
    normalized_title = normalize_text(
        title
    )

    title_index = None

    for index, line in enumerate(lines):
        if normalize_text(line) == normalized_title:
            title_index = index
            break

    if title_index is None:
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

    h1 = page.locator("h1")

    if await h1.count() > 0:
        return (
            await h1.first.inner_text()
        ).strip()

    return None


# --------------------------------------------------
# Main parser
# --------------------------------------------------

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

    title = await get_job_title(
        page
    )

    body_text = await page.locator(
        "body"
    ).inner_text()

    lines = clean_lines(
        body_text
    )

    # ----------------------------------------
    # Top metadata
    # ----------------------------------------

    top_metadata = extract_top_metadata(
        lines,
        title,
    )

    # ----------------------------------------
    # Key requirements
    # ----------------------------------------

    key_requirements = extract_section(
        lines,
        SECTION_LABELS[
            "key_requirements"
        ],
        SECTION_LABELS[
            "job_description"
        ],
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
    # Job description
    # ----------------------------------------

    job_description_lines = (
        extract_section(
            lines,
            SECTION_LABELS[
                "job_description"
            ],
            SECTION_LABELS[
                "job_requirements"
            ],
        )
    )

    job_description = "\n".join(
        job_description_lines
    )

    # ----------------------------------------
    # Job requirements section
    # ----------------------------------------

    job_requirements_lines = (
        extract_section(
            lines,
            SECTION_LABELS[
                "job_requirements"
            ],
            JOB_REQUIREMENTS_END_LABELS,
        )
    )

    # ----------------------------------------
    # Company info
    # ----------------------------------------

    company_info = {
        "size": get_value_after_labels(
            lines,
            FIELD_LABELS[
                "company_size"
            ],
        ),

        "industry": get_value_after_labels(
            lines,
            FIELD_LABELS[
                "industry"
            ],
        ),

        "type": get_value_after_labels(
            lines,
            FIELD_LABELS[
                "company_type"
            ],
        ),

        "establishment_year": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "establishment_year"
                ],
            )
        ),

        "ownership_type": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "ownership_type"
                ],
            )
        ),
    }

    # ----------------------------------------
    # Final object
    # ----------------------------------------

    job = {
        "job_id": job_id,
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
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "working_days"
                ],
            )
        ),

        "business_trips": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "business_trips"
                ],
            )
        ),

        "facilities_and_benefits": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "facilities"
                ],
            )
        ),

        "experience": experience,

        "gender": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "gender"
                ],
            )
        ),

        "education": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "education"
                ],
            )
        ),

        "military_service": (
            get_value_after_labels(
                lines,
                FIELD_LABELS[
                    "military_service"
                ],
            )
        ),

        "software": software,

        "company_info": (
            company_info
        ),

        "key_requirements_raw": (
            key_requirements
        ),

        "job_description": (
            job_description
        ),

        "job_requirements_raw": (
            job_requirements_lines
        ),
    }

    return job


# --------------------------------------------------
# Persistence
# --------------------------------------------------

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


def load_failures():
    if not FAILURES_PATH.exists():
        return {}

    with FAILURES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_failures(failures):
    FAILURES_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with FAILURES_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            failures,
            file,
            ensure_ascii=False,
            indent=2,
        )


def parsed_job_exists(job_id):
    output_path = (
        PARSED_DIR
        / f"job_{job_id}.json"
    )

    return output_path.exists()


async def parse_job_with_retries(
    page,
    job_id,
    url,
    max_retries=MAX_RETRIES,
):
    last_error = None

    for attempt in range(
        1,
        max_retries + 1,
    ):
        try:
            job = await parse_job(
                page=page,
                job_id=job_id,
                url=url,
            )

            return job, None

        except (
            PlaywrightTimeoutError,
            PlaywrightError,
            Exception,
        ) as error:
            last_error = error

            print(
                f"  Attempt "
                f"{attempt}/{max_retries} failed"
            )

            print(
                f"  {type(error).__name__}: "
                f"{error}"
            )

            if attempt < max_retries:
                wait_seconds = (
                    RETRY_DELAY_SECONDS
                    * attempt
                )

                print(
                    f"  Retrying in "
                    f"{wait_seconds}s..."
                )

                await page.wait_for_timeout(
                    wait_seconds * 1000
                )

    return None, last_error

async def main():
    raw_jobs = load_raw_jobs()

    PARSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    failures = load_failures()

    total_candidates = len(raw_jobs)

    already_parsed = 0
    parsed_this_run = 0
    failed_this_run = 0

    print("\n" + "=" * 70)
    print("BULK JOB PARSER")
    print("=" * 70)

    print(
        f"Total candidates: "
        f"{total_candidates}"
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

        for index, (
            job_id,
            raw_job,
        ) in enumerate(
            raw_jobs.items(),
            start=1,
        ):
            print(
                "\n"
                + "-" * 70
            )

            print(
                f"[{index}/{total_candidates}] "
                f"Job {job_id}"
            )

            # ----------------------------------
            # Resume
            # ----------------------------------

            if parsed_job_exists(job_id):
                already_parsed += 1

                print(
                    "✓ Already parsed — skipping"
                )

                continue

            url = raw_job["url"]

            # ----------------------------------
            # Parse + retries
            # ----------------------------------

            job, error = (
                await parse_job_with_retries(
                    page=page,
                    job_id=job_id,
                    url=url,
                )
            )

            # ----------------------------------
            # Failed
            # ----------------------------------

            if job is None:
                failed_this_run += 1

                failures[job_id] = {
                    "url": url,
                    "error_type": (
                        type(error).__name__
                        if error
                        else None
                    ),
                    "error": (
                        str(error)
                        if error
                        else None
                    ),
                }

                save_failures(
                    failures
                )

                print(
                    f"✗ Failed permanently: "
                    f"{job_id}"
                )

                continue

            # ----------------------------------
            # Success
            # ----------------------------------

            output_path = save_parsed_job(
                job
            )

            parsed_this_run += 1

            # اگر قبلاً failure بوده،
            # بعد از موفقیت پاکش کن
            if job_id in failures:
                del failures[job_id]

                save_failures(
                    failures
                )

            print(
                f"✓ Parsed: "
                f"{job['title']}"
            )

            print(
                f"  Company: "
                f"{job['company_name']}"
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
                f"  Saved: "
                f"{output_path}"
            )

            # فشار کمتر روی سایت
            await page.wait_for_timeout(
                REQUEST_DELAY_MS
            )

        await browser.close()

    # ------------------------------------------
    # Final statistics
    # ------------------------------------------

    total_parsed = len(
        list(
            PARSED_DIR.glob(
                "job_*.json"
            )
        )
    )

    remaining = (
        total_candidates
        - total_parsed
    )

    print("\n" + "=" * 70)
    print("PARSE SUMMARY")
    print("=" * 70)

    print(
        f"Total candidates: "
        f"{total_candidates}"
    )

    print(
        f"Already parsed: "
        f"{already_parsed}"
    )

    print(
        f"Parsed this run: "
        f"{parsed_this_run}"
    )

    print(
        f"Failed this run: "
        f"{failed_this_run}"
    )

    print(
        f"Total parsed: "
        f"{total_parsed}"
    )

    print(
        f"Remaining: "
        f"{remaining}"
    )

    print(
        f"Failure log entries: "
        f"{len(failures)}"
    )


if __name__ == "__main__":
    asyncio.run(main())