import json
import os
import time
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import load_config  

# Load .env variables
load_dotenv()

# Control mode - False to try real APIs, True to force mock
USE_MOCK = False

def get_llm_judgment(company_name, company_summary, peer_context, year=None):
    """
    Get LLM judgment for a company's financial data with multi-provider fallback.
    Priority: Google Gemini → Groq API → Mock
    """
    config = load_config()
    prompt = build_analysis_prompt(company_name, company_summary, peer_context, year)

    print(f"* Analyzing {company_name} ({year}) with multi-provider AI...") if year else print(
        f"* Analyzing {company_name} with multi-provider AI..."
    )

    # Try Groq API First
    response = call_groq_api(prompt)
    if response:
        print(f">> Groq analysis complete for {company_name} ({year})") if year else print(
            f"✓ Groq analysis complete for {company_name}"
        )
        return parse_llm_response(response)

    # Try Gemini Second
    response = call_gemini_api(prompt)
    if response:
        print(f">> Gemini analysis complete for {company_name} ({year})") if year else print(
            f"✓ Gemini analysis complete for {company_name}"
        )
        return parse_llm_response(response)

    # Fallback to mock
    print(f">> Mock analysis complete for {company_name} ({year})") if year else print(
        f"✓ Mock analysis complete for {company_name}"
    )
    return parse_llm_response(_get_mock_response(company_name, company_summary, peer_context, year))



def build_analysis_prompt(company_name, company_summary, peer_context, year=None):
    """Build prompt for LLM analysis."""
    def fmt_num(val):
        return f"{val:,.0f}" if isinstance(val, (int, float)) else "N/A"

    year_info = f"YEAR: {year}\n" if year else ""

    return f"""
ANALYST TASK: Evaluate the plausibility of a company's financial data.

{year_info}COMPANY: {company_name}
REVENUE TREND: {company_summary}

PEER CONTEXT (other companies in same country & industry):
- Number of peers: {peer_context.get('peer_count', 0)}
- Median revenue: {fmt_num(peer_context.get('median_revenue'))}
- Revenue range (25th-75th percentile): {fmt_num(peer_context.get('q25_revenue'))} to {fmt_num(peer_context.get('q75_revenue'))}

INSTRUCTIONS:
1. Analyze if the company's revenue trend is plausible given the peer context.
2. Respond with ONLY a valid JSON object containing these keys:
   - "verdict" (must be: "plausible", "implausible", or "uncertain")
   - "explanation" (brief 1-2 sentence justification)
   - "confidence" (number between 0 and 1)

EXAMPLE RESPONSE:
{{"verdict": "implausible", "explanation": "Brief reason here.", "confidence": 0.9}}"""


def call_gemini_api(prompt, model="gemini-1.5-flash", max_tokens=300):
    """Call Google Gemini API (free tier)."""
    if USE_MOCK:
        return None  # Skip if mock mode forced

    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("*>> GEMINI_API_KEY not found in environment variables")
            return None

        # Configure with safety settings disabled for analytical tasks
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": max_tokens,
        }

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model_instance = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        json_enforced_prompt = prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON, no additional text."

        response = model_instance.generate_content(json_enforced_prompt)
        if response and response.text:
            print("*>> Gemini API call successful!")
            return response.text
        else:
            print("*>> Gemini API returned empty response")
            return None

    except ImportError:
        print("*>> google-generativeai package not installed. Install with: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"*>> Gemini API error: {str(e)[:200]}...")
        return None

def call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=300):
    """Call Groq API - FREE TIER available with fast performance"""
    if USE_MOCK:
        return None

    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print(">> GROQ_API_KEY not found in environment variables")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial data quality analyst. Analyze revenue trends and respond with ONLY valid JSON.",
                },
                {"role": "user", "content": prompt}
            ],
            "model": model,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f">> Groq API error {response.status_code}: {response.text[:200]}...")
            return None

    except Exception as e:
        print(f">> Groq API call failed: {str(e)[:200]}...")
        return None
    
