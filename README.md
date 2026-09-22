# Job Market Analyzer

An AI-powered system for analyzing Artificial Intelligence and Data Science job markets using Large Language Models (LLMs).

## Overview

Job Market Analyzer transforms unstructured job descriptions into structured insights using AI.

The project collects job advertisements, processes their content, and uses local LLMs to extract meaningful information such as:

- Job roles
- Required skills
- Responsibilities
- Seniority levels
- Engineering expectations

The goal is to understand current AI job market trends and identify the skills and requirements companies are looking for.

---

## Workflow
Job Advertisements
|
v
Data Collection
|
v
Job Parsing
|
v
LLM-based Extraction
|
v
Structured Analysis
---

## Features

- Collect and process AI/Data Science job advertisements
- Extract structured information from job descriptions
- Classify AI-related roles
- Identify required technologies and skills
- Analyze job requirements using LLMs
- Evaluate extraction quality with benchmark datasets

---

## Technologies

- Python
- Large Language Models (LLMs)
- Ollama
- Qwen3:4b-instruct
- Pydantic
- Git & GitHub

---

## Dataset

Current dataset:

- 271 parsed job advertisements
- Persian and English job descriptions
- AI, Machine Learning, Data Science, and related roles

A benchmark dataset is used to evaluate extraction quality before large-scale analysis.

---

## Project Structure
job-market-analyzer/

├── ai_schema.py # Data validation schemas
├── ai_prompt.py # LLM extraction prompts
├── local_ai_extractor.py # Local LLM extraction pipeline
├── evaluate_benchmark.py # Benchmark evaluation
├── job_parser.py # Job data processing
└── data/ # Dataset and results
---

## Example Output

The system converts job descriptions into structured data:

json
{
  "role": "data_scientist",
  "skills": [
    "Python",
    "SQL",
    "Scikit-learn"
  ],
  "seniority": "mid"
}

Current Status

Implemented:

✅ Data collection
✅ Job parsing
✅ LLM-based extraction
✅ Schema validation
✅ Benchmark evaluation

The project is currently being improved for higher extraction quality and large-scale job market analysis.
