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
# BENCHMARK ASSUMPTIONS (Hardcoded)
# ============================================================================

MANUFACTURING_COST_PER_GRAM = {
    "Packaged Snacks": 0.15,
    "Personal Care": 0.25,
    "Supplements": 0.50,
    "Beverages": 0.10,
    "Home Care": 0.12,
    "Baby Products": 0.35,
    "Pet Food": 0.18,
    "Other": 0.20
}

PACKAGING_COST = {
    "Packaged Snacks": 8,
    "Personal Care": 15,
    "Supplements": 20,
    "Beverages": 12,
    "Home Care": 10,
    "Baby Products": 18,
    "Pet Food": 14,
    "Other": 12
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
    
    # Calculate unit economics early (needed for agents)
    economics_data = calculate_unit_economics(category, sku_weight, target_mrp, launch_channel)
    
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

def calculate_unit_economics(category, weight, mrp, channel):
    """Calculate all unit economics components."""
    
    manufacturing_cost = MANUFACTURING_COST_PER_GRAM.get(category, 0.20) * weight
    packaging_cost = PACKAGING_COST.get(category, 12)
    platform_fees = PLATFORM_MARGIN[channel] * mrp
    logistics_cost = LOGISTICS_COST[channel]
    returns_cost = RETURNS_RATE[channel] * mrp
    gst = GST_RATE * mrp
    
    total_cost = (
        manufacturing_cost + 
        packaging_cost + 
        platform_fees + 
        logistics_cost + 
        returns_cost + 
        gst
    )
    
    net_margin = mrp - total_cost
    margin_percentage = (net_margin / mrp) * 100 if mrp > 0 else 0
    
    return {
        "manufacturing_cost": manufacturing_cost,
        "packaging_cost": packaging_cost,
        "platform_fees": platform_fees,
        "logistics_cost": logistics_cost,
        "returns_cost": returns_cost,
        "gst": gst,
        "total_cost": total_cost,
        "net_margin": net_margin,
        "margin_percentage": margin_percentage
    }


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
        
        product_category = st.selectbox(
            "Product Category",
            options=list(MANUFACTURING_COST_PER_GRAM.keys()),
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
        
        with st.expander("📋 View Cost Assumptions"):
            st.markdown(f"**Manufacturing:** ₹{MANUFACTURING_COST_PER_GRAM[product_category]}/gram")
            st.markdown(f"**Packaging:** ₹{PACKAGING_COST[product_category]}/unit")
            st.markdown(f"**Platform Margin:** {int(PLATFORM_MARGIN[launch_channel]*100)}%")
            st.markdown(f"**Logistics:** ₹{LOGISTICS_COST[launch_channel]}/unit")
            st.markdown(f"**Returns:** {int(RETURNS_RATE[launch_channel]*100)}%")
            st.markdown(f"**GST:** {int(GST_RATE*100)}%")
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
            economics = calculate_unit_economics(product_category, sku_weight, target_mrp, launch_channel)
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
            
            # Cost breakdown table
            st.markdown("**Cost Breakdown**")
            cost_data = pd.DataFrame({
                "Component": ["Manufacturing", "Packaging", "Platform Fees", "Logistics", "Returns", "GST"],
                "Amount": [
                    f"₹{economics['manufacturing_cost']:.0f}",
                    f"₹{economics['packaging_cost']:.0f}",
                    f"₹{economics['platform_fees']:.0f}",
                    f"₹{economics['logistics_cost']:.0f}",
                    f"₹{economics['returns_cost']:.0f}",
                    f"₹{economics['gst']:.0f}"
                ],
                "% of MRP": [
                    f"{(economics['manufacturing_cost']/target_mrp*100):.1f}%",
                    f"{(economics['packaging_cost']/target_mrp*100):.1f}%",
                    f"{(economics['platform_fees']/target_mrp*100):.1f}%",
                    f"{(economics['logistics_cost']/target_mrp*100):.1f}%",
                    f"{(economics['returns_cost']/target_mrp*100):.1f}%",
                    f"{(economics['gst']/target_mrp*100):.1f}%"
                ]
            })
            st.dataframe(cost_data, hide_index=True, use_container_width=True)
            
            # Channel comparison
            st.markdown("**Channel Comparison**")
            ecom = calculate_unit_economics(product_category, sku_weight, target_mrp, "E-commerce")
            qcom = calculate_unit_economics(product_category, sku_weight, target_mrp, "Quick Commerce")
            col1, col2 = st.columns(2)
            with col1:
                e_rec = get_recommendation(ecom["margin_percentage"])
                st.markdown(f"**E-commerce:** ₹{ecom['net_margin']:.0f} ({ecom['margin_percentage']:.1f}%) → {e_rec[1]}")
            with col2:
                q_rec = get_recommendation(qcom["margin_percentage"])
                st.markdown(f"**Quick Commerce:** ₹{qcom['net_margin']:.0f} ({qcom['margin_percentage']:.1f}%) → {q_rec[1]}")
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
