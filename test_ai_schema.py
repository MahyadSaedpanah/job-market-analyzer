import json

from pydantic import ValidationError

from ai_schema import AIJobAnalysis


SAMPLE_ANALYSIS = {
    "job_id": "1481754",

    "role_classification": {
        "primary_role": "data_scientist",
        "secondary_roles": [
            "machine_learning_engineer"
        ],
        "target_group": "core",
        "relevance_score": 100,
        "reason": (
            "The position is explicitly a Data Scientist role "
            "focused on production machine learning systems."
        ),
    },

    "seniority": "mid",

    "experience": {
        "min_years": 3,
        "max_years": None,
        "raw_text": (
            "3+ years of experience as a Data Scientist "
            "or Machine Learning Engineer."
        ),
    },

    "education": {
        "required": None,
        "minimum_degree": None,
        "fields": [],
        "preferred_fields": [],
        "evidence": None,
    },

    "skills": [
        {
            "canonical_name": "Python",
            "raw_name": "Python",
            "category": "programming_language",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": "Strong Python programming skills.",
        },
        {
            "canonical_name": "SQL",
            "raw_name": "SQL",
            "category": "query_language",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Experience with SQL and large-scale data analysis."
            ),
        },
        {
            "canonical_name": "XGBoost",
            "raw_name": "XGBoost",
            "category": "ml_framework",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Excellent knowledge of machine learning algorithms "
                "including tree-based models (XGBoost, LightGBM, CatBoost)."
            ),
        },
        {
            "canonical_name": "LightGBM",
            "raw_name": "LightGBM",
            "category": "ml_framework",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Excellent knowledge of machine learning algorithms "
                "including tree-based models (XGBoost, LightGBM, CatBoost)."
            ),
        },
        {
            "canonical_name": "CatBoost",
            "raw_name": "CatBoost",
            "category": "ml_framework",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Excellent knowledge of machine learning algorithms "
                "including tree-based models (XGBoost, LightGBM, CatBoost)."
            ),
        },
        {
            "canonical_name": "Clustering",
            "raw_name": "clustering",
            "category": "machine_learning",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Excellent knowledge of machine learning algorithms "
                "including clustering."
            ),
        },
        {
            "canonical_name": "Time Series Forecasting",
            "raw_name": "time-series forecasting",
            "category": "time_series",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Excellent knowledge of time-series forecasting."
            ),
        },
        {
            "canonical_name": "Recommendation Systems",
            "raw_name": "recommendation systems",
            "category": "recommendation_system",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Excellent knowledge of recommendation systems."
            ),
        },
        {
            "canonical_name": "Statistics",
            "raw_name": "statistics",
            "category": "statistics",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Strong understanding of statistics and probability."
            ),
        },
        {
            "canonical_name": "Pandas",
            "raw_name": "Pandas",
            "category": "data_library",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Experience using Pandas, NumPy, and Scikit-learn."
            ),
        },
        {
            "canonical_name": "NumPy",
            "raw_name": "NumPy",
            "category": "data_library",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Experience using Pandas, NumPy, and Scikit-learn."
            ),
        },
        {
            "canonical_name": "Scikit-learn",
            "raw_name": "Scikit-learn",
            "category": "ml_framework",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Experience using Pandas, NumPy, and Scikit-learn."
            ),
        },
        {
            "canonical_name": "Git",
            "raw_name": "Git",
            "category": "version_control",
            "requirement": "required",
            "proficiency": "unspecified",
            "evidence": (
                "Familiarity with Git and collaborative "
                "software development."
            ),
        },
    ],

    "responsibilities": [
        {
            "text": (
                "Design and develop machine learning models "
                "for real-world business problems."
            ),
            "category": "model_development",
        },
        {
            "text": (
                "Explore large datasets to discover patterns "
                "and generate actionable insights."
            ),
            "category": "data_analysis",
        },
        {
            "text": (
                "Build features and data pipelines "
                "for production ML systems."
            ),
            "category": "data_pipeline",
        },
        {
            "text": (
                "Deploy and monitor machine learning "
                "models in production."
            ),
            "category": "deployment",
        },
    ],

    "soft_skills": [
        {
            "canonical_name": "Communication",
            "raw_name": "Strong communication skills",
            "requirement": "required",
            "evidence": (
                "Strong communication skills and ability to explain "
                "technical concepts to non-technical stakeholders."
            ),
        }
    ],

    "domain_knowledge": [],

    "engineering_expectations": [
        {
            "type": "production_deployment",
            "requirement": "required",
            "evidence": (
                "Experience deploying models into production."
            ),
        },
        {
            "type": "monitoring",
            "requirement": "required",
            "evidence": (
                "Deploy and monitor machine learning models "
                "in production."
            ),
        },
        {
            "type": "clean_code",
            "requirement": "required",
            "evidence": (
                "Write clean, maintainable, and "
                "well-tested Python code."
            ),
        },
        {
            "type": "git",
            "requirement": "required",
            "evidence": (
                "Familiarity with Git and collaborative "
                "software development."
            ),
        },
    ],

    "confidence": {
        "role_classification": 99,
        "seniority": 75,
    },
}


def main():
    try:
        validated = AIJobAnalysis.model_validate(
            SAMPLE_ANALYSIS
        )

        print("=" * 70)
        print("VALIDATION SUCCESS")
        print("=" * 70)

        print(
            f"Job ID: "
            f"{validated.job_id}"
        )

        print(
            f"Primary role: "
            f"{validated.role_classification.primary_role.value}"
        )

        print(
            f"Skills: "
            f"{len(validated.skills)}"
        )

        print(
            f"Responsibilities: "
            f"{len(validated.responsibilities)}"
        )

        print(
            f"Engineering expectations: "
            f"{len(validated.engineering_expectations)}"
        )

        print("\nValidated JSON:")
        print(
            json.dumps(
                validated.model_dump(
                    mode="json"
                ),
                ensure_ascii=False,
                indent=2,
            )
        )

    except ValidationError as error:
        print("=" * 70)
        print("VALIDATION FAILED")
        print("=" * 70)

        print(error)


if __name__ == "__main__":
    main()