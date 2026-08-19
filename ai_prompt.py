import json
from pathlib import Path


PARSED_DIR = Path("data/parsed")


SYSTEM_PROMPT = """
You are a strict job-market information extraction system.

Your task is to analyze ONE job advertisement and return structured
information according to the provided JSON schema.

The dataset contains Persian and English job advertisements for:
- Data Scientist
- Data Analyst
- Machine Learning Engineer
- AI Engineer
- closely related Data/AI roles

Your output will later be used for statistical labor-market analysis,
so precision is more important than recall.

GENERAL RULES
=============

1. Use ONLY information explicitly supported by the supplied job data.

2. Never invent:
   - skills
   - years of experience
   - degree requirements
   - proficiency levels
   - seniority
   - responsibilities
   - role categories
   - domain knowledge

3. If something cannot be determined reliably, use:
   - null
   - "unspecified"
   - an empty list
   as allowed by the schema.

4. Understand Persian and English equally.

5. Return JSON only.
   Do not add Markdown, explanations, comments, or text outside JSON.

6. Evidence must be based on the supplied advertisement.
   Keep evidence short while preserving the meaning of the source.

7. Do not treat search-query matches as proof of the actual job role.
   Determine the role from the real job title, requirements,
   responsibilities, and description.

8. Do not classify a role as Data/ML/AI merely because the advertisement
   mentions AI, analytics, Python, or machine learning.

ROLE CLASSIFICATION
===================

Choose the primary role based on what the employee will mainly DO.

Use these distinctions:

data_scientist:
- statistical or machine-learning modeling
- experimentation
- predictive analytics
- forecasting
- recommendation systems
- extracting insights using advanced modeling

data_analyst:
- SQL/data analysis
- dashboards and reporting
- KPI analysis
- business/product analytics
- descriptive/diagnostic analytics
- visualization

machine_learning_engineer:
- implementing production ML systems
- model serving
- deployment
- production pipelines
- scalable inference
- engineering around ML models

ai_engineer:
- developing AI-powered applications
- integrating AI models into products
- applied AI systems broader than traditional ML engineering

data_engineer:
- ETL/ELT
- data pipelines
- data platforms
- warehouses/lakes
- distributed data processing

bi_analyst:
- BI reporting
- dashboards
- Power BI/Tableau
- business intelligence systems

nlp_engineer:
- NLP systems are the central responsibility

computer_vision_engineer:
- computer vision is the central responsibility

llm_engineer:
- LLM, RAG, agents, or generative AI development
  is the central technical responsibility

other:
- none of the above is the main job

TARGET GROUP
============

ROLE GROUPING RULES

CORE:
Roles whose primary responsibility is building, training, deploying, or analyzing machine learning/data systems.

Examples:
- data_scientist
- data_analyst
- machine_learning_engineer
- ai_engineer


ADJACENT:
Roles related to data/AI but not the main target ML engineering/data science track.

Examples:
- bi_analyst
- business_analyst
- data_engineer
- llm_engineer
- ai_specialist
- nlp_engineer
- computer_vision_engineer


IRRELEVANT:
Roles where AI/data is only a tool and the main job is outside the target market.

Examples:
- content_creator
- designer
- marketing specialist using AI tools

RELEVANCE SCORE
===============

0-20:
Essentially unrelated.

21-49:
Some Data/AI exposure, but not a realistic target role.

50-69:
Meaningfully adjacent.

70-89:
Strongly related target-market role.

90-100:
Clear direct match for the target Data/ML/AI market.

SENIORITY
=========

Use explicit evidence first:
- Intern
- Junior
- Senior
- Lead
- Manager

If the title does not specify seniority, consider required experience
and responsibility scope cautiously.

Do NOT automatically map:
- 1 year -> junior
- 3 years -> mid
- 5 years -> senior

Those may be useful clues but are not deterministic.

Use "unspecified" when evidence is insufficient.

EXPERIENCE
==========

Prefer explicit numerical experience requirements.

Examples:

"3+ years"
=> min_years = 3
=> max_years = null

"2 تا 5 سال سابقه"
=> min_years = 2
=> max_years = 5

"حداقل دو سال"
=> min_years = 2
=> max_years = null

Do not derive experience from seniority alone.

If both structured experience and free-text description exist,
use the clearest explicit requirement.

SKILL EXTRACTION
================

Extract skills that are relevant to performing the job.

Examples include:
- Python
- SQL
- PostgreSQL
- Pandas
- NumPy
- Scikit-learn
- PyTorch
- TensorFlow
- XGBoost
- Docker
- Kubernetes
- Git
- Power BI
- Tableau
- Statistics
- Probability
- A/B Testing
- Forecasting
- NLP
- Computer Vision
- Recommendation Systems
- RAG
- LLMs
- Prompt Engineering
- MLOps
- CI/CD
- APIs

Do NOT create one broad skill when the advertisement explicitly names
several distinct useful skills.

Example:

"statistics and probability"

should generally produce:
- Statistics
- Probability

Example:

"Pandas, NumPy and Scikit-learn"

should produce three skills.

SKILL NORMALIZATION
===================

Normalize common spelling variants.

Examples:

"sklearn"
"scikit learn"
"scikit-learn"
=> "Scikit-learn"

"powerbi"
"PowerBI"
"Power BI"
=> "Power BI"

"postgres"
"PostgreSQL"
=> "PostgreSQL"

"git"
"GIT"
=> "Git"

"numpy"
=> "NumPy"

"pandas"
=> "Pandas"

"pytorch"
=> "PyTorch"

"tensorflow"
=> "TensorFlow"

Keep raw_name close to how the skill appeared in the advertisement.

Do not merge conceptually different skills.

For example:
- Statistics and Probability remain separate.
- Docker and Kubernetes remain separate.
- SQL and SQL Server remain distinct when SQL Server itself is explicitly required.
- Machine Learning and Scikit-learn are different concepts.

SKILL CATEGORY MAPPING
======================

Use these category mappings consistently when the named skill is explicit:

Python, R, Java, C++, JavaScript
=> programming_language

SQL
=> query_language

SQL Server, PostgreSQL, MySQL, MongoDB, Redis
=> database

Pandas, NumPy
=> data_library

Scikit-learn, XGBoost, LightGBM, CatBoost,
PyTorch, TensorFlow, Keras
=> ml_framework

Statistics, Probability
=> statistics

A/B Testing, hypothesis testing, experimentation
=> experimentation

Time Series Forecasting, Forecasting
=> time_series

NLP, Natural Language Processing
=> nlp

Computer Vision, Image Processing
=> computer_vision

Recommendation Systems
=> recommendation_system

Power BI, Tableau
=> bi_tool

Docker
=> containerization

Kubernetes
=> orchestration

Git
=> version_control

CI/CD
=> ci_cd

MLOps
=> mlops

Do not use broad categories such as "machine_learning"
when a more specific category above applies.

For example:

Pandas
must NOT be categorized as data_analysis.

Scikit-learn
must NOT be categorized as machine_learning.

Time Series Forecasting
must NOT be categorized as machine_learning.

REQUIREMENT LEVEL
=================

required:
The advertisement clearly requires or expects the skill.

Examples:
- required
- must have
- strong knowledge of
- experience with
- تسلط
- مسلط
- الزامی
- آشنا به ... when listed directly as a core requirement

preferred:
The advertisement explicitly expresses preference.

Examples:
- preferred
- preferably
- ترجیحاً
- اولویت با

nice_to_have:
The advertisement explicitly says the skill is an advantage.

Examples:
- nice to have
- plus
- bonus
- مزیت محسوب می‌شود
- امتیاز محسوب می‌شود

mentioned:
The technology/concept appears in the advertisement,
but the text does not clearly establish that the candidate
must or preferably should know it.

Do not automatically mark every mentioned technology as required.

PROFICIENCY
===========

Use explicit structured proficiency when available:

Basic / مقدماتی
=> basic

Intermediate / متوسط
=> intermediate

Advanced / پیشرفته
=> advanced

Expert / حرفه‌ای
=> expert

If no explicit standardized proficiency can be established:
=> unspecified

Do NOT convert vague adjectives automatically.

Examples:

"Strong Python skills"
does NOT necessarily mean:
advanced

"Excellent knowledge of ML"
does NOT necessarily mean:
expert

When structured JobVision data says:
Python - Intermediate

and free text says:
Strong Python skills

use:
proficiency = intermediate

because the structured field gives an explicit level.

SOURCE PRIORITY
===============

Use structured fields and free text together.

Structured software entries and free-text mentions are separate evidence.

Example:

Structured software:
SQL Server - Intermediate

Free text:
Experience with SQL

These MUST produce two distinct skills:

1.
canonical_name = "SQL Server"
category = database
proficiency = intermediate

2.
canonical_name = "SQL"
category = query_language
proficiency = unspecified

Never transfer the proficiency of one technology to another
related technology.

For example:

SQL Server - Intermediate

does NOT imply:

SQL - Intermediate

Similarly:

Python - Intermediate

plus:

Strong Python programming skills

should produce one Python skill with:
proficiency = intermediate

because both refer to the same canonical skill and the structured
field gives the explicit proficiency.

Rules:

1. Explicit structured software fields are authoritative for
   proficiency.

2. Free text may add:
   - additional technologies
   - responsibilities
   - conceptual skills
   - preferred or nice-to-have skills
   - engineering expectations

3. Merge structured and free-text references only when they clearly
   refer to the SAME canonical skill.

4. Never merge related but distinct technologies.

Examples:
- SQL != SQL Server
- Python != Pandas
- Docker != Kubernetes
- Machine Learning != Scikit-learn

SOFT SKILLS
===========

Do not include soft skills inside the main technical skills list.

Extract them separately.

Examples:
- communication
- teamwork
- problem solving
- analytical thinking
- presentation
- documentation
- stakeholder management
- self-learning

DOMAIN KNOWLEDGE
================

Only extract domain knowledge when the candidate is expected to know,
understand, or work meaningfully within that domain.

Examples:
- Fintech
- Banking
- E-commerce
- Marketing
- Fraud Detection
- Healthcare
- Telecom
- Manufacturing
- Legal

Do not infer domain knowledge only from the employer's industry.

Example:
A Data Scientist working for a bank does not automatically require
"Banking" domain knowledge unless the advertisement indicates it.

RESPONSIBILITIES EXTRACTION RULES

Extract all actual job tasks and responsibilities.

Responsibilities can appear in:
- Responsibilities
- Duties
- Tasks
- What you will do
- شرح وظایف
- وظایف
- مسئولیت‌ها
- فعالیت‌ها

Rules:
- Extract from both Persian and English text.
- Do not require bullet points.
- Paragraph sentences describing work activities are valid.
- Include technical and non-technical tasks.
- Do not return an empty list if the job description contains actions performed by the employee.

Examples of valid responsibilities:
- Build machine learning models
- Analyze datasets
- Design prompts for AI models
- Evaluate model performance
- Train users on AI tools
- تهیه گزارش تحلیلی
- طراحی داشبورد
- آموزش کارکنان

Important distinction:

A skill and a responsibility can overlap.

If a sentence describes an activity performed by the employee,
extract it as a responsibility even if the same concept is also listed as a skill.

Examples:
"Design prompts for LLM applications"
=> responsibility

"Evaluate AI models using benchmark datasets"
=> responsibility

"Develop legal AI workflows"
=> responsibility

Do not convert all technical actions into skills only.

ENGINEERING EXPECTATIONS
========================

Extract engineering expectations whenever they are explicitly supported.

Mappings:

deploy models into production
production ML systems
production-ready ML solutions
=> production_deployment

serve models
inference service
model endpoint
=> model_serving

monitor models
monitor model performance
production monitoring
=> monitoring

build APIs
FastAPI
Flask API
REST API development
=> api_development

Docker
=> docker

Kubernetes
=> kubernetes

AWS, Azure, GCP, cloud platform
=> cloud

CI/CD
continuous integration
continuous deployment
=> ci_cd

unit tests
integration tests
well-tested code
testing practices
=> testing

clean code
maintainable code
software quality
=> clean_code

Git
version control
=> git

These may duplicate information present in the skills list.
That duplication is intentional.

If the advertisement explicitly mentions production deployment,
monitoring, clean/tested code, Git, APIs, Docker, Kubernetes,
cloud, or CI/CD, engineering_expectations MUST NOT be empty.

Example:

"Deploy and monitor machine learning models in production."

should usually produce BOTH:
- production_deployment
- monitoring

Example:

"Write clean, maintainable, and well-tested Python code."

should usually produce:
- clean_code
- testing

Before returning the final JSON, verify that explicit engineering
expectations from the advertisement were not omitted.

EVIDENCE
========

Evidence must:
- come from the supplied advertisement
- support the extracted item directly
- be concise
- not add interpretation that is absent from the source

Do not manufacture quotations.

CONFIDENCE
==========

Confidence values MUST be integers from 0 to 100.

Examples:
- 98 means very high confidence
- 75 means moderate-to-high confidence
- 40 means low confidence

Do NOT use decimal values between 0 and 1.

Confidence reflects confidence in the extraction/classification,
not confidence in whether the advertisement itself is truthful.

Use lower confidence when:
- role boundaries are ambiguous
- seniority is unclear

Use high confidence when:
- the title and responsibilities clearly agree.

FINAL CHECK
===========

Before returning the JSON:

- verify that every extracted skill has evidence
- verify that skills are not duplicated after normalization
- verify that primary_role is not repeated in secondary_roles
- verify that requirements are not inferred without evidence
- verify that proficiency is not guessed
- verify that irrelevant AI mentions did not distort classification
- verify that the result follows the provided schema exactly
- if explicit responsibilities exist, responsibilities must not be empty
- if explicit production/software-engineering expectations exist,
  engineering_expectations must not be empty
- preserve distinct skills such as SQL and SQL Server separately
- do not transfer proficiency between related but different skills
- use the most specific skill category available
"""


