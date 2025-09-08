import pandas as pd
from .data_preparation import load_raw_data, run_rule_based_checks
from .analysis import run_llm_analysis
from .reporting import generate_quality_report, generate_llm_report, save_to_excel
from .config import RAW_DATA_PATH, SNAPSHOT_PATH, FINAL_OUTPUT_PATH, RULE_BASED_REPORT_PATH, LLM_REPORT_PATH
from openpyxl import load_workbook
from openpyxl.styles import Alignment
import os

def main():
    """Run the complete data quality pipeline."""
    print("Starting data quality pipeline...")
    
    # 1. Load and prepare data
    print("Loading and preparing data...")
    df = load_raw_data(RAW_DATA_PATH)
    
    # 2. Run rule-based checks
    print("Running rule-based quality checks...")
    df, check_results = run_rule_based_checks(df)
    
    # 3. Save the snapshot for the next stage
    df.to_csv(SNAPSHOT_PATH, index=False)
    print(f"Saved rule-based results to: {SNAPSHOT_PATH}")
    
    # 4. Generate quality report
    print("Generating quality report...")
    generate_quality_report(check_results, RULE_BASED_REPORT_PATH)
    
    # 5. Run LLM analysis
    print("Running LLM-powered analysis...")
    df, llm_results = run_llm_analysis(df)
    
    # --- FINAL MISSING VALUE STANDARDIZATION ---
    print("Standardizing missing values for final output...")
    
    # Define columns to clean up for presentation
    columns_to_standardize = [
        'revenue', 'revenue_unit', 'fiscal_period_end', 
        'yoy_change', 'llm_verdict', 'llm_explanation', 'llm_confidence'
    ]
    
    # Count missing values before replacement
    missing_before = df[columns_to_standardize].isna().sum().sum()
    print(f" - Missing values found in key columns: {missing_before}")
    
    # Replace NaN values with "N/A" for clean presentation
    df[columns_to_standardize] = df[columns_to_standardize].fillna("N/A")
    
    # Count after replacement
    missing_after = df[columns_to_standardize].isna().sum().sum()
    values_standardized = missing_before - missing_after
    print(f" - Missing values standardized to 'N/A': {values_standardized}")
    
    # 6. Generate LLM report (include standardization info)
    print("Generating LLM report...")
    generate_llm_report(llm_results, LLM_REPORT_PATH, values_standardized)
    
    # 7. Save final results with professional formatting
    print("Saving final results...")
    output_path = save_to_excel(df, FINAL_OUTPUT_PATH)
    
    print(f"Pipeline complete! Results saved to: {output_path}")
    return df, check_results, llm_results, values_standardized

if __name__ == "__main__":
    main()