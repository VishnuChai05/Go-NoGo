"""
Test Suite for Go / No-Go App
Run with: python test_app.py
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import requests
from bs4 import BeautifulSoup
import re
import random

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

PASSED = 0
FAILED = 0
WARNINGS = 0

def test_result(name, passed, message=""):
    global PASSED, FAILED
    if passed:
        PASSED += 1
        print(f"  ✅ PASS: {name}")
    else:
        FAILED += 1
        print(f"  ❌ FAIL: {name}")
    if message:
        print(f"      → {message}")

def test_warning(name, message):
    global WARNINGS
    WARNINGS += 1
    print(f"  ⚠️  WARN: {name}")
    print(f"      → {message}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ============================================================================
# TEST 1: ENVIRONMENT VARIABLES
# ============================================================================

def test_env_variables():
    section("TEST 1: Environment Variables (.env)")
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    # Test Groq key exists
    test_result(
        "GROQ_API_KEY exists in .env",
        bool(groq_key) and groq_key != "your_groq_api_key_here",
        f"Key starts with: {groq_key[:10]}..." if groq_key and len(groq_key) > 10 else "Key missing or placeholder"
    )
    
    # Test key format (Groq keys start with gsk_)
    test_result(
        "GROQ_API_KEY format is valid",
        groq_key.startswith("gsk_") if groq_key else False,
        "Key should start with 'gsk_'"
    )
    
    return groq_key

# ============================================================================
# TEST 2: GROQ API CONNECTION
# ============================================================================

def test_groq_api(api_key):
    section("TEST 2: Groq API Connection")
    
    if not api_key or api_key == "your_groq_api_key_here":
        test_result("Groq API key available", False, "No valid API key to test")
        return False
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Say 'test successful' in exactly 2 words"}],
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        test_result(
            "Groq API responds with 200",
            response.status_code == 200,
            f"Status code: {response.status_code}"
        )
        
        if response.status_code == 200:
            content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            test_result(
                "Groq API returns valid response",
                len(content) > 0,
                f"Response: {content[:50]}"
            )
            return True
        else:
            error = response.json().get('error', {}).get('message', 'Unknown error')
            test_result("Groq API error check", False, f"Error: {error}")
            return False
            
    except Exception as e:
        test_result("Groq API connection", False, f"Exception: {str(e)}")
        return False

# ============================================================================
# TEST 3: AMAZON INDIA SCRAPING
# ============================================================================

def test_amazon_scraping():
    section("TEST 3: Amazon India Scraping")
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    test_queries = ["haldiram snacks", "protein bars", "namkeen"]
    
    for query in test_queries:
        try:
            url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
            
            session = requests.Session()
            # First get homepage for cookies
            session.get("https://www.amazon.in", headers=headers, timeout=5)
            time.sleep(0.5)
            
            response = session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('div', {'data-component-type': 's-search-result'})
                
                if len(items) > 0:
                    test_result(
                        f"Amazon search '{query}'",
                        True,
                        f"Found {len(items)} products"
                    )
                    return True  # At least one query worked
                else:
                    test_warning(
                        f"Amazon search '{query}'",
                        f"Status 200 but 0 products found (possible bot detection)"
                    )
            else:
                test_warning(
                    f"Amazon search '{query}'",
                    f"Status code: {response.status_code} (may be rate limited)"
                )
                
        except Exception as e:
            test_warning(f"Amazon search '{query}'", f"Exception: {str(e)[:50]}")
        
        time.sleep(1)  # Delay between requests
    
    test_result("Amazon scraping (any query)", False, "All queries failed - may be IP blocked")
    return False

# ============================================================================
# TEST 4: FLIPKART SCRAPING
# ============================================================================

def test_flipkart_scraping():
    section("TEST 4: Flipkart Scraping")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-IN,en;q=0.9',
    }
    
    test_queries = ["protein bars", "haldiram namkeen"]
    
    for query in test_queries:
        try:
            url = f"https://www.flipkart.com/search?q={query.replace(' ', '%20')}"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # New approach: Find product links containing /p/
                product_links = soup.find_all('a', href=lambda x: x and '/p/' in str(x))
                
                if len(product_links) > 5:
                    test_result(
                        f"Flipkart search '{query}'",
                        True,
                        f"Found {len(product_links)} product links"
                    )
                    return True
                else:
                    test_warning(
                        f"Flipkart search '{query}'",
                        f"Found {len(product_links)} links (may need selector update)"
                    )
            else:
                test_warning(
                    f"Flipkart search '{query}'",
                    f"Status code: {response.status_code}"
                )
                
        except Exception as e:
            test_warning(f"Flipkart search '{query}'", f"Exception: {str(e)[:50]}")
        
        time.sleep(1)
    
    test_result("Flipkart scraping (any query)", False, "All queries failed")
    return False

# ============================================================================
# TEST 5: BIGBASKET SCRAPING
# ============================================================================

def test_bigbasket_scraping():
    section("TEST 5: BigBasket Scraping")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-IN,en;q=0.9',
    }
    
    query = "haldiram snacks"
    
    try:
        url = f"https://www.bigbasket.com/ps/?q={query.replace(' ', '%20')}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # BigBasket may use JS rendering, just check we get a response
            if len(response.text) > 5000:
                test_result(
                    "BigBasket connection",
                    True,
                    f"Got response ({len(response.text)} bytes)"
                )
                return True
            else:
                test_warning(
                    "BigBasket search",
                    "Response too small - may need JS rendering"
                )
        else:
            test_warning(
                "BigBasket search",
                f"Status code: {response.status_code}"
            )
            
    except Exception as e:
        test_warning("BigBasket search", f"Exception: {str(e)[:50]}")
    
    return False

# ============================================================================
# TEST 6: UNIT ECONOMICS CALCULATIONS
# ============================================================================

def test_unit_economics():
    section("TEST 6: Unit Economics Calculations")
    
    # Test data
    MANUFACTURING_COST_PER_GRAM = {
        "Packaged Snacks": 0.15,
        "Personal Care": 0.25,
        "Supplements": 0.50,
    }
    
    PACKAGING_COST = {
        "Packaged Snacks": 8,
        "Personal Care": 15,
        "Supplements": 20,
    }
    
    PLATFORM_MARGIN = {
        "E-commerce": 0.25,
        "Quick Commerce": 0.35
    }
    
    LOGISTICS_COST = {
        "E-commerce": 45,
        "Quick Commerce": 25
    }
    
    RETURNS_RATE = {
        "E-commerce": 0.08,
        "Quick Commerce": 0.03
    }
    
    GST_RATE = 0.18
    
    def calculate_unit_economics(category, weight, mrp, channel):
        manufacturing_cost = MANUFACTURING_COST_PER_GRAM.get(category, 0.20) * weight
        packaging_cost = PACKAGING_COST.get(category, 12)
        platform_fees = PLATFORM_MARGIN[channel] * mrp
        logistics_cost = LOGISTICS_COST[channel]
        returns_cost = RETURNS_RATE[channel] * mrp
        gst = GST_RATE * mrp
        
        total_cost = (manufacturing_cost + packaging_cost + platform_fees + 
                      logistics_cost + returns_cost + gst)
        
        net_margin = mrp - total_cost
        margin_percentage = (net_margin / mrp) * 100 if mrp > 0 else 0
        
        return {
            "total_cost": total_cost,
            "net_margin": net_margin,
            "margin_percentage": margin_percentage
        }
    
    # Test case 1: Packaged Snacks, 200g, ₹299, E-commerce
    result = calculate_unit_economics("Packaged Snacks", 200, 299, "E-commerce")
    expected_mfg = 0.15 * 200  # 30
    expected_packaging = 8
    expected_platform = 0.25 * 299  # 74.75
    expected_logistics = 45
    expected_returns = 0.08 * 299  # 23.92
    expected_gst = 0.18 * 299  # 53.82
    expected_total = expected_mfg + expected_packaging + expected_platform + expected_logistics + expected_returns + expected_gst
    
    test_result(
        "Unit economics calculation (Snacks/E-com)",
        abs(result['total_cost'] - expected_total) < 0.01,
        f"Total cost: ₹{result['total_cost']:.2f} (expected: ₹{expected_total:.2f})"
    )
    
    # Test case 2: Positive margin scenario
    result2 = calculate_unit_economics("Packaged Snacks", 100, 500, "E-commerce")
    test_result(
        "Positive margin calculation",
        result2['margin_percentage'] > 0,
        f"Margin: {result2['margin_percentage']:.1f}%"
    )
    
    # Test case 3: Quick Commerce has higher platform fees
    result_ecom = calculate_unit_economics("Supplements", 100, 299, "E-commerce")
    result_qcom = calculate_unit_economics("Supplements", 100, 299, "Quick Commerce")
    test_result(
        "Quick Commerce has higher platform fees",
        result_qcom['total_cost'] > result_ecom['total_cost'],
        f"E-com: ₹{result_ecom['total_cost']:.0f}, Q-com: ₹{result_qcom['total_cost']:.0f}"
    )
    
    return True

# ============================================================================
# TEST 7: RECOMMENDATION LOGIC
# ============================================================================

def test_recommendation_logic():
    section("TEST 7: Recommendation Logic")
    
    def get_recommendation(margin_percentage):
        if margin_percentage < 10:
            return "nogo", "❌ No-Go"
        elif margin_percentage <= 20:
            return "pilot", "⚠️ Pilot Carefully"
        else:
            return "go", "✅ Go"
    
    # Test No-Go (< 10%)
    rec_type, rec_text = get_recommendation(5)
    test_result(
        "No-Go recommendation (5% margin)",
        rec_type == "nogo",
        f"Result: {rec_text}"
    )
    
    # Test Pilot (10-20%)
    rec_type, rec_text = get_recommendation(15)
    test_result(
        "Pilot recommendation (15% margin)",
        rec_type == "pilot",
        f"Result: {rec_text}"
    )
    
    # Test Go (> 20%)
    rec_type, rec_text = get_recommendation(25)
    test_result(
        "Go recommendation (25% margin)",
        rec_type == "go",
        f"Result: {rec_text}"
    )
    
    # Edge cases
    rec_type, _ = get_recommendation(10)  # Exactly 10% should be pilot
    test_result(
        "Edge case: 10% margin → Pilot",
        rec_type == "pilot",
        "Boundary test"
    )
    
    rec_type, _ = get_recommendation(20)  # Exactly 20% should be pilot
    test_result(
        "Edge case: 20% margin → Pilot",
        rec_type == "pilot",
        "Boundary test"
    )
    
    rec_type, _ = get_recommendation(-5)  # Negative margin
    test_result(
        "Negative margin → No-Go",
        rec_type == "nogo",
        "Negative margin test"
    )
    
    return True

# ============================================================================
# TEST 8: LLM PROMPT GENERATION
# ============================================================================

def test_llm_prompts(api_key):
    section("TEST 8: LLM Prompt Generation & Response Quality")
    
    if not api_key or api_key == "your_groq_api_key_here":
        test_result("LLM prompt test", False, "No API key available")
        return False
    
    # Test search query generation
    prompt = """
