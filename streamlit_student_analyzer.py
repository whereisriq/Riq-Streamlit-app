import os
os.environ["RICH_DISABLE"] = "true"
os.environ["CREWAI_DISABLE_RICH"] = "1"

import csv
import io
import tempfile
import streamlit as st
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Analyzer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #f5f3ee; color: #1a1a2e; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #e8e4d9 !important; }
section[data-testid="stSidebar"] .stMarkdown h3 { color: #f5c842 !important; }
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #252540 !important;
    border-color: #3a3a5c !important;
    color: #e8e4d9 !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: .83rem !important;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #1a1a2e 60%, #2d1b69 100%);
    border-radius: 20px;
    padding: 3rem 3.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "🎓";
    position: absolute;
    right: 3rem; top: 50%;
    transform: translateY(-50%);
    font-size: 7rem;
    opacity: .12;
}
.hero h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    color: #f5f3ee;
    margin: 0 0 .5rem;
    line-height: 1.15;
}
.hero h1 span { color: #f5c842; }
.hero p {
    color: #9b98b8;
    font-size: .9rem;
    font-family: 'DM Mono', monospace;
    margin: 0;
}

/* Stat cards */
.stat-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat-card {
    flex: 1; min-width: 140px;
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    border-left: 4px solid #2d1b69;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
}
.stat-card .label {
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: #888;
    font-weight: 600;
    margin-bottom: .3rem;
}
.stat-card .value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.9rem;
    color: #1a1a2e;
    line-height: 1;
}
.stat-card .sub {
    font-size: .75rem;
    color: #aaa;
    margin-top: .2rem;
}

