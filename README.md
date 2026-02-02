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

- 🔍 **Competitor Scraping** - Real-time data from Amazon India, Flipkart, BigBasket
- 📊 **Market Sizing** - TAM/SAM/SOM estimates for Indian market
- 💰 **Unit Economics Calculator** - Manufacturing, platform fees, logistics, returns, GST
- 🤖 **Multi-Agent AI Board** - 4 specialized agents with real frameworks
- 💬 **Agent Chat** - Ask follow-up questions to any expert
- 📈 **Channel Comparison** - E-commerce vs Quick Commerce analysis

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: Groq (Llama 3.3 70B) / OpenAI (GPT-4o-mini)
- **Scraping**: BeautifulSoup4, Requests
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
├── app.py              # Main Streamlit application
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

## 📊 Unit Economics Benchmarks

The app uses these default assumptions (editable in sidebar):

| Category | Manufacturing (₹/g) | Packaging (₹/unit) |
|----------|--------------------|--------------------|
| Packaged Snacks | 0.15 | 8 |
| Personal Care | 0.25 | 15 |
| Supplements | 0.50 | 20 |
| Beverages | 0.10 | 12 |

| Channel | Platform Fee | Logistics | Returns |
|---------|-------------|-----------|---------|
| E-commerce | 25% | ₹45 | 8% |
| Quick Commerce | 35% | ₹25 | 3% |

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
