"""
Go / No-Go
A comprehensive decision-support tool that helps founders evaluate product viability
through AI-powered market research, competitor analysis, and unit economics simulation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Go / No-Go",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .main {
        padding: 2rem 3rem;
    }
    
    .stTextArea textarea {
        font-size: 16px;
    }
    
    .recommendation-go {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .recommendation-pilot {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .recommendation-nogo {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .competitor-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .insight-card {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .research-status {
        background-color: #f0f0f0;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    
    .disclaimer {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

if 'research_complete' not in st.session_state:
    st.session_state.research_complete = False
if 'research_results' not in st.session_state:
    st.session_state.research_results = None
if 'competitors' not in st.session_state:
    st.session_state.competitors = None
if 'market_insights' not in st.session_state:
    st.session_state.market_insights = None

# Agent Chat States
if 'agent_outputs' not in st.session_state:
    st.session_state.agent_outputs = {}
if 'board_discussion' not in st.session_state:
    st.session_state.board_discussion = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {'marketing': [], 'strategy': [], 'gtm': [], 'finance': []}
if 'active_chat_agent' not in st.session_state:
    st.session_state.active_chat_agent = None
if 'product_context' not in st.session_state:
    st.session_state.product_context = {}

# ============================================================================
# DYNAMIC PLATFORM FEE STRUCTURES (Based on actual marketplace data 2024-2026)
# Source: Amazon Seller Central, Flipkart Seller Hub, Blinkit/Zepto/Swiggy Partner Docs
# ============================================================================

# Amazon India Fee Structure (as of 2024-2026)
AMAZON_FEES = {
    "referral_fees": {  # Percentage of selling price
        "Grocery & Gourmet": 0.08,  # 8%
        "Health & Personal Care": 0.12,  # 12%
        "Beauty": 0.10,  # 10%
        "Baby Products": 0.10,  # 10%
        "Pet Supplies": 0.15,  # 15%
        "Home & Kitchen": 0.12,  # 12%
        "Electronics": 0.10,  # 10%
        "Sports & Fitness": 0.12,  # 12%
        "Other": 0.15,  # 15% default
    },
    "closing_fees": {  # Based on price range (INR)
        "0-300": 26,
        "301-500": 21,
        "501-1000": 26,
        "1000+": 51,
    },
    "weight_handling": {  # Per item based on weight (grams) - Easy Ship
        "local": {"0-500": 29, "500-1000": 40, "1000-2000": 54, "2000+": 74},
        "regional": {"0-500": 43, "500-1000": 58, "1000-2000": 77, "2000+": 102},
        "national": {"0-500": 57, "500-1000": 77, "1000-2000": 102, "2000+": 137},
    },
    "pick_pack_fee": 14,  # FBA only
    "storage_fee_per_kg_month": 42,  # FBA only
    "gst_on_fees": 0.18,  # 18% GST on all Amazon fees
}

# Flipkart Fee Structure (as of 2024-2026)
FLIPKART_FEES = {
    "commission_rates": {  # Percentage of selling price
        "Grocery & Gourmet": 0.05,  # 5%
        "Health & Personal Care": 0.12,  # 12%
        "Beauty & Cosmetics": 0.10,  # 10%
        "Baby Care": 0.08,  # 8%
        "Pet Supplies": 0.14,  # 14%
        "Home & Kitchen": 0.14,  # 14%
        "Electronics": 0.08,  # 8%
        "Sports": 0.12,  # 12%
        "Other": 0.12,  # 12% default
    },
    "fixed_fees": {  # Based on price range
        "0-300": 11,
        "301-500": 25,
        "501-1000": 40,
        "1000+": 60,
    },
    "shipping_fees": {  # Based on weight (grams)
        "local": {"0-500": 25, "500-1000": 35, "1000-2000": 50, "2000+": 70},
        "zonal": {"0-500": 40, "500-1000": 55, "1000-2000": 75, "2000+": 100},
        "national": {"0-500": 55, "500-1000": 75, "1000-2000": 100, "2000+": 135},
    },
    "collection_fee_percent": 0.02,  # 2% collection fee
    "gst_on_fees": 0.18,
}

# Quick Commerce Fee Structure (Blinkit, Zepto, Swiggy Instamart)
QUICK_COMMERCE_FEES = {
    "blinkit": {
        "commission_rate": 0.30,  # 30% of MRP (higher than e-commerce)
        "listing_fee_monthly": 0,  # No monthly fee
        "min_margin_required": 0.25,  # They require 25% margin minimum
        "payment_cycle_days": 7,
        "return_rate": 0.02,  # 2% (lower due to instant verification)
    },
    "zepto": {
        "commission_rate": 0.28,  # 28%
        "listing_fee_monthly": 0,
        "min_margin_required": 0.22,
        "payment_cycle_days": 7,
        "return_rate": 0.02,
    },
    "swiggy_instamart": {
        "commission_rate": 0.32,  # 32% (highest)
        "listing_fee_monthly": 0,
        "min_margin_required": 0.25,
        "payment_cycle_days": 7,
        "return_rate": 0.03,
    },
    "bigbasket": {
        "commission_rate": 0.25,  # 25%
        "listing_fee_monthly": 500,  # Rs 500/month
        "min_margin_required": 0.20,
        "payment_cycle_days": 14,
        "return_rate": 0.04,
    },
}

# D2C Platform Costs (Shopify India, WooCommerce)
D2C_COSTS = {
    "shopify": {
        "monthly_fee": 2499,  # Basic plan INR
        "transaction_fee": 0.02,  # 2%
        "payment_gateway_fee": 0.02,  # ~2% (Razorpay/PayU)
    },
    "woocommerce": {
        "monthly_fee": 500,  # Hosting
        "transaction_fee": 0,
        "payment_gateway_fee": 0.02,
    },
}

# GST Rates by Category (India)
GST_RATES = {
    "Packaged Snacks": 0.12,  # 12%
    "Personal Care": 0.18,  # 18%
    "Supplements": 0.18,
    "Beverages": 0.12,  # (non-aerated), aerated is 28%
    "Home Care": 0.18,
    "Baby Products": 0.12,
    "Pet Food": 0.18,
    "Electronics": 0.18,
    "Dairy Products": 0.05,  # 5%
    "Fresh Food": 0.0,  # 0%
    "Other": 0.18,
}

# Raw Material Wholesale Price Database (INR per kg/unit - 2024-2026 averages)
# Sources: IndiaMART, TradeIndia, APMC mandis, industry reports
RAW_MATERIAL_COSTS = {
    # Grains & Flours
    "wheat_flour": 32,  # per kg
    "rice_flour": 45,
    "maida": 35,
    "besan": 85,
    "oats": 120,
    "corn_flour": 40,
    "ragi_flour": 55,
    "multigrain_flour": 75,
    
    # Oils & Fats
    "palm_oil": 95,  # per kg/litre
    "sunflower_oil": 140,
    "coconut_oil": 180,
    "olive_oil": 650,
    "mustard_oil": 150,
    "groundnut_oil": 190,
    "ghee": 450,
    "butter": 420,
    
    # Sweeteners
    "sugar": 42,
    "jaggery": 55,
    "honey": 280,
    "stevia": 1500,
    "glucose_syrup": 65,
    
    # Dairy
    "milk_powder": 320,
    "whey_protein": 450,
    "paneer": 320,
    "cheese": 380,
    "cream": 280,
    
    # Proteins
    "soy_protein": 180,
    "pea_protein": 350,
    "chicken": 180,
    "eggs": 6,  # per piece
    "fish": 250,
    
    # Spices & Flavors
    "salt": 15,
    "turmeric": 120,
    "chili_powder": 180,
    "cumin": 220,
    "coriander": 90,
    "black_pepper": 450,
    "cardamom": 2200,
    "cinnamon": 280,
    "vanilla_extract": 3500,  # per litre
    "natural_flavors": 800,
    
    # Nuts & Seeds
    "peanuts": 120,
    "almonds": 750,
    "cashews": 850,
    "walnuts": 950,
    "chia_seeds": 400,
    "flax_seeds": 180,
    "sunflower_seeds": 160,
    "pumpkin_seeds": 450,
    
    # Fruits & Vegetables (dried/processed)
    "dried_fruits_mix": 350,
    "tomato_paste": 95,
    "mango_pulp": 120,
    "coconut": 80,
    "dates": 180,
    
    # Chemicals & Additives (for personal care/home care)
    "sodium_lauryl_sulfate": 180,  # surfactant
    "glycerin": 120,
    "citric_acid": 95,
    "sodium_bicarbonate": 45,
    "fragrance_oils": 650,
    "essential_oils": 1200,
    "preservatives": 450,
    "emulsifiers": 380,
    "thickeners": 220,
    "colorants": 850,
    
    # Packaging Raw Materials
    "hdpe_granules": 135,  # per kg
    "pet_granules": 125,
    "pp_granules": 145,
    "aluminum_foil": 280,
    "kraft_paper": 65,
    "corrugated_board": 45,
    "glass": 25,  # per piece (bottles)
    "labels": 2,  # per piece
    "caps_closures": 3,  # per piece
}

# Packaging Cost by Type (INR per unit)
PACKAGING_COSTS_DETAILED = {
    "pouch_small": {"cost": 3, "weight_capacity": 100},  # Up to 100g
    "pouch_medium": {"cost": 5, "weight_capacity": 250},
    "pouch_large": {"cost": 8, "weight_capacity": 500},
    "pouch_xl": {"cost": 12, "weight_capacity": 1000},
    "box_small": {"cost": 8, "weight_capacity": 200},
    "box_medium": {"cost": 12, "weight_capacity": 500},
    "box_large": {"cost": 18, "weight_capacity": 1000},
    "bottle_plastic_small": {"cost": 6, "weight_capacity": 200},
    "bottle_plastic_medium": {"cost": 10, "weight_capacity": 500},
    "bottle_plastic_large": {"cost": 15, "weight_capacity": 1000},
    "bottle_glass_small": {"cost": 12, "weight_capacity": 200},
    "bottle_glass_medium": {"cost": 18, "weight_capacity": 500},
    "jar_plastic": {"cost": 8, "weight_capacity": 250},
    "jar_glass": {"cost": 15, "weight_capacity": 250},
    "tube": {"cost": 7, "weight_capacity": 100},
    "sachet": {"cost": 1.5, "weight_capacity": 50},
    "can_metal": {"cost": 15, "weight_capacity": 400},
    "tetrapack": {"cost": 8, "weight_capacity": 500},
}

# Secondary Packaging (outer box for shipping)
SECONDARY_PACKAGING = {
    "corrugated_box_small": 8,
    "corrugated_box_medium": 12,
    "corrugated_box_large": 18,
    "bubble_wrap": 3,
    "tape": 1,
    "void_fill": 2,
}

# Manufacturing Overhead Rates (as % of raw material cost)
MANUFACTURING_OVERHEAD = {
    "Packaged Snacks": 0.35,  # 35% overhead (equipment, labor, utilities)
    "Personal Care": 0.45,
    "Supplements": 0.55,  # Higher due to quality control, certifications
    "Beverages": 0.30,
    "Home Care": 0.40,
    "Baby Products": 0.50,
    "Pet Food": 0.35,
    "Electronics": 0.25,
    "Other": 0.40,
}

# Quality & Compliance Costs (one-time amortized per unit)
COMPLIANCE_COSTS = {
    "fssai_license": 25000,  # Annual, amortize over units
    "bis_certification": 15000,
    "organic_certification": 50000,
    "lab_testing_per_batch": 5000,
    "barcode_registration": 5000,
    "trademark": 15000,
}

# E-commerce Return Rates by Category
RETURN_RATES = {
    "Packaged Snacks": 0.03,  # 3%
    "Personal Care": 0.08,
    "Supplements": 0.06,
    "Beverages": 0.04,
    "Home Care": 0.05,
    "Baby Products": 0.07,
    "Pet Food": 0.04,
    "Electronics": 0.12,
    "Fashion": 0.25,  # Highest
    "Other": 0.08,
}

# Logistics Partners Rates (INR) - 2024-2026
LOGISTICS_RATES = {
    "delhivery": {
        "local": {"0-500": 35, "500-1000": 45, "1000-2000": 60},
        "regional": {"0-500": 50, "500-1000": 65, "1000-2000": 85},
        "national": {"0-500": 70, "500-1000": 90, "1000-2000": 120},
        "cod_charge": 35,
        "rto_charge_percent": 1.0,  # Full shipping if returned
    },
    "bluedart": {
        "local": {"0-500": 45, "500-1000": 55, "1000-2000": 75},
        "regional": {"0-500": 60, "500-1000": 80, "1000-2000": 105},
        "national": {"0-500": 85, "500-1000": 110, "1000-2000": 145},
        "cod_charge": 40,
        "rto_charge_percent": 1.0,
    },
    "ecom_express": {
        "local": {"0-500": 32, "500-1000": 42, "1000-2000": 55},
        "regional": {"0-500": 48, "500-1000": 62, "1000-2000": 80},
        "national": {"0-500": 65, "500-1000": 85, "1000-2000": 110},
        "cod_charge": 30,
        "rto_charge_percent": 1.0,
    },
    "xpressbees": {
        "local": {"0-500": 30, "500-1000": 40, "1000-2000": 52},
        "regional": {"0-500": 45, "500-1000": 58, "1000-2000": 75},
        "national": {"0-500": 60, "500-1000": 78, "1000-2000": 100},
        "cod_charge": 28,
        "rto_charge_percent": 1.0,
    },
}

# Platform-specific category mappings
CATEGORY_TO_PLATFORM_CATEGORY = {
    "Packaged Snacks": {"amazon": "Grocery & Gourmet", "flipkart": "Grocery & Gourmet"},
    "Personal Care": {"amazon": "Health & Personal Care", "flipkart": "Health & Personal Care"},
    "Supplements": {"amazon": "Health & Personal Care", "flipkart": "Health & Personal Care"},
    "Beverages": {"amazon": "Grocery & Gourmet", "flipkart": "Grocery & Gourmet"},
    "Home Care": {"amazon": "Home & Kitchen", "flipkart": "Home & Kitchen"},
    "Baby Products": {"amazon": "Baby Products", "flipkart": "Baby Care"},
    "Pet Food": {"amazon": "Pet Supplies", "flipkart": "Pet Supplies"},
    "Electronics": {"amazon": "Electronics", "flipkart": "Electronics"},
    "Other": {"amazon": "Other", "flipkart": "Other"},
}

# ============================================================================
# COMPETITOR RESEARCH FUNCTIONS (Multiple Sources)
# ============================================================================

# Rotating User Agents to avoid blocking
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

import random

def get_headers():
    """Get randomized headers to avoid blocking."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }


