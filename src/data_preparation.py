import pandas as pd
import numpy as np
import re
from pathlib import Path
from .config import VOLATILITY_THRESHOLD
import logging

logger = logging.getLogger(__name__)

def load_raw_data(filepath):
    """Load and standardize column names from raw Excel file."""
    try:
        df = pd.read_excel(filepath)
        # Check if expected columns exist
        expected_cols = ["timevalue", "providerkey", "companynameofficial"]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}")
    except Exception as e:
        logger.error(f"Failed to load data from {filepath}: {e}")
        raise
    
    # Standardize column names
    column_mapping = {
        "timevalue": "year",
        "providerkey": "provider_id", 
        "companynameofficial": "company_name",
        "fiscalperiodend": "fiscal_period_end",
        "operationstatustype": "operation_status",
        "ipostatustype": "ipo_status",
        "geonameen": "country",
        "industrycode": "industry_code",
        "REVENUE": "revenue",
        "unit_REVENUE": "revenue_unit"
    }
    return df.rename(columns=column_mapping)

def correct_fiscal_period_end(date_val):
    """
    Attempts to correct a date value to the standard 'DD-MMM' format.
    Returns a tuple: (corrected_value, was_corrected_flag)
    """
    original_value = date_val
    corrected_value = original_value  # Default to original
    
    # Check if already in correct format
    if isinstance(date_val, str) and re.match(r'^\d{2}-[A-Za-z]{3}$', date_val, re.IGNORECASE):
        return corrected_value, False 
    
    # Handle string dates that need conversion
    if isinstance(date_val, str):
        try:
            parsed_date = pd.to_datetime(date_val)
            corrected_value = parsed_date.strftime('%d-%b')
        except (ValueError, TypeError):
            pass  # corrected_value remains original_value
    
    # Handle pandas Timestamp objects
    try:
        if hasattr(date_val, 'strftime'):
            corrected_value = date_val.strftime('%d-%b')
    except:
        pass
    
    # Determine if correction was made
    was_corrected = (corrected_value != original_value)
    
    return corrected_value, was_corrected

def infer_missing_revenue_unit(row):
    """Infer missing revenue_unit based on country."""
    if pd.notna(row.get('revenue_unit')) and row['revenue_unit'] != '':
        return row['revenue_unit']
    if row.get('country') == 'United Kingdom':
        return 'GBP'
    return row.get('revenue_unit')

def run_rule_based_checks(df):
    """Execute all rule-based data quality checks."""
    df = df.copy()
    
    # 1. Date format correction 
    df['fiscal_period_end_original'] = df['fiscal_period_end']
    
    # Apply the correction and track changes
    correction_results = df['fiscal_period_end'].apply(correct_fiscal_period_end)
    df['fiscal_period_end'] = correction_results.apply(lambda x: x[0])  # The corrected value
    df['date_was_corrected'] = correction_results.apply(lambda x: x[1])  # The flag (True/False)
    
    # Check format consistency on the CORRECTED values
    date_pattern = r'^\d{2}-[A-Za-z]{3}$'
    df['flag_date_format'] = ~df['fiscal_period_end'].astype(str).str.match(date_pattern, na=False)
    
    # 2. Infer missing revenue units
    df['revenue_unit'] = df.apply(infer_missing_revenue_unit, axis=1)
    
    # 3. Standardize company names
    df['company_name_original'] = df['company_name']
    df['company_name'] = df['company_name'].str.upper()
    
    # 4. Check data types
    expected_dtypes = {"year": "int64", "company_name": "object", "revenue": "float64"}
    dtype_issues = {}
    for col, expected in expected_dtypes.items():
        if col in df.columns:
            actual = str(df[col].dtype)
            if actual != expected:
                dtype_issues[col] = {"expected": expected, "actual": actual}
    
    # 5. Check missing values
    critical_cols = ["year", "company_name", "revenue"]
    missing_summary = df[critical_cols].isnull().sum()
    
    # 6. Check duplicates
    duplicates = df[df.duplicated(subset=["company_name", "year"], keep=False)]
    
    # 7. Calculate YoY volatility
    df = df.sort_values(by=["company_name", "year"])
    df["yoy_change"] = df.groupby("company_name")["revenue"].pct_change(fill_method=None)
    df["yoy_volatility_flag"] = abs(df["yoy_change"]) > VOLATILITY_THRESHOLD
    
    # 8. Standardize missing values for final output
    columns_to_standardize = ['revenue', 'revenue_unit', 'fiscal_period_end']
    df[columns_to_standardize] = df[columns_to_standardize].fillna("N/A")
    
    # --- DATE CORRECTION REPORTING ---
    correction_count = df['date_was_corrected'].sum()
    
    print(f"\nDate Format Correction Summary:")
    print(f" - Records corrected: {correction_count}")
    print(f" - Records with remaining format issues: {df['flag_date_format'].sum()}")
    
    # Show sample of corrected dates
    if correction_count > 0:
        corrected_samples = df[df['date_was_corrected']].head(3)
        print("\nSample of successfully corrected dates:")
        for _, row in corrected_samples.iterrows():
            print(f"   - {row['company_name']} ({row['year']}): '{row['fiscal_period_end_original']}' -> '{row['fiscal_period_end']}'")
    else:
        print("No date corrections were needed!")
    
    # Show remaining issues if any
    if df['flag_date_format'].sum() > 0:
        problem_dates = df[df['flag_date_format']]
        print("\nRecords that still have formatting issues:")
        print(problem_dates[['company_name', 'year', 'fiscal_period_end_original', 'fiscal_period_end']].head())
    
    return df, {
        "dtype_issues": dtype_issues,
        "missing_summary": missing_summary,
        "duplicates": duplicates,
        "volatility_flags": df[df["yoy_volatility_flag"]],
        "date_corrections_count": correction_count,
        "remaining_date_issues": df['flag_date_format'].sum()
    }