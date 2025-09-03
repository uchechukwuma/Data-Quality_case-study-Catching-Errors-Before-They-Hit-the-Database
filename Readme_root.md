# Data Quality Case Study

**Goal:** Detect and flag data quality issues in company financial data extracted from multiple sources, producing a clean Excel output and a concise PowerPoint summary.

---

## 🧭 Project Overview
This project implements **automated data quality checks** for company financials, including:  

- **Completeness:** Check for missing required fields  
- **Correctness:** Validate numeric fields, currency units  
- **Consistency:** Identify unusual year-over-year revenue spikes  
- **Uniqueness:** Detect duplicate records per provider & year  
- **LLM Plausibility:** Use GPT-based prompts to flag suspicious values  

The pipeline outputs a flagged Excel file and calculates a **risk score** for prioritization.

---

## 📁 Project Structure
├── config
├── data/
│ ├── raw/ # Input Excel files
│ └── processed/ # Output flagged files (gitignored)
├── src/ # Python scripts for checks & LLM
├── notebooks/ # Exploratory analysis
├── tests/ # Unit tests
├── presentation/ # PowerPoint deck
├── requirements.txt
├── README.md
└── .gitignore


---

## 🚀 Quickstart
### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/data-quality-casestudy.git
cd data-quality-casestudy
```
### 2. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run data quality checks
python src/data_quality_checks.py
Output: data/processed/flagged_output.xlsx with flags and risk scores.
(Screenshot to be added after first run)

#### 4. Optional LLM check
Set your OPENAI_API_KEY in .env to enable GPT plausibility checks.
The script falls back to rule-based heuristics if no key is provided.

#### 5. 📊 Results
Flagged rows include: missing fields, duplicate entries, revenue spikes, and implausible values detected by GPT.
Each row is assigned a risk score to prioritize review.
Insert a small screenshot of the flagged Excel table here.

#### 6. 🧪 Testing
Run unit tests:
pytest

#### 7. 🎯 Next Steps / Future Improvements
Peer/industry comparison for more robust anomaly detection
Active learning loop with analyst feedback for LLM improvements
Production orchestration using Airflow or dbt (optional)


## 🧑‍💻 Author
Uchechukwu Obi  
[LinkedIn Profile](www.linkedin.com/in/uchechukwu-obi)