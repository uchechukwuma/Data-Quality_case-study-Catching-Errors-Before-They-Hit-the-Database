import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def sample_raw_data():
    """Fixture providing sample raw data for testing."""
    return pd.DataFrame({
        'timevalue': [2023, 2022, 2021],
        'providerkey': ['TEST1', 'TEST2', 'TEST3'],
        'companynameofficial': ['Test Company 1', 'Test Company 2', 'Test Company 3'],
        'fiscalperiodend': ['31-Mar', '2022-12-31', '30-Jun'],
        'operationstatustype': ['ACTIVE', 'ACTIVE', 'INACTIVE'],
        'ipostatustype': ['PUBLIC', 'PRIVATE', 'PUBLIC'],
        'geonameen': ['United Kingdom', 'India', 'United States'],
        'industrycode': ['7010', '6201', '4510'],
        'REVENUE': [1000000, 2000000, np.nan],
        'unit_REVENUE': ['GBP', 'INR', None]
    })

@pytest.fixture
def sample_processed_data():
    """Fixture providing sample processed data for testing."""
    return pd.DataFrame({
        'year': [2023, 2022, 2021],
        'provider_id': ['TEST1', 'TEST2', 'TEST3'],
        'company_name': ['TEST COMPANY 1', 'TEST COMPANY 2', 'TEST COMPANY 3'],
        'fiscal_period_end': ['31-Mar', '31-Dec', '30-Jun'],
        'operation_status': ['ACTIVE', 'ACTIVE', 'INACTIVE'],
        'ipo_status': ['PUBLIC', 'PRIVATE', 'PUBLIC'],
        'country': ['United Kingdom', 'India', 'United States'],
        'industry_code': ['7010', '6201', '4510'],
        'revenue': [1000000.0, 2000000.0, np.nan],
        'revenue_unit': ['GBP', 'INR', 'N/A'],
        'yoy_change': [0.1, -0.2, np.nan],
        'yoy_volatility_flag': [False, True, False]
    })

@pytest.fixture
def mock_llm_response():
    """Fixture providing mock LLM response."""
    return {
        "verdict": "plausible",
        "explanation": "Test explanation",
        "confidence": 0.85
    }