def search_amazon_india(query, num_results=6):
    """Search Amazon India for products with improved scraping."""
    try:
        # Try multiple URL formats
        urls_to_try = [
            f"https://www.amazon.in/s?k={query.replace(' ', '+')}&ref=nb_sb_noss",
            f"https://www.amazon.in/s?k={query.replace(' ', '%20')}",
            f"https://www.amazon.in/s?field-keywords={query.replace(' ', '+')}",
        ]
        
        products = []
        
        for url in urls_to_try:
            try:
                session = requests.Session()
                # First visit homepage to get cookies
                session.get("https://www.amazon.in", headers=get_headers(), timeout=5)
                time.sleep(0.5)
                
                response = session.get(url, headers=get_headers(), timeout=15)
                
                if response.status_code == 200 and len(response.text) > 10000:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors for product containers
                    items = soup.find_all('div', {'data-component-type': 's-search-result'})
                    
                    if not items:
                        items = soup.find_all('div', {'data-asin': True, 'data-index': True})
                    
                    if not items:
                        items = soup.select('[data-asin]:not([data-asin=""])')[:num_results]
                    
                    for item in items[:num_results]:
                        try:
                            # Product title - try multiple selectors
                            title_elem = item.find('h2') or item.find('span', {'class': 'a-text-normal'})
                            title = title_elem.get_text(strip=True) if title_elem else None
                            
                            if not title or len(title) < 5:
                                continue
                            
                            # Product link
                            link_elem = item.find('a', {'class': 'a-link-normal'}) or (title_elem.find('a') if title_elem else None)
                            link = None
                            if link_elem and link_elem.get('href'):
                                href = link_elem['href']
                                link = f"https://www.amazon.in{href}" if href.startswith('/') else href
                            
                            # Price - try multiple selectors
                            price = "N/A"
                            price_elem = item.find('span', {'class': 'a-price-whole'})
                            if not price_elem:
                                price_elem = item.find('span', {'class': 'a-offscreen'})
                            if price_elem:
                                price_text = price_elem.get_text(strip=True).replace(',', '').replace('₹', '')
                                if price_text and price_text[0].isdigit():
                                    price = price_text.split('.')[0]
                            
                            # Rating
                            rating = "N/A"
                            rating_elem = item.find('span', {'class': 'a-icon-alt'})
                            if rating_elem:
                                rating = rating_elem.get_text(strip=True)
                            
                            # Reviews count
                            reviews = "N/A"
                            reviews_elem = item.find('span', {'class': 'a-size-base', 'dir': 'auto'})
                            if not reviews_elem:
                                reviews_elem = item.find('span', {'class': 'a-size-small'})
                            if reviews_elem:
                                reviews = reviews_elem.get_text(strip=True)
                            
                            # Best seller badge
                            bestseller = bool(item.find('span', string=re.compile('Best', re.I)))
                            
                            products.append({
                                'title': title[:100] + '...' if len(title) > 100 else title,
                                'price': f"₹{price}" if price != "N/A" else price,
                                'rating': rating,
                                'reviews': reviews,
                                'bestseller': bestseller,
                                'link': link,
                                'source': 'Amazon India'
                            })
                            
                        except Exception:
                            continue
                    
                    if products:
                        break
                        
            except Exception:
                continue
        
        return products if products else None
        
    except Exception as e:
        return None


def search_flipkart(query, num_results=6):
    """Search Flipkart for products using product link detection."""
    try:
        url = f"https://www.flipkart.com/search?q={query.replace(' ', '%20')}"
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        seen_titles = set()
        
        # Find all product links (contain /p/ in URL)
        product_links = soup.find_all('a', href=lambda x: x and '/p/' in str(x))
        
        for link_elem in product_links:
            if len(products) >= num_results:
                break
                
            try:
                href = link_elem.get('href', '')
                
                # Get the parent container to find price and other details
                parent = link_elem.find_parent('div')
                if not parent:
                    parent = link_elem
                
                # Try to get title from link text or nearby elements
                title = link_elem.get_text(strip=True)
                
                # If title is too short, look in parent
                if len(title) < 10:
                    # Look for title in parent container
                    for elem in parent.find_all(['div', 'a', 'span']):
                        text = elem.get_text(strip=True)
                        if len(text) > 20 and len(text) < 200 and text not in seen_titles:
                            title = text
                            break
                
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                
                seen_titles.add(title)
                
                # Find price - look for ₹ symbol in nearby elements
                price = "N/A"
                # Go up a few levels to find price
                search_container = parent
                for _ in range(5):
                    if search_container.parent:
                        search_container = search_container.parent
                    price_text = search_container.get_text()
                    price_match = re.search(r'₹\s*([\d,]+)', price_text)
                    if price_match:
                        price = price_match.group(1).replace(',', '')
                        break
                
                # Find rating
                rating = "N/A"
                rating_match = re.search(r'(\d\.?\d?)\s*(?:out of 5|★)', search_container.get_text())
                if rating_match:
                    rating = f"{rating_match.group(1)} out of 5"
                
                link = f"https://www.flipkart.com{href}" if href.startswith('/') else href
                
                products.append({
                    'title': title[:100] + '...' if len(title) > 100 else title,
                    'price': f"₹{price}" if price != "N/A" else price,
                    'rating': rating,
                    'reviews': "N/A",
                    'bestseller': False,
                    'link': link,
                    'source': 'Flipkart'
                })
                    
            except Exception:
                continue
        
        return products if products else None
        
    except Exception:
        return None


def search_bigbasket(query, num_results=6):
    """Search BigBasket for products (good for FMCG/grocery items)."""
    try:
        url = f"https://www.bigbasket.com/ps/?q={query.replace(' ', '%20')}"
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # BigBasket uses specific data attributes
        items = soup.find_all('div', {'data-qa': 'product'})
        
        if not items:
            # Fallback - look for product cards
            items = soup.find_all('div', class_=lambda x: x and 'product' in str(x).lower())
        
        for item in items[:num_results]:
            try:
                title_elem = item.find('a', {'data-qa': 'product-name'}) or item.find('h3') or item.find('a')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                if not title or len(title) < 5:
                    continue
                
                price = "N/A"
                price_elem = item.find('span', {'data-qa': 'product-price'})
                if not price_elem:
                    # Look for price pattern
                    price_match = re.search(r'₹\s*([\d,]+)', item.get_text())
                    if price_match:
                        price = price_match.group(1).replace(',', '')
                else:
                    price = price_elem.get_text(strip=True).replace('₹', '').replace(',', '')
                
                products.append({
                    'title': title[:100] + '...' if len(title) > 100 else title,
                    'price': f"₹{price}" if price != "N/A" else price,
                    'rating': "N/A",
                    'reviews': "N/A",
                    'bestseller': False,
                    'link': None,
                    'source': 'BigBasket'
                })
                
            except Exception:
                continue
        
        return products if products else None
        
    except Exception:
        return None


def search_google_shopping(query, num_results=6):
    """Search Google Shopping for products via scraping."""
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}+price+india&tbm=shop&hl=en&gl=in"
        response = requests.get(url, headers=get_headers(), timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Google Shopping results
        items = soup.find_all('div', {'class': 'sh-dgr__grid-result'})
        
        if not items:
            items = soup.find_all('div', {'class': 'sh-dgr__content'})
        
        for item in items[:num_results]:
            try:
                # Title
                title_elem = item.find('h3') or item.find('h4')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                if not title:
                    continue
                
                # Price
                price = "N/A"
                price_elem = item.find('span', {'class': 'a8Pemb'}) or item.find('span', string=re.compile(r'₹'))
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'[\d,]+', price_text.replace('₹', ''))
                    if price_match:
                        price = price_match.group().replace(',', '')
                
                # Source/Store
                source_elem = item.find('div', {'class': 'aULzUe'})
                source = source_elem.get_text(strip=True) if source_elem else "Google Shopping"
                
                products.append({
                    'title': title[:100] + '...' if len(title) > 100 else title,
                    'price': f"₹{price}" if price != "N/A" else price,
                    'rating': "N/A",
                    'reviews': "N/A",
                    'bestseller': False,
                    'link': None,
                    'source': source
                })
                
            except Exception:
                continue
        
        return products if products else None
        
    except Exception:
        return None


def get_competitor_data_via_llm(product_description, category, api_key, api_provider):
    """Use LLM to provide known competitor information when scraping fails."""
    
    llm_call = call_openai if api_provider == "OpenAI" else call_llm
    
    prompt = f"""
You are a market research expert with deep knowledge of Indian consumer brands.

For this product idea:
Product: {product_description}
Category: {category}

Provide a list of 5-7 REAL, EXISTING competitor products/brands that are currently sold on Amazon India, Flipkart, or BigBasket.

For each competitor, provide:
1. Brand Name
2. Product Name (specific SKU)
3. Approximate MRP (₹) - be realistic
4. Platform (Amazon/Flipkart/BigBasket/D2C)
5. Why they're a competitor

Focus on:
- Direct competitors (same product type)
- Indirect competitors (substitutes)
- Include both big brands (like Haldiram's, ITC, Britannia, Mamaearth, etc.) and D2C brands

Format your response as a structured list. Be specific with real product names and realistic prices.
Only include products that actually exist in the Indian market.
"""
    
    response = llm_call(prompt, api_key)
    return response


def search_all_sources(query, num_results=6):
    """Search multiple sources and combine results."""
    all_products = []
    sources_tried = []
    
    # Try Amazon first
    amazon_results = search_amazon_india(query, num_results)
    sources_tried.append("Amazon India")
    if amazon_results:
        all_products.extend(amazon_results)
    
    # Try Flipkart
    if len(all_products) < num_results:
        flipkart_results = search_flipkart(query, num_results - len(all_products))
        sources_tried.append("Flipkart")
        if flipkart_results:
            all_products.extend(flipkart_results)
    
    # Try BigBasket for FMCG items
    if len(all_products) < num_results:
        bigbasket_results = search_bigbasket(query, num_results - len(all_products))
        sources_tried.append("BigBasket")
        if bigbasket_results:
            all_products.extend(bigbasket_results)
    
    return all_products[:num_results], sources_tried


# ============================================================================
# LLM INTEGRATION (Using Groq - Free API)
# ============================================================================

def call_llm(prompt, api_key):
    """Call Groq LLM API for analysis."""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a sharp business analyst helping founders evaluate product ideas. Be direct, data-driven, and actionable. Avoid fluff."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        return None


def call_openai(prompt, api_key):
    """Call OpenAI API for analysis."""
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a sharp business analyst helping founders evaluate product ideas. Be direct, data-driven, and actionable. Avoid fluff."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        return None

# ============================================================================
# SPECIALIZED AI AGENTS
# ============================================================================

def call_agent(prompt, api_key, api_provider, system_persona):
    """Call an AI agent with a specific persona."""
    try:
        if api_provider == "OpenAI":
            url = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o-mini"
        else:
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.3-70b-versatile"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_persona},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2500
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=90)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        return None


# Agent Personas - Enhanced with Frameworks & Case Studies
AGENT_PERSONAS = {
    'marketing': {
        'name': 'Maya',
        'role': 'CMO',
        'emoji': '🎯',
        'persona': """You are Maya, a sharp CMO with 15+ years building D2C brands in India.

YOUR BACKGROUND:
- Led marketing at Mamaearth (₹0 to ₹1000 Cr), Boat (category creator), Sugar Cosmetics (digital-first beauty)
- Studied failures too: why Wow Skin Science struggled, why some D2C brands burn cash on CAC

FRAMEWORKS YOU USE:
- STP (Segmentation, Targeting, Positioning) - but for Indian consumers specifically
- AIDA funnel - Awareness → Interest → Desire → Action
- CAC/LTV ratio - healthy is 1:3 minimum, you've seen brands die at 1:1.5
- The "Hero SKU" strategy - launch with 1-2 products, not 10
- Influencer ROI matrix - micro (10K-100K) vs macro vs celebrity

INDIAN MARKET INSIGHTS:
- Trust markers matter: "As seen on Shark Tank", celebrity endorsements work
- Regional language content = 3x engagement in Tier 2/3
- Instagram Reels > YouTube for discovery, but YouTube for consideration
- Festival seasons (Diwali, Holi) = 3-5x sales but also 3x CAC

Be specific with numbers and real examples. Give 3-4 sentence responses that are actionable."""
    },
    'strategy': {
        'name': 'Arjun', 
        'role': 'Strategy Consultant',
        'emoji': '♟️',
        'persona': """You are Arjun, ex-McKinsey Partner who now advises D2C founders in India.

YOUR BACKGROUND:
- 12 years at McKinsey, led Consumer & Retail practice for South Asia
- Advised Tata Consumer, ITC Foods, and 20+ D2C brands on market entry
- Seen both ₹100 Cr exits and spectacular failures

FRAMEWORKS YOU APPLY:
- Porter's Five Forces - but adapted for Indian e-commerce (platform power is HUGE)
- BCG Growth-Share Matrix - which products to invest vs milk vs divest
- Blue Ocean vs Red Ocean - finding whitespace in crowded categories
- Moat Analysis: Brand, Cost, Network, Switching Costs, Distribution
- The "Insurgent vs Incumbent" framework - how startups beat giants

COMPETITIVE INTELLIGENCE:
- Big brands (HUL, ITC, Nestle) are slow but have distribution moats
- D2C brands win on: speed, niche focus, community, digital-native DNA
- Private labels (Amazon Basics, Flipkart SmartBuy) are the silent killers
- Category matters: personal care = crowded, pet food = whitespace

RED FLAGS YOU'VE SEEN KILL STARTUPS:
- "We have no competitors" = founder hasn't researched
- Competing on price alone = race to bottom
- No clear differentiation beyond packaging

Be direct, use frameworks, cite specific examples. Give 3-4 sentence responses."""
    },
    'gtm': {
        'name': 'Vikram',
        'role': 'GTM/Sales Head', 
        'emoji': '🚀',
        'persona': """You are Vikram, Head of Sales who's launched 50+ products across Indian e-commerce.

YOUR BACKGROUND:
- Ex-Amazon India (Category Manager, launched 100+ brands)
- Built GTM for Yogabar, Slurrp Farm, and The Whole Truth
- Know the platform game inside-out: listing tricks, A+ content, ads strategy

PLAYBOOKS YOU'VE PROVEN:
1. "Amazon First" strategy - build reviews, ranking, then expand
2. "Quick Commerce Hack" - Zepto/Blinkit for impulse, higher margins on D2C
3. "The 100 Reviews Rule" - product needs 100+ reviews before scaling ads
4. "Price Ladder" - launch 10% below MRP, slowly increase as reviews build
5. "Lightning Deal Loop" - use deals to boost BSR, then organic takes over

PLATFORM-SPECIFIC KNOWLEDGE:
- Amazon: A+ content = 15% conversion lift, Vine reviews = early momentum
- Flipkart: Big Billion Days = plan 3 months ahead, SuperCoins audience = value seekers
- Quick Commerce: 500 dark stores = ₹50L/month potential, but margins tight
- D2C: Shopify + Shiprocket, CAC is ₹300-800 for most categories

LAUNCH MISTAKES YOU'VE SEEN:
- Launching on 5 platforms = focus dilution, launch on 1, win, expand
- Ignoring Amazon SEO = your listing is invisible
- No inventory buffer = stockouts kill ranking permanently

Give specific, tactical advice. 3-4 sentences with exact actions and timelines."""
    },
    'finance': {
        'name': 'Priya',
        'role': 'CFO',
        'emoji': '💰',
        'persona': """You are Priya, CFO who's built finance functions at 3 D2C unicorns.

YOUR BACKGROUND:
- Finance lead at Licious (meat delivery), Nykaa (beauty), and a failed D2C brand (learned the hard way)
- Raised ₹500 Cr+ across Seed to Series C rounds
- Seen what metrics VCs actually care about vs what founders think they care

FINANCIAL FRAMEWORKS:
- Unit Economics Waterfall: MRP → Platform fees → Logistics → Returns → COGS → Margin
- CAC Payback Period: healthy < 6 months, dangerous > 12 months
- LTV:CAC ratio: 3:1 minimum for VC-backed, 2:1 for bootstrapped
- Break-even analysis: Fixed costs / Contribution margin = units needed
- Burn Multiple: Net burn / Net new ARR (< 2 is good, > 3 is trouble)

FUNDING STAGE KNOWLEDGE:
- Bootstrapped: Need 30%+ margins, ₹10-20L runway
- Pre-Seed (₹50L-2Cr): Prove product-market fit, 100+ organic customers
- Seed (₹2-10Cr): ₹50L+ monthly revenue, clear path to ₹5Cr ARR
- Series A: ₹5Cr+ ARR, 20%+ month-on-month growth, unit economics positive

RED FLAGS IN D2C FINANCIALS:
- Platform fees > 30% of MRP = margin compression
- Returns > 10% = product or listing problem
- CAC increasing quarter over quarter = saturation signal
- Gross margin < 50% = no room for marketing

Be numbers-driven, cite benchmarks. 3-4 sentences with specific financial guidance."""
    },
    'moderator': {
        'name': 'Board Moderator',
        'role': 'CEO',
        'emoji': '👔',
        'persona': """You are the CEO moderating a board discussion. Your job is to:
1. Synthesize different viewpoints into a clear narrative
2. Identify where agents agree (consensus) and disagree (risks)
3. Push for actionable, specific conclusions
4. Drive toward a clear GO/NO-GO/PILOT recommendation with confidence level

You've seen hundreds of pitches. You know the difference between optimism and delusion.
Be decisive. Founders need clarity, not more questions."""
    }
}

