# 🚀 Go / No-Go

**AI-Powered Product Viability Assessment for Founders**

Go/No-Go is a comprehensive decision-support tool that helps founders evaluate product viability through AI-powered market research, competitor analysis, and unit economics simulation.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🎯 What It Does

Describe your product idea → Get a **GO / PILOT / NO-GO** verdict from an AI Advisory Board in minutes.

### The Verdicts

| Verdict | What It Means | When You'll See It |
|---------|---------------|-------------------|
| ✅ **GO** | Strong viability! Unit economics work, market opportunity exists. | Margin > 20%, favorable conditions |
| ⚠️ **PILOT** | Promising but risky. Test with small batch first. | Margin 10-20%, some concerns |
| ❌ **NO-GO** | Economics don't work. Pivot before proceeding. | Margin < 10%, red flags |

---

## 🤖 Meet Your AI Advisory Board

Four expert AI agents analyze your product and debate to reach a consensus:

| Agent | Role | What They Analyze |
|-------|------|-------------------|
| 🎯 **Maya** | CMO | Brand positioning, target audience, CAC/LTV, marketing channels |
| ♟️ **Arjun** | Strategy Consultant | Competitive moats, SWOT, Porter's Five Forces, differentiation |
| 🚀 **Vikram** | GTM/Sales Head | Launch sequence, Amazon/Flipkart tactics, 90-day playbook |
| 💰 **Priya** | CFO | Unit economics, break-even, funding path, financial risks |

### How The Board Works

1. **Individual Analysis** - Each agent analyzes from their expertise
2. **Board Discussion** - Agents debate, agree, and disagree (2 rounds)
3. **CEO Synthesis** - Final verdict with consensus points and risks
4. **Chat with Agents** - Deep dive with any agent for follow-up questions

---

## ✨ Features

### 🔍 Market Intelligence
- **Competitor Scraping** - Real-time data from Amazon India, Flipkart, BigBasket
- **Live Wholesale Prices** - IndiaMART scraping for real-time ingredient costs
- **Market Sizing** - TAM/SAM/SOM estimates for Indian market

### 💰 Dynamic Unit Economics
- **Platform-Specific Fees** - Actual fee structures from:
  - **Amazon India**: Referral fees (8-15%), closing fees, weight handling
  - **Flipkart**: Commission rates, fixed fees, shipping fees
  - **Quick Commerce**: Blinkit (30%), Zepto (28%), Swiggy Instamart (32%), BigBasket (25%)
- **AI-Powered Cost Estimation** - LLM analyzes your product to identify ingredients and estimate costs
- **73+ Raw Materials Database** - Wholesale prices for common FMCG ingredients
- **Category-Specific GST** - 0-18% based on product category
- **Multi-Carrier Logistics** - Delhivery, Bluedart, Xpressbees, Ecom Express rates
- **Smart Packaging Selection** - Auto-selects packaging type based on category and weight

### 🤖 AI Advisory Board
- **4 Specialized Agents** - CMO, Strategy, GTM, CFO perspectives
- **Real Debate** - Agents discuss and challenge each other
- **Agent Chat** - Ask follow-up questions to any expert

### 📊 Analysis & Visualization
- **Channel Comparison** - E-commerce vs Quick Commerce profitability
- **Cost Breakdown Charts** - Visual waterfall of all costs
- **Price Source Indicators** - Shows whether prices are live, from database, or AI-estimated

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: Groq (Llama 3.3 70B) / OpenAI (GPT-4o-mini)
- **Scraping**: BeautifulSoup4, Requests
- **Data Sources**: Amazon, Flipkart, BigBasket, IndiaMART
- **Visualization**: Plotly
- **Data**: Pandas

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Go-NoGo.git
cd Go-NoGo
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
# Optional: OPENAI_API_KEY=your_openai_api_key_here
```

Get your free Groq API key at: https://console.groq.com/

### 4. Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 📁 Project Structure

```
Go-NoGo/
├── app.py              # Main Streamlit application (3500+ lines)
│                       # - AI Advisory Board (4 agents)
│                       # - Dynamic Unit Economics Engine
│                       # - Competitor Scraping (Amazon, Flipkart, BigBasket)
│                       # - IndiaMART Price Scraping
│                       # - Platform Fee Calculators
├── requirements.txt    # Python dependencies
├── .env               # API keys (not in repo)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