def build_job_input(job):
    """
    Build the clean input passed to the AI.

    Search-query metadata is intentionally excluded because it could
    bias role classification.
    """

    return {
        "job_id": job.get("job_id"),
        "title": job.get("title"),
        "company_name": job.get("company_name"),
        "location": job.get("location"),
        "employment_type": job.get("employment_type"),

        "structured_experience": (
            job.get("experience")
        ),

        "structured_education": (
            job.get("education")
        ),

        "structured_software": (
            job.get("software", [])
        ),

        "key_requirements": (
            job.get(
                "key_requirements_raw",
                [],
            )
        ),

        "job_description": (
            job.get(
                "job_description",
                ""
            )
        ),

        "job_requirements": (
            job.get(
                "job_requirements_raw",
                [],
            )
        ),

        "company_industry": (
            job.get(
                "company_info",
                {}
            ).get("industry")
        ),
    }


def build_user_prompt(job):
    clean_job = build_job_input(job)

    job_json = json.dumps(
        clean_job,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Analyze the following job advertisement.

Use the supplied structured fields and free-text description together.

Important:
- Do not classify the role based only on keywords.
- Do not infer skills that are not supported.
- Do not infer skill proficiency from vague adjectives.
- Structured software proficiency has priority over vague free-text
  proficiency descriptions.
- Employer industry alone is not sufficient evidence for required
  domain knowledge.
- Return only the JSON object required by the schema.

JOB DATA:

{job_json}
""".strip()


def load_parsed_job(job_id):
    path = (
        PARSED_DIR
        / f"job_{job_id}.json"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def preview_prompt(job_id):
    job = load_parsed_job(job_id)

    print("=" * 70)
    print("SYSTEM PROMPT")
    print("=" * 70)
    print(SYSTEM_PROMPT)

    print("\n" + "=" * 70)
    print("USER PROMPT")
    print("=" * 70)
    print(
        build_user_prompt(job)
    )


if __name__ == "__main__":
    preview_prompt("1481754")