MARKETING_AGENT_PERSONA = AGENT_PERSONAS['marketing']['persona']

STRATEGY_AGENT_PERSONA = """
You are a razor-sharp strategy consultant from McKinsey/BCG with deep expertise in Indian consumer markets.
You think in frameworks but communicate in plain language.
Your expertise:
- Competitive moats and differentiation
- Market entry strategies and timing
- SWOT analysis with actionable insights
- Porter's Five Forces applied practically
- Blue ocean vs red ocean thinking

You're brutally honest about competitive dynamics. You tell founders what they need to hear, not what they want to hear.
Focus on sustainable competitive advantage, not just features.
"""

GTM_AGENT_PERSONA = """
You are a battle-tested GTM (Go-To-Market) specialist who has launched 50+ products in India.
You've worked across Amazon, Flipkart, Zepto, Blinkit, and D2C channels.
Your expertise:
- Launch sequencing (which channel first, why)
- Listing optimization and A+ content
- Pricing ladder strategy (launch vs long-term)
- Distribution partnerships and retail expansion
- First 90 days playbook

You think in terms of velocity, visibility, and velocity. You know the Indian e-commerce ecosystem inside-out.
Give specific, week-by-week actionable plans, not vague strategies.
"""

FINANCE_AGENT_PERSONA = """
You are a pragmatic CFO who has built and scaled multiple D2C brands from ₹0 to ₹100 Cr revenue.
You've seen what kills promising products: poor unit economics.
Your expertise:
- Unit economics deep-dive (not just margins - CAC, LTV, payback period)
- Pricing strategy and elasticity
- Break-even analysis and runway planning
- Funding requirements and investor expectations
- Financial red flags and kill criteria

You're the voice of financial discipline. You help founders avoid the trap of "growth at all costs."
Every recommendation must tie back to numbers and sustainability.
"""


# ============================================================================
# MULTI-AGENT BOARD MEETING SYSTEM
# ============================================================================

def run_agent_quick_analysis(agent_type, product_context, api_key, api_provider):
    """Run a single agent's analysis with framework-driven insights."""
    persona = AGENT_PERSONAS[agent_type]
    
    prompts = {
        'marketing': f"""
Analyze this product opportunity (200 words MAX):

Product: {product_context['description']}
Category: {product_context['category']} | MRP: ₹{product_context['mrp']}
Competitors: {product_context.get('competitors_summary', 'Not available')}

Using your marketing frameworks, provide:

1. **Target Customer** - Who exactly? (age, city tier, psychographic - not just demographics)
2. **Positioning** - Where does this sit? Premium/mid/value? What's the ONE thing to own?
3. **Acquisition Strategy** - Top 2 channels and WHY (cite CAC benchmarks if relevant)
4. **Content Angle** - What messaging will resonate? What proof points?
5. **Risk Flag** - What could make CAC unsustainable? (be specific)
6. **Verdict** - GO/PILOT/NO-GO with 1 clear reason

Reference real Indian D2C examples where relevant.
""",
        'strategy': f"""
Analyze this product opportunity (200 words MAX):

Product: {product_context['description']}
Category: {product_context['category']} | MRP: ₹{product_context['mrp']}
Competitors: {product_context.get('competitors_summary', 'Not available')}

Using your strategy frameworks, provide:

1. **Moat Assessment** - What's the defensibility? (Brand/Cost/Network/Switching/Distribution)
2. **Competitive Position** - Blue ocean or red ocean? Who are the real threats?
3. **Differentiation** - What's the ONE thing that makes this different? Is it sustainable?
4. **Market Timing** - Is this the right moment? Why/why not?
5. **Risk Flag** - What competitive dynamic could kill this? (incumbents, private labels, etc.)
6. **Verdict** - GO/PILOT/NO-GO with 1 clear reason

Apply Porter's Five Forces or BCG thinking where relevant.
""",
        'gtm': f"""
Analyze this product opportunity (200 words MAX):

Product: {product_context['description']}
Category: {product_context['category']} | MRP: ₹{product_context['mrp']}
Primary Channel: {product_context['channel']}

Using your launch playbooks, provide:

1. **Channel Sequence** - Where to launch FIRST and WHY? (Amazon vs Flipkart vs D2C vs Quick Commerce)
2. **Week 1-4 Priorities** - What are the 3 most critical actions?
3. **The 100 Reviews Problem** - How to get initial traction? (Vine, deals, influencers?)
4. **Pricing Ladder** - Launch price vs MRP? Discount strategy?
5. **Risk Flag** - What GTM mistake would kill momentum? (stockouts, wrong platform, etc.)
6. **Verdict** - GO/PILOT/NO-GO with 1 clear reason

Reference specific platform tactics (Amazon A+, Flipkart BBD, etc.)
""",
        'finance': f"""
Analyze this product opportunity (200 words MAX):

Product: {product_context['description']}
Category: {product_context['category']} | MRP: ₹{product_context['mrp']}
Unit Economics: Margin {product_context['margin_pct']:.1f}%, Cost ₹{product_context['total_cost']:.0f}

Using your financial frameworks, provide:

1. **Unit Economics Health** - Healthy (>20%) / Tight (10-20%) / Broken (<10%)? Why?
2. **Break-even Reality** - At this margin, how many units/month to cover ₹2L fixed costs?
3. **Funding Path** - Can this bootstrap or needs funding? At what stage?
4. **CAC/LTV Math** - With typical category CAC (₹200-500), does LTV math work?
5. **Risk Flag** - What financial trap could kill this? (margin compression, CAC inflation, etc.)
6. **Verdict** - GO/PILOT/NO-GO with 1 clear reason

Cite D2C benchmarks (Nykaa margins, typical platform take rates, etc.)
"""
    }
    
    return call_agent(prompts[agent_type], api_key, api_provider, persona['persona'])


def run_board_discussion(agent_outputs, product_context, api_key, api_provider):
    """Run a moderated discussion between agents (2 rounds with richer dialogue)."""
    discussion = []
    
    # Round 1: Each agent responds to others' analyses with substance
    round1_prompt = f"""
You're in a board meeting discussing a new product launch. Your colleagues shared their analyses:

🎯 MAYA (CMO): {agent_outputs.get('marketing', 'No input')[:400]}

♟️ ARJUN (Strategy): {agent_outputs.get('strategy', 'No input')[:400]}

🚀 VIKRAM (GTM): {agent_outputs.get('gtm', 'No input')[:400]}

💰 PRIYA (CFO): {agent_outputs.get('finance', 'No input')[:400]}

Now respond in 3-4 sentences:
1. Name ONE colleague you're responding to and whether you AGREE or DISAGREE
2. Explain WHY with a specific reason, data point, or framework
3. Add ONE insight from your expertise that others might have missed
4. If you see a risk no one mentioned, flag it

Be direct and specific. Reference real examples or benchmarks if relevant.
"""
    
    for agent_type in ['marketing', 'strategy', 'gtm', 'finance']:
        response = call_agent(round1_prompt, api_key, api_provider, AGENT_PERSONAS[agent_type]['persona'])
        if response:
            discussion.append({
                'round': 1,
                'agent': agent_type,
                'name': AGENT_PERSONAS[agent_type]['name'],
                'emoji': AGENT_PERSONAS[agent_type]['emoji'],
                'message': response[:400]  # Allow longer responses
            })
    
    # Round 2: Final positions with conditions
    round2_summary = "\\n".join([f"{d['emoji']} {d['name']}: {d['message']}" for d in discussion])
    
    final_prompt = f"""
The board has debated. Here's what was said:

{round2_summary}

Now give your FINAL POSITION in 2-3 sentences:
1. Your vote: GO / PILOT / NO-GO
2. ONE specific condition that MUST be met for your vote to hold
3. ONE metric you'd track in the first 30 days to validate

Be decisive. The founder needs clarity.
"""
    
    for agent_type in ['marketing', 'strategy', 'gtm', 'finance']:
        response = call_agent(final_prompt, api_key, api_provider, AGENT_PERSONAS[agent_type]['persona'])
        if response:
            discussion.append({
                'round': 2,
                'agent': agent_type,
                'name': AGENT_PERSONAS[agent_type]['name'],
                'emoji': AGENT_PERSONAS[agent_type]['emoji'],
                'message': response[:300]  # Slightly longer final positions
            })
    
    return discussion


def generate_board_verdict(agent_outputs, discussion, product_context, api_key, api_provider):
    """Moderator synthesizes everything into final verdict."""
    
    discussion_text = "\\n".join([f"R{d['round']} {d['emoji']}: {d['message']}" for d in discussion])
    
    prompt = f"""
You are the CEO synthesizing board discussion.

PRODUCT: {product_context['description']}
MRP: ₹{product_context['mrp']} | Margin: {product_context['margin_pct']:.1f}%

INITIAL ANALYSES:
🎯 Marketing: {agent_outputs.get('marketing', 'N/A')[:400]}
♟️ Strategy: {agent_outputs.get('strategy', 'N/A')[:400]}
🚀 GTM: {agent_outputs.get('gtm', 'N/A')[:400]}
💰 Finance: {agent_outputs.get('finance', 'N/A')[:400]}

DISCUSSION:
{discussion_text}

Provide FINAL BOARD VERDICT:

## 🎯 VERDICT: [GO / PILOT / NO-GO]
**Confidence:** [High/Medium/Low] | **Votes:** [X GO, Y PILOT, Z NO-GO]

## 📋 Executive Summary
(3 sentences: what is this, why this verdict, what's next)

## ✅ Board Consensus
(3 points all agents agreed on)

## ⚠️ Key Debates & Risks
(2-3 points of disagreement or concern)

## 🎬 Immediate Next Steps
1. [This week - most critical]
2. [Next 2 weeks]
3. [Month 1]

## 💀 Kill Criteria
(2 specific conditions to pivot/stop)
"""
    
    return call_agent(prompt, api_key, api_provider, AGENT_PERSONAS['moderator']['persona'])


def chat_with_agent(agent_type, user_message, product_context, agent_analysis, chat_history, api_key, api_provider):
    """Have a conversation with a specific agent."""
    persona = AGENT_PERSONAS[agent_type]
    
    history_text = ""
    for msg in chat_history[-5:]:
        history_text += f"User: {msg['user']}\\n{persona['name']}: {msg['agent']}\\n\\n"
    
    prompt = f"""
You are {persona['name']} ({persona['role']}). You analyzed this product:

PRODUCT: {product_context.get('description', 'N/A')}
YOUR ANALYSIS: {agent_analysis[:600] if agent_analysis else 'Not available'}

PREVIOUS CHAT:
{history_text}

USER ASKS: {user_message}

Respond helpfully. Stay in character. Under 150 words unless detail requested.
"""
    
    return call_agent(prompt, api_key, api_provider, persona['persona'])


def run_marketing_agent(product_description, category, target_mrp, competitors_found, api_key, api_provider):
    """Marketing Agent - Brand positioning, messaging, customer acquisition."""
    
    competitor_context = ""
    if competitors_found:
        competitor_context = "\n\nCompetitors in market:\n" + "\n".join([
            f"- {c['title']} @ {c['price']}" for c in competitors_found[:5]
        ])
    
    prompt = f"""
Analyze this product from a CMO's perspective:

PRODUCT: {product_description}
CATEGORY: {category}
TARGET MRP: ₹{target_mrp}
{competitor_context}

Provide your marketing assessment:

## 🎯 Brand Positioning
- Where should this brand sit in the market? (Premium/Mid/Value)
- What's the ONE thing this brand should own in consumers' minds?
- Suggested brand personality and tone

## 👥 Target Customer Deep-Dive
- Primary audience (be specific - age, income, city tier, lifestyle)
- Secondary audience (expansion opportunity)
- Customer pain points this solves
- Purchase triggers and occasions

## 📱 Channel Strategy (Rank by priority)
For each channel, give: Budget %, Expected CAC, Why
1. Instagram/Facebook Ads
2. Google/YouTube Ads  
3. Influencer Marketing
4. Content Marketing
5. Offline/BTL

## ✍️ Messaging & Content
- Hero message (one line that sells)
- 3 proof points to communicate
- Content pillars for social media
- UGC strategy

## 🎪 Launch Campaign Idea
- One big creative idea for launch
- Estimated budget needed
- Expected reach/impact

## ⚠️ Marketing Red Flags
- What could make customer acquisition too expensive?
- Category-specific marketing challenges

Be specific to Indian consumers and this exact product.
"""
    
    return call_agent(prompt, api_key, api_provider, MARKETING_AGENT_PERSONA)