---

## 🔑 API Keys

### Groq (Recommended - Free)
1. Go to https://console.groq.com/
2. Sign up and create an API key
3. Add to `.env` as `GROQ_API_KEY`

### OpenAI (Optional)
1. Go to https://platform.openai.com/
2. Create an API key
3. Add to `.env` as `OPENAI_API_KEY`

---

## 📊 Unit Economics Engine

### Platform Fee Structures (Real Data)

| Platform | Commission | Other Fees |
|----------|------------|------------|
| **Amazon India** | 8-15% referral | ₹21-51 closing + weight handling |
| **Flipkart** | 5-14% commission | Fixed fees + shipping |
| **Blinkit** | 30% | Included logistics |
| **Zepto** | 28% | Included logistics |
| **Swiggy Instamart** | 32% | Included logistics |
| **BigBasket** | 25% | Included logistics |

### Raw Material Pricing Sources

1. **IndiaMART Live Scraping** - Real-time wholesale prices (primary source)
2. **Built-in Database** - 73+ ingredients with wholesale prices (fallback)
3. **AI Estimation** - LLM-based pricing when other sources unavailable

### Category-Specific Rates

| Category | GST Rate | Return Rate | Mfg Overhead |
|----------|----------|-------------|--------------|
| Packaged Snacks | 12% | 3% | 35% |
| Personal Care | 18% | 5% | 40% |
| Supplements | 18% | 4% | 55% |
| Beverages | 12% | 2% | 30% |
| Fresh Food | 0% | 8% | 25% |

### Logistics Partners

| Carrier | Local | Regional | National |
|---------|-------|----------|----------|
| Delhivery | ₹35 | ₹50 | ₹70 |
| Bluedart | ₹45 | ₹65 | ₹85 |
| Xpressbees | ₹30 | ₹45 | ₹60 |
| Ecom Express | ₹32 | ₹48 | ₹65 |

---

## 🧠 Agent Knowledge Base

Each agent is equipped with:

- **Maya (Marketing)**: STP framework, AIDA funnel, CAC/LTV ratios, Hero SKU strategy
- **Arjun (Strategy)**: Porter's Five Forces, BCG Matrix, Blue Ocean, Moat Analysis
- **Vikram (GTM)**: Amazon First strategy, 100 Reviews Rule, Price Ladder, Lightning Deal Loop
- **Priya (Finance)**: Unit Economics Waterfall, CAC Payback, Burn Multiple, Funding stages

Real Indian D2C case studies: Mamaearth, Boat, Licious, Nykaa, Yogabar, Sugar Cosmetics

---

## 🚢 Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect your GitHub repo
4. Add secrets in Streamlit Cloud dashboard:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
5. Deploy!

---

## 📝 Example Usage

**Input:**
```
A premium millet-based snack brand targeting health-conscious urban millennials. 
100g pack of baked ragi chips with no added sugar, priced at ₹149.
Positioned as a guilt-free alternative to fried chips.
```

**Output:**
- ✅ **GO** with 85% confidence
- Target: Urban millennials, 25-35, metros, health-conscious
- Channel: Amazon first, then Quick Commerce
- Margin: 22.4% (healthy)
- Risk: Crowded healthy snacks category

### Unit Economics Breakdown (Dynamic)
```
MRP: ₹149
├── Raw Materials: ₹18.50 (via IndiaMART live prices)
├── Packaging: ₹11.33 (auto-selected pouch)
├── Platform Fees: ₹37.25 (Amazon referral + closing)
├── Logistics: ₹45.00 (Delhivery national)
├── Returns: ₹4.47 (3% @ category rate)
├── GST: ₹17.88 (12% for snacks)
└── Net Margin: ₹14.57 (9.8%)
```

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- Add more competitor sources
- Enhance agent knowledge with case studies
- Improve scraping reliability
- Add new analysis features

---

## 📄 License

MIT License - feel free to use for your own projects!

---

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for free LLM API
- [Streamlit](https://streamlit.io/) for the awesome framework
- Indian D2C ecosystem for inspiration

---

**Built with ❤️ for founders who value clarity over optimism**
