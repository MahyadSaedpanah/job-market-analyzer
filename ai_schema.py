import json
from enum import Enum
from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


SCHEMA_OUTPUT_PATH = Path(
    "data/schema/ai_job_analysis.schema.json"
)


# ============================================================
# Base model
# ============================================================

class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# ============================================================
# Role classification
# ============================================================

class PrimaryRole(str, Enum):
    DATA_SCIENTIST = "data_scientist"
    DATA_ANALYST = "data_analyst"
    MACHINE_LEARNING_ENGINEER = "machine_learning_engineer"
    AI_ENGINEER = "ai_engineer"

    DATA_ENGINEER = "data_engineer"
    BI_ANALYST = "bi_analyst"
    NLP_ENGINEER = "nlp_engineer"
    COMPUTER_VISION_ENGINEER = "computer_vision_engineer"
    LLM_ENGINEER = "llm_engineer"

    OTHER = "other"


class TargetGroup(str, Enum):
    CORE = "core"
    ADJACENT = "adjacent"
    IRRELEVANT = "irrelevant"


class Seniority(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    UNSPECIFIED = "unspecified"


class RoleClassification(SchemaModel):
    primary_role: PrimaryRole

    secondary_roles: list[PrimaryRole] = Field(
        default_factory=list
    )

    target_group: TargetGroup

    relevance_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Relevance to the target Data/ML/AI job market."
        ),
    )

    reason: str = Field(
        min_length=1,
        description=(
            "Short explanation for the classification."
        ),
    )

    @model_validator(mode="after")
    def validate_secondary_roles(self):
        if self.primary_role in self.secondary_roles:
            raise ValueError(
                "primary_role must not also appear "
                "in secondary_roles"
            )

        if len(self.secondary_roles) != len(
            set(self.secondary_roles)
        ):
            raise ValueError(
                "secondary_roles must be unique"
            )

        return self


# ============================================================
# Experience
# ============================================================

class Experience(SchemaModel):
    min_years: float | None = Field(
        default=None,
        ge=0,
    )

    max_years: float | None = Field(
        default=None,
        ge=0,
    )

    raw_text: str | None = None

    @model_validator(mode="after")
    def validate_year_range(self):
        if (
            self.min_years is not None
            and self.max_years is not None
            and self.max_years < self.min_years
        ):
            raise ValueError(
                "max_years cannot be less than min_years"
            )

        return self


# ============================================================
# Education
# ============================================================

class DegreeLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    UNSPECIFIED = "unspecified"


class Education(SchemaModel):
    required: bool | None = None

    minimum_degree: DegreeLevel | None = None

    fields: list[str] = Field(
        default_factory=list
    )

    preferred_fields: list[str] = Field(
        default_factory=list
    )

    evidence: str | None = None


# ============================================================
# Skills
# ============================================================

class SkillCategory(str, Enum):
    PROGRAMMING_LANGUAGE = "programming_language"
    QUERY_LANGUAGE = "query_language"

    DATABASE = "database"
    DATA_WAREHOUSE = "data_warehouse"

    DATA_ANALYSIS = "data_analysis"
    DATA_VISUALIZATION = "data_visualization"
    BI_TOOL = "bi_tool"

    MACHINE_LEARNING = "machine_learning"
    DEEP_LEARNING = "deep_learning"
    STATISTICS = "statistics"
    EXPERIMENTATION = "experimentation"

    ML_FRAMEWORK = "ml_framework"
    DATA_LIBRARY = "data_library"

    TIME_SERIES = "time_series"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION_SYSTEM = "recommendation_system"
    GENERATIVE_AI = "generative_ai"
    LLM = "llm"
    RAG = "rag"
    AI_AGENTS = "ai_agents"

    DATA_ENGINEERING = "data_engineering"
    BIG_DATA = "big_data"

    API_BACKEND = "api_backend"
    DEPLOYMENT = "deployment"
    MLOPS = "mlops"
    DEVOPS = "devops"
    CLOUD = "cloud"
    CONTAINERIZATION = "containerization"
    ORCHESTRATION = "orchestration"
    VERSION_CONTROL = "version_control"
    CI_CD = "ci_cd"

    SOFTWARE_ENGINEERING = "software_engineering"

    BUSINESS_ANALYTICS = "business_analytics"
    DOMAIN_KNOWLEDGE = "domain_knowledge"

    SOFT_SKILL = "soft_skill"
    LANGUAGE_SKILL = "language_skill"

    OTHER = "other"