def run_strategy_agent(product_description, category, target_mrp, competitors_found, api_key, api_provider):
    """Strategy Agent - Competitive positioning, differentiation, market dynamics."""
    
    competitor_context = ""
    if competitors_found:
        competitor_context = "\n\nCompetitors found:\n" + "\n".join([
            f"- {c['title']} @ {c['price']} (Rating: {c['rating']})" for c in competitors_found[:6]
        ])
    
    prompt = f"""
Analyze this product from a strategy consultant's perspective:

PRODUCT: {product_description}
CATEGORY: {category}  
TARGET MRP: ₹{target_mrp}
{competitor_context}

Provide your strategic assessment:

## 🏰 Competitive Landscape
- Market structure (fragmented vs consolidated?)
- Who are the 800-lb gorillas? (Big brands to watch)
- Where are the gaps/whitespace?

## ⚔️ Competitive Moat Analysis
For this product, rate each potential moat (Strong/Weak/None):
1. **Brand**: Can they build a loved brand?
2. **Distribution**: Can they lock in shelf space?
3. **Cost**: Can they be the low-cost producer?
4. **Network Effects**: Any virality potential?
5. **Switching Costs**: Will customers stick?

## 🔍 SWOT Analysis

| Strengths | Weaknesses |
|-----------|------------|
| (list 3-4) | (list 3-4) |

| Opportunities | Threats |
|---------------|----------|
| (list 3-4) | (list 3-4) |

## 🎯 Strategic Positioning Options
Present 2-3 different positioning strategies:
1. **Option A**: [Name] - Description, Pros, Cons
2. **Option B**: [Name] - Description, Pros, Cons
3. **Recommended**: Which option and why

## 🚧 Barriers to Entry
- What's stopping others from copying this?
- What's stopping big players from crushing this?
- Defensibility timeline (how long until moat is built?)

## 💀 Strategy Kill Criteria
- What strategic signals should make founder pivot/stop?
- Non-negotiable requirements for success

Be brutally honest. This is for decision-making, not motivation.
"""
    
    return call_agent(prompt, api_key, api_provider, STRATEGY_AGENT_PERSONA)


def run_gtm_agent(product_description, category, target_mrp, launch_channel, api_key, api_provider):
    """GTM Agent - Go-to-market execution, launch playbook."""
    
    prompt = f"""
Create a go-to-market plan for this product:

PRODUCT: {product_description}
CATEGORY: {category}
TARGET MRP: ₹{target_mrp}
PRIMARY CHANNEL: {launch_channel}

Provide your GTM playbook:

## 🚀 Launch Sequence (Channel Prioritization)
Rank these channels for launch (1=first, with reasoning):

| Rank | Channel | Why this order | Timeline |
|------|---------|----------------|----------|
| 1 | ? | ? | Week ? |
| 2 | ? | ? | Week ? |
| 3 | ? | ? | Week ? |

Channels: Amazon, Flipkart, Zepto, Blinkit, Instamart, D2C Website, Retail

## 📋 Pre-Launch Checklist (Week -4 to -1)
- [ ] Task 1
- [ ] Task 2
- [ ] (list 8-10 critical tasks)

## 📅 90-Day Launch Calendar

### Week 1-2: Launch
- Day-by-day activities
- Key metrics to track
- Budget allocation

### Week 3-4: Optimize
- What to measure
- How to iterate
- Common problems and fixes

### Month 2: Scale
- Expansion triggers (when to add channels)
- Inventory planning
- Marketing scale-up

### Month 3: Sustain
- Repeat purchase activation
- Review/rating acceleration
- Operational efficiency

## 📦 Platform-Specific Playbook

### Amazon India
- Listing optimization tips
- A+ Content must-haves
- Advertising strategy (Sponsored Products/Brands)
- Prime badge timeline

### Quick Commerce (Zepto/Blinkit)
- Onboarding requirements
- Dark store strategy
- Pricing considerations

## 💰 Launch Pricing Strategy
- Launch price vs MRP
- Discount ladder (Week 1, Month 1, Month 3)
- Bundle/combo strategy
- When to stop discounting

## 🎯 Key Milestones & KPIs
| Milestone | Target | Timeline | Why it matters |
|-----------|--------|----------|----------------|
| Reviews | ? | Week ? | ? |
| Ranking | ? | Month ? | ? |
| Revenue | ? | Month ? | ? |

## ⚠️ GTM Risks & Mitigations
- Top 3 things that could derail launch
- Contingency plans for each

Be specific and actionable. Founders should be able to execute this plan tomorrow.
"""
    
    return call_agent(prompt, api_key, api_provider, GTM_AGENT_PERSONA)


def run_finance_agent(product_description, category, target_mrp, sku_weight, launch_channel, economics_data, api_key, api_provider):
    """Finance Agent - Unit economics, financial projections, funding."""
    
    prompt = f"""
Provide financial analysis for this product:

PRODUCT: {product_description}
CATEGORY: {category}
TARGET MRP: ₹{target_mrp}
SKU WEIGHT: {sku_weight}g
PRIMARY CHANNEL: {launch_channel}

CURRENT UNIT ECONOMICS:
- Manufacturing: ₹{economics_data['manufacturing_cost']:.2f}
- Packaging: ₹{economics_data['packaging_cost']:.2f}
- Platform Fees: ₹{economics_data['platform_fees']:.2f}
- Logistics: ₹{economics_data['logistics_cost']:.2f}
- Returns: ₹{economics_data['returns_cost']:.2f}
- GST: ₹{economics_data['gst']:.2f}
- Total Cost: ₹{economics_data['total_cost']:.2f}
- Net Margin: ₹{economics_data['net_margin']:.2f} ({economics_data['margin_percentage']:.1f}%)

Provide your CFO assessment:

## 💰 Unit Economics Health Check

| Metric | Current | Healthy Benchmark | Verdict |
|--------|---------|-------------------|----------|
| Gross Margin | ?% | ?% | 🟢/🟡/🔴 |
| Contribution Margin | ?% | ?% | 🟢/🟡/🔴 |
| Platform Fee Load | ?% | ?% | 🟢/🟡/🔴 |

## 📊 Financial Projections (Conservative)

### Year 1 Scenario Analysis
| Scenario | Monthly Units | Revenue | Profit | Break-even |
|----------|---------------|---------|--------|------------|
| Bear | ? | ₹? | ₹? | Month ? |
| Base | ? | ₹? | ₹? | Month ? |
| Bull | ? | ₹? | ₹? | Month ? |

## 🎯 CAC & LTV Analysis
- Estimated CAC for this category: ₹?
- Required LTV for healthy business: ₹?
- Break-even orders per customer: ?
- Payback period: ? months

## 💸 Funding Requirements

### Bootstrap Path (No external funding)
- Minimum capital needed: ₹?
- Monthly burn rate: ₹?
- Runway needed: ? months
- Feasibility: High/Medium/Low

### Growth Path (With funding)
- Seed round size: ₹?
- Use of funds breakdown
- Metrics needed for Series A

## 🔧 Margin Improvement Levers
Rank by impact (High/Medium/Low):

| Lever | Current → Target | Impact | Difficulty |
|-------|------------------|--------|------------|
| Reduce manufacturing cost | ? | ? | ? |
| Increase MRP | ? | ? | ? |
| Negotiate platform fees | ? | ? | ? |
| Reduce returns | ? | ? | ? |
| Scale discounts | ? | ? | ? |

## 💀 Financial Kill Criteria
- At what margin should founder stop/pivot?
- Red flag metrics to watch monthly
- When to raise alarm with investors

## 📈 Path to Profitability
- Month-by-month margin improvement roadmap
- Key assumptions that must hold true
- Biggest financial risk

## 💡 CFO's Verdict
- Overall financial viability: GO / PILOT / NO-GO
- Confidence level: High/Medium/Low
- Top 3 financial concerns
- #1 thing to fix before launch

Be conservative with projections. Founders often overestimate revenue and underestimate costs.
"""
    
    return call_agent(prompt, api_key, api_provider, FINANCE_AGENT_PERSONA)


def run_board_summary(product_description, marketing_output, strategy_output, gtm_output, finance_output, api_key, api_provider):
    """Generate a unified board summary from all agents."""
    
    prompt = f"""
You are the CEO synthesizing inputs from your leadership team on a new product launch decision.

PRODUCT: {product_description}

---
MARKETING (CMO) SAYS:
{marketing_output[:1500] if marketing_output else 'Not available'}

---
STRATEGY (Consultant) SAYS:
{strategy_output[:1500] if strategy_output else 'Not available'}

---
GTM (Head of Sales) SAYS:
{gtm_output[:1500] if gtm_output else 'Not available'}

---  
FINANCE (CFO) SAYS:
{finance_output[:1500] if finance_output else 'Not available'}

---

Synthesize into a FINAL BOARD DECISION:

## 🎯 THE VERDICT: [GO / PILOT / NO-GO]

Confidence: [High/Medium/Low]

## 📋 Executive Summary (5 sentences max)
[What is this product, why does it work/not work, what's the path forward]

## ✅ Where All Agents Agree
- Point 1
- Point 2
- Point 3

## ⚠️ Where Agents Disagree (Risks)
- Point 1
- Point 2

## 🎬 Recommended Next Steps (Priority Order)
1. [Most critical action]
2. [Second priority]
3. [Third priority]
4. [Fourth priority]
5. [Fifth priority]

## 📊 Key Metrics to Track
| Metric | Target | Timeline | Owner |
|--------|--------|----------|-------|
| ? | ? | ? | Marketing/GTM/Finance |

## 💀 Kill Criteria
Stop/pivot if:
1. [Condition 1]
2. [Condition 2]
3. [Condition 3]

Make this actionable. The founder should know exactly what to do after reading this.
"""
    
    return call_agent(prompt, api_key, api_provider, "You are a decisive CEO who synthesizes diverse opinions into clear action. Be direct and specific.")


# ============================================================================
# RESEARCH AGENT (Main Orchestrator) - WITH BOARD MEETING
# ============================================================================

def run_market_research_agent(product_description, category, target_mrp, api_key, api_provider, 
                               do_competitor_analysis, do_marketing_analysis, do_market_sizing,
                               progress_callback=None, sku_weight=200, launch_channel="E-commerce",
                               do_strategy_analysis=True, do_gtm_analysis=True, do_finance_analysis=True):
    """Run the AI research agent with internal board meeting."""
    
    results = {
        'product_analysis': None,
        'competitors': None,
        'competitor_analysis': None,
        'market_size': None,
        # Board meeting outputs (internal - not shown directly)
        'agent_outputs': {},
        'board_discussion': [],
        'board_verdict': None,
        # Legacy fields
        'recommendations': None
    }
    
    llm_call = call_openai if api_provider == "OpenAI" else call_llm
    
    # Calculate unit economics early (needed for agents) - now with dynamic pricing
    economics_data = calculate_unit_economics(
        category, sku_weight, target_mrp, launch_channel,
        product_description, api_key, api_provider
    )
    
    # Build product context for agents
    product_context = {
        'description': product_description,
        'category': category,
        'mrp': target_mrp,
        'channel': launch_channel,
        'weight': sku_weight,
        'margin_pct': economics_data['margin_percentage'],
        'total_cost': economics_data['total_cost'],
        'net_margin': economics_data['net_margin'],
        'manufacturing_cost': economics_data.get('manufacturing_cost', 0),
        'platform_fees': economics_data.get('platform_fees', 0),
        'logistics_cost': economics_data.get('logistics_cost', 0),
        'contribution_margin': economics_data.get('contribution_margin', 0),
        'competitors_summary': 'Analyzing...'
    }
    
    # Step 1: Analyze the product description
    if progress_callback:
        progress_callback(5, "📋 Analyzing product description...")
    
    product_prompt = f"""
Analyze this product idea for the Indian market in a CONCISE way:

Product: {product_description}
Category: {category}
Target MRP: ₹{target_mrp}

Provide (keep each point to 2 sentences max):
1. **Product Summary** - What is this?
2. **Target Customer** - Who buys this?
3. **Value Proposition** - Why would they pay ₹{target_mrp}?
4. **Initial Viability** - High/Medium/Low with one reason
"""
    
    results['product_analysis'] = llm_call(product_prompt, api_key)
    
    # Step 2: Search for competitors
    if do_competitor_analysis:
        if progress_callback:
            progress_callback(10, "🔍 Searching for competitors...")
        
        search_query_prompt = f"""
Generate 3 search queries to find competing products on Amazon/Flipkart for:
Product: {product_description}
Category: {category}

Return ONLY 3 queries, one per line. No numbering or quotes.
"""
        search_queries_response = llm_call(search_query_prompt, api_key)
        
        all_competitors = []
        sources_used = []
        
        if search_queries_response:
            queries = [q.strip() for q in search_queries_response.strip().split('\n') if q.strip()][:3]
            
            for i, query in enumerate(queries):
                query = query.replace('"', '').replace("'", "").strip()[:50]
                if not query:
                    continue
                
                if progress_callback:
                    progress_callback(15 + i*5, f"🔎 Searching: '{query}'...")
                
                products, sources = search_all_sources(query, num_results=4)
                
                if products:
                    for p in products:
                        if not any(existing['title'] == p['title'] for existing in all_competitors):
                            all_competitors.append(p)
                    sources_used.extend([s for s in sources if s not in sources_used])
                
                time.sleep(0.3)
        
        results['sources_searched'] = sources_used
        
        if all_competitors:
            results['competitors'] = all_competitors[:8]
            # Build competitor summary for agents
            product_context['competitors_summary'] = ", ".join([
                f"{c['title'][:40]} @ {c['price']}" for c in all_competitors[:5]
            ])
    
    # Step 3: Market Sizing (if enabled)
    if do_market_sizing:
        if progress_callback:
            progress_callback(30, "📊 Estimating market size...")
        
        market_prompt = f"""
Estimate market opportunity for this product in India (be CONCISE):

Product: {product_description}
Category: {category}
MRP: ₹{target_mrp}

Provide:
1. **TAM** - Overall category size (₹ Cr), growth rate
2. **SAM** - Online segment size, target demographic
3. **SOM** - Realistic Year 1 target (₹ and units/month)
4. **Timing** - Is 2025 good timing? One reason.
"""
        results['market_size'] = llm_call(market_prompt, api_key)
    
    # ================================================================
    # BOARD MEETING: Agents analyze and discuss internally
    # ================================================================
    
    if progress_callback:
        progress_callback(40, "🤖 Board Meeting: Agents analyzing...")
    
    # Store context for later chat
    st.session_state.product_context = product_context
    
    agent_outputs = {}
    
    # Run all 4 agents' quick analyses
    if do_marketing_analysis:
        if progress_callback:
            progress_callback(45, "🎯 Maya (Marketing) analyzing...")
        agent_outputs['marketing'] = run_agent_quick_analysis('marketing', product_context, api_key, api_provider)
    
    if do_strategy_analysis:
        if progress_callback:
            progress_callback(55, "♟️ Arjun (Strategy) analyzing...")
        agent_outputs['strategy'] = run_agent_quick_analysis('strategy', product_context, api_key, api_provider)
    
    if do_gtm_analysis:
        if progress_callback:
            progress_callback(65, "🚀 Vikram (GTM) analyzing...")
        agent_outputs['gtm'] = run_agent_quick_analysis('gtm', product_context, api_key, api_provider)
    
    if do_finance_analysis:
        if progress_callback:
            progress_callback(75, "💰 Priya (Finance) analyzing...")
        agent_outputs['finance'] = run_agent_quick_analysis('finance', product_context, api_key, api_provider)
    
    results['agent_outputs'] = agent_outputs
    st.session_state.agent_outputs = agent_outputs  # Store for chat
    
    # Run board discussion (agents debate)
    if len(agent_outputs) >= 2:
        if progress_callback:
            progress_callback(85, "🗣️ Board Meeting: Agents discussing...")
        
        discussion = run_board_discussion(agent_outputs, product_context, api_key, api_provider)
        results['board_discussion'] = discussion
        st.session_state.board_discussion = discussion
    
    # Generate final verdict
    if progress_callback:
        progress_callback(95, "👔 CEO synthesizing final verdict...")
    
    results['board_verdict'] = generate_board_verdict(
        agent_outputs, 
        results.get('board_discussion', []),
        product_context, 
        api_key, 
        api_provider
    )
    
    if progress_callback:
        progress_callback(100, "✅ Board Meeting complete!")
    
    return results

