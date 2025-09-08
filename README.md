# Data Quality Case Study

**Goal:** Automate detection and flagging of data quality issues in company financial datasets extracted from multiple sources, producing **Excel reports** and a concise **PowerPoint summary**.

---

## 🧭 Project Overview
This project implements a **data quality assurance pipeline** for financial data. It combines **rule-based checks** with **LLM-powered contextual analysis** to highlight anomalies and prioritize review.  

Key quality measures implemented:
- **Completeness** – Check for missing required fields  
- **Correctness** – Validate numeric fields and fiscal period formats  
- **Consistency** – Identify unusual year-over-year revenue spikes  
- **Uniqueness** – Detect duplicate records per provider & year  
- **LLM Plausibility** – Use Groq API (primary), fallback Gemini API, and mock fallback to flag suspicious values  

The pipeline outputs:
- A **flagged Excel file** with risk scores  
- A **PowerPoint summary deck**  
- Console logs showing LLM fallback decisions  

---

## 📁 Project Structure
```text
├── config/                  # Config files & settings
├── data/
│   ├── raw/                 # Input Excel files
│   └── processed/           # Output flagged files (gitignored)
├── src/                     # Production-grade Python scripts
│   ├── analysis.py          # Peer/LLM analysis
│   ├── data_preparation.py  # Cleaning & transformations
│   ├── llm_utils.py         # LLM API calls & parsing
│   └── reporting.py         # Excel outputs
├── notebooks/               # Exploratory Jupyter notebooks (3 stages)
├── tests/                   # Unit tests (pytest)
├── presentation/            # PowerPoint deliverable
├── reports/                 # Automated report output
├── requirements.txt
├── README.md
└── .gitignore
```

## 🚀 Quickstart
1. Clone the repo
git clone https://github.com/YOUR_USERNAME/data-quality-casestudy.git
cd data-quality-casestudy
2. Create environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
3. Run the pipeline
python src/main.py

Output:
data/processed/flagged_output.xlsx → Flagged dataset with risk scores
presentation/data_quality_summary.pptx → Auto-generated PowerPoint

## ⚙️ LLM Integration
Primary: Groq API

Fallback 1: Gemini API

Fallback 2: Mock responses (ensures output is always generated)

Only the top 3 most volatile companies are analyzed with LLM for efficient resource management.

## 🧪 Testing
Run all unit tests:

pytest
Over 25+ tests cover rule-based checks, LLM utilities, reporting, and full integration.

## 📊 Results
Automated detection of missing values, duplicates, and revenue anomalies

AI-assisted peer/contextual analysis for plausibility checks

Unified Excel + PowerPoint reporting for decision-making


## 🎯 Next Steps
Add peer/industry benchmarks to strengthen anomaly detection

Build an active learning loop with analyst feedback for LLM refinement

Orchestrate with Airflow/dbt for scalable production deployment

## 🧑‍💻 Author Uchechukwu Obi 
[www.linkedin.com/in/uchechukwu-obi]

