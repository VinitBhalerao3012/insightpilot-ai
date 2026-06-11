import streamlit as st
import pandas as pd
import duckdb
import os
from groq import Groq



st.set_page_config(
    page_title="InsightPilot AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 InsightPilot AI")
st.subheader("AI Business Analyst Agent")

# ── AI FUNCTION ──────────────────────────────────────────────
def ask_groq(question: str, df: pd.DataFrame, conn) -> dict:
    """Send question + dataset context to Groq AI."""

    # Build schema context
    schema_lines = []
    for col in df.columns:
        if df[col].dtype == "object":
            samples = df[col].dropna().unique()[:4].tolist()
            schema_lines.append(f"  - {col} (text): examples = {samples}")
        else:
            schema_lines.append(
                f"  - {col} (numeric): "
                f"min={df[col].min()}, "
                f"max={df[col].max()}, "
                f"avg={round(df[col].mean(), 2)}"
            )

    schema_text = "\n".join(schema_lines)

    prompt = f"""You are an expert data analyst. A user uploaded a CSV with {len(df)} rows and {len(df.columns)} columns.

Dataset schema:
{schema_text}

The dataframe is in a variable called `df`.
The data is also in a DuckDB SQL table called `data` accessible via `conn.execute()`.

User question: {question}

Instructions:
1. Write Python code using pandas to answer the question
2. Store the final answer in a variable called `result`
3. `result` must be a string, number, or pandas DataFrame
4. After the code, write a 2-3 sentence plain English business insight

Use EXACTLY this format:
CODE:
```python
result = ...
```
INSIGHT:
Your plain English business insight here."""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )

    response = chat.choices[0].message.content

    # Parse CODE and INSIGHT
    code_part = ""
    insight_part = ""

    if "CODE:" in response and "INSIGHT:" in response:
        code_section = response.split("INSIGHT:")[0].replace("CODE:", "").strip()
        insight_part = response.split("INSIGHT:")[1].strip()

        if "```python" in code_section:
            code_part = code_section.split("```python")[1].split("```")[0].strip()
        else:
            code_part = code_section.strip()
    else:
        insight_part = response

    return {"code": code_part, "insight": insight_part}

# ── FILE UPLOAD ───────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📁 Upload your CSV file",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)
    conn = duckdb.connect()
    conn.register("data", df)

    st.success("Dataset uploaded successfully!")

    # ── DATASET PREVIEW ───────────────────────────────────────
    st.write("## Dataset Preview")
    st.dataframe(df.head())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", df.shape[0])
    with col2:
        st.metric("Columns", df.shape[1])
    with col3:
        st.metric("Missing Values", df.isnull().sum().sum())

    # ── DATASET PROFILE ───────────────────────────────────────
    st.write("## Dataset Profile")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    profile_col1, profile_col2, profile_col3 = st.columns(3)
    with profile_col1:
        st.metric("Numeric Columns", len(numeric_cols))
    with profile_col2:
        st.metric("Categorical Columns", len(categorical_cols))
    with profile_col3:
        st.metric("Date Columns", 0)

    st.write("### Numeric Columns")
    st.write(numeric_cols)
    st.write("### Categorical Columns")
    st.write(categorical_cols)

    # ── DATA QUALITY REPORT ───────────────────────────────────
    st.write("## Data Quality Report")

    total_missing = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()

    quality_col1, quality_col2 = st.columns(2)
    with quality_col1:
        st.metric("Missing Values", total_missing)
    with quality_col2:
        st.metric("Duplicate Rows", duplicate_rows)

    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Values": df.isnull().sum().values,
        "Missing %": ((df.isnull().sum().values / len(df)) * 100).round(2)
    })

    st.write("### Missing Value Analysis")
    st.dataframe(missing_df.sort_values(by="Missing Values", ascending=False))

    # ── KPI DETECTION ─────────────────────────────────────────
    st.write("## KPI Detection")

    kpi_keywords = [
        "sales", "revenue", "profit", "income", "cost",
        "quantity", "salary", "rate", "score",
        "satisfaction", "performance"
    ]

    detected_kpis = []
    for col in df.columns:
        for keyword in kpi_keywords:
            if keyword in col.lower():
                detected_kpis.append(col)
                break

    if detected_kpis:
        st.success(f"{len(detected_kpis)} KPI columns detected")
        st.write(detected_kpis)
    else:
        st.warning("No KPI columns automatically detected")

    # ── KPI STATISTICAL SUMMARY ───────────────────────────────
    st.write("## KPI Statistical Summary")

    if detected_kpis:
        kpi_summary = df[detected_kpis].describe().T
        kpi_summary = kpi_summary[["mean", "min", "50%", "max", "std"]]
        kpi_summary = kpi_summary.rename(columns={
            "mean": "Average", "min": "Minimum",
            "50%": "Median", "max": "Maximum",
            "std": "Standard Deviation"
        })
        st.dataframe(kpi_summary)
    else:
        st.warning("No KPI columns available for statistical summary.")

    # ── SQL PLAYGROUND ────────────────────────────────────────
    st.write("## SQL Playground")
    st.info("Your uploaded CSV is available as a SQL table named `data`.")

    sql_query = st.text_area(
        "Enter SQL query",
        value="SELECT * FROM data LIMIT 10",
        height=160
    )

    if st.button("Run SQL Query"):
        try:
            result = conn.execute(sql_query).fetchdf()
            st.success("SQL query executed successfully.")
            st.dataframe(result)
        except Exception as e:
            st.error(f"SQL Error: {e}")

    # ── AI — ASK YOUR DATA ────────────────────────────────────
    st.write("## 🤖 Ask Your Data (Powered by Groq AI)")
    st.caption("Ask any business question in plain English — Llama 3.3 AI will analyse your data instantly.")

    with st.expander("💡 Example questions you can ask"):
        st.write("""
        - Which department has the highest attrition rate?
        - What is the average monthly income by job role?
        - How many employees work overtime?
        - What percentage of employees left the company?
        - What is the attrition rate by gender?
        - Which job role has the lowest job satisfaction?
        - What is the average age of employees who left vs stayed?
        - Show top 5 departments by average salary
        """)

    user_question = st.text_input(
        "Ask a business question about your dataset",
        placeholder="e.g. Which department has highest attrition rate?",
        key="ai_question"
    )

    if user_question:
        with st.spinner("🤖 AI is analysing your data..."):
            try:
                response = ask_groq(user_question, df, conn)

                # Show AI insight
                st.success(f"**💡 AI Insight:** {response['insight']}")

                # Show and execute generated code
                if response["code"]:
                    with st.expander("🔍 View AI-generated analysis code"):
                        st.code(response["code"], language="python")

                    # Execute code safely
                    local_vars = {
                        "df": df,
                        "conn": conn,
                        "pd": pd
                    }
                    try:
                        exec(response["code"], {}, local_vars)
                        result = local_vars.get("result")

                        if result is not None:
                            st.write("### 📊 Analysis Result")
                            if isinstance(result, pd.DataFrame):
                                st.dataframe(result)
                            else:
                                st.write(result)

                    except Exception as e:
                        st.warning(f"Could not execute generated code: {e}")

            except Exception as e:
                st.error(f"AI Error: {e}")
                st.info("Make sure GROQ_API_KEY is set in your .env file")

else:
    st.info("Upload a CSV file to begin analysis.")