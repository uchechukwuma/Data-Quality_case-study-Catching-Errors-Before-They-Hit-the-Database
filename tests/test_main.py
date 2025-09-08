import pytest
from unittest.mock import patch, MagicMock
from src.main import main

class TestMain:
    
    @patch('src.main.load_raw_data')
    @patch('src.main.run_rule_based_checks')
    @patch('src.main.run_llm_analysis')
    @patch('src.main.generate_quality_report')
    @patch('src.main.generate_llm_report')
    @patch('src.main.save_to_excel')
    def test_main_pipeline_flow(self, mock_save, mock_llm_report, mock_quality_report, 
                               mock_llm_analysis, mock_rule_checks, mock_load):
        """Test the complete pipeline flow."""
        # Mock each step
        mock_df = MagicMock()
        mock_load.return_value = mock_df
        mock_rule_checks.return_value = (mock_df, {'test': 'results'})
        mock_llm_analysis.return_value = (mock_df, {'llm': 'results'})
        mock_save.return_value = '/fake/path/output.xlsx'
        
        # Run main pipeline
        result = main()
        
        # Verify all steps were called in order
        mock_load.assert_called_once()
        mock_rule_checks.assert_called_once_with(mock_df)
        mock_llm_analysis.assert_called_once_with(mock_df)
        mock_quality_report.assert_called_once()
        mock_llm_report.assert_called_once()
        mock_save.assert_called_once()
        
        # Verify return values
        assert len(result) == 4  

    @patch('src.main.load_raw_data')
    def test_main_file_not_found(self, mock_load):
        """Test error handling for missing input file."""
        mock_load.side_effect = FileNotFoundError("Test file not found")
        
        with pytest.raises(FileNotFoundError):
            main()