/* Subject table */
.subject-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
    margin-bottom: 1.5rem;
}
.subject-table th {
    background: #1a1a2e;
    color: #f5c842;
    padding: .8rem 1.2rem;
    text-align: left;
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: .08em;
    font-weight: 600;
}
.subject-table td {
    padding: .75rem 1.2rem;
    border-bottom: 1px solid #f0ede8;
    font-size: .9rem;
    color: #2a2a3e;
}
.subject-table tr:last-child td { border-bottom: none; }
.subject-table tr:hover td { background: #faf9f5; }

/* Progress bar */
.bar-wrap { background: #eee; border-radius: 100px; height: 8px; overflow: hidden; }
.bar-fill  { height: 8px; border-radius: 100px; background: linear-gradient(90deg,#2d1b69,#7c3aed); }

/* Report box */
.report-box {
    background: white;
    border-radius: 16px;
    padding: 2.4rem 2.8rem;
    box-shadow: 0 4px 24px rgba(0,0,0,.08);
    line-height: 1.8;
    font-size: .95rem;
    color: #2a2a3e;
    white-space: pre-wrap;
    font-family: 'DM Sans', sans-serif;
}
.report-label {
    font-family: 'DM Mono', monospace;
    font-size: .72rem;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: .6rem;
}

/* Section heading */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.35rem;
    color: #1a1a2e;
    margin: 1.8rem 0 .8rem;
    display: flex;
    align-items: center;
    gap: .5rem;
}

/* Run button */
div.stButton > button {
    background: linear-gradient(135deg, #2d1b69, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    padding: .7rem 2rem;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
    letter-spacing: .01em;
    transition: opacity .2s;
}
div.stButton > button:hover { opacity: .85; }

/* Download button */
div[data-testid="stDownloadButton"] button {
    background: white;
    color: #2d1b69;
    border: 2px solid #2d1b69;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    width: 100%;
}

/* Uploader */
section[data-testid="stFileUploadDropzone"] {
    background: white !important;
    border: 2px dashed #c8c4d8 !important;
    border-radius: 12px !important;
}

/* Status badge */
.badge-ok  { display:inline-block; background:#d1fae5; color:#065f46; border-radius:100px; padding:.2rem .8rem; font-size:.78rem; font-weight:600; }
.badge-err { display:inline-block; background:#fee2e2; color:#991b1b; border-radius:100px; padding:.2rem .8rem; font-size:.78rem; font-weight:600; }

/* Alert box */
.info-box {
    background: #ede9fe;
    border-left: 4px solid #7c3aed;
    border-radius: 8px;
    padding: .9rem 1.2rem;
    font-size: .88rem;
    color: #4c1d95;
    margin-bottom: 1rem;
}

hr { border-color: #e8e4d9; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_csv_bytes(raw_bytes: bytes):
    text = raw_bytes.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    data = list(reader)
    return data


def compute_stats(data):
    if not data:
        return {}
    headers = list(data[0].keys())
    numeric_cols = []
    for h in headers:
        try:
            float(data[0][h])
            numeric_cols.append(h)
        except (ValueError, KeyError):
            pass

    stats = {}
    for col in numeric_cols:
        vals = []
        for row in data:
            try:
                vals.append(float(row[col]))
            except (ValueError, KeyError):
                pass
        if vals:
            stats[col] = {
                "min": min(vals),
                "max": max(vals),
                "avg": sum(vals) / len(vals),
                "count": len(vals),
            }
    return stats, numeric_cols, headers


def format_for_agent(data, stats, numeric_cols, headers):
    summary = f"""
CSV DATA SUMMARY:
================
Total Students: {len(data)}
Columns: {', '.join(headers)}
Score Columns: {', '.join(numeric_cols)}

STATISTICS:
"""
    for col, s in stats.items():
        summary += f"\n{col}:"
        summary += f"\n  - Average: {s['avg']:.2f}"
        summary += f"\n  - Minimum: {s['min']:.2f}"
        summary += f"\n  - Maximum: {s['max']:.2f}"

    summary += "\n\nSAMPLE DATA (First 10 students):\n" + "=" * 50 + "\n"
    for i, row in enumerate(data[:10], 1):
        summary += f"\nStudent {i}:\n"
        for k, v in row.items():
            summary += f"  {k}: {v}\n"
    if len(data) > 10:
        summary += f"\n... and {len(data) - 10} more students"
    return summary


# ── Crew runner ───────────────────────────────────────────────────────────────
def run_crew(data_summary: str):
    from dotenv import load_dotenv
    load_dotenv()
    from crewai import Agent, Task, Crew, Process
    from crewai.llm import LLM

    llm = LLM(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.6,
        base_url="https://api.groq.com/openai/v1",
    )

    analyst = Agent(
        role="Student Performance Data Analyst",
        goal="Analyze student scores, identify patterns, trends, and performance insights",
        backstory=(
            "You are an experienced educational data analyst with expertise in interpreting "
            "student performance metrics. You identify patterns, trends, strengths, and "
            "weaknesses using statistical thinking and educational psychology."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )
    educator = Agent(
        role="Educational Advisor",
        goal="Provide actionable recommendations for improving student performance",
        backstory=(
            "You are a seasoned educator with 15 years of teaching experience. "
            "You provide practical, evidence-based recommendations that teachers can implement."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )
    writer = Agent(
        role="Educational Report Writer",
        goal="Create clear, comprehensive reports for teachers and administrators",
        backstory=(
            "You communicate data insights to educators through clear, jargon-free reports "
            "that are actionable and help educators make informed decisions."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )

    analysis_task = Task(
        description=f"""
Analyze the following student performance data:

{data_summary}

Include:
1. Overall performance assessment and score distribution
2. Subject-specific insights (highest/lowest averages, most variation)
3. Patterns and trends (correlations, high vs struggling students)
4. Key concerns (at-risk students, subjects needing urgent attention)

Be specific with numbers from the data.
""",
        agent=analyst,
        expected_output="Comprehensive analysis with overall assessment, subject insights, patterns, and concerns.",
    )

    recommendations_task = Task(
        description="""
Based on the analysis, generate actionable recommendations covering:
1. Immediate interventions and priority students
2. Instructional strategies for weak subjects
3. Assessment improvements
4. Student support programs (tutoring, peer learning)
5. Monitoring plan with timeline
""",
        agent=educator,
        expected_output="Practical recommendations with immediate actions, strategies, and monitoring plan.",
        context=[analysis_task],
    )

    report_task = Task(
        description="""
Write a comprehensive Student Performance Report (800-1000 words) with:
1. EXECUTIVE SUMMARY (100-150 words) — snapshot, key findings, critical actions
2. PERFORMANCE ANALYSIS (300-400 words) — detailed breakdown with numbers
3. KEY INSIGHTS (150-200 words) — patterns, concerns, achievements
4. RECOMMENDATIONS (250-300 words) — immediate, short-term, long-term actions
5. CONCLUSION (50-100 words) — priorities and expected outcomes

Use clear, jargon-free language. Include specific data points. Professional yet accessible tone.
""",
        agent=writer,
        expected_output="Polished 800-1000 word report ready to share with teachers and school leadership.",
        context=[analysis_task, recommendations_task],
    )

    crew = Crew(
        agents=[analyst, educator, writer],
        tasks=[analysis_task, recommendations_task, report_task],
        process=Process.sequential,
        verbose=False,
    )
    return crew.kickoff()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    groq_key = st.text_input(
        "GROQ API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Paste your Groq key or add it to a .env file",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    st.markdown("---")
    st.markdown("### 💾 Export Options")
    save_report = st.checkbox("Enable report download", value=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:.78rem;font-family:DM Mono,monospace;color:#5a5a80;line-height:1.8'>
    Model: llama-3.1-8b-instant<br>
    Provider: Groq<br>
    Orchestration: CrewAI<br>
    Agents: Analyst · Educator · Writer
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 CSV Format")
    st.markdown("""
    <div style='font-size:.8rem;color:#9b98b8;line-height:1.7'>
    Your CSV should have:<br>
    • A name/ID column<br>
    • Numeric score columns<br><br>
    <span style='font-family:DM Mono,monospace;font-size:.75rem'>
    Name,Math,English,Science<br>
    Alice,85,92,78<br>
    Bob,72,68,75
    </span>
    </div>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>Student Performance <span>Analyzer</span></h1>
  <p>Upload a CSV → AI analyzes scores → Generates a full performance report</p>
</div>
""", unsafe_allow_html=True)


# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload student results CSV",
    type=["csv"],
    label_visibility="collapsed",
)

# ── Preview + Stats ───────────────────────────────────────────────────────────
csv_data = None
stats = None
numeric_cols = []
all_headers = []

if uploaded:
    raw = uploaded.read()
    csv_data = parse_csv_bytes(raw)

    if not csv_data:
        st.error("❌ The CSV file appears to be empty.")
    else:
        stats, numeric_cols, all_headers = compute_stats(csv_data)

        # Stat cards
        st.markdown('<div class="section-title">📊 Data Overview</div>', unsafe_allow_html=True)

        cols = st.columns(min(len(numeric_cols) + 1, 5))
        with cols[0]:
            st.markdown(f"""
            <div class="stat-card" style="border-color:#f5c842">
              <div class="label">Students</div>
              <div class="value">{len(csv_data)}</div>
              <div class="sub">{len(numeric_cols)} subjects</div>
            </div>""", unsafe_allow_html=True)

        for i, col in enumerate(numeric_cols[:4]):
            s = stats[col]
            with cols[i + 1]:
                color = "#10b981" if s["avg"] >= 75 else "#f59e0b" if s["avg"] >= 60 else "#ef4444"
                st.markdown(f"""
                <div class="stat-card" style="border-color:{color}">
                  <div class="label">{col}</div>
                  <div class="value">{s['avg']:.1f}</div>
                  <div class="sub">{s['min']:.0f} – {s['max']:.0f} range</div>
                </div>""", unsafe_allow_html=True)

        # Subject performance table
        if stats:
            st.markdown('<div class="section-title">📈 Subject Breakdown</div>', unsafe_allow_html=True)

            rows_html = ""
            for subj, s in stats.items():
                pct = s["avg"] / 100 * 100
                bar_color = "linear-gradient(90deg,#10b981,#34d399)" if pct >= 75 else \
                            "linear-gradient(90deg,#f59e0b,#fbbf24)" if pct >= 60 else \
                            "linear-gradient(90deg,#ef4444,#f87171)"
                rows_html += f"""
                <tr>
                  <td><strong>{subj}</strong></td>
                  <td>{s['avg']:.1f}</td>
                  <td>{s['min']:.0f}</td>
                  <td>{s['max']:.0f}</td>
                  <td style="width:180px">
                    <div class="bar-wrap">
                      <div class="bar-fill" style="width:{pct:.0f}%;background:{bar_color}"></div>
                    </div>
                  </td>
                </tr>"""

            st.markdown(f"""
            <table class="subject-table">
              <thead><tr>
                <th>Subject</th><th>Average</th><th>Min</th><th>Max</th><th>Score</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)

        # Data preview
        with st.expander("👁️  Preview raw data"):
            import pandas as pd
            df = pd.DataFrame(csv_data)
            st.dataframe(df, use_container_width=True, height=240)

        st.markdown("---")
        st.markdown("""
        <div class="info-box">
        🤖 The AI crew will run <strong>3 agents in sequence</strong>: 
        Data Analyst → Educational Advisor → Report Writer. 
        This typically takes <strong>2–4 minutes</strong>.
        </div>
        """, unsafe_allow_html=True)

        run_btn = st.button("🚀  Analyze & Generate Report", use_container_width=True)

        if run_btn:
            if not os.getenv("GROQ_API_KEY"):
                st.error("❌ Please enter your GROQ API key in the sidebar.")
                st.stop()

            data_summary = format_for_agent(csv_data, stats, numeric_cols, all_headers)

            progress = st.empty()
            progress.markdown("""
            <div class="info-box">
            ⏳ <strong>Crew is running…</strong><br>
            Agent 1 of 3: Data Analyst is examining scores and patterns…
            </div>""", unsafe_allow_html=True)

            with st.spinner("🤖 Agents at work — this takes 2–4 minutes…"):
                try:
                    result = run_crew(data_summary)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.stop()

            progress.empty()
            result_text = str(result)

            # ── Report output ──
            st.markdown('<div class="section-title">📝 Generated Report</div>', unsafe_allow_html=True)
            st.markdown('<div class="report-label">AI-generated · Analyst · Educator · Writer</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-box">{result_text}</div>', unsafe_allow_html=True)

            st.markdown("")

            # ── Downloads ──
            if save_report:
                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "⬇️ Download Report (.txt)",
                        data=result_text,
                        file_name="student_performance_report.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

                with col2:
                    # Stats summary
                    stats_txt = f"QUICK STATISTICS\n{'='*60}\n\n"
                    stats_txt += f"Total Students: {len(csv_data)}\n"
                    stats_txt += f"Subjects Analyzed: {', '.join(numeric_cols)}\n\n"
                    stats_txt += "Subject Averages:\n"
                    for col, s in stats.items():
                        stats_txt += f"  {col}: {s['avg']:.2f} (Range: {s['min']:.0f}–{s['max']:.0f})\n"

                    st.download_button(
                        "⬇️ Download Stats (.txt)",
                        data=stats_txt,
                        file_name="student_stats_summary.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            st.success("✅ Report generated successfully!")

else:
    # Empty state
    st.markdown("""
    <div style="text-align:center;padding:3rem;background:white;border-radius:16px;
    border:2px dashed #d4d0e8;color:#aaa;">
      <div style="font-size:3.5rem;margin-bottom:1rem">📂</div>
      <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:#555;margin-bottom:.5rem">
        Upload a CSV to get started
      </div>
      <div style="font-size:.88rem">
        Drag & drop or click the upload area above
      </div>
    </div>
    """, unsafe_allow_html=True)