# ============================================================================
# UNIT ECONOMICS CALCULATIONS
# ============================================================================

def get_platform_fees(mrp, weight, category, platform="amazon", shipping_zone="national"):
    """Calculate detailed platform fees based on actual marketplace fee structures."""
    
    platform_category = CATEGORY_TO_PLATFORM_CATEGORY.get(category, {}).get(platform, "Other")
    
    if platform == "amazon":
        # Referral fee
        referral_rate = AMAZON_FEES["referral_fees"].get(platform_category, 0.15)
        referral_fee = mrp * referral_rate
        
        # Closing fee based on price
        if mrp <= 300:
            closing_fee = AMAZON_FEES["closing_fees"]["0-300"]
        elif mrp <= 500:
            closing_fee = AMAZON_FEES["closing_fees"]["301-500"]
        elif mrp <= 1000:
            closing_fee = AMAZON_FEES["closing_fees"]["501-1000"]
        else:
            closing_fee = AMAZON_FEES["closing_fees"]["1000+"]
        
        # Weight handling fee
        weight_brackets = AMAZON_FEES["weight_handling"][shipping_zone]
        if weight <= 500:
            weight_fee = weight_brackets["0-500"]
        elif weight <= 1000:
            weight_fee = weight_brackets["500-1000"]
        elif weight <= 2000:
            weight_fee = weight_brackets["1000-2000"]
        else:
            weight_fee = weight_brackets["2000+"]
        
        # GST on fees
        total_fees = referral_fee + closing_fee + weight_fee
        gst_on_fees = total_fees * AMAZON_FEES["gst_on_fees"]
        
        return {
            "referral_fee": referral_fee,
            "closing_fee": closing_fee,
            "weight_handling_fee": weight_fee,
            "gst_on_fees": gst_on_fees,
            "total_platform_fee": total_fees + gst_on_fees,
            "platform": "Amazon",
            "fee_breakdown": f"Referral: ₹{referral_fee:.1f} ({referral_rate*100:.0f}%) + Closing: ₹{closing_fee} + Shipping: ₹{weight_fee}"
        }
    
    elif platform == "flipkart":
        # Commission
        commission_rate = FLIPKART_FEES["commission_rates"].get(platform_category, 0.12)
        commission = mrp * commission_rate
        
        # Fixed fee
        if mrp <= 300:
            fixed_fee = FLIPKART_FEES["fixed_fees"]["0-300"]
        elif mrp <= 500:
            fixed_fee = FLIPKART_FEES["fixed_fees"]["301-500"]
        elif mrp <= 1000:
            fixed_fee = FLIPKART_FEES["fixed_fees"]["501-1000"]
        else:
            fixed_fee = FLIPKART_FEES["fixed_fees"]["1000+"]
        
        # Shipping fee
        shipping_brackets = FLIPKART_FEES["shipping_fees"][shipping_zone]
        if weight <= 500:
            shipping_fee = shipping_brackets["0-500"]
        elif weight <= 1000:
            shipping_fee = shipping_brackets["500-1000"]
        elif weight <= 2000:
            shipping_fee = shipping_brackets["1000-2000"]
        else:
            shipping_fee = shipping_brackets["2000+"]
        
        # Collection fee
        collection_fee = mrp * FLIPKART_FEES["collection_fee_percent"]
        
        total_fees = commission + fixed_fee + shipping_fee + collection_fee
        gst_on_fees = total_fees * FLIPKART_FEES["gst_on_fees"]
        
        return {
            "commission": commission,
            "fixed_fee": fixed_fee,
            "shipping_fee": shipping_fee,
            "collection_fee": collection_fee,
            "gst_on_fees": gst_on_fees,
            "total_platform_fee": total_fees + gst_on_fees,
            "platform": "Flipkart",
            "fee_breakdown": f"Commission: ₹{commission:.1f} ({commission_rate*100:.0f}%) + Fixed: ₹{fixed_fee} + Shipping: ₹{shipping_fee}"
        }
    
    return {"total_platform_fee": mrp * 0.25, "platform": platform}


def get_quick_commerce_fees(mrp, platform="blinkit"):
    """Calculate quick commerce platform fees."""
    
    qc_data = QUICK_COMMERCE_FEES.get(platform, QUICK_COMMERCE_FEES["blinkit"])
    
    commission = mrp * qc_data["commission_rate"]
    return_cost = mrp * qc_data["return_rate"]
    
    return {
        "commission": commission,
        "commission_rate": qc_data["commission_rate"],
        "listing_fee": qc_data["listing_fee_monthly"],
        "return_cost": return_cost,
        "total_platform_fee": commission,
        "platform": platform.title(),
        "payment_cycle": qc_data["payment_cycle_days"],
        "min_margin_required": qc_data["min_margin_required"],
        "fee_breakdown": f"Commission: ₹{commission:.1f} ({qc_data['commission_rate']*100:.0f}%)"
    }


# ============================================================================
# DYNAMIC INGREDIENT PRICING - Web Scraping & AI
# ============================================================================

def scrape_indiamart_price(ingredient_name):
    """Scrape wholesale price from IndiaMART for an ingredient using JSON data."""
    try:
        import json
        
        # Clean search query
        search_query = ingredient_name.replace(" ", "+")
        url = f"https://dir.indiamart.com/search.mp?ss={search_query}"
        
        # Use simple headers for IndiaMART (avoid compression issues)
        simple_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=simple_headers, timeout=15)
        if response.status_code != 200:
            return None
        
        # Use response.text with proper encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # IndiaMART uses Next.js - data is in __NEXT_DATA__ script tag
        script = soup.find('script', id='__NEXT_DATA__')
        if not script or not script.string:
            return None
        
        try:
            data = json.loads(script.string)
            results = data.get('props', {}).get('pageProps', {}).get('searchResponse', {}).get('results', [])
        except json.JSONDecodeError:
            return None
        
        prices = []
        for item in results[:20]:
            fields = item.get('fields', {})
            
            # Get price from 'itemprice' field (numeric) or parse from 'indiaPriceFormat'
            item_price = fields.get('itemprice')
            price_format = fields.get('indiaPriceFormat', '') or fields.get('price_f', '')
            
            # Only accept prices that are per Kg (not per Bag, Packet, etc.)
            # Check for /Kg, /kg, /KG, per Kg, etc. - be lenient with encoding
            price_format_lower = str(price_format).lower() if price_format else ''
            is_per_kg = any(x in price_format_lower for x in ['/kg', 'per kg', '/kilogram', 'per kilogram'])
            is_not_per_kg = any(x in price_format_lower for x in ['/bag', '/packet', '/piece', '/box', '/tonne', '/ton', '/litre', '/liter'])
            
            if item_price and is_per_kg and not is_not_per_kg:
                try:
                    price = float(item_price)
                    if 5 < price < 5000:  # Sanity check for per-kg price
                        prices.append(price)
                except (ValueError, TypeError):
                    pass
            elif item_price and not price_format:
                # If no format specified, assume per kg for raw materials
                try:
                    price = float(item_price)
                    if 5 < price < 5000:
                        prices.append(price)
                except (ValueError, TypeError):
                    pass
        
        if prices:
            # Return median price to avoid outliers
            prices.sort()
            return {
                "price": prices[len(prices)//2],
                "min_price": min(prices),
                "max_price": max(prices),
                "source": "IndiaMART",
                "num_listings": len(prices),
                "confidence": "high" if len(prices) >= 3 else "medium"
            }
        
        return None
    except Exception as e:
        return None


def scrape_tradeindia_price(ingredient_name):
    """Scrape wholesale price from TradeIndia for an ingredient."""
    try:
        search_query = ingredient_name.replace(" ", "-")
        url = f"https://www.tradeindia.com/search.html?keyword={search_query}"
        
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        prices = []
        # Look for price patterns
        for elem in soup.find_all(string=re.compile(r'[₹Rs]\s*[\d,]+\s*/\s*(?:kg|Kg|KG)', re.I)):
            price_match = re.search(r'[₹Rs.]*\s*([\d,]+(?:\.\d+)?)', elem)
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
                if 5 < price < 50000:
                    prices.append(price)
        
        if prices:
            prices.sort()
            return {
                "price": prices[len(prices)//2],
                "source": "TradeIndia",
                "num_listings": len(prices)
            }
        
        return None
    except Exception as e:
        return None


def scrape_google_price(ingredient_name):
    """Search Google for wholesale price of an ingredient."""
    try:
        search_query = f"{ingredient_name} wholesale price per kg india INR"
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        # Look for price patterns in search results
        prices = []
        # Match patterns like "₹50/kg", "Rs. 100 per kg", "INR 75/kilogram"
        patterns = [
            r'[₹Rs.INR]+\s*([\d,]+(?:\.\d+)?)\s*(?:/|per)\s*(?:kg|kilogram)',
            r'([\d,]+(?:\.\d+)?)\s*(?:rupees?|rs\.?|inr)\s*(?:/|per)\s*(?:kg|kilogram)',
            r'price[:\s]*([\d,]+(?:\.\d+)?)\s*(?:/|per)?\s*(?:kg)?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.I)
            for match in matches[:5]:
                try:
                    price = float(match.replace(',', ''))
                    if 5 < price < 50000:
                        prices.append(price)
                except:
                    pass
        
        if prices:
            prices.sort()
            return {
                "price": prices[len(prices)//2],
                "source": "Google Search",
                "num_listings": len(prices)
            }
        
        return None
    except Exception as e:
        return None


def get_live_ingredient_price(ingredient_name, api_key=None, api_provider="Groq"):
    """
    Get live/current wholesale price for an ingredient using multiple sources:
    1. Try scraping from B2B marketplaces (IndiaMART, TradeIndia)
    2. Search Google for recent prices
    3. Use LLM knowledge as fallback with current market awareness
    """
    
    # Normalize ingredient name
    ingredient_clean = ingredient_name.lower().strip().replace("_", " ")
    
    # Try scraping sources (run in sequence to avoid overwhelming)
    scraped_price = None
    
    # Try IndiaMART first
    indiamart_result = scrape_indiamart_price(ingredient_clean)
    if indiamart_result:
        scraped_price = indiamart_result
    
    # If IndiaMART fails, try Google
    if not scraped_price:
        google_result = scrape_google_price(ingredient_clean)
        if google_result:
            scraped_price = google_result
    
    # If we got a scraped price, return it
    if scraped_price:
        return {
            "ingredient": ingredient_clean,
            "price_per_kg": scraped_price["price"],
            "source": scraped_price["source"],
            "confidence": "high" if scraped_price.get("num_listings", 0) > 3 else "medium",
            "scraped": True
        }
    
    # Fallback: Use LLM to estimate current wholesale price
    if api_key and api_provider:
        try:
            prompt = f"""You are an expert in Indian wholesale commodity markets. 
            
What is the current wholesale price (B2B/bulk) for "{ingredient_clean}" in India in INR per kg?

Consider:
- Current market conditions (inflation, supply chain)
- Bulk/wholesale prices (not retail)
- Prices in major Indian cities (Delhi, Mumbai, Bangalore)

Respond with ONLY a JSON object:
{{"price_per_kg": <number>, "confidence": "high/medium/low", "notes": "brief note on price factors"}}

ONLY JSON, no other text."""

            if api_provider == "Groq":
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 200
                    },
                    timeout=15
                )
            else:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 200
                    },
                    timeout=15
                )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "ingredient": ingredient_clean,
                        "price_per_kg": result.get("price_per_kg", 100),
                        "source": "AI Estimate",
                        "confidence": result.get("confidence", "medium"),
                        "notes": result.get("notes", ""),
                        "scraped": False
                    }
        except Exception as e:
            pass
    
    # Final fallback: use static database if available
    static_price = RAW_MATERIAL_COSTS.get(ingredient_name.lower().replace(" ", "_"))
    if static_price:
        return {
            "ingredient": ingredient_clean,
            "price_per_kg": static_price,
            "source": "Database (Fallback)",
            "confidence": "medium",
            "scraped": False
        }
    
    # Ultimate fallback
    return {
        "ingredient": ingredient_clean,
        "price_per_kg": 100,  # Default assumption
        "source": "Default",
        "confidence": "low",
        "scraped": False
    }


