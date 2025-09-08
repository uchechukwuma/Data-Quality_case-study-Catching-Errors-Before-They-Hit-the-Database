import pytest
import pandas as pd
import numpy as np
from src.data_preparation import load_raw_data, correct_fiscal_period_end, infer_missing_revenue_unit, run_rule_based_checks

class TestDataPreparation:
    
    def test_load_raw_data_column_mapping(self, sample_raw_data, tmp_path):
        """Test that raw data columns are correctly mapped."""
        # Save sample data to temporary file
        test_file = tmp_path / "test_data.xlsx"
        sample_raw_data.to_excel(test_file, index=False)
        
        # Load using function
        df = load_raw_data(test_file)
        
        # Check column mapping
        expected_columns = ['year', 'provider_id', 'company_name', 'fiscal_period_end', 
                          'operation_status', 'ipo_status', 'country', 'industry_code',
                          'revenue', 'revenue_unit']
        assert all(col in df.columns for col in expected_columns)
        assert 'timevalue' not in df.columns  

    def test_correct_fiscal_period_end(self):
        """Test date format correction function."""
        # Test already correct format
        result, corrected = correct_fiscal_period_end('31-Mar')
        assert result == '31-Mar'
        assert not corrected
        
        # Test pandas timestamp conversion
        result, corrected = correct_fiscal_period_end('2023-03-31')
        assert result == '31-Mar'
        assert corrected
        
        # Test invalid string
        result, corrected = correct_fiscal_period_end('InvalidDate')
        assert result == 'InvalidDate'
        assert not corrected

    def test_infer_missing_revenue_unit(self):
        """Test revenue unit inference logic."""
        # Test with existing unit
        row = {'revenue_unit': 'USD', 'country': 'United States'}
        result = infer_missing_revenue_unit(row)
        assert result == 'USD'
        
        # Test UK inference
        row = {'revenue_unit': None, 'country': 'United Kingdom'}
        result = infer_missing_revenue_unit(row)
        assert result == 'GBP'
        
        # Test no inference
        row = {'revenue_unit': None, 'country': 'Germany'}
        result = infer_missing_revenue_unit(row)
        assert result is None

    def test_run_rule_based_checks(self, sample_raw_data, tmp_path):
        """Test complete rule-based checks pipeline."""
        test_file = tmp_path / "test_data.xlsx"
        sample_raw_data.to_excel(test_file, index=False)
        
        df = load_raw_data(test_file)
        df, results = run_rule_based_checks(df)
        
        # Check results structure
        expected_keys = ['dtype_issues', 'missing_summary', 'duplicates', 
                        'volatility_flags', 'date_corrections_count', 'remaining_date_issues']
        assert all(key in results for key in expected_keys)
        
        # Check data transformations
        assert 'yoy_change' in df.columns
        assert 'yoy_volatility_flag' in df.columns
        assert 'date_was_corrected' in df.columns
        
        # Check missing value standardization
        assert df['revenue_unit'].isna().sum() == 0

    def test_volatility_calculation(self):
        """Test YoY volatility flagging."""
        # Define test_df inside the method, not at class level
        test_df = pd.DataFrame({
            'company_name': ['A', 'A', 'A', 'B', 'B'],
            'year': [2023, 2022, 2021, 2023, 2022],
            'revenue': [150, 100, 90, 200, 50],  # A: +50%, +11%; B: +300%
            'fiscal_period_end': ['31-Mar', '31-Mar', '31-Mar', '31-Dec', '31-Dec']
        })
        
        df, results = run_rule_based_checks(test_df)
        
        # Company B should be flagged for volatility (>50% threshold)
        volatility_flags = df[df['yoy_volatility_flag']]
        assert len(volatility_flags) > 0
        assert all(volatility_flags['company_name'] == 'B')