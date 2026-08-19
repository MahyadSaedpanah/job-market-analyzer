import json
import shutil
from pathlib import Path

from ollama import chat, ResponseError
from pydantic import ValidationError

from ai_prompt import SYSTEM_PROMPT, build_user_prompt
from ai_schema import AIJobAnalysis
from ai_postprocessor import postprocess_analysis


MODEL_NAME = "qwen3:4b-instruct"

BENCHMARK_MANIFEST_PATH = Path("data/benchmark/manifest.json")
BENCHMARK_JOBS_DIR = Path("data/benchmark/jobs")

RESULTS_DIR = Path("data/benchmark/results/qwen3_4b_instruct")
RAW_DIR = RESULTS_DIR / "raw"
VALIDATED_DIR = RESULTS_DIR / "validated"
PROCESSED_DIR = RESULTS_DIR / "processed"

FAILURE_LOG_PATH = RESULTS_DIR / "failures.json"
SUMMARY_PATH = RESULTS_DIR / "summary.json"

# اگر خواستی نتایج را همزمان در Google Drive هم ذخیره کنی:
DRIVE_SYNC_DIR = Path("/content/drive/MyDrive/job-market-analyzer-results/qwen3_4b_instruct")


def ensure_dirs():
    for path in [
        RAW_DIR,
        VALIDATED_DIR,
        PROCESSED_DIR,
        DRIVE_SYNC_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def load_manifest():
    with BENCHMARK_MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_job(job_id):
    path = BENCHMARK_JOBS_DIR / f"job_{job_id}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sync_file_to_drive(path):
    relative = path.relative_to(RESULTS_DIR)
    destination = DRIVE_SYNC_DIR / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def run_one_job(job):
    job_id = job["job_id"]
    title = job.get("title")

    raw_path = RAW_DIR / f"job_{job_id}_raw.txt"
    validated_path = VALIDATED_DIR / f"job_{job_id}.json"
    processed_path = PROCESSED_DIR / f"job_{job_id}.json"

    if processed_path.exists():
        print(f"SKIP  {job_id} | {title}")
        return {
            "job_id": job_id,
            "status": "skipped",
            "title": title,
        }

    print(f"RUN   {job_id} | {title}")

    user_prompt = build_user_prompt(job)

    response = chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        format=AIJobAnalysis.model_json_schema(),
        think=False,
        options={
            "temperature": 0,
            "num_ctx": 16384,
            "num_predict": 4096,
        },
    )

    raw_content = response.message.content
    save_text(raw_path, raw_content)
    sync_file_to_drive(raw_path)

    validated = AIJobAnalysis.model_validate_json(raw_content)
    save_json(validated_path, validated.model_dump(mode="json"))
    sync_file_to_drive(validated_path)

    processed = postprocess_analysis(validated)
    save_json(processed_path, processed.model_dump(mode="json"))
    sync_file_to_drive(processed_path)

    return {
        "job_id": job_id,
        "status": "success",
        "title": title,
        "primary_role": processed.role_classification.primary_role.value,
        "target_group": processed.role_classification.target_group.value,
        "skills": len(processed.skills),
        "responsibilities": len(processed.responsibilities),
        "engineering_expectations": len(processed.engineering_expectations),
    }


def main():
    ensure_dirs()

    manifest = load_manifest()

    results = []
    failures = []

    print("=" * 70)
    print("BENCHMARK RUN")
    print("=" * 70)
    print(f"Model: {MODEL_NAME}")
    print(f"Jobs in manifest: {len(manifest)}")

    for item in manifest:
        job_id = item["job_id"]

        try:
            job = load_job(job_id)
            result = run_one_job(job)
            results.append(result)

        except ResponseError as e:
            failures.append({
                "job_id": job_id,
                "error_type": "ollama_response_error",
                "error": str(e),
            })
            print(f"FAIL  {job_id} | Ollama error")

        except ValidationError as e:
            failures.append({
                "job_id": job_id,
                "error_type": "validation_error",
                "error": str(e),
            })
            print(f"FAIL  {job_id} | Validation error")

        except Exception as e:
            failures.append({
                "job_id": job_id,
                "error_type": "unexpected_error",
                "error": str(e),
            })
            print(f"FAIL  {job_id} | Unexpected error")

        save_json(FAILURE_LOG_PATH, failures)
        sync_file_to_drive(FAILURE_LOG_PATH)

    summary = {
        "model": MODEL_NAME,
        "total_jobs": len(manifest),
        "success_count": sum(1 for x in results if x["status"] == "success"),
        "skipped_count": sum(1 for x in results if x["status"] == "skipped"),
        "failure_count": len(failures),
        "results": results,
    }

    save_json(SUMMARY_PATH, summary)
    sync_file_to_drive(SUMMARY_PATH)

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Success: {summary['success_count']}")
    print(f"Skipped: {summary['skipped_count']}")
    print(f"Failures: {summary['failure_count']}")
    print(f"Saved summary: {SUMMARY_PATH}")
    print(f"Synced to drive: {DRIVE_SYNC_DIR}")


if __name__ == "__main__":
    main()