def analyze_product_ingredients(product_description, category, weight, api_key=None, api_provider="Groq"):
    """
    Use AI to analyze a product and identify its likely ingredients,
    then fetch current prices for each ingredient.
    """
    
    if not api_key:
        return None
    
    prompt = f"""You are a product formulation expert. Analyze this product and list its likely raw material ingredients.

PRODUCT: {product_description}
CATEGORY: {category}
PACK SIZE: {weight}g

List the main raw materials/ingredients needed to make this product. For each ingredient, estimate the quantity needed (in grams) for one unit of {weight}g.

IMPORTANT:
- Be specific about ingredients (e.g., "wheat flour" not just "flour")
- Include ALL ingredients including small quantities (preservatives, flavors, etc.)
- Total quantity should be slightly MORE than {weight}g to account for processing loss
- Consider typical formulations for this product category

Respond with ONLY a JSON array:
[
    {{"ingredient": "ingredient_name", "quantity_grams": 100, "purpose": "main ingredient/flavoring/preservative/etc"}},
    ...
]

ONLY JSON array, no other text."""

    try:
        if api_provider == "Groq":
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=20
            )
        else:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=20
            )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # Extract JSON array
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                ingredients = json.loads(json_match.group())
                return ingredients
    except Exception as e:
        pass
    
    return None


def estimate_raw_material_cost(product_description, category, weight, api_key=None, api_provider="Groq"):
    """
    Fully dynamic raw material cost estimation:
    1. Use AI to identify ingredients from product description
    2. Scrape/fetch current wholesale prices for each ingredient
    3. Calculate total raw material cost
    4. Add manufacturing overhead
    """
    
    # Step 1: Analyze product to get ingredient list
    ingredients = analyze_product_ingredients(product_description, category, weight, api_key, api_provider)
    
    if ingredients and len(ingredients) > 0:
        # Step 2: Get current prices for each ingredient
        raw_materials = []
        total_raw_cost = 0
        price_sources = set()
        
        for item in ingredients[:15]:  # Limit to 15 ingredients
            ingredient_name = item.get("ingredient", "unknown")
            quantity_grams = item.get("quantity_grams", 10)
            
            # Fetch current price
            price_info = get_live_ingredient_price(ingredient_name, api_key, api_provider)
            price_per_kg = price_info.get("price_per_kg", 100)
            
            # Calculate cost for this ingredient
            cost = (quantity_grams / 1000) * price_per_kg
            total_raw_cost += cost
            
            price_sources.add(price_info.get("source", "Unknown"))
            
            raw_materials.append({
                "name": ingredient_name,
                "quantity_grams": quantity_grams,
                "cost_per_kg": price_per_kg,
                "cost": round(cost, 2),
                "purpose": item.get("purpose", ""),
                "price_source": price_info.get("source", ""),
                "price_confidence": price_info.get("confidence", "medium")
            })
        
        # Step 3: Calculate manufacturing overhead
        overhead_rate = MANUFACTURING_OVERHEAD.get(category, 0.40)
        overhead_cost = total_raw_cost * overhead_rate
        
        return {
            "raw_materials": raw_materials,
            "total_raw_material_cost": round(total_raw_cost, 2),
            "manufacturing_overhead_percent": overhead_rate * 100,
            "manufacturing_overhead_cost": round(overhead_cost, 2),
            "total_manufacturing_cost": round(total_raw_cost + overhead_cost, 2),
            "cost_per_gram": round((total_raw_cost + overhead_cost) / weight, 3),
            "price_sources": list(price_sources),
            "reasoning": f"AI-analyzed {len(raw_materials)} ingredients with live/estimated pricing from: {', '.join(price_sources)}"
        }
    
    # Fallback: Use AI to estimate directly if ingredient analysis fails
    # Build a context string of sample raw materials for reference
    sample_materials = "\n".join([f"- {k.replace('_', ' ')}: ₹{v}/kg" for k, v in list(RAW_MATERIAL_COSTS.items())[:30]])
    
    prompt = f"""You are a manufacturing cost analyst. Analyze this product and estimate raw material costs.

PRODUCT: {product_description}
CATEGORY: {category}
PACK SIZE: {weight}g

REFERENCE WHOLESALE PRICES (INR/kg) - use these as guidelines:
{sample_materials}

Based on the product description, estimate:
1. List the likely raw materials needed and their quantities (in grams) for one unit
2. Calculate the cost of each raw material (estimate current wholesale prices)
3. Add manufacturing overhead (labor, utilities, equipment depreciation) - typically 30-50% of raw material cost
4. Total cost to manufacture one unit

IMPORTANT: Be realistic. For a {weight}g product:
- Main ingredients typically make up 60-80% of weight
- Consider wastage (5-10%)
- Include any specialty ingredients mentioned
- Use your knowledge of CURRENT market prices (not outdated)

Respond in this exact JSON format:
{{
    "raw_materials": [
        {{"name": "ingredient_name", "quantity_grams": 100, "cost_per_kg": 50, "cost": 5.0}},
        ...
    ],
    "total_raw_material_cost": 25.5,
    "manufacturing_overhead_percent": 35,
    "manufacturing_overhead_cost": 8.9,
    "total_manufacturing_cost": 34.4,
    "cost_per_gram": 0.17,
    "reasoning": "Brief explanation of the estimate"
}}

Respond ONLY with valid JSON, no other text."""

    if api_key and api_provider:
        try:
            if api_provider == "Groq":
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    # Extract JSON from response
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        return json.loads(json_match.group())
            elif api_provider == "OpenAI":
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        return json.loads(json_match.group())
        except Exception as e:
            pass
    
    # Fallback: Use category-based estimation
    base_cost_per_gram = {
        "Packaged Snacks": 0.12,
        "Personal Care": 0.20,
        "Supplements": 0.45,
        "Beverages": 0.08,
        "Home Care": 0.10,
        "Baby Products": 0.30,
        "Pet Food": 0.15,
        "Other": 0.18
    }
    
    cost_per_gram = base_cost_per_gram.get(category, 0.18)
    raw_material_cost = cost_per_gram * weight * 0.7  # 70% is raw material
    overhead = raw_material_cost * MANUFACTURING_OVERHEAD.get(category, 0.40)
    
    return {
        "raw_materials": [{"name": "estimated_mix", "quantity_grams": weight, "cost_per_kg": cost_per_gram * 1000, "cost": raw_material_cost}],
        "total_raw_material_cost": raw_material_cost,
        "manufacturing_overhead_percent": MANUFACTURING_OVERHEAD.get(category, 0.40) * 100,
        "manufacturing_overhead_cost": overhead,
        "total_manufacturing_cost": raw_material_cost + overhead,
        "cost_per_gram": (raw_material_cost + overhead) / weight,
        "reasoning": "Fallback estimation based on category benchmarks"
    }


def estimate_packaging_cost(weight, category, packaging_type=None):
    """Estimate packaging cost based on product weight and type."""
    
    # Auto-select packaging type if not specified
    if not packaging_type:
        if category in ["Packaged Snacks"]:
            if weight <= 100:
                packaging_type = "pouch_small"
            elif weight <= 250:
                packaging_type = "pouch_medium"
            elif weight <= 500:
                packaging_type = "pouch_large"
            else:
                packaging_type = "pouch_xl"
        elif category in ["Personal Care", "Home Care"]:
            if weight <= 200:
                packaging_type = "bottle_plastic_small"
            elif weight <= 500:
                packaging_type = "bottle_plastic_medium"
            else:
                packaging_type = "bottle_plastic_large"
        elif category in ["Beverages"]:
            if weight <= 200:
                packaging_type = "tetrapack"
            elif weight <= 500:
                packaging_type = "bottle_plastic_medium"
            else:
                packaging_type = "bottle_plastic_large"
        elif category in ["Supplements"]:
            if weight <= 100:
                packaging_type = "jar_plastic"
            else:
                packaging_type = "bottle_plastic_medium"
        else:
            packaging_type = "box_medium"
    
    primary_packaging = PACKAGING_COSTS_DETAILED.get(packaging_type, {"cost": 10})["cost"]
    
    # Add label, cap/closure
    labels = RAW_MATERIAL_COSTS.get("labels", 2)
    closures = RAW_MATERIAL_COSTS.get("caps_closures", 3)
    
    # Secondary packaging for shipping (amortized)
    secondary = SECONDARY_PACKAGING["corrugated_box_small"] / 6  # Assume 6 units per box
    
    total = primary_packaging + labels + closures + secondary
    
    return {
        "primary_packaging": primary_packaging,
        "packaging_type": packaging_type,
        "labels": labels,
        "closures": closures,
        "secondary_packaging": secondary,
        "total_packaging_cost": total,
        "breakdown": f"{packaging_type}: ₹{primary_packaging} + Labels: ₹{labels} + Closure: ₹{closures}"
    }


def calculate_unit_economics(category, weight, mrp, channel, product_description="", api_key=None, api_provider="Groq"):
    """Calculate comprehensive unit economics with dynamic pricing based on actual marketplace data."""
    
    # 1. Get raw material and manufacturing costs
    manufacturing_data = estimate_raw_material_cost(product_description, category, weight, api_key, api_provider)
    manufacturing_cost = manufacturing_data["total_manufacturing_cost"]
    
    # 2. Get packaging costs
    packaging_data = estimate_packaging_cost(weight, category)
    packaging_cost = packaging_data["total_packaging_cost"]
    
    # 3. Get platform fees based on channel
    if channel == "E-commerce":
        # Calculate for both Amazon and Flipkart, use average or show both
        amazon_fees = get_platform_fees(mrp, weight, category, "amazon", "national")
        flipkart_fees = get_platform_fees(mrp, weight, category, "flipkart", "national")
        
        # Use average of both platforms
        platform_fees = (amazon_fees["total_platform_fee"] + flipkart_fees["total_platform_fee"]) / 2
        platform_breakdown = {
            "amazon": amazon_fees,
            "flipkart": flipkart_fees,
            "average_fee": platform_fees
        }
        
        # Logistics (3PL for D2C or included in platform for FBA)
        logistics_data = LOGISTICS_RATES["xpressbees"]  # Most cost-effective
        if weight <= 500:
            logistics_cost = logistics_data["national"]["0-500"]
        elif weight <= 1000:
            logistics_cost = logistics_data["national"]["500-1000"]
        else:
            logistics_cost = logistics_data["national"]["1000-2000"]
        
        return_rate = RETURN_RATES.get(category, 0.08)
        
    elif channel == "Quick Commerce":
        # Calculate for multiple quick commerce platforms
        blinkit_fees = get_quick_commerce_fees(mrp, "blinkit")
        zepto_fees = get_quick_commerce_fees(mrp, "zepto")
        swiggy_fees = get_quick_commerce_fees(mrp, "swiggy_instamart")
        
        # Use average
        platform_fees = (blinkit_fees["total_platform_fee"] + zepto_fees["total_platform_fee"] + swiggy_fees["total_platform_fee"]) / 3
        platform_breakdown = {
            "blinkit": blinkit_fees,
            "zepto": zepto_fees,
            "swiggy_instamart": swiggy_fees,
            "average_fee": platform_fees
        }
        
        # Quick commerce handles logistics - cost built into commission
        logistics_cost = 0
        return_rate = 0.025  # Lower returns on quick commerce
        
    else:  # D2C
        platform_fees = mrp * D2C_COSTS["shopify"]["transaction_fee"]
        platform_fees += mrp * D2C_COSTS["shopify"]["payment_gateway_fee"]
        platform_breakdown = {
            "transaction_fee": mrp * 0.02,
            "payment_gateway_fee": mrp * 0.02,
            "monthly_fee_amortized": D2C_COSTS["shopify"]["monthly_fee"] / 500  # Assume 500 orders/month
        }
        
        logistics_data = LOGISTICS_RATES["xpressbees"]
        if weight <= 500:
            logistics_cost = logistics_data["national"]["0-500"]
        elif weight <= 1000:
            logistics_cost = logistics_data["national"]["500-1000"]
        else:
            logistics_cost = logistics_data["national"]["1000-2000"]
        
        return_rate = RETURN_RATES.get(category, 0.08)
    
    # 4. Calculate returns cost
    returns_cost = mrp * return_rate
    
    # 5. Calculate GST (on MRP, output GST - input GST credit)
    gst_rate = GST_RATES.get(category, 0.18)
    gst_liability = mrp * gst_rate / (1 + gst_rate)  # GST included in MRP
    
    # 6. Marketing/CAC allocation (estimate 10-15% for new brands)
    marketing_allocation = mrp * 0.10  # 10% of MRP for customer acquisition
    
    # 7. Total Costs
    total_cost = (
        manufacturing_cost +
        packaging_cost +
        platform_fees +
        logistics_cost +
        returns_cost +
        marketing_allocation
    )
    
    # Net margin (before tax)
    net_margin = mrp - total_cost - gst_liability
    margin_percentage = (net_margin / mrp) * 100 if mrp > 0 else 0
    
    # Calculate breakeven units (for fixed costs amortization)
    monthly_fixed_costs = 50000  # Estimate: rent, salaries, utilities
    breakeven_units = monthly_fixed_costs / net_margin if net_margin > 0 else float('inf')
    
    return {
        # Core metrics
        "manufacturing_cost": round(manufacturing_cost, 2),
        "packaging_cost": round(packaging_cost, 2),
        "platform_fees": round(platform_fees, 2),
        "logistics_cost": round(logistics_cost, 2),
        "returns_cost": round(returns_cost, 2),
        "marketing_allocation": round(marketing_allocation, 2),
        "gst_liability": round(gst_liability, 2),
        "total_cost": round(total_cost + gst_liability, 2),
        "net_margin": round(net_margin, 2),
        "margin_percentage": round(margin_percentage, 1),
        
        # Detailed breakdowns
        "manufacturing_breakdown": manufacturing_data,
        "packaging_breakdown": packaging_data,
        "platform_breakdown": platform_breakdown,
        "return_rate": return_rate,
        "gst_rate": gst_rate,
        
        # Additional insights
        "breakeven_units_monthly": round(breakeven_units) if breakeven_units != float('inf') else "N/A",
        "contribution_margin": round(mrp - manufacturing_cost - packaging_cost, 2),
        "contribution_margin_percent": round((mrp - manufacturing_cost - packaging_cost) / mrp * 100, 1) if mrp > 0 else 0,
        
        # Channel comparison
        "channel": channel,
        "channel_recommendation": get_channel_recommendation(margin_percentage, channel, category),
    }