def _get_mock_response(company_name, company_summary, peer_context, year):
    """Generate realistic, year-specific mock responses."""
    peer_count = peer_context.get("peer_count", 0)
    median_revenue = peer_context.get("median_revenue", 0)
    analysis_year = peer_context.get("analysis_year", year)

    try:
        analysis_year_int = int(analysis_year) if analysis_year is not None else 2023
    except (ValueError, TypeError):
        analysis_year_int = 2023

    years = company_summary.split("; ")
    current_year_data = years[-1] if years else ""

    has_high_volatility = any("%" in part and ("+50%" in part or "-50%" in part) for part in years)
    has_negative_growth = any("%" in part and "-" in part for part in years[-2:])
    has_extreme_values = any("MISSING" in part or "UNKNOWN" in part for part in years)

    if peer_count == 0:
        return json.dumps({
            "verdict": "uncertain",
            "explanation": f"{analysis_year_int}: Insufficient peer data for reliable comparison. No comparable companies in same industry/country.",
            "confidence": 0.4,
        })

    if has_high_volatility:
        explanations = [
            f"{analysis_year_int}: Extreme volatility ({current_year_data}) significantly deviates from {peer_count} peers (median: ${median_revenue:,.0f}).",
            f"{analysis_year_int}: Revenue pattern shows abnormal fluctuations compared to industry benchmarks of ${median_revenue:,.0f}.",
            f"{analysis_year_int}: Unusual YoY changes detected, inconsistent with {peer_count} comparable companies.",
        ]
        verdict = "implausible"
        confidence = 0.85

    elif has_negative_growth:
        explanations = [
            f"{analysis_year_int}: Revenue decline {current_year_data} contrasts with positive peer median of ${median_revenue:,.0f}.",
            f"{analysis_year_int}: Negative growth pattern differs from industry trends among {peer_count} peers.",
            f"{analysis_year_int}: Downturn detected while peers maintained median revenue of ${median_revenue:,.0f}.",
        ]
        yoy_change = peer_context.get("yoy_change", 0)
        try:
            yoy_abs = abs(float(yoy_change)) if yoy_change not in [None, "N/A", ""] else 0
        except (ValueError, TypeError):
            yoy_abs = 0

        verdict = "implausible" if yoy_abs > 0.3 else "uncertain"
        confidence = 0.7

    else:
        explanations = [
            f"{analysis_year_int}: Revenue trend {current_year_data} aligns with peer median of ${median_revenue:,.0f}.",
            f"{analysis_year_int}: Pattern consistent with {peer_count} industry peers (median: ${median_revenue:,.0f}).",
            f"{analysis_year_int}: Growth trajectory matches sector benchmarks of ${median_revenue:,.0f}.",
        ]
        verdict = "plausible"
        confidence = 0.75

    year_modifier = analysis_year_int % 10
    explanation = explanations[year_modifier % len(explanations)]
    confidence = max(0.4, min(0.95, confidence + (year_modifier * 0.01)))

    return json.dumps({
        "verdict": verdict,
        "explanation": explanation,
        "confidence": round(confidence, 2),
    })


def parse_llm_response(response_text):
    """Parse LLM response into structured dictionary with robust error handling."""
    if not response_text or not isinstance(response_text, str):
        return {
            "verdict": "uncertain",
            "explanation": "No response received from AI analysis",
            "confidence": 0.5,
        }

    try:
        cleaned_response = response_text.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:].rsplit("```", 1)[0].strip()
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:].rsplit("```", 1)[0].strip()

        if "{" in cleaned_response and "}" in cleaned_response:
            start = cleaned_response.find("{")
            end = cleaned_response.rfind("}") + 1
            cleaned_response = cleaned_response[start:end]

        result = json.loads(cleaned_response)

        required_fields = ["verdict", "explanation", "confidence"]
        if not all(field in result for field in required_fields):
            raise ValueError("Missing required fields in AI response")

        if result["verdict"] not in ["plausible", "implausible", "uncertain"]:
            result["verdict"] = "uncertain"

        try:
            confidence = float(result["confidence"])
            result["confidence"] = round(max(0.0, min(1.0, confidence)), 2)
        except (ValueError, TypeError):
            result["confidence"] = 0.5

        return result

    except json.JSONDecodeError as e:
        print(f"*>> JSON parse error: {e}. Response: {response_text[:200]}...")
        return _parse_text_fallback(response_text)
    except Exception as e:
        print(f"*>> Response parsing error: {e}")
        return _parse_text_fallback(response_text)


def _parse_text_fallback(response_text):
    """Fallback parsing for non-JSON responses."""
    response_lower = response_text.lower()

    result = {
        "verdict": "uncertain",
        "explanation": f"AI response analysis: {response_text[:150]}...",
        "confidence": 0.5,
    }

    if any(word in response_lower for word in ["implausible", "suspicious", "anomal", "error", "invalid"]):
        result["verdict"] = "implausible"
        result["confidence"] = 0.7
    elif any(word in response_lower for word in ["plausible", "reasonable", "consistent", "valid", "correct"]):
        result["verdict"] = "plausible"
        result["confidence"] = 0.7

    return result
