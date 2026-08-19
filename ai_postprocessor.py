import json
from pathlib import Path

from ai_schema import (
    AIJobAnalysis,
    EngineeringExpectation,
    EngineeringExpectationType,
    RequirementLevel,
    ResponsibilityCategory,
    SkillCategory,
)


INPUT_PATH = Path(
    "data/benchmark/results/qwen3_4b_instruct/job_1481754.json"
)

OUTPUT_PATH = Path(
    "data/benchmark/results/qwen3_4b_instruct/"
    "job_1481754_processed.json"
)


# ------------------------------------------------------------
# Canonical skill normalization
# ------------------------------------------------------------

SKILL_NORMALIZATION = {
    "git": ("Git", SkillCategory.VERSION_CONTROL),

    "time_series": (
        "Time Series Forecasting",
        SkillCategory.TIME_SERIES,
    ),
    "time series": (
        "Time Series Forecasting",
        SkillCategory.TIME_SERIES,
    ),
    "time-series forecasting": (
        "Time Series Forecasting",
        SkillCategory.TIME_SERIES,
    ),

    "recommendation_system": (
        "Recommendation Systems",
        SkillCategory.RECOMMENDATION_SYSTEM,
    ),
    "recommendation system": (
        "Recommendation Systems",
        SkillCategory.RECOMMENDATION_SYSTEM,
    ),
    "recommendation systems": (
        "Recommendation Systems",
        SkillCategory.RECOMMENDATION_SYSTEM,
    ),

    "statistics": (
        "Statistics",
        SkillCategory.STATISTICS,
    ),

    "probability": (
        "Probability",
        SkillCategory.STATISTICS,
    ),

    "experimentation": (
        "Experimentation",
        SkillCategory.EXPERIMENTATION,
    ),

    "pandas": (
        "Pandas",
        SkillCategory.DATA_LIBRARY,
    ),

    "numpy": (
        "NumPy",
        SkillCategory.DATA_LIBRARY,
    ),

    "scikit-learn": (
        "Scikit-learn",
        SkillCategory.ML_FRAMEWORK,
    ),

    "sklearn": (
        "Scikit-learn",
        SkillCategory.ML_FRAMEWORK,
    ),

    "xgboost": (
        "XGBoost",
        SkillCategory.ML_FRAMEWORK,
    ),

    "lightgbm": (
        "LightGBM",
        SkillCategory.ML_FRAMEWORK,
    ),

    "catboost": (
        "CatBoost",
        SkillCategory.ML_FRAMEWORK,
    ),

    "python": (
        "Python",
        SkillCategory.PROGRAMMING_LANGUAGE,
    ),

    "sql": (
        "SQL",
        SkillCategory.QUERY_LANGUAGE,
    ),

    "sql server": (
        "SQL Server",
        SkillCategory.DATABASE,
    ),
}


def normalize_skills(analysis):
    for skill in analysis.skills:
        key = (
            skill.canonical_name
            .strip()
            .casefold()
        )

        if key not in SKILL_NORMALIZATION:
            continue

        canonical_name, category = (
            SKILL_NORMALIZATION[key]
        )

        skill.canonical_name = canonical_name
        skill.category = category


# ------------------------------------------------------------
# Responsibility corrections
# ------------------------------------------------------------

def normalize_responsibilities(analysis):
    for responsibility in analysis.responsibilities:
        text = responsibility.text.casefold()

        if (
            "clean" in text
            or "maintainable" in text
            or "well-tested" in text
        ):
            responsibility.category = (
                ResponsibilityCategory
                .SOFTWARE_ENGINEERING
            )

        elif (
            "document" in text
            or "documentation" in text
        ):
            responsibility.category = (
                ResponsibilityCategory
                .DOCUMENTATION
            )

        elif (
            "monitor" in text
            or "monitoring" in text
        ):
            # Deployment sentences can stay deployment,
            # but pure improvement/monitoring work becomes monitoring.
            if "deploy" not in text:
                responsibility.category = (
                    ResponsibilityCategory
                    .MONITORING
                )


# ------------------------------------------------------------
# Engineering expectation helpers
# ------------------------------------------------------------

def add_expectation(
    expectations,
    expectation_type,
    requirement,
    evidence,
):
    if expectation_type in expectations:
        return

    expectations[expectation_type] = (
        EngineeringExpectation(
            type=expectation_type,
            requirement=requirement,
            evidence=evidence,
        )
    )