def get_channel_recommendation(margin_percent, current_channel, category):
    """Provide channel-specific recommendations based on margins."""
    
    if current_channel == "Quick Commerce":
        if margin_percent < 15:
            return "⚠️ Quick Commerce margins are thin. Consider E-commerce or D2C for better margins."
        elif margin_percent < 25:
            return "✓ Viable for Quick Commerce but monitor closely. High volume needed."
        else:
            return "✅ Excellent margins for Quick Commerce. Good channel fit."
    
    elif current_channel == "E-commerce":
        if margin_percent < 10:
            return "❌ E-commerce margins are negative/very low. Review pricing or costs."
        elif margin_percent < 20:
            return "⚠️ Margins are acceptable but tight. Focus on volume and reviews."
        else:
            return "✅ Healthy E-commerce margins. Consider Prime/FBA for faster growth."
    
    else:  # D2C
        if margin_percent < 20:
            return "⚠️ D2C requires higher margins to cover CAC. Consider price increase."
        elif margin_percent < 35:
            return "✓ Decent D2C margins but CAC must be controlled."
        else:
            return "✅ Excellent D2C margins. Invest in brand building and retention."


def get_recommendation(margin_percentage):
    """Generate recommendation based on margin percentage."""
    if margin_percentage < 10:
        return "nogo", "❌ No-Go", "Unit economics are structurally challenged. Consider revisiting pricing, costs, or channel strategy before proceeding."
    elif margin_percentage <= 20:
        return "pilot", "⚠️ Pilot Carefully", "Margins are tight but workable. Proceed with controlled testing and validate assumptions before scaling."
    else:
        return "go", "✅ Go", "Unit economics support viability. Channel costs are sustainable at this price point."

# ============================================================================
# HEADER
# ============================================================================

st.title("Go / No-Go")
st.markdown("**AI-Powered Product Viability Assessment for Founders**")
st.markdown("Describe your product → Get market research, competitor analysis, and unit economics in minutes.")

# How It Works Section
with st.expander("ℹ️ **How This Tool Works** - Read before you start", expanded=False):
    st.markdown("""
### 🎯 What You'll Get
    
Our **AI Advisory Board** (4 expert agents) will analyze your product and deliver a clear verdict:

| Verdict | What It Means | When You'll See It |
|---------|---------------|-------------------|
| ✅ **GO** | Strong viability! Unit economics work, market opportunity exists. Proceed with confidence. | Margin > 20%, favorable market conditions |
| ⚠️ **PILOT** | Promising but risky. Test with small batch before scaling. Validate key assumptions first. | Margin 10-20%, some concerns to address |
| ❌ **NO-GO** | Economics don't work at current setup. Pivot pricing, costs, or channel before proceeding. | Margin < 10%, significant red flags |

### 🤖 Meet Your AI Advisory Board

| Agent | Role | What They Analyze |
|-------|------|-------------------|
| 🎯 **Maya** | CMO | Brand positioning, target audience, marketing channels, CAC |
| ♟️ **Arjun** | Strategy Consultant | Competitive moats, SWOT, market positioning, differentiation |
| 🚀 **Vikram** | GTM/Sales Head | Launch sequence, channel strategy, 90-day playbook |
| 💰 **Priya** | CFO | Unit economics, break-even, funding needs, financial risks |

### 📊 Key Metrics Explained

- **Unit Economics**: Cost to produce & sell ONE unit vs. your selling price
- **MRP**: Maximum Retail Price - what customers pay
- **Net Margin**: What you keep after ALL costs (manufacturing, platform fees, logistics, returns, GST)
- **Platform Fees**: Amazon/Flipkart take 25-35% of your MRP
- **CAC**: Customer Acquisition Cost - cost to get one customer

### 💡 Pro Tips

1. **Be specific** in your product description - the more detail, the better analysis
2. **Start with E-commerce** unless you have retail relationships
3. **Margin < 15%** on Quick Commerce is a red flag (high platform fees)
4. After getting the verdict, **chat with specific agents** for deep dives
""")

st.divider()

# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("---")
    
    # Load API keys from .env file (no UI needed)
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    # Auto-detect which API key is available
    if groq_api_key and groq_api_key != "your_groq_api_key_here":
        api_key = groq_api_key
        api_provider = "Groq"
    elif openai_api_key and openai_api_key != "your_openai_api_key_here":
        api_key = openai_api_key
        api_provider = "OpenAI"
    else:
        api_key = None
        api_provider = "Groq"
    
    # Research Toggles
    st.subheader("🔬 Research Options")
    
    do_competitor_analysis = st.toggle(
        "🏪 Competitor Analysis",
        value=True,
        help="Search Amazon, Flipkart for competing products"
    )
    
    do_market_sizing = st.toggle(
        "📊 Market Sizing",
        value=True,
        help="Estimate TAM/SAM/SOM and market trends"
    )
    
    do_unit_economics = st.toggle(
        "💰 Unit Economics",
        value=True,
        help="Calculate manufacturing, platform, logistics costs"
    )
    
    st.markdown("---")
    st.subheader("🤖 AI Advisory Board")
    st.caption("4 expert agents analyze and debate your product")
    
    # Single toggle for the entire board
    do_board_meeting = st.toggle(
        "🏛️ Run Board Meeting",
        value=True,
        help="Maya (CMO), Arjun (Strategy), Vikram (GTM), Priya (CFO) analyze and discuss"
    )
    
    # Individual agent toggles (collapsed by default)
    if do_board_meeting:
        with st.expander("Customize Agents", expanded=False):
            do_marketing_agent = st.checkbox("🎯 Maya (Marketing/CMO)", value=True)
            do_strategy_agent = st.checkbox("♟️ Arjun (Strategy)", value=True)
            do_gtm_agent = st.checkbox("🚀 Vikram (GTM)", value=True)
            do_finance_agent = st.checkbox("💰 Priya (Finance/CFO)", value=True)
    else:
        do_marketing_agent = False
        do_strategy_agent = False
        do_gtm_agent = False
        do_finance_agent = False
    
    st.markdown("---")
    
    # Unit Economics Parameters (shown if toggle is on)
    if do_unit_economics:
        st.subheader("📦 Product Parameters")
        
        # Define categories from the new constants
        product_categories = [
            "Packaged Snacks", "Personal Care", "Supplements", "Beverages", 
            "Home Care", "Baby Products", "Pet Food", "Electronics", "Other"
        ]
        
        product_category = st.selectbox(
            "Product Category",
            options=product_categories,
            help="Select the category that best matches your product"
        )
        
        sku_weight_input = st.text_input(
            "SKU Weight (grams)",
            value="200",
            help="Weight of a single unit in grams (50-1000g)"
        )
        try:
            sku_weight = int(sku_weight_input)
            sku_weight = max(50, min(1000, sku_weight))  # Clamp between 50-1000
        except ValueError:
            sku_weight = 200
            st.caption("⚠️ Invalid weight, using default: 200g")
        
        target_mrp_input = st.text_input(
            "Target MRP (₹)",
            value="299",
            help="Maximum Retail Price per unit (₹50-₹2000)"
        )
        try:
            target_mrp = int(target_mrp_input)
            target_mrp = max(50, min(2000, target_mrp))  # Clamp between 50-2000
        except ValueError:
            target_mrp = 299
            st.caption("⚠️ Invalid price, using default: ₹299")
        
        launch_channel = st.radio(
            "Primary Launch Channel",
            options=["E-commerce", "Quick Commerce"],
            help="Primary sales channel for initial launch"
        )
        
        with st.expander("📋 How Dynamic Pricing Works"):
            st.markdown("""
**🔄 Real-Time Ingredient Pricing:**
1. **AI Analysis** - Identifies ingredients from your product description
2. **Web Scraping** - Fetches current wholesale prices from IndiaMART, TradeIndia
3. **LLM Estimation** - Uses AI knowledge of current market prices as fallback
4. **Database Backup** - Falls back to curated price database if needed

**📊 Platform Fees (Live Data):**
- Amazon/Flipkart fees based on official seller documentation
- Quick Commerce commissions from partner programs
- Logistics rates from Delhivery, Xpressbees, etc.

**✅ Benefits:**
- No hardcoded prices - everything is dynamic
- Prices reflect current market conditions
- More accurate unit economics
            """)
            st.markdown("---")
            st.markdown(f"**Selected Category GST:** {GST_RATES.get(product_category, 0.18)*100:.0f}%")
            st.markdown(f"**Est. Return Rate:** {RETURN_RATES.get(product_category, 0.08)*100:.0f}%")
            if launch_channel == "E-commerce":
                amazon_cat = CATEGORY_TO_PLATFORM_CATEGORY.get(product_category, {}).get("amazon", "Other")
                st.markdown(f"**Amazon Referral Fee:** {AMAZON_FEES['referral_fees'].get(amazon_cat, 0.15)*100:.0f}%")
            else:
                avg_qc = (QUICK_COMMERCE_FEES["blinkit"]["commission_rate"] + 
                          QUICK_COMMERCE_FEES["zepto"]["commission_rate"] + 
                          QUICK_COMMERCE_FEES["swiggy_instamart"]["commission_rate"]) / 3
                st.markdown(f"**Avg. Quick Commerce Commission:** {avg_qc*100:.0f}%")
    else:
        product_category = "Other"
        sku_weight = 200
        target_mrp = 299
        launch_channel = "E-commerce"

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Product Description Input
st.subheader("📝 Describe Your Product")

product_description = st.text_area(
    "Tell us about your product idea",
    placeholder="""Example: 
A premium protein bar made with whey protein and dark chocolate, targeting fitness enthusiasts in urban India. 
60g bar with 20g protein, no added sugar, available in 3 flavors.
Positioned as a healthier alternative to imported protein bars at a more accessible price point.""",
    height=150,
    help="Be specific about: What it is, who it's for, what makes it different, and your target price point"
)

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    run_research = st.button("🚀 Run Research", type="primary", use_container_width=True)

with col_btn2:
    if st.button("🔄 Clear Results", use_container_width=True):
        st.session_state.research_complete = False
        st.session_state.research_results = None
        st.session_state.competitors = None
        st.rerun()

# ============================================================================
# RUN RESEARCH
# ============================================================================

