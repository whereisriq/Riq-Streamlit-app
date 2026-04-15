import os
os.environ["RICH_DISABLE"] = "true"
os.environ["CREWAI_DISABLE_RICH"] = "1"

import io
import streamlit as st
import pandas as pd
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial Report Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background: #f0faf4; color: #0f2a1a; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0a1f12 !important;
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #c8e6d0 !important; }
section[data-testid="stSidebar"] h3 { color: #4ade80 !important; }
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #132b1a !important;
    border-color: #1f4a28 !important;
    color: #c8e6d0 !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: .82rem !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0a1f12 0%, #0d3320 60%, #0a2a1a 100%);
    border-radius: 20px;
    padding: 3rem 3.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -80px; right: -80px;
    width: 320px; height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, #4ade8022, transparent 65%);
}
.hero::after {
    content: "💹";
    position: absolute;
    right: 3.5rem; top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: .15;
}
.hero h1 {
    font-size: 2.7rem;
    font-weight: 800;
    color: #f0faf4;
    margin: 0 0 .4rem;
    letter-spacing: -.5px;
    line-height: 1.15;
}
.hero h1 span { color: #4ade80; }
.hero p {
    color: #5a8a6a;
    font-family: 'Space Mono', monospace;
    font-size: .82rem;
    margin: 0;
}

/* ── KPI cards ── */
.kpi-row { display:flex; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.kpi-card {
    flex: 1; min-width: 150px;
    background: white;
    border-radius: 16px;
    padding: 1.3rem 1.5rem;
    box-shadow: 0 2px 16px rgba(0,80,30,.07);
    border-top: 4px solid #4ade80;
    position: relative;
    overflow: hidden;
}
.kpi-card.red   { border-top-color: #f87171; }
.kpi-card.blue  { border-top-color: #60a5fa; }
.kpi-card.amber { border-top-color: #fbbf24; }
.kpi-label {
    font-size: .7rem;
    text-transform: uppercase;
    letter-spacing: .12em;
    font-weight: 700;
    color: #6b9e7a;
    margin-bottom: .4rem;
}
.kpi-value {
    font-size: 1.85rem;
    font-weight: 800;
    color: #0a1f12;
    font-family: 'Space Mono', monospace;
    line-height: 1;
}
.kpi-value.positive { color: #16a34a; }
.kpi-value.negative { color: #dc2626; }
.kpi-sub {
    font-size: .73rem;
    color: #aaa;
    margin-top: .3rem;
}

/* ── Section title ── */
.sec-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0a1f12;
    margin: 2rem 0 .8rem;
    display: flex;
    align-items: center;
    gap: .5rem;
    border-left: 4px solid #4ade80;
    padding-left: .8rem;
}

/* ── Chart container ── */
.chart-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 16px rgba(0,80,30,.07);
    margin-bottom: 1rem;
}

/* ── Data table ── */
.fin-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,80,30,.07);
    margin-bottom: 1.5rem;
}
.fin-table th {
    background: #0a1f12;
    color: #4ade80;
    padding: .75rem 1.1rem;
    text-align: left;
    font-size: .75rem;
    text-transform: uppercase;
    letter-spacing: .08em;
}
.fin-table td {
    padding: .65rem 1.1rem;
    border-bottom: 1px solid #f0faf4;
    font-size: .88rem;
    color: #1a3a22;
}
.fin-table tr:last-child td { border-bottom: none; }
.fin-table tr:hover td { background: #f6fef8; }
.pos { color: #16a34a; font-weight: 600; font-family: 'Space Mono', monospace; font-size:.85rem; }
.neg { color: #dc2626; font-weight: 600; font-family: 'Space Mono', monospace; font-size:.85rem; }

/* ── Report box ── */
.report-wrap {
    background: white;
    border-radius: 18px;
    padding: 2.4rem 2.8rem;
    box-shadow: 0 4px 24px rgba(0,80,30,.09);
    line-height: 1.8;
    font-size: .95rem;
    color: #1a3a22;
    white-space: pre-wrap;
}
.report-tag {
    font-family: 'Space Mono', monospace;
    font-size: .7rem;
    color: #6b9e7a;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: .6rem;
}

/* ── Info box ── */
.info-box {
    background: #dcfce7;
    border-left: 4px solid #4ade80;
    border-radius: 8px;
    padding: .85rem 1.2rem;
    font-size: .87rem;
    color: #14532d;
    margin-bottom: 1rem;
}

/* ── Run button ── */
div.stButton > button {
    background: linear-gradient(135deg, #16a34a, #4ade80);
    color: #0a1f12;
    border: none;
    border-radius: 12px;
    padding: .75rem 2rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    width: 100%;
    transition: opacity .2s;
    letter-spacing: .01em;
}
div.stButton > button:hover { opacity: .85; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
    background: white;
    color: #16a34a;
    border: 2px solid #4ade80;
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── File uploader ── */
section[data-testid="stFileUploadDropzone"] {
    background: white !important;
    border: 2px dashed #86efac !important;
    border-radius: 14px !important;
}

hr { border-color: #d1fae5; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def detect_columns(df):
    """Detect income, expense, amount, and category columns heuristically."""
    cols = [c.lower() for c in df.columns]
    original = list(df.columns)

    income_col   = next((original[i] for i, c in enumerate(cols) if "income"  in c), None)
    expense_col  = next((original[i] for i, c in enumerate(cols) if "expense" in c or "cost" in c or "spend" in c), None)
    amount_col   = next((original[i] for i, c in enumerate(cols) if "amount"  in c or "value" in c or "total" in c), None)
    type_col     = next((original[i] for i, c in enumerate(cols) if "type"    in c or "category" in c or "kind" in c), None)
    date_col     = next((original[i] for i, c in enumerate(cols) if "date"    in c or "month"    in c or "period" in c), None)

    return {
        "income":   income_col,
        "expense":  expense_col,
        "amount":   amount_col,
        "type":     type_col,
        "date":     date_col,
    }


def compute_kpis(df, detected):
    """Return basic KPIs from the dataframe."""
    kpis = {}

    # Case 1: separate income & expense columns
    if detected["income"] and detected["expense"]:
        try:
            inc = pd.to_numeric(df[detected["income"]], errors="coerce").sum()
            exp = pd.to_numeric(df[detected["expense"]], errors="coerce").sum()
            kpis = {"total_income": inc, "total_expenses": exp, "net_balance": inc - exp}
        except Exception:
            pass

    # Case 2: amount + type column (Income / Expense labels)
    elif detected["amount"] and detected["type"]:
        try:
            df["_amt"] = pd.to_numeric(df[detected["amount"]], errors="coerce")
            type_vals = df[detected["type"]].str.lower()
            inc = df.loc[type_vals.str.contains("income|revenue|credit", na=False), "_amt"].sum()
            exp = df.loc[type_vals.str.contains("expense|debit|cost|spend", na=False), "_amt"].sum()
            kpis = {"total_income": inc, "total_expenses": exp, "net_balance": inc - exp}
        except Exception:
            pass

    # Case 3: just numeric columns — sum them all
    if not kpis:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            total = df[numeric_cols].sum().sum()
            kpis = {"total_income": None, "total_expenses": None, "net_balance": total}

    return kpis


def fmt(val):
    if val is None:
        return "N/A"
    return f"${val:,.2f}"


# ── Crew runner ───────────────────────────────────────────────────────────────
def run_crew(df: pd.DataFrame, file_name: str) -> str:
    from dotenv import load_dotenv
    load_dotenv()
    from crewai import Agent, Task, Crew, Process
    from crewai.llm import LLM

    llm = LLM(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.5,
        base_url="https://api.groq.com/openai/v1",
    )

    preview = df.head(50).to_dict()

    analyzer = Agent(
        role="Financial Data Analyzer",
        goal="Analyze income and expense data to assess financial health",
        backstory=(
            "You are a finance expert who interprets company or personal financial data. "
            "You identify trends, compute key ratios, and summarize overall financial status "
            "clearly and accurately."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )

    reporter = Agent(
        role="Financial Report Writer",
        goal="Create a clear, structured summary of financial health",
        backstory=(
            "You are a professional financial writer who converts analysis into readable insights. "
            "Your summaries include clear takeaways, trends, and actionable points."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )

    analysis_task = Task(
        description=f"""
Analyze this financial dataset and provide a structured overview.

CSV: {file_name}

DATA PREVIEW:
{preview}

Compute:
1. Total income
2. Total expenses
3. Net balance
4. Key trends and anomalies
5. Any potential risks or opportunities

Present your analysis in bullet points or tables where appropriate.
""",
        agent=analyzer,
        expected_output=(
            "Structured financial analysis including totals, net balance, "
            "trends/anomalies, and risk/opportunity insights."
        ),
    )

    reporting_task = Task(
        description="""
Based on the financial analysis, create a concise report summarizing financial health.

Include:
1. Key financial metrics (income, expenses, net balance)
2. Observed trends (positive or negative)
3. Recommendations or notes for improvement
4. Clear sections or bullet points

Write professionally, clearly, and ensure it is easy to understand.
""",
        agent=reporter,
        expected_output=(
            "Polished financial summary report (250-400 words) with metrics overview, "
            "trend analysis, recommendations, and structured readable format."
        ),
        context=[analysis_task],
    )

    crew = Crew(
        agents=[analyzer, reporter],
        tasks=[analysis_task, reporting_task],
        process=Process.sequential,
        verbose=False,
    )

    return str(crew.kickoff())


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    groq_key = st.text_input(
        "GROQ API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Paste your Groq key or add to .env",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    st.markdown("---")
    st.markdown("### 💾 Export")
    save_report = st.checkbox("Enable download buttons", value=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:.77rem;color:#4a7a5a;font-family:Space Mono,monospace;line-height:1.9'>
    Model: llama-3.1-8b-instant<br>
    Provider: Groq<br>
    Orchestration: CrewAI<br>
    Agents: Analyzer · Reporter
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Supported CSV Formats")
    st.markdown("""
    <div style='font-size:.8rem;color:#4a7a5a;line-height:1.8'>
    ✅ Income + Expense columns<br>
    ✅ Amount + Type column<br>
    ✅ Any numeric financial data<br><br>
    <span style='font-family:Space Mono,monospace;font-size:.73rem'>
    Date,Description,Income,Expense<br>
    2024-01,Sales,5000,<br>
    2024-01,Rent,,1200
    </span>
    </div>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>Financial Report <span>Analyzer</span></h1>
  <p>Upload CSV → AI analyzes income & expenses → Generates financial health report</p>
</div>
""", unsafe_allow_html=True)


# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload financial CSV",
    type=["csv"],
    label_visibility="collapsed",
)

df = None

if uploaded:
    try:
        raw = uploaded.read()
        df = pd.read_csv(io.BytesIO(raw))

        if df.empty:
            st.error("❌ The CSV file is empty.")
            st.stop()

        detected = detect_columns(df)
        kpis = compute_kpis(df, detected)

        # ── KPI Cards ──
        st.markdown('<div class="sec-title">💰 Financial Overview</div>', unsafe_allow_html=True)

        net = kpis.get("net_balance")
        net_class = "positive" if net and net >= 0 else "negative"
        net_label = "Surplus" if net and net >= 0 else "Deficit"

        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi-card">
            <div class="kpi-label">Total Income</div>
            <div class="kpi-value positive">{fmt(kpis.get('total_income'))}</div>
            <div class="kpi-sub">Revenue / Credits</div>
          </div>
          <div class="kpi-card red">
            <div class="kpi-label">Total Expenses</div>
            <div class="kpi-value negative">{fmt(kpis.get('total_expenses'))}</div>
            <div class="kpi-sub">Costs / Debits</div>
          </div>
          <div class="kpi-card {'blue' if net and net >= 0 else 'amber'}">
            <div class="kpi-label">Net Balance</div>
            <div class="kpi-value {net_class}">{fmt(net)}</div>
            <div class="kpi-sub">{net_label}</div>
          </div>
          <div class="kpi-card amber">
            <div class="kpi-label">Total Rows</div>
            <div class="kpi-value">{len(df):,}</div>
            <div class="kpi-sub">{len(df.columns)} columns</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Numeric column summary table ──
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            st.markdown('<div class="sec-title">📊 Column Summary</div>', unsafe_allow_html=True)

            rows_html = ""
            for col in numeric_cols:
                total = df[col].sum()
                avg   = df[col].mean()
                mn    = df[col].min()
                mx    = df[col].max()
                cls   = "pos" if total >= 0 else "neg"
                sign  = "+" if total >= 0 else ""
                rows_html += f"""
                <tr>
                  <td><strong>{col}</strong></td>
                  <td class="{cls}">{sign}${total:,.2f}</td>
                  <td>${avg:,.2f}</td>
                  <td>${mn:,.2f}</td>
                  <td>${mx:,.2f}</td>
                </tr>"""

            st.markdown(f"""
            <table class="fin-table">
              <thead><tr>
                <th>Column</th><th>Total</th><th>Average</th><th>Min</th><th>Max</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)

        # ── Charts ──
        if numeric_cols:
            st.markdown('<div class="sec-title">📈 Visualizations</div>', unsafe_allow_html=True)

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.caption("Column Totals")
                totals = df[numeric_cols].sum()
                st.bar_chart(totals, color="#4ade80")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_b:
                # Date/trend chart if date column exists
                date_col = detected.get("date")
                if date_col and date_col in df.columns:
                    try:
                        df["_date"] = pd.to_datetime(df[date_col], errors="coerce")
                        trend = df.groupby("_date")[numeric_cols].sum()
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        st.caption(f"Trend over {date_col}")
                        st.line_chart(trend, color=["#4ade80", "#f87171", "#60a5fa"][:len(numeric_cols)])
                        st.markdown('</div>', unsafe_allow_html=True)
                    except Exception:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        st.caption("Column Distribution")
                        st.area_chart(df[numeric_cols].describe().loc[["mean", "min", "max"]].T, color="#4ade80")
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                    st.caption("Row-level trend (first 50 rows)")
                    st.line_chart(df[numeric_cols].head(50), color=["#4ade80", "#f87171", "#60a5fa"][:len(numeric_cols)])
                    st.markdown('</div>', unsafe_allow_html=True)

        # ── Raw data preview ──
        with st.expander("👁️  Preview raw data"):
            st.dataframe(df, width='stretch', height=260)

        st.markdown("---")
        st.markdown("""
        <div class="info-box">
        🤖 The AI crew runs <strong>2 agents in sequence</strong>: 
        Financial Analyzer → Report Writer. 
        This typically takes <strong>1–3 minutes</strong>.
        </div>
        """, unsafe_allow_html=True)

        run_btn = st.button("🚀  Analyze & Generate Report", width='stretch')

        if run_btn:
            if not os.getenv("GROQ_API_KEY"):
                st.error("❌ Please enter your GROQ API key in the sidebar.")
                st.stop()

            with st.spinner("🤖 Agents at work — Analyzer → Reporter…"):
                try:
                    result = run_crew(df, uploaded.name)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.stop()

            # ── Report output ──
            st.markdown('<div class="sec-title">📝 Financial Report</div>', unsafe_allow_html=True)
            st.markdown('<div class="report-tag">AI-generated · Analyzer · Reporter</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-wrap">{result}</div>', unsafe_allow_html=True)

            st.markdown("")

            if save_report:
                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "⬇️ Download Report (.txt)",
                        data=result,
                        file_name="financial_report.txt",
                        mime="text/plain",
                        width='stretch',
                    )

                with col2:
                    # Quick stats export
                    stats_lines = f"FINANCIAL QUICK STATS\n{'='*50}\n\n"
                    stats_lines += f"File: {uploaded.name}\n"
                    stats_lines += f"Rows: {len(df)} | Columns: {len(df.columns)}\n\n"
                    if kpis.get("total_income") is not None:
                        stats_lines += f"Total Income:   {fmt(kpis['total_income'])}\n"
                        stats_lines += f"Total Expenses: {fmt(kpis['total_expenses'])}\n"
                    stats_lines += f"Net Balance:    {fmt(kpis.get('net_balance'))}\n\n"
                    stats_lines += "Column Totals:\n"
                    for col in numeric_cols:
                        stats_lines += f"  {col}: ${df[col].sum():,.2f}\n"

                    st.download_button(
                        "⬇️ Download Stats (.txt)",
                        data=stats_lines,
                        file_name="financial_stats.txt",
                        mime="text/plain",
                        width='stretch',
                    )

            st.success("✅ Report generated successfully!")

    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")

else:
    # Empty state
    st.markdown("""
    <div style="text-align:center;padding:3.5rem;background:white;border-radius:18px;
    border:2px dashed #86efac;color:#aaa;box-shadow:0 2px 16px rgba(0,80,30,.06)">
      <div style="font-size:4rem;margin-bottom:1rem">📂</div>
      <div style="font-size:1.25rem;font-weight:700;color:#2d6a40;margin-bottom:.4rem">
        Upload a financial CSV to get started
      </div>
      <div style="font-size:.88rem;color:#86a893">
        Supports income/expense reports, transaction logs, budget sheets
      </div>
    </div>
    """, unsafe_allow_html=True)