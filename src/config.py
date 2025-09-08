from pathlib import Path
from datetime import datetime
import yaml
import os
from dotenv import load_dotenv 

# Project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent

# Directory paths
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" 
REPORTS_PATH = PROJECT_ROOT / "reports"

# Ensure directories exist
DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

# Get current timestamp for unique filenames
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")  

# --- FILE PATHS ---
# Input file (from the original task)
RAW_DATA_PATH = DATA_RAW_PATH / "CaseStudy_Quality_sample25.xlsx"

# Intermediate file
SNAPSHOT_PATH = DATA_PROCESSED_PATH / "rule_checks_snapshot_LATEST.csv"

# Final output files (unique per run with pipeline identifier and timestamp)
FINAL_OUTPUT_PATH = DATA_PROCESSED_PATH / f"final_checked_data_PIPELINE_{TIMESTAMP}.xlsx"

# Report files (unique per run with pipeline identifier and timestamp)
RULE_BASED_REPORT_PATH = REPORTS_PATH / f"rule_based_checks_report_PIPELINE_{TIMESTAMP}.txt"
LLM_REPORT_PATH = REPORTS_PATH / f"llm_anomaly_report_PIPELINE_{TIMESTAMP}.txt"

# Quality check parameters
VOLATILITY_THRESHOLD = 0.5  # 50%
TOP_N_COMPANIES = 3  # For LLM analysis

def load_config():
    """
    Load configuration from YAML file and environment variables.
    Returns combined configuration dictionary.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Load YAML configuration
    config_path = PROJECT_ROOT / "config" / "config.yaml"
    try:
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        yaml_config = {}

    # Combine with environment variables (env vars take precedence)
    config = {
        **yaml_config,
        'groq_api_key': os.getenv('GROQ_API_KEY'),  
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),  
    }

    # Set defaults if not specified
    config.setdefault('model_gemini', 'gemini-1.5-flash')  
    config.setdefault('model_groq', 'llama-3.1-8b-instant')  
    config.setdefault('max_tokens', 350)
    config.setdefault('temperature', 0.1)
    config.setdefault('top_n_companies', 3) 
    config.setdefault('volatility_threshold', 0.5)

    # Validate required keys
    if not config['gemini_api_key']:
        print(">> Warning: GEMINI_API_KEY not found. Gemini calls may fail.")
    if not config['groq_api_key']:
        print(">> Warning: GROQ_API_KEY not found. Groq calls may fail.")

    return config
