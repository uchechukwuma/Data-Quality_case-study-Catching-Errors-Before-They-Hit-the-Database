import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
import numpy as np
from .llm_utils import get_llm_judgment
from .config import load_config
config = load_config()
TOP_N_COMPANIES = config.get('top_n_companies', 3)
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, module='pandas.core.dtypes.cast')


def summarize_company_data(df_company, max_years=3):
    """Create compact summary of company's revenue trend UP TO target year."""
    df_sorted = df_company.sort_values('year')
    
    summary_parts = []
    for _, row in df_sorted.iterrows():
        revenue_val = row.get('revenue')
        revenue_str = f"{int(revenue_val):,}" if pd.notna(revenue_val) and revenue_val != "N/A" else "MISSING"
        
        yoy_val = row.get('yoy_change')
        if pd.isna(yoy_val):
            yoy_str = "MISSING"
        else:
            yoy_str = f"{yoy_val:+.0%}"
        
        fiscal_val = row.get('fiscal_period_end')
        year_val = str(fiscal_val) if fiscal_val != "N/A" else "UNKNOWN"
        
        summary_parts.append(f"{year_val}: {revenue_str} ({yoy_str})")
    
    return "; ".join(summary_parts)

def get_peer_context(full_df, company_row, target_year):
    """Get summary statistics for peers in same country and industry FOR SPECIFIC YEAR."""
    country = company_row['country']
    industry = company_row['industry_code']
    company_id = company_row['provider_id']
    
    # Filter peers for the SPECIFIC YEAR
    peer_mask = (
        (full_df['country'] == country) & 
        (full_df['industry_code'] == industry) & 
        (full_df['provider_id'] != company_id) &
        (full_df['year'] == target_year)  
    )
    peers_df = full_df[peer_mask]
    
    if peers_df.empty:
        return {"peer_count": 0, "message": f"No peers found for {target_year}"}
    peer_revenue = peers_df['revenue'].replace("N/A", np.nan)
    peer_revenue = pd.to_numeric(peer_revenue, errors='coerce').dropna()
    
    if peer_revenue.empty:
        return {"peer_count": len(peers_df), "message": f"No peer revenue data for {target_year}"}
    
    return {
        "peer_count": len(peers_df['provider_id'].unique()),
        "median_revenue": peer_revenue.median(),
        "mean_revenue": peer_revenue.mean(),
        "q25_revenue": peer_revenue.quantile(0.25),
        "q75_revenue": peer_revenue.quantile(0.75),
        "analysis_year": target_year  # year context
    }

def run_llm_analysis(df):
    """Run LLM analysis on top volatile companies - YEAR BY YEAR."""
    df = df.copy()
    
    # Prepare new columns
    df['llm_verdict'] = pd.NA
    df['llm_explanation'] = pd.NA
    df['llm_confidence'] = pd.NA
    
    # Select top volatile companies
    high_volatility_companies = (
        df[df['yoy_volatility_flag'] == True]
        .groupby('company_name')['yoy_change']
        .apply(lambda x: x.abs().max())
        .nlargest(TOP_N_COMPANIES)
        .index.tolist()
    )
    
    results = {}
    for company_name in high_volatility_companies:
        company_data = df[df['company_name'] == company_name]
        
        # Analyze EACH YEAR separately
        for index, company_row in company_data.iterrows():
            target_year = company_row['year']
            
            # Get year-specific summary
            year_data = company_data[company_data['year'] <= target_year].tail(3)  # Last 3 years including current
            company_summary = summarize_company_data(year_data)
            
            # Get year-specific peer context
            peer_context = get_peer_context(df, company_row, target_year)
            
            # Get LLM judgment for THIS SPECIFIC YEAR
            llm_result = get_llm_judgment(company_name, company_summary, peer_context)
            
            # Store results for this specific year
            df.loc[index, 'llm_verdict'] = llm_result.get('verdict', 'uncertain')
            df.loc[index, 'llm_explanation'] = llm_result.get('explanation', '')
            df.loc[index, 'llm_confidence'] = llm_result.get('confidence', 0.5)
            
            # Store in results by company-year key
            year_key = f"{company_name}_{target_year}"
            results[year_key] = llm_result
    
    return df, results