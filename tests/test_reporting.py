import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import mock_open, patch
from src.reporting import generate_quality_report, generate_llm_report, save_to_excel

class TestReporting:
    
    def test_generate_quality_report(self, tmp_path):
        """Test quality report generation."""
        check_results = {
            'dtype_issues': {'year': {'expected': 'int64', 'actual': 'object'}},
            'missing_summary': pd.Series({'year': 2, 'revenue': 5}),
            'duplicates': pd.DataFrame(columns=['year', 'company_name']),
            'volatility_flags': pd.DataFrame({'company_name': ['Test Corp']}),
            'date_corrections_count': 3,
            'remaining_date_issues': 1
        }
        
        report_path = tmp_path / "quality_report.txt"
        generate_quality_report(check_results, report_path)
        
        # Check report was created and contains expected content
        assert report_path.exists()
        content = report_path.read_text()
        assert "Data Quality Assessment Report" in content
        assert "3" in content  # date corrections
        assert "High Volatility: 1" in content  # Check for the count instead of specific name

    def test_generate_llm_report(self, tmp_path):
        """Test LLM report generation."""
        llm_results = {
            'TEST CORP': {
                'verdict': 'implausible',
                'explanation': 'Revenue pattern anomaly',
                'confidence': 0.85
            }
        }
        
        report_path = tmp_path / "llm_report.txt"
        generate_llm_report(llm_results, report_path, values_standardized=10)
        
        content = report_path.read_text()
        assert "LLM Anomaly Detection Report" in content
        assert "implausible" in content
        assert "10" in content  # standardized values

    def test_save_to_excel_formatting(self, sample_processed_data, tmp_path):
        """Test Excel saving with professional formatting."""
        # Add some LLM results for testing
        test_df = sample_processed_data.copy()
        test_df['llm_verdict'] = ['plausible', 'N/A', 'N/A']
        test_df['llm_explanation'] = ['Test explanation', 'N/A', 'N/A']
        test_df['llm_confidence'] = [0.8, 'N/A', 'N/A']
        
        output_path = tmp_path / "test_output.xlsx"
        result_path = save_to_excel(test_df, output_path)
        
        # Check file was created
        assert result_path.exists()
        
        # Verify structure was maintained
        df_reloaded = pd.read_excel(output_path)
        assert 'llm_verdict' in df_reloaded.columns
        assert 'llm_explanation' in df_reloaded.columns
        
        # Check that LLM-processed records come first
        first_row_verdict = df_reloaded.iloc[0]['llm_verdict']
        assert first_row_verdict == 'plausible'

    def test_save_to_excel_missing_company_handling(self, sample_processed_data, tmp_path):
        """Test handling of records with missing company names."""
        test_df = sample_processed_data.copy()
        test_df.loc[2, 'company_name'] = None  # Add missing company name
        
        # Add required LLM columns with default values
        test_df['llm_verdict'] = 'N/A'
        test_df['llm_explanation'] = 'N/A' 
        test_df['llm_confidence'] = 'N/A'
        
        output_path = tmp_path / "test_output.xlsx"
        save_to_excel(test_df, output_path)
        
        # Verify file was created and handled missing values
        df_reloaded = pd.read_excel(output_path)
        missing_mask = df_reloaded['company_name'].isna() | (df_reloaded['company_name'] == 'N/A')
        assert missing_mask.any()  # Should have missing values