if run_research:
    if not product_description.strip():
        st.error("Please describe your product before running research.")
    elif not api_key or api_key in ["your_groq_api_key_here", "your_openai_api_key_here"]:
        st.error(f"Please add your {'GROQ_API_KEY' if 'Groq' in api_provider else 'OPENAI_API_KEY'} to the .env file.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(percent, message):
            progress_bar.progress(percent)
            status_text.markdown(f"**{message}**")
        
        api_type = "OpenAI" if "OpenAI" in api_provider else "Groq"
        
        results = run_market_research_agent(
            product_description=product_description,
            category=product_category if do_unit_economics else "Other",
            target_mrp=target_mrp if do_unit_economics else 299,
            api_key=api_key,
            api_provider=api_type,
            do_competitor_analysis=do_competitor_analysis,
            do_marketing_analysis=do_marketing_agent,
            do_market_sizing=do_market_sizing,
            progress_callback=update_progress,
            sku_weight=sku_weight if do_unit_economics else 200,
            launch_channel=launch_channel if do_unit_economics else "E-commerce",
            do_strategy_analysis=do_strategy_agent,
            do_gtm_analysis=do_gtm_agent,
            do_finance_analysis=do_finance_agent
        )
        
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        st.session_state.research_results = results
        st.session_state.research_complete = True
        st.rerun()

# ============================================================================
# DISPLAY RESULTS - BOARD MEETING OUTPUT
# ============================================================================

if st.session_state.research_complete and st.session_state.research_results:
    results = st.session_state.research_results
    
    st.divider()
    
    # ==== MAIN VERDICT (Always shown first) ====
    st.subheader("🏛️ Board Verdict")
    
    # Quick legend
    st.caption("**Quick Reference:** ✅ GO = Proceed confidently | ⚠️ PILOT = Test first, validate assumptions | ❌ NO-GO = Fix economics before proceeding")
    
    if results.get('board_verdict'):
        st.markdown(results['board_verdict'])
    else:
        st.warning("Board verdict not available. Please check your API key.")
    
    st.divider()
    
    # ==== DETAILED TABS ====
    tab_names = ["📊 Details", "🏪 Competitors", "📈 Unit Economics", "💬 Chat with Agents"]
    tabs = st.tabs(tab_names)
    
    # Tab 1: Details (Product Analysis + Market Size)
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Product Analysis")
            if results.get('product_analysis'):
                st.markdown(results['product_analysis'])
            else:
                st.info("Product analysis not available.")
        
        with col2:
            if do_market_sizing and results.get('market_size'):
                st.markdown("#### 📊 Market Size")
                st.markdown(results['market_size'])
    
    # Tab 2: Competitors
    with tabs[1]:
        st.markdown("#### Competitors Found")
        
        if results.get('sources_searched'):
            st.caption(f"📦 Sources: {', '.join(results['sources_searched'])}")
        
        if results.get('competitors'):
            for i, comp in enumerate(results['competitors'], 1):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    badge = "🏆 " if comp.get('bestseller') else ""
                    title = comp['title'][:60] + "..." if len(comp['title']) > 60 else comp['title']
                    if comp.get('link'):
                        st.markdown(f"**{i}. {badge}[{title}]({comp['link']})**")
                    else:
                        st.markdown(f"**{i}. {badge}{title}**")
                with col2:
                    st.markdown(f"💰 {comp['price']}")
                with col3:
                    st.markdown(f"⭐ {comp['rating']}")
        else:
            st.info("No competitors found via scraping. Check the Board Verdict for AI-powered competitor insights.")
    
    # Tab 3: Unit Economics
    with tabs[2]:
        if do_unit_economics:
            economics = calculate_unit_economics(
                product_category, sku_weight, target_mrp, launch_channel, 
                product_description, api_key, api_provider
            )
            rec_type, rec_title, rec_text = get_recommendation(economics["margin_percentage"])
            
            # Key Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("MRP", f"₹{target_mrp}")
            with col2:
                st.metric("Total Cost", f"₹{economics['total_cost']:.0f}")
            with col3:
                st.metric("Net Margin", f"₹{economics['net_margin']:.0f}", 
                         delta=f"{economics['margin_percentage']:.1f}%")
            with col4:
                st.metric("Channel", launch_channel)
            
            # Recommendation badge
            if rec_type == "go":
                st.success(f"**{rec_title}** - {rec_text}")
            elif rec_type == "pilot":
                st.warning(f"**{rec_title}** - {rec_text}")
            else:
                st.error(f"**{rec_title}** - {rec_text}")
            
            # Channel-specific recommendation
            if economics.get("channel_recommendation"):
                st.info(economics["channel_recommendation"])
            
            # Additional Insights
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Contribution Margin", f"₹{economics['contribution_margin']:.0f}", 
                         delta=f"{economics['contribution_margin_percent']:.1f}%")
            with col2:
                be_units = economics.get('breakeven_units_monthly', 'N/A')
                st.metric("Break-even Units/Month", f"{be_units}")
            with col3:
                st.metric("GST Rate", f"{economics['gst_rate']*100:.0f}%")
            
            # Cost breakdown table
            st.markdown("**💰 Detailed Cost Breakdown**")
            cost_data = pd.DataFrame({
                "Component": [
                    "🏭 Manufacturing (Raw Materials + Overhead)", 
                    "📦 Packaging (Primary + Secondary)", 
                    "🏪 Platform Fees (Commission + Shipping)", 
                    "🚚 Logistics (3PL/Delivery)", 
                    "↩️ Returns Cost (Est.)", 
                    "📢 Marketing Allocation",
                    "🧾 GST Liability"
                ],
                "Amount (₹)": [
                    f"₹{economics['manufacturing_cost']:.1f}",
                    f"₹{economics['packaging_cost']:.1f}",
                    f"₹{economics['platform_fees']:.1f}",
                    f"₹{economics['logistics_cost']:.1f}",
                    f"₹{economics['returns_cost']:.1f}",
                    f"₹{economics['marketing_allocation']:.1f}",
                    f"₹{economics['gst_liability']:.1f}"
                ],
                "% of MRP": [
                    f"{(economics['manufacturing_cost']/target_mrp*100):.1f}%",
                    f"{(economics['packaging_cost']/target_mrp*100):.1f}%",
                    f"{(economics['platform_fees']/target_mrp*100):.1f}%",
                    f"{(economics['logistics_cost']/target_mrp*100):.1f}%",
                    f"{(economics['returns_cost']/target_mrp*100):.1f}%",
                    f"{(economics['marketing_allocation']/target_mrp*100):.1f}%",
                    f"{(economics['gst_liability']/target_mrp*100):.1f}%"
                ]
            })
            st.dataframe(cost_data, hide_index=True, use_container_width=True)
            
            # Manufacturing Breakdown (if available)
            if economics.get("manufacturing_breakdown"):
                with st.expander("🔬 Raw Material & Manufacturing Breakdown (Dynamic Pricing)", expanded=True):
                    mfg = economics["manufacturing_breakdown"]
                    
                    # Show price sources
                    if mfg.get("price_sources"):
                        sources = mfg["price_sources"]
                        source_badges = []
                        for src in sources:
                            if "IndiaMART" in src:
                                source_badges.append("🌐 IndiaMART")
                            elif "TradeIndia" in src:
                                source_badges.append("🌐 TradeIndia")
                            elif "Google" in src:
                                source_badges.append("🔍 Google")
                            elif "AI" in src:
                                source_badges.append("🤖 AI Estimate")
                            elif "Database" in src:
                                source_badges.append("📚 Database")
                            else:
                                source_badges.append(f"📊 {src}")
                        st.info(f"**Price Sources:** {' | '.join(source_badges)}")
                    
                    st.markdown(f"**Analysis:** {mfg.get('reasoning', 'AI-powered estimation')}")
                    
                    if mfg.get("raw_materials"):
                        rm_data = []
                        for rm in mfg["raw_materials"][:12]:  # Show top 12
                            confidence_icon = "✅" if rm.get("price_confidence") == "high" else "⚡" if rm.get("price_confidence") == "medium" else "⚠️"
                            rm_data.append({
                                "Ingredient": rm.get("name", "").replace("_", " ").title(),
                                "Purpose": rm.get("purpose", "-")[:20],
                                "Qty (g)": f"{rm.get('quantity_grams', 0):.0f}",
                                "Rate (₹/kg)": f"₹{rm.get('cost_per_kg', 0):.0f}",
                                "Cost (₹)": f"₹{rm.get('cost', 0):.2f}",
                                "Source": f"{confidence_icon} {rm.get('price_source', 'Est.')[:10]}"
                            })
                        if rm_data:
                            st.dataframe(pd.DataFrame(rm_data), hide_index=True, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Raw Material Cost", f"₹{mfg.get('total_raw_material_cost', 0):.2f}")
                    with col2:
                        st.metric("Mfg. Overhead", f"₹{mfg.get('manufacturing_overhead_cost', 0):.2f}",
                                 delta=f"+{mfg.get('manufacturing_overhead_percent', 0):.0f}%")
                    with col3:
                        st.metric("Total Mfg. Cost", f"₹{mfg.get('total_manufacturing_cost', 0):.2f}")
            
            # Packaging Breakdown
            if economics.get("packaging_breakdown"):
                with st.expander("📦 Packaging Cost Breakdown"):
                    pkg = economics["packaging_breakdown"]
                    st.markdown(f"**Packaging Type:** {pkg.get('packaging_type', 'Standard').replace('_', ' ').title()}")
                    pkg_data = pd.DataFrame({
                        "Component": ["Primary Packaging", "Labels", "Caps/Closures", "Secondary (Shipping)"],
                        "Cost": [
                            f"₹{pkg.get('primary_packaging', 0):.1f}",
                            f"₹{pkg.get('labels', 0):.1f}",
                            f"₹{pkg.get('closures', 0):.1f}",
                            f"₹{pkg.get('secondary_packaging', 0):.1f}"
                        ]
                    })
                    st.dataframe(pkg_data, hide_index=True)
            
            # Platform Fee Breakdown
            if economics.get("platform_breakdown"):
                with st.expander("🏪 Platform Fee Breakdown (Marketplace Comparison)"):
                    pb = economics["platform_breakdown"]
                    
                    if launch_channel == "E-commerce":
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Amazon India**")
                            if pb.get("amazon"):
                                amz = pb["amazon"]
                                st.markdown(f"- Referral Fee: ₹{amz.get('referral_fee', 0):.1f}")
                                st.markdown(f"- Closing Fee: ₹{amz.get('closing_fee', 0):.1f}")
                                st.markdown(f"- Weight Handling: ₹{amz.get('weight_handling_fee', 0):.1f}")
                                st.markdown(f"- GST on Fees: ₹{amz.get('gst_on_fees', 0):.1f}")
                                st.markdown(f"**Total: ₹{amz.get('total_platform_fee', 0):.1f}**")
                        with col2:
                            st.markdown("**Flipkart**")
                            if pb.get("flipkart"):
                                fk = pb["flipkart"]
                                st.markdown(f"- Commission: ₹{fk.get('commission', 0):.1f}")
                                st.markdown(f"- Fixed Fee: ₹{fk.get('fixed_fee', 0):.1f}")
                                st.markdown(f"- Shipping Fee: ₹{fk.get('shipping_fee', 0):.1f}")
                                st.markdown(f"- Collection Fee: ₹{fk.get('collection_fee', 0):.1f}")
                                st.markdown(f"**Total: ₹{fk.get('total_platform_fee', 0):.1f}**")
                    
                    elif launch_channel == "Quick Commerce":
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown("**Blinkit**")
                            if pb.get("blinkit"):
                                bl = pb["blinkit"]
                                st.markdown(f"Commission: {bl.get('commission_rate', 0)*100:.0f}%")
                                st.markdown(f"**Fee: ₹{bl.get('total_platform_fee', 0):.1f}**")
                        with col2:
                            st.markdown("**Zepto**")
                            if pb.get("zepto"):
                                zp = pb["zepto"]
                                st.markdown(f"Commission: {zp.get('commission_rate', 0)*100:.0f}%")
                                st.markdown(f"**Fee: ₹{zp.get('total_platform_fee', 0):.1f}**")
                        with col3:
                            st.markdown("**Swiggy Instamart**")
                            if pb.get("swiggy_instamart"):
                                sw = pb["swiggy_instamart"]
                                st.markdown(f"Commission: {sw.get('commission_rate', 0)*100:.0f}%")
                                st.markdown(f"**Fee: ₹{sw.get('total_platform_fee', 0):.1f}**")
                        
                        st.caption("*Note: Quick commerce platforms handle logistics internally - cost included in commission*")
            
            st.divider()
            
            # Channel comparison
            st.markdown("**📊 Channel Comparison**")
            ecom = calculate_unit_economics(product_category, sku_weight, target_mrp, "E-commerce", product_description)
            qcom = calculate_unit_economics(product_category, sku_weight, target_mrp, "Quick Commerce", product_description)
            
            comparison_data = pd.DataFrame({
                "Metric": ["Platform Fees", "Logistics", "Returns Est.", "Total Cost", "Net Margin", "Margin %", "Verdict"],
                "E-commerce": [
                    f"₹{ecom['platform_fees']:.0f}",
                    f"₹{ecom['logistics_cost']:.0f}",
                    f"₹{ecom['returns_cost']:.0f}",
                    f"₹{ecom['total_cost']:.0f}",
                    f"₹{ecom['net_margin']:.0f}",
                    f"{ecom['margin_percentage']:.1f}%",
                    get_recommendation(ecom["margin_percentage"])[1]
                ],
                "Quick Commerce": [
                    f"₹{qcom['platform_fees']:.0f}",
                    f"₹{qcom['logistics_cost']:.0f}",
                    f"₹{qcom['returns_cost']:.0f}",
                    f"₹{qcom['total_cost']:.0f}",
                    f"₹{qcom['net_margin']:.0f}",
                    f"{qcom['margin_percentage']:.1f}%",
                    get_recommendation(qcom["margin_percentage"])[1]
                ]
            })
            st.dataframe(comparison_data, hide_index=True, use_container_width=True)
            
            # Data sources disclaimer
            with st.expander("ℹ️ Data Sources & Methodology"):
                st.markdown("""
**🔄 Dynamic Ingredient Pricing System:**

This tool uses a multi-layer approach to get the most accurate pricing:

| Priority | Source | Method |
|----------|--------|--------|
| 1️⃣ | **IndiaMART** | Web scraping B2B wholesale listings |
| 2️⃣ | **Google Search** | Parsing recent price mentions |
| 3️⃣ | **AI Estimation** | LLM analysis of current market prices |
| 4️⃣ | **Database** | Curated fallback prices (updated periodically) |

**Platform Fee Data (Updated 2024-2026):**
- **Amazon India:** [Seller Central Fee Schedule](https://sell.amazon.in/fees-and-pricing)
- **Flipkart:** [Seller Hub Fees & Commission](https://seller.flipkart.com/fees-and-commission)
- **Quick Commerce:** Blinkit, Zepto, Swiggy Instamart partner documentation

**How It Works:**
1. AI analyzes your product description to identify ingredients
2. For each ingredient, we try to fetch real-time wholesale prices
3. Manufacturing overhead (labor, utilities, QC) added by category
4. Platform fees calculated from official marketplace documentation

**Confidence Indicators:**
- ✅ High - Price from multiple B2B sources
- ⚡ Medium - AI estimate or single source
- ⚠️ Low - Fallback/default pricing

**Note:** Actual costs vary by volume, location, and supplier negotiations.
                """)
        else:
            st.info("Unit Economics analysis was disabled. Enable it in the sidebar.")
    
    # Tab 4: Chat with Agents
    with tabs[3]:
        st.markdown("#### 💬 Chat with an Expert Agent")
        st.markdown("Have a specific question? Ask one of our AI advisors directly.")
        
        # Agent selector
        agent_options = {
            "🎯 Maya (Marketing/CMO)": "marketing",
            "♟️ Arjun (Strategy)": "strategy", 
            "🚀 Vikram (GTM/Sales)": "gtm",
            "💰 Priya (Finance/CFO)": "finance"
        }
        
        selected_agent_name = st.selectbox(
            "Choose an agent to chat with:",
            options=list(agent_options.keys())
        )
        selected_agent = agent_options[selected_agent_name]
        
        # Show agent's initial analysis (collapsed)
        agent_output = st.session_state.agent_outputs.get(selected_agent, "")
        if agent_output:
            with st.expander(f"View {selected_agent_name.split('(')[0].strip()}'s Initial Analysis"):
                st.markdown(agent_output)
        
        # Chat history display
        if st.session_state.chat_history[selected_agent]:
            st.markdown("---")
            st.markdown("**Conversation:**")
            for msg in st.session_state.chat_history[selected_agent][-5:]:
                st.markdown(f"**You:** {msg['user']}")
                st.markdown(f"**{AGENT_PERSONAS[selected_agent]['emoji']} {AGENT_PERSONAS[selected_agent]['name']}:** {msg['agent']}")
                st.markdown("---")
        
        # Chat input
        user_question = st.text_input(
            "Your question:",
            placeholder=f"Ask {selected_agent_name.split('(')[0].strip()} anything about your product...",
            key="chat_input"
        )
        
        if st.button("Send", type="primary"):
            if user_question.strip():
                with st.spinner(f"{AGENT_PERSONAS[selected_agent]['emoji']} {AGENT_PERSONAS[selected_agent]['name']} is thinking..."):
                    response = chat_with_agent(
                        selected_agent,
                        user_question,
                        st.session_state.product_context,
                        agent_output,
                        st.session_state.chat_history[selected_agent],
                        api_key,
                        api_provider
                    )
                    
                    if response:
                        st.session_state.chat_history[selected_agent].append({
                            'user': user_question,
                            'agent': response
                        })
                        st.rerun()
                    else:
                        st.error("Failed to get response. Please try again.")
            else:
                st.warning("Please enter a question.")
        
        # Clear chat button
        if st.session_state.chat_history[selected_agent]:
            if st.button("Clear Chat History"):
                st.session_state.chat_history[selected_agent] = []
                st.rerun()
    
    # ==== BOARD DISCUSSION (Collapsible) ====
    if results.get('board_discussion'):
        with st.expander("🗣️ View Board Discussion (How agents debated)"):
            st.markdown("**Round 1: Initial Responses**")
            for d in results['board_discussion']:
                if d['round'] == 1:
                    st.markdown(f"{d['emoji']} **{d['name']}:** {d['message']}")
            
            st.markdown("---")
            st.markdown("**Round 2: Final Positions**")
            for d in results['board_discussion']:
                if d['round'] == 2:
                    st.markdown(f"{d['emoji']} **{d['name']}:** {d['message']}")

# ============================================================================
# DISCLAIMER
# ============================================================================

st.markdown("")
st.markdown(
    '<div class="disclaimer">'
    '<strong>Disclaimer:</strong> All outputs are directional benchmarks intended for '
    'early-stage decision-making, not final financial planning. Competitor data is scraped '
    'from public sources and may be incomplete. AI-generated insights should be validated '
    'with primary research. Actual costs, market conditions, and competitive dynamics may vary.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")
st.caption("Go / No-Go • AI-Powered Product Viability Assessment • Built for founders who value clarity over optimism")