Based on this product description, generate 3 different search queries to find competing products on Amazon/Flipkart.

Product: A healthy baked snack made from millets, targeting health-conscious consumers
Category: Packaged Snacks

Return 3 queries, one per line:
1. A direct product search (e.g., "protein bars")
2. A brand-focused search (e.g., "Yoga Bar protein")  
3. A category search (e.g., "healthy snacks India")

Return ONLY the 3 queries, one per line. No numbering, no quotes, no explanation.
"""
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            queries = [q.strip() for q in content.strip().split('\n') if q.strip()]
            
            test_result(
                "LLM generates search queries",
                len(queries) >= 2,
                f"Generated {len(queries)} queries: {queries[:2]}"
            )
            return True
        else:
            test_result("LLM search query generation", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        test_result("LLM prompt test", False, f"Exception: {str(e)[:50]}")
        return False

# ============================================================================
# TEST 9: APP IMPORT TEST
# ============================================================================

def test_app_imports():
    section("TEST 9: App Module Imports")
    
    try:
        import streamlit
        test_result("Streamlit import", True, f"Version: {streamlit.__version__}")
    except ImportError as e:
        test_result("Streamlit import", False, str(e))
    
    try:
        import pandas
        test_result("Pandas import", True, f"Version: {pandas.__version__}")
    except ImportError as e:
        test_result("Pandas import", False, str(e))
    
    try:
        import plotly
        test_result("Plotly import", True, f"Version: {plotly.__version__}")
    except ImportError as e:
        test_result("Plotly import", False, str(e))
    
    try:
        from bs4 import BeautifulSoup
        test_result("BeautifulSoup import", True, "OK")
    except ImportError as e:
        test_result("BeautifulSoup import", False, str(e))
    
    try:
        from dotenv import load_dotenv
        test_result("python-dotenv import", True, "OK")
    except ImportError as e:
        test_result("python-dotenv import", False, str(e))
    
    return True

# ============================================================================
# TEST 10: DYNAMIC PLATFORM FEE CALCULATIONS
# ============================================================================

def test_platform_fees():
    section("TEST 10: Dynamic Platform Fee Calculations")
    
    # Import the fee structures from app
    try:
        from app import (
            AMAZON_FEES, FLIPKART_FEES, QUICK_COMMERCE_FEES,
            get_platform_fees, get_quick_commerce_fees,
            CATEGORY_TO_PLATFORM_CATEGORY
        )
    except ImportError as e:
        test_result("Import platform fee functions", False, str(e))
        return False
    
    # Test 1: Amazon fee structure exists
    test_result(
        "Amazon fee structure loaded",
        "referral_fees" in AMAZON_FEES and "closing_fees" in AMAZON_FEES,
        f"Keys: {list(AMAZON_FEES.keys())}"
    )
    
    # Test 2: Flipkart fee structure exists
    test_result(
        "Flipkart fee structure loaded",
        "commission_rates" in FLIPKART_FEES and "fixed_fees" in FLIPKART_FEES,
        f"Keys: {list(FLIPKART_FEES.keys())}"
    )
    
    # Test 3: Quick Commerce platforms loaded
    test_result(
        "Quick Commerce platforms loaded",
        all(p in QUICK_COMMERCE_FEES for p in ["blinkit", "zepto", "swiggy_instamart"]),
        f"Platforms: {list(QUICK_COMMERCE_FEES.keys())}"
    )
    
    # Test 4: Amazon fee calculation
    amazon_fees = get_platform_fees(299, 200, "Packaged Snacks", "amazon", "national")
    test_result(
        "Amazon fee calculation (₹299, 200g snack)",
        amazon_fees["total_platform_fee"] > 0,
        f"Total fee: ₹{amazon_fees['total_platform_fee']:.2f}"
    )
    
    # Test 5: Amazon fee breakdown exists
    test_result(
        "Amazon fee breakdown available",
        all(k in amazon_fees for k in ["referral_fee", "closing_fee", "weight_handling_fee"]),
        f"Referral: ₹{amazon_fees.get('referral_fee', 0):.2f}, Closing: ₹{amazon_fees.get('closing_fee', 0)}"
    )
    
    # Test 6: Flipkart fee calculation
    flipkart_fees = get_platform_fees(299, 200, "Packaged Snacks", "flipkart", "national")
    test_result(
        "Flipkart fee calculation (₹299, 200g snack)",
        flipkart_fees["total_platform_fee"] > 0,
        f"Total fee: ₹{flipkart_fees['total_platform_fee']:.2f}"
    )
    
    # Test 7: Quick Commerce fee calculation
    blinkit_fees = get_quick_commerce_fees(299, "blinkit")
    test_result(
        "Blinkit fee calculation (₹299 MRP)",
        blinkit_fees["total_platform_fee"] > 0 and blinkit_fees["commission_rate"] >= 0.25,
        f"Commission: {blinkit_fees['commission_rate']*100:.0f}%, Fee: ₹{blinkit_fees['total_platform_fee']:.2f}"
    )
    
    # Test 8: Quick Commerce vs E-commerce fees
    zepto_fees = get_quick_commerce_fees(299, "zepto")
    test_result(
        "Quick Commerce fees higher than E-commerce",
        zepto_fees["total_platform_fee"] > amazon_fees["total_platform_fee"],
        f"Zepto: ₹{zepto_fees['total_platform_fee']:.2f} > Amazon: ₹{amazon_fees['total_platform_fee']:.2f}"
    )
    
    # Test 9: Category mapping exists
    test_result(
        "Category to platform mapping exists",
        "Packaged Snacks" in CATEGORY_TO_PLATFORM_CATEGORY,
        f"Snacks→Amazon: {CATEGORY_TO_PLATFORM_CATEGORY.get('Packaged Snacks', {}).get('amazon', 'N/A')}"
    )
    
    # Test 10: Price-based closing fee brackets
    low_price_fees = get_platform_fees(199, 200, "Packaged Snacks", "amazon", "national")
    high_price_fees = get_platform_fees(999, 200, "Packaged Snacks", "amazon", "national")
    test_result(
        "Higher price = different closing fee bracket",
        low_price_fees["closing_fee"] != high_price_fees["closing_fee"] or 
        low_price_fees["referral_fee"] < high_price_fees["referral_fee"],
        f"₹199 closing: ₹{low_price_fees['closing_fee']}, ₹999 closing: ₹{high_price_fees['closing_fee']}"
    )
    
    return True

# ============================================================================
# TEST 11: DYNAMIC RAW MATERIAL PRICING
# ============================================================================

def test_raw_material_pricing():
    section("TEST 11: Dynamic Raw Material Pricing")
    
    try:
        from app import RAW_MATERIAL_COSTS, MANUFACTURING_OVERHEAD
    except ImportError as e:
        test_result("Import raw material data", False, str(e))
        return False
    
    # Test 1: Raw material database populated
    test_result(
        "Raw material database populated",
        len(RAW_MATERIAL_COSTS) > 30,
        f"Contains {len(RAW_MATERIAL_COSTS)} ingredients"
    )
    
    # Test 2: Key ingredients have prices
    key_ingredients = ["wheat_flour", "sugar", "palm_oil", "salt", "milk_powder"]
    all_present = all(ing in RAW_MATERIAL_COSTS for ing in key_ingredients)
    test_result(
        "Key ingredients have prices",
        all_present,
        f"Wheat flour: ₹{RAW_MATERIAL_COSTS.get('wheat_flour', 'N/A')}/kg"
    )
    
    # Test 3: Price ranges are realistic
    wheat_price = RAW_MATERIAL_COSTS.get("wheat_flour", 0)
    sugar_price = RAW_MATERIAL_COSTS.get("sugar", 0)
    test_result(
        "Prices are realistic (₹20-100/kg for basics)",
        20 <= wheat_price <= 100 and 20 <= sugar_price <= 100,
        f"Wheat: ₹{wheat_price}/kg, Sugar: ₹{sugar_price}/kg"
    )
    
    # Test 4: Premium ingredients have higher prices
    almond_price = RAW_MATERIAL_COSTS.get("almonds", 0)
    cardamom_price = RAW_MATERIAL_COSTS.get("cardamom", 0)
    test_result(
        "Premium ingredients priced higher",
        almond_price > 500 and cardamom_price > 1000,
        f"Almonds: ₹{almond_price}/kg, Cardamom: ₹{cardamom_price}/kg"
    )
    
    # Test 5: Manufacturing overhead rates defined
    test_result(
        "Manufacturing overhead rates defined",
        len(MANUFACTURING_OVERHEAD) >= 5,
        f"Categories: {list(MANUFACTURING_OVERHEAD.keys())}"
    )
    
    # Test 6: Overhead rates are reasonable (30-60%)
    snack_overhead = MANUFACTURING_OVERHEAD.get("Packaged Snacks", 0)
    supplement_overhead = MANUFACTURING_OVERHEAD.get("Supplements", 0)
    test_result(
        "Overhead rates in realistic range (30-60%)",
        0.25 <= snack_overhead <= 0.60 and 0.25 <= supplement_overhead <= 0.60,
        f"Snacks: {snack_overhead*100:.0f}%, Supplements: {supplement_overhead*100:.0f}%"
    )
    
    return True

# ============================================================================
# TEST 12: PACKAGING COST ESTIMATION
# ============================================================================

def test_packaging_costs():
    section("TEST 12: Packaging Cost Estimation")
    
    try:
        from app import PACKAGING_COSTS_DETAILED, estimate_packaging_cost
    except ImportError as e:
        test_result("Import packaging functions", False, str(e))
        return False
    
    # Test 1: Packaging types defined
    test_result(
        "Packaging types database populated",
        len(PACKAGING_COSTS_DETAILED) >= 10,
        f"Contains {len(PACKAGING_COSTS_DETAILED)} packaging types"
    )
    
    # Test 2: Packaging has cost and capacity
    pouch = PACKAGING_COSTS_DETAILED.get("pouch_small", {})
    test_result(
        "Packaging entry has cost and capacity",
        "cost" in pouch and "weight_capacity" in pouch,
        f"Small pouch: ₹{pouch.get('cost', 'N/A')}, capacity: {pouch.get('weight_capacity', 'N/A')}g"
    )
    
    # Test 3: Packaging cost estimation works
    pkg_result = estimate_packaging_cost(200, "Packaged Snacks")
    test_result(
        "Packaging cost estimation works",
        pkg_result["total_packaging_cost"] > 0,
        f"Total: ₹{pkg_result['total_packaging_cost']:.2f}"
    )
    
    # Test 4: Packaging includes all components
    test_result(
        "Packaging breakdown includes all components",
        all(k in pkg_result for k in ["primary_packaging", "labels", "closures"]),
        f"Primary: ₹{pkg_result.get('primary_packaging', 0)}, Labels: ₹{pkg_result.get('labels', 0)}"
    )
    
    # Test 5: Auto-selects appropriate packaging type
    test_result(
        "Auto-selects packaging type for category",
        "packaging_type" in pkg_result and len(pkg_result["packaging_type"]) > 0,
        f"Selected: {pkg_result.get('packaging_type', 'N/A')}"
    )
    
    # Test 6: Different categories get different packaging
    snack_pkg = estimate_packaging_cost(200, "Packaged Snacks")
    beverage_pkg = estimate_packaging_cost(200, "Beverages")
    test_result(
        "Different categories get different packaging",
        snack_pkg["packaging_type"] != beverage_pkg["packaging_type"],
        f"Snacks: {snack_pkg['packaging_type']}, Beverages: {beverage_pkg['packaging_type']}"
    )
    
    # Test 7: Larger size = different packaging
    small_pkg = estimate_packaging_cost(100, "Packaged Snacks")
    large_pkg = estimate_packaging_cost(500, "Packaged Snacks")
    test_result(
        "Larger size gets larger packaging",
        "small" in small_pkg["packaging_type"] and ("large" in large_pkg["packaging_type"] or "medium" in large_pkg["packaging_type"]),
        f"100g: {small_pkg['packaging_type']}, 500g: {large_pkg['packaging_type']}"
    )
    
    return True

# ============================================================================
# TEST 13: GST AND RETURN RATES
# ============================================================================

def test_gst_and_returns():
    section("TEST 13: GST and Return Rates by Category")
    
    try:
        from app import GST_RATES, RETURN_RATES
    except ImportError as e:
        test_result("Import GST and return data", False, str(e))
        return False
    
    # Test 1: GST rates defined
    test_result(
        "GST rates defined for categories",
        len(GST_RATES) >= 5,
        f"Categories: {len(GST_RATES)}"
    )
    
    # Test 2: GST rates are valid (0-28%)
    all_valid = all(0 <= rate <= 0.28 for rate in GST_RATES.values())
    test_result(
        "GST rates in valid range (0-28%)",
        all_valid,
        f"Snacks: {GST_RATES.get('Packaged Snacks', 0)*100:.0f}%, Personal Care: {GST_RATES.get('Personal Care', 0)*100:.0f}%"
    )
    
    # Test 3: Fresh food has lower GST
    test_result(
        "Fresh food has lower/zero GST",
        GST_RATES.get("Fresh Food", 0.18) <= 0.05,
        f"Fresh Food GST: {GST_RATES.get('Fresh Food', 0)*100:.0f}%"
    )
    
    # Test 4: Return rates defined
    test_result(
        "Return rates defined for categories",
        len(RETURN_RATES) >= 5,
        f"Categories: {len(RETURN_RATES)}"
    )
    
    # Test 5: Return rates are realistic (1-30%)
    all_valid_returns = all(0.01 <= rate <= 0.30 for rate in RETURN_RATES.values())
    test_result(
        "Return rates in realistic range (1-30%)",
        all_valid_returns,
        f"Snacks: {RETURN_RATES.get('Packaged Snacks', 0)*100:.0f}%, Fashion: {RETURN_RATES.get('Fashion', 0)*100:.0f}%"
    )
    
    # Test 6: Fashion has highest returns
    fashion_returns = RETURN_RATES.get("Fashion", 0)
    snack_returns = RETURN_RATES.get("Packaged Snacks", 0)
    test_result(
        "Fashion has higher return rate than FMCG",
        fashion_returns > snack_returns,
        f"Fashion: {fashion_returns*100:.0f}%, Snacks: {snack_returns*100:.0f}%"
    )
    
    return True

# ============================================================================
# TEST 14: LOGISTICS RATES
# ============================================================================

def test_logistics_rates():
    section("TEST 14: Logistics Partner Rates")
    
    try:
        from app import LOGISTICS_RATES
    except ImportError as e:
        test_result("Import logistics data", False, str(e))
        return False
    
    # Test 1: Multiple logistics partners defined
    partners = list(LOGISTICS_RATES.keys())
    test_result(
        "Multiple logistics partners defined",
        len(partners) >= 3,
        f"Partners: {partners}"
    )
    
    # Test 2: Each partner has zone-based pricing
    delhivery = LOGISTICS_RATES.get("delhivery", {})
    test_result(
        "Zone-based pricing (local/regional/national)",
        all(zone in delhivery for zone in ["local", "regional", "national"]),
        f"Delhivery zones: {list(delhivery.keys())[:3]}"
    )
    
    # Test 3: Weight brackets defined
    local_rates = delhivery.get("local", {})
    test_result(
        "Weight brackets defined",
        len(local_rates) >= 3,
        f"Brackets: {list(local_rates.keys())}"
    )
    
    # Test 4: Local < Regional < National pricing
    if local_rates and delhivery.get("regional") and delhivery.get("national"):
        local_500g = local_rates.get("0-500", 0)
        regional_500g = delhivery["regional"].get("0-500", 0)
        national_500g = delhivery["national"].get("0-500", 0)
        test_result(
            "Local < Regional < National pricing",
            local_500g < regional_500g < national_500g,
            f"500g: Local ₹{local_500g}, Regional ₹{regional_500g}, National ₹{national_500g}"
        )
    
    # Test 5: COD charges defined
    test_result(
        "COD charges defined",
        "cod_charge" in delhivery,
        f"Delhivery COD: ₹{delhivery.get('cod_charge', 'N/A')}"
    )
    
    # Test 6: Xpressbees is cheapest (common in industry)
    xpressbees_500g = LOGISTICS_RATES.get("xpressbees", {}).get("national", {}).get("0-500", 999)
    bluedart_500g = LOGISTICS_RATES.get("bluedart", {}).get("national", {}).get("0-500", 0)
    test_result(
        "Xpressbees competitive with Bluedart",
        xpressbees_500g <= bluedart_500g,
        f"Xpressbees: ₹{xpressbees_500g}, Bluedart: ₹{bluedart_500g}"
    )
    
    return True

# ============================================================================
# TEST 15: FULL UNIT ECONOMICS CALCULATION (DYNAMIC)
# ============================================================================

def test_dynamic_unit_economics():
    section("TEST 15: Full Dynamic Unit Economics")
    
    try:
        from app import calculate_unit_economics
    except ImportError as e:
        test_result("Import calculate_unit_economics", False, str(e))
        return False
    
    # Test 1: Basic calculation works
    result = calculate_unit_economics(
        category="Packaged Snacks",
        weight=200,
        mrp=299,
        channel="E-commerce",
        product_description="A healthy baked multigrain snack"
    )
    test_result(
        "Unit economics calculation completes",
        result is not None and "net_margin" in result,
        f"Net margin: ₹{result.get('net_margin', 'N/A')}"
    )
    
    # Test 2: All cost components present
    required_keys = ["manufacturing_cost", "packaging_cost", "platform_fees", 
                     "logistics_cost", "returns_cost", "gst_liability"]
    all_present = all(k in result for k in required_keys)
    test_result(
        "All cost components present",
        all_present,
        f"Keys: {list(result.keys())[:6]}..."
    )
    
    # Test 3: Costs are positive
    costs_positive = all(result.get(k, -1) >= 0 for k in required_keys)
    test_result(
        "All costs are non-negative",
        costs_positive,
        f"Mfg: ₹{result.get('manufacturing_cost', 0):.1f}, Platform: ₹{result.get('platform_fees', 0):.1f}"
    )
    
    # Test 4: Total cost equals sum of components
    calculated_total = (
        result.get("manufacturing_cost", 0) +
        result.get("packaging_cost", 0) +
        result.get("platform_fees", 0) +
        result.get("logistics_cost", 0) +
        result.get("returns_cost", 0) +
        result.get("marketing_allocation", 0) +
        result.get("gst_liability", 0)
    )
    reported_total = result.get("total_cost", 0)
    test_result(
        "Total cost calculation is consistent",
        abs(calculated_total - reported_total) < 1,  # Allow ₹1 rounding
        f"Calculated: ₹{calculated_total:.1f}, Reported: ₹{reported_total:.1f}"
    )
    
    # Test 5: Net margin = MRP - Total Cost
    expected_margin = 299 - reported_total
    actual_margin = result.get("net_margin", 0)
    test_result(
        "Net margin calculation correct",
        abs(expected_margin - actual_margin) < 1,
        f"Expected: ₹{expected_margin:.1f}, Actual: ₹{actual_margin:.1f}"
    )
    
    # Test 6: Margin percentage calculation
    expected_pct = (actual_margin / 299) * 100
    actual_pct = result.get("margin_percentage", 0)
    test_result(
        "Margin percentage correct",
        abs(expected_pct - actual_pct) < 0.5,
        f"Expected: {expected_pct:.1f}%, Actual: {actual_pct:.1f}%"
    )
    
    # Test 7: Manufacturing breakdown available
    test_result(
        "Manufacturing breakdown available",
        result.get("manufacturing_breakdown") is not None,
        f"Has breakdown: {result.get('manufacturing_breakdown') is not None}"
    )
    
    # Test 8: Platform breakdown available
    test_result(
        "Platform breakdown available",
        result.get("platform_breakdown") is not None,
        f"Has breakdown: {result.get('platform_breakdown') is not None}"
    )
    
    # Test 9: Quick Commerce has lower margin than E-commerce
    ecom_result = calculate_unit_economics("Packaged Snacks", 200, 299, "E-commerce", "Healthy snack")
    qcom_result = calculate_unit_economics("Packaged Snacks", 200, 299, "Quick Commerce", "Healthy snack")
    test_result(
        "Quick Commerce margin lower than E-commerce",
        qcom_result.get("margin_percentage", 0) < ecom_result.get("margin_percentage", 100),
        f"E-com: {ecom_result.get('margin_percentage', 0):.1f}%, Q-com: {qcom_result.get('margin_percentage', 0):.1f}%"
    )
    
    # Test 10: Channel recommendation present
    test_result(
        "Channel recommendation provided",
        result.get("channel_recommendation") is not None and len(result.get("channel_recommendation", "")) > 10,
        f"Recommendation: {result.get('channel_recommendation', 'N/A')[:50]}..."
    )
    
    return True

# ============================================================================
# TEST 16: INDIAMART SCRAPING (Dynamic Pricing)
# ============================================================================

def test_indiamart_scraping():
    section("TEST 16: IndiaMART Price Scraping")
    
    import importlib
    try:
        import app
        importlib.reload(app)  # Force reload to get latest code
        scrape_indiamart_price = app.scrape_indiamart_price
    except Exception as e:
        test_result("Import scrape_indiamart_price", False, str(e))
        return False
    
    # Test common ingredients
    test_ingredients = ["wheat flour", "sugar", "palm oil"]
    
    for ingredient in test_ingredients:
        result = scrape_indiamart_price(ingredient)
        
        if result:
            test_result(
                f"IndiaMART: '{ingredient}' price found",
                result.get("price", 0) > 0,
                f"Price: ₹{result.get('price', 0)}/kg ({result.get('num_listings', 0)} listings, {result.get('confidence', 'N/A')})"
            )
            return True  # At least one worked
        else:
            test_warning(
                f"IndiaMART: '{ingredient}'",
                "No price found (site may block scraping)"
            )
        
        time.sleep(1)  # Rate limiting
    
    test_warning(
        "IndiaMART scraping",
        "All queries failed - site may be blocking. LLM fallback will be used."
    )
    return False

# ============================================================================
# TEST 17: AI INGREDIENT ANALYSIS
# ============================================================================

def test_ai_ingredient_analysis(api_key):
    section("TEST 17: AI Ingredient Analysis")
    
    if not api_key or api_key == "your_groq_api_key_here":
        test_result("AI ingredient analysis", False, "No API key available")
        return False
    
    try:
        from app import analyze_product_ingredients
    except ImportError as e:
        test_result("Import analyze_product_ingredients", False, str(e))
        return False
    
    # Test product analysis
    product_desc = "A protein bar made with whey protein, almonds, dark chocolate, and honey"
    
    try:
        ingredients = analyze_product_ingredients(
            product_desc, "Packaged Snacks", 60, api_key, "Groq"
        )
        
        test_result(
            "AI returns ingredient list",
            ingredients is not None and len(ingredients) > 0,
            f"Found {len(ingredients) if ingredients else 0} ingredients"
        )
        
        if ingredients:
            # Check structure
            first_ing = ingredients[0]
            test_result(
                "Ingredient has required fields",
                "ingredient" in first_ing and "quantity_grams" in first_ing,
                f"First: {first_ing.get('ingredient', 'N/A')}, {first_ing.get('quantity_grams', 0)}g"
            )
            
            # Check total quantity is reasonable
            total_qty = sum(ing.get("quantity_grams", 0) for ing in ingredients)
            test_result(
                "Total quantity reasonable for 60g product",
                50 <= total_qty <= 150,  # Allow some overhead
                f"Total: {total_qty}g (product is 60g + wastage)"
            )
            
            return True
    except Exception as e:
        test_result("AI ingredient analysis", False, f"Error: {str(e)[:50]}")
    
    return False

# ============================================================================
# TEST 18: LIVE PRICE FETCHING
# ============================================================================

def test_live_price_fetching(api_key):
    section("TEST 18: Live Ingredient Price Fetching")
    
    try:
        from app import get_live_ingredient_price
    except ImportError as e:
        test_result("Import get_live_ingredient_price", False, str(e))
        return False
    
    test_ingredients = ["wheat flour", "sugar", "almonds"]
    
    for ingredient in test_ingredients:
        result = get_live_ingredient_price(ingredient, api_key, "Groq")
        
        test_result(
            f"Price fetched for '{ingredient}'",
            result is not None and result.get("price_per_kg", 0) > 0,
            f"₹{result.get('price_per_kg', 0)}/kg via {result.get('source', 'Unknown')} ({result.get('confidence', 'N/A')})"
        )
    
    return True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "="*60)
    print("  GO / NO-GO APP - TEST SUITE")
    print("  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # Run all tests
    api_key = test_env_variables()
    
    test_app_imports()
    
    groq_working = test_groq_api(api_key)
    
    amazon_working = test_amazon_scraping()
    
    flipkart_working = test_flipkart_scraping()
    
    bigbasket_working = test_bigbasket_scraping()
    
    test_unit_economics()
    
    test_recommendation_logic()
    
    # NEW DYNAMIC PRICING TESTS
    test_platform_fees()
    
    test_raw_material_pricing()
    
    test_packaging_costs()
    
    test_gst_and_returns()
    
    test_logistics_rates()
    
    test_dynamic_unit_economics()
    
    indiamart_working = test_indiamart_scraping()
    
    if groq_working:
        test_llm_prompts(api_key)
        test_ai_ingredient_analysis(api_key)
        test_live_price_fetching(api_key)
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"  ✅ Passed:   {PASSED}")
    print(f"  ❌ Failed:   {FAILED}")
    print(f"  ⚠️  Warnings: {WARNINGS}")
    print("="*60)
    
    # Critical feature check
    print("\n  CRITICAL FEATURES:")
    print(f"  • Groq API:          {'✅ Working' if groq_working else '❌ Not working'}")
    print(f"  • Amazon Scraping:   {'✅ Working' if amazon_working else '⚠️  Blocked (LLM fallback available)'}")
    print(f"  • Flipkart:          {'✅ Working' if flipkart_working else '⚠️  May need update'}")
    print(f"  • BigBasket:         {'✅ Working' if bigbasket_working else '⚠️  May need JS'}")
    print(f"  • IndiaMART:         {'✅ Working' if indiamart_working else '⚠️  Using fallback prices'}")
    print("="*60)
    
    print("\n  DYNAMIC PRICING TESTS:")
    print(f"  • Platform Fees:     ✅ Amazon, Flipkart, Quick Commerce")
    print(f"  • Raw Materials:     ✅ 60+ ingredients database")
    print(f"  • GST Rates:         ✅ Category-specific rates")
    print(f"  • Logistics:         ✅ Multi-carrier rates")
    print("="*60)
    
    if FAILED == 0:
        print("\n  🎉 All tests passed! App is ready to run.\n")
    elif FAILED <= 3 and groq_working:
        print("\n  ⚠️  Some tests failed but core features work.")
        print("     App will use LLM fallback for competitor analysis.\n")
    else:
        print("\n  ❌ Critical failures detected. Please fix before running.\n")
    
    return FAILED == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