class RequirementLevel(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"
    MENTIONED = "mentioned"


class ProficiencyLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNSPECIFIED = "unspecified"


class Skill(SchemaModel):
    canonical_name: str = Field(
        min_length=1,
        description=(
            "Normalized skill name, e.g. "
            "'Scikit-learn' or 'Power BI'."
        ),
    )

    raw_name: str = Field(
        min_length=1,
        description=(
            "How the skill appeared in the original job ad."
        ),
    )

    category: SkillCategory

    requirement: RequirementLevel

    proficiency: ProficiencyLevel = (
        ProficiencyLevel.UNSPECIFIED
    )

    evidence: str = Field(
        min_length=1,
        description=(
            "Short supporting text from the job advertisement."
        ),
    )


# ============================================================
# Responsibilities
# ============================================================

class ResponsibilityCategory(str, Enum):
    DATA_ANALYSIS = "data_analysis"
    MODEL_DEVELOPMENT = "model_development"
    EXPERIMENTATION = "experimentation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    DATA_PIPELINE = "data_pipeline"
    REPORTING = "reporting"
    STAKEHOLDER_COMMUNICATION = (
        "stakeholder_communication"
    )
    RESEARCH = "research"
    OTHER = "other"


class Responsibility(SchemaModel):
    text: str = Field(
        min_length=1
    )

    category: ResponsibilityCategory


# ============================================================
# Soft skills
# ============================================================

class SoftSkill(SchemaModel):
    canonical_name: str = Field(
        min_length=1
    )

    raw_name: str = Field(
        min_length=1
    )

    requirement: RequirementLevel

    evidence: str = Field(
        min_length=1
    )


# ============================================================
# Domain knowledge
# ============================================================

class DomainKnowledge(SchemaModel):
    canonical_name: str = Field(
        min_length=1
    )

    raw_name: str = Field(
        min_length=1
    )

    requirement: RequirementLevel

    evidence: str = Field(
        min_length=1
    )


# ============================================================
# Engineering expectations
# ============================================================

class EngineeringExpectationType(str, Enum):
    PRODUCTION_DEPLOYMENT = "production_deployment"
    MODEL_SERVING = "model_serving"
    MONITORING = "monitoring"
    API_DEVELOPMENT = "api_development"

    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"
    CI_CD = "ci_cd"

    TESTING = "testing"
    CLEAN_CODE = "clean_code"
    GIT = "git"


class EngineeringExpectation(SchemaModel):
    type: EngineeringExpectationType

    requirement: RequirementLevel

    evidence: str = Field(
        min_length=1
    )


# ============================================================
# Confidence
# ============================================================

class ExtractionConfidence(SchemaModel):
    role_classification: float = Field(
        ge=0,
        le=1,
    )

    seniority: float = Field(
        ge=0,
        le=1,
    )


# ============================================================
# Final AI output
# ============================================================

class AIJobAnalysis(SchemaModel):
    job_id: str = Field(
        min_length=1
    )

    role_classification: RoleClassification

    seniority: Seniority

    experience: Experience

    education: Education

    skills: list[Skill] = Field(
        default_factory=list
    )

    responsibilities: list[Responsibility] = Field(
        default_factory=list
    )

    soft_skills: list[SoftSkill] = Field(
        default_factory=list
    )

    domain_knowledge: list[DomainKnowledge] = Field(
        default_factory=list
    )

    engineering_expectations: list[
        EngineeringExpectation
    ] = Field(
        default_factory=list
    )

    confidence: ExtractionConfidence

    @model_validator(mode="after")
    def validate_unique_skills(self):
        names = [
            skill.canonical_name.casefold()
            for skill in self.skills
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "skills must contain unique canonical names"
            )

        return self

    @model_validator(mode="after")
    def validate_unique_engineering_expectations(self):
        expectation_types = [
            item.type
            for item in self.engineering_expectations
        ]

        if len(expectation_types) != len(
            set(expectation_types)
        ):
            raise ValueError(
                "engineering_expectations "
                "must contain unique types"
            )

        return self


# ============================================================
# Export JSON Schema
# ============================================================

def save_json_schema():
    SCHEMA_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    schema = (
        AIJobAnalysis.model_json_schema()
    )

    with SCHEMA_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            schema,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Schema saved to: "
        f"{SCHEMA_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    save_json_schema()