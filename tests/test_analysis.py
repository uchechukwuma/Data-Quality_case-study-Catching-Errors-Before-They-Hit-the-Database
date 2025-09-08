import pytest
import pandas as pd
import numpy as np
from src.analysis import summarize_company_data, get_peer_context, run_llm_analysis

class TestAnalysis:
    
    def test_summarize_company_data(self, sample_processed_data):
        """Test company data summarization."""
        company_data = sample_processed_data[sample_processed_data['company_name'] == 'TEST COMPANY 1']
        summary = summarize_company_data(company_data)
        
        assert '1,000,000' in summary  # Revenue with formatting
        assert '+10%' in summary or 'MISSING' in summary  # YoY change

    def test_get_peer_context_with_peers(self):
        """Test peer context with available peers."""
        # Create mock dataset with multiple companies in same country/industry
        data = pd.DataFrame([
            {"company_name": "A", "provider_id": "1", "country": "US", "industry_code": "TECH", "revenue": 1000, "year": 2023},
            {"company_name": "B", "provider_id": "2", "country": "US", "industry_code": "TECH", "revenue": 1200, "year": 2023},
            {"company_name": "C", "provider_id": "3", "country": "US", "industry_code": "TECH", "revenue": 1100, "year": 2023},
        ])
        target_company = data.iloc[0]
        target_year = target_company['year']
        
        context = get_peer_context(data, target_company, target_year)
        
        assert context['peer_count'] > 0
        assert 'median_revenue' in context

    def test_get_peer_context_no_peers(self):
        """Test peer context with no peers available."""
        # Create dataset with only one unique company
        data = pd.DataFrame([
            {"company_name": "UniqueCo", "provider_id": "unique_id_123", "country": "Mars", "industry_code": "MARS001", "revenue": 1000, "year": 2023}
        ])
        target_company = data.iloc[0]
        target_year = target_company['year']
        
        context = get_peer_context(data, target_company, target_year)
        
        assert context['peer_count'] == 0
        assert 'message' in context

    def test_run_llm_analysis_mock_mode(self, sample_processed_data):
        """Test LLM analysis in mock mode."""
        # Ensure we have some volatile companies
        volatile_df = sample_processed_data.copy()
        volatile_df.loc[0, 'yoy_volatility_flag'] = True
        volatile_df.loc[1, 'yoy_volatility_flag'] = True
        
        # Run analysis
        result_df, llm_results = run_llm_analysis(volatile_df)
        
        # Should have LLM columns
        assert 'llm_verdict' in result_df.columns
        assert 'llm_explanation' in result_df.columns
        assert 'llm_confidence' in result_df.columns
        
        # Should have results for volatile companies
        assert len(llm_results) > 0
        
        # Check that non-volatile companies don't have LLM results
        non_volatile_mask = ~result_df['yoy_volatility_flag']
        non_volatile_llm = result_df.loc[non_volatile_mask, 'llm_verdict']
        assert all(non_volatile_llm.isin(['N/A', pd.NA]))
