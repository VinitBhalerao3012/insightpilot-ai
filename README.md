# InsightPilot AI — AI-Powered Business Analyst Agent

An AI-powered data analysis tool that lets you upload any CSV dataset and ask business questions in plain English. Powered by Groq/Llama 3.3 AI.

## Features
- Upload any CSV dataset
- Automatic data profiling and quality report
- KPI detection and statistical summary
- SQL Playground — run queries directly on your data
- AI-powered Q&A — ask any business question in plain English
- AI generates and executes real pandas code automatically

## Tools & Technologies
- Python, Streamlit, Pandas, DuckDB
- Groq API (Llama 3.3 70B)
- Natural Language to Code generation

## ⚙️ How to Run Locally
1. Clone the repo
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Get a free API key from console.groq.com
4. Set your key:
```bash
export GROQ_API_KEY=your_key_here
```
5. Run the app:
```bash
python -m streamlit run app.py
```

## Author
**Vinit Bhalerao**
Data Analyst | Python | SQL | Power BI | AI
[LinkedIn](https://linkedin.com/in/bhalerao-vinit3013) | [Portfolio](https://vinitbportfolio.netlify.app)