def derive_engineering_expectations(analysis):
    expectations = {
        item.type: item
        for item in analysis.engineering_expectations
    }

    # --------------------------------------------------------
    # Derive from responsibilities
    # --------------------------------------------------------

    for responsibility in analysis.responsibilities:
        text = responsibility.text
        normalized = text.casefold()

        if (
            "deploy" in normalized
            and (
                "production" in normalized
                or "model" in normalized
            )
        ):
            add_expectation(
                expectations,
                EngineeringExpectationType
                .PRODUCTION_DEPLOYMENT,
                RequirementLevel.REQUIRED,
                text,
            )

        if (
            "monitor" in normalized
            or "monitoring" in normalized
        ):
            add_expectation(
                expectations,
                EngineeringExpectationType.MONITORING,
                RequirementLevel.REQUIRED,
                text,
            )

        if (
            "well-tested" in normalized
            or "testing" in normalized
            or "tests" in normalized
        ):
            add_expectation(
                expectations,
                EngineeringExpectationType.TESTING,
                RequirementLevel.REQUIRED,
                text,
            )

        if (
            "clean" in normalized
            or "maintainable" in normalized
        ):
            add_expectation(
                expectations,
                EngineeringExpectationType.CLEAN_CODE,
                RequirementLevel.REQUIRED,
                text,
            )

        if (
            "api" in normalized
            and (
                "build" in normalized
                or "develop" in normalized
                or "implement" in normalized
            )
        ):
            add_expectation(
                expectations,
                EngineeringExpectationType.API_DEVELOPMENT,
                RequirementLevel.REQUIRED,
                text,
            )

    # --------------------------------------------------------
    # Derive from explicit skills
    # --------------------------------------------------------

    for skill in analysis.skills:
        name = skill.canonical_name.casefold()

        if name == "git":
            add_expectation(
                expectations,
                EngineeringExpectationType.GIT,
                skill.requirement,
                skill.evidence,
            )

        elif name == "docker":
            add_expectation(
                expectations,
                EngineeringExpectationType.DOCKER,
                skill.requirement,
                skill.evidence,
            )

        elif name == "kubernetes":
            add_expectation(
                expectations,
                EngineeringExpectationType.KUBERNETES,
                skill.requirement,
                skill.evidence,
            )

        elif name in {
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "google cloud platform",
        }:
            add_expectation(
                expectations,
                EngineeringExpectationType.CLOUD,
                skill.requirement,
                skill.evidence,
            )

        elif name in {
            "ci/cd",
            "ci cd",
            "continuous integration",
            "continuous deployment",
        }:
            add_expectation(
                expectations,
                EngineeringExpectationType.CI_CD,
                skill.requirement,
                skill.evidence,
            )

    analysis.engineering_expectations = list(
        expectations.values()
    )


# ------------------------------------------------------------
# Main processing
# ------------------------------------------------------------

def postprocess_analysis(analysis):
    normalize_skills(analysis)
    normalize_responsibilities(analysis)
    derive_engineering_expectations(analysis)

    # Validate the processed result again.
    return AIJobAnalysis.model_validate(
        analysis.model_dump(
            mode="json"
        )
    )


def main():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_data = json.load(file)

    analysis = AIJobAnalysis.model_validate(
        raw_data
    )

    processed = postprocess_analysis(
        analysis
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            processed.model_dump(
                mode="json"
            ),
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("=" * 70)
    print("POST-PROCESSING SUCCESS")
    print("=" * 70)

    print(
        f"Skills: "
        f"{len(processed.skills)}"
    )

    print(
        f"Responsibilities: "
        f"{len(processed.responsibilities)}"
    )

    print(
        "Engineering expectations:",
        len(
            processed.engineering_expectations
        ),
    )

    print("\nNORMALIZED SKILLS")
    print("-" * 70)

    for skill in processed.skills:
        print(
            f"{skill.canonical_name:<30}"
            f" | {skill.category.value}"
        )

    print("\nRESPONSIBILITIES")
    print("-" * 70)

    for item in processed.responsibilities:
        print(
            f"{item.category.value:<24}"
            f" | {item.text}"
        )

    print("\nENGINEERING EXPECTATIONS")
    print("-" * 70)

    for item in processed.engineering_expectations:
        print(
            f"{item.type.value:<24}"
            f" | {item.requirement.value:<12}"
            f" | {item.evidence}"
        )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()