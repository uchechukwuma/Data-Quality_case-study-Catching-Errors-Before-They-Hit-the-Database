# tests/integration/test_full_pipeline.py
import pytest
import pandas as pd
from unittest.mock import patch
from src.main import main


class TestIntegration:

    @pytest.mark.integration
    def test_full_pipeline_integration(self, tmp_path):
        """Integration test of the full pipeline with sample data."""

        # --- Create minimal test data ---
        test_data = pd.DataFrame({
            'timevalue': [2023, 2022],
            'providerkey': ['TEST1', 'TEST2'],
            'companynameofficial': ['Integration Test Inc', 'Another Company Ltd'],
            'fiscalperiodend': ['31-Mar', '2022-12-31'],
            'operationstatustype': ['ACTIVE', 'ACTIVE'],
            'ipostatustype': ['PUBLIC', 'PUBLIC'],
            'geonameen': ['United Kingdom', 'India'],
            'industrycode': ['7010', '7010'],
            'REVENUE': [1000000, 2000000],
            'unit_REVENUE': ['GBP', 'INR']
        })

        # Save test data to temp file
        test_file = tmp_path / "integration_test_data.xlsx"
        test_data.to_excel(test_file, index=False)

        # Expected output files
        expected_snapshot = tmp_path / "snapshot.csv"
        expected_final_output = tmp_path / "final_output.xlsx"
        expected_quality_report = tmp_path / "quality_report.txt"
        expected_llm_report = tmp_path / "llm_report.txt"

        # --- Patch config + main only ---
        with patch('src.main.RAW_DATA_PATH', test_file), \
             patch('src.main.SNAPSHOT_PATH', expected_snapshot), \
             patch('src.main.FINAL_OUTPUT_PATH', expected_final_output), \
             patch('src.main.RULE_BASED_REPORT_PATH', expected_quality_report), \
             patch('src.main.LLM_REPORT_PATH', expected_llm_report), \
             patch('src.config.RAW_DATA_PATH', test_file), \
             patch('src.config.SNAPSHOT_PATH', expected_snapshot), \
             patch('src.config.FINAL_OUTPUT_PATH', expected_final_output), \
             patch('src.config.RULE_BASED_REPORT_PATH', expected_quality_report), \
             patch('src.config.LLM_REPORT_PATH', expected_llm_report):

            # Run the pipeline
            result_df, check_results, llm_results, values_standardized = main()

            # --- Assertions ---
            assert isinstance(result_df, pd.DataFrame)
            assert isinstance(check_results, dict)
            assert isinstance(llm_results, dict)

            import numpy as np
            assert isinstance(values_standardized, (int, np.integer))
            assert int(values_standardized) >= 0

            # Verify output files exist
            assert expected_snapshot.exists()
            assert expected_final_output.exists()
            assert expected_quality_report.exists()
            assert expected_llm_report.exists()

            # Verify pipeline transformations
            assert 'yoy_change' in result_df.columns
            assert 'llm_verdict' in result_df.columns
