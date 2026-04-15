import os
os.environ["RICH_DISABLE"] = "true"
os.environ["CREWAI_DISABLE_RICH"] = "1"

import streamlit as st
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Exam Question Generator",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&family=Lato:wght@300;400;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Lato', sans-serif; }
.stApp { background: #f4f6fb; color: #1a1f36; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1a1f36 !important;
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #c8d0e8 !important; }
section[data-testid="stSidebar"] h3 { color: #7eb3ff !important; }
section[data-testid="stSidebar"] .stTextInput > div > div > input,
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #242a45 !important;
    border-color: #323a60 !important;
    color: #c8d0e8 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .82rem !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #1a1f36 0%, #243060 60%, #1e2a50 100%);
    border-radius: 22px;
    padding: 2.8rem 3.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -80px; left: -80px;
    width: 320px; height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, #7eb3ff18, transparent 65%);
}
.hero::after {
    content: "📘";
    position: absolute;
    right: 3.5rem; top: 50%;
    transform: translateY(-50%);
    font-size: 6.5rem;
    opacity: .13;
}
.hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.7rem;
    font-weight: 800;
    color: #f0f4ff;
    margin: 0 0 .4rem;
    line-height: 1.15;
}
.hero h1 span { color: #7eb3ff; }
.hero p {
    color: #6070a0;
    font-family: 'JetBrains Mono', monospace;
    font-size: .82rem;
    margin: 0;
}

/* ── Form card ── */
.form-card {
    background: white;
    border-radius: 18px;
    padding: 2rem 2.2rem;
    box-shadow: 0 2px 20px rgba(26,31,54,.08);
    border: 1px solid #e4e8f5;
    margin-bottom: 1.5rem;
}

/* ── Difficulty pills ── */
.diff-row { display:flex; gap:.7rem; margin-top:.3rem; }
.diff-pill {
    flex:1; text-align:center;
    border-radius: 10px;
    padding: .7rem .5rem;
    font-weight: 700;
    font-size: .85rem;
    border: 2px solid;
    cursor: pointer;
}
.diff-easy   { background:#d1fae5; color:#065f46; border-color:#6ee7b7; }
.diff-medium { background:#dbeafe; color:#1e40af; border-color:#93c5fd; }
.diff-hard   { background:#fee2e2; color:#991b1b; border-color:#fca5a5; }

/* ── Pipeline ── */
.pipeline {
    display:flex; align-items:center;
    gap:0; margin:1.5rem 0; flex-wrap:wrap;
}
.pipe-step {
    flex:1; min-width:110px;
    background:white;
    border:1.5px solid #e4e8f5;
    border-radius:12px;
    padding:.7rem .8rem;
    font-size:.8rem;
    font-weight:700;
    color:#3a4a7a;
    text-align:center;
}
.pipe-step.active {
    background:#1a1f36;
    color:#7eb3ff;
    border-color:#1a1f36;
}
.pipe-arrow { color:#c0c8e0; font-size:1.1rem; padding:0 .3rem; flex-shrink:0; }

/* ── Stat chips ── */
.stat-row { display:flex; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.stat-chip {
    flex:1; min-width:110px;
    background:white;
    border:1.5px solid #e4e8f5;
    border-radius:14px;
    padding:.85rem 1rem;
    text-align:center;
    box-shadow:0 1px 8px rgba(26,31,54,.05);
}
.stat-chip .sv {
    font-family:'JetBrains Mono',monospace;
    font-size:1.5rem; font-weight:700; color:#1a1f36;
}
.stat-chip .sl {
    font-size:.68rem; text-transform:uppercase;
    letter-spacing:.1em; color:#8090b8; margin-top:.2rem;
}

/* ── Questions output ── */
.q-wrap {
    background:white;
    border-radius:20px;
    padding:2.5rem 3rem;
    box-shadow:0 4px 28px rgba(26,31,54,.09);
    border:1px solid #e4e8f5;
    line-height:1.85;
    color:#1a1f36;
    font-size:.97rem;
    white-space:pre-wrap;
}
.q-meta {
    font-family:'JetBrains Mono',monospace;
    font-size:.7rem; color:#8090b8;
    text-transform:uppercase; letter-spacing:.12em;
    margin-bottom:.8rem;
    display:flex; gap:1.2rem; flex-wrap:wrap;
}

/* ── Difficulty badge ── */
.badge {
    display:inline-block;
    border-radius:100px;
    padding:.18rem .75rem;
    font-size:.75rem; font-weight:700;
    font-family:'JetBrains Mono',monospace;
}
.badge-easy   { background:#d1fae5; color:#065f46; }
.badge-medium { background:#dbeafe; color:#1e40af; }
.badge-hard   { background:#fee2e2; color:#991b1b; }

/* ── Info box ── */
.info-box {
    background:#eff6ff;
    border-left:4px solid #7eb3ff;
    border-radius:8px;
    padding:.85rem 1.2rem;
    font-size:.87rem; color:#1e3a6e;
    margin-bottom:1rem;
}

/* ── Bloom taxonomy reference ── */
.bloom-table {
    width:100%; border-collapse:collapse;
    background:white; border-radius:12px;
    overflow:hidden;
    box-shadow:0 2px 10px rgba(26,31,54,.06);
    font-size:.82rem;
}
.bloom-table th {
    background:#1a1f36; color:#7eb3ff;
    padding:.6rem 1rem; text-align:left;
    font-size:.72rem; text-transform:uppercase;
    letter-spacing:.08em;
}
.bloom-table td {
    padding:.55rem 1rem;
    border-bottom:1px solid #f0f2f8;
    color:#2a3560;
}
.bloom-table tr:last-child td { border-bottom:none; }

/* ── Run button ── */
div.stButton > button {
    background: linear-gradient(135deg, #1a1f36, #2d3875);
    color: #7eb3ff;
    border: none;
    border-radius: 12px;
    padding: .8rem 2rem;
    font-family: 'Lato', sans-serif;
    font-weight: 700; font-size: 1rem;
    width: 100%;
    letter-spacing: .02em;
    transition: opacity .2s;
}
div.stButton > button:hover { opacity: .85; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
    background: white;
    color: #1a1f36;
    border: 2px solid #b0c0e0;
    border-radius: 10px;
    font-weight: 700;
    width: 100%;
    font-family: 'Lato', sans-serif;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background: #f8f9fd !important;
    border-color: #d8deee !important;
    color: #1a1f36 !important;
    border-radius: 10px !important;
}

hr { border-color: #e4e8f5; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Crew runner ───────────────────────────────────────────────────────────────
def run_crew(subject: str, topic: str, difficulty: str) -> str:
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

    generator = Agent(
        role="Exam Question Designer",
        goal="Generate high-quality exam questions aligned with learning objectives",
        backstory=(
            "You are an experienced educator and assessment specialist. "
            "You design exam questions that are clear, fair, and aligned with "
            "Bloom's taxonomy and academic standards."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )
    reviewer = Agent(
        role="Assessment Quality Reviewer",
        goal="Evaluate exam questions for clarity, difficulty, and educational alignment",
        backstory=(
            "You are a senior academic reviewer specializing in assessment validation. "
            "You ensure questions are unambiguous, appropriately difficult, and aligned "
            "with learning outcomes."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )
    editor = Agent(
        role="Exam Question Editor",
        goal="Refine exam questions based on review feedback",
        backstory=(
            "You specialize in improving assessment items. You rewrite questions to enhance "
            "clarity, balance difficulty, and ensure fairness while preserving learning intent."
        ),
        verbose=False, allow_delegation=False, llm=llm,
    )

    gen_task = Task(
        description=f"""
Generate 6 exam questions for:

Subject: {subject}
Topic: {topic}
Difficulty Level: {difficulty}

Requirements:
- Include a mix of question types (short answer, essay, applied)
- Align with Bloom's taxonomy
- Avoid ambiguity
- Ensure academic integrity

Label each question with:
- Question number
- Question type
- Bloom's level
""",
        agent=generator,
        expected_output="6 well-structured exam questions with clear wording, labeled Bloom's levels, and appropriate difficulty.",
    )

    review_task = Task(
        description="""
Review the generated exam questions.

Assess each question for:
1. Clarity of wording
2. Alignment with topic and difficulty
3. Cognitive level (Bloom's taxonomy)
4. Potential ambiguity or bias
5. Overall assessment quality

Provide structured feedback per question.
""",
        agent=reviewer,
        expected_output="Structured review with strengths, weaknesses, difficulty assessment, and improvement suggestions per question.",
        context=[gen_task],
    )

    refine_task = Task(
        description="""
Improve and rewrite the exam questions based on the reviewer's feedback.

Goals:
- Improve clarity
- Adjust difficulty where needed
- Preserve learning objectives
- Ensure fairness and consistency

Output only the FINAL revised questions.
""",
        agent=editor,
        expected_output="A finalized set of polished, clear, unambiguous exam questions matching stated difficulty and educational standards.",
        context=[gen_task, review_task],
    )

    crew = Crew(
        agents=[generator, reviewer, editor],
        tasks=[gen_task, review_task, refine_task],
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
        help="Paste your key or add it to a .env file",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    st.markdown("---")
    st.markdown("### 💾 Export")
    save_txt = st.checkbox("Plain text (.txt)", value=True)
    save_md  = st.checkbox("Markdown (.md)",    value=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:.77rem;color:#5060a0;font-family:JetBrains Mono,monospace;line-height:1.9'>
    Model: llama-3.1-8b-instant<br>
    Provider: Groq<br>
    Orchestration: CrewAI<br>
    Agents: Generator · Reviewer · Editor
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🧠 Bloom's Taxonomy")
    st.markdown("""
    <table class="bloom-table">
      <thead><tr><th>Level</th><th>Action Verbs</th></tr></thead>
      <tbody>
        <tr><td>Remember</td><td>List, Define, Recall</td></tr>
        <tr><td>Understand</td><td>Explain, Summarize</td></tr>
        <tr><td>Apply</td><td>Use, Solve, Calculate</td></tr>
        <tr><td>Analyze</td><td>Compare, Differentiate</td></tr>
        <tr><td>Evaluate</td><td>Justify, Critique</td></tr>
        <tr><td>Create</td><td>Design, Construct</td></tr>
      </tbody>
    </table>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>AI <span>Exam Question</span> Generator</h1>
  <p>Enter subject & topic → 3 AI agents generate, review & refine → 6 polished questions</p>
</div>
""", unsafe_allow_html=True)

# ── Pipeline ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pipeline">
  <div class="pipe-step">✏️ Generator</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">🔍 Reviewer</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">✂️ Editor</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step active">📄 6 Questions</div>
</div>
""", unsafe_allow_html=True)

# ── Form ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="form-card">', unsafe_allow_html=True)
st.markdown("#### 🎓 Exam Parameters")

col1, col2 = st.columns(2)

with col1:
    subject = st.text_input(
        "Subject / Course",
        placeholder="e.g. Biology, World History, Computer Science",
        help="The course or subject name",
    )

with col2:
    topic = st.text_input(
        "Specific Topic",
        placeholder="e.g. Photosynthesis, The French Revolution, Recursion",
        help="The specific topic within the subject",
    )

st.markdown("**Difficulty Level**")
difficulty = st.select_slider(
    "Difficulty",
    options=["easy", "medium", "hard"],
    value="medium",
    label_visibility="collapsed",
)

diff_colors = {"easy": "diff-easy", "medium": "diff-medium", "hard": "diff-hard"}
diff_desc = {
    "easy":   "Recall & understanding — suitable for introductory assessment",
    "medium": "Application & analysis — tests deeper comprehension",
    "hard":   "Evaluation & creation — challenges advanced learners",
}
st.markdown(f"""
<div class="diff-row">
  <div class="diff-pill {'diff-easy'   if difficulty=='easy'   else ''}" style="{'opacity:.4' if difficulty!='easy'   else ''}">🟢 Easy</div>
  <div class="diff-pill {'diff-medium' if difficulty=='medium' else ''}" style="{'opacity:.4' if difficulty!='medium' else ''}">🔵 Medium</div>
  <div class="diff-pill {'diff-hard'   if difficulty=='hard'   else ''}" style="{'opacity:.4' if difficulty!='hard'   else ''}">🔴 Hard</div>
</div>
<div style='font-size:.82rem;color:#6070a0;margin-top:.6rem'>{diff_desc[difficulty]}</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Subject suggestions ───────────────────────────────────────────────────────
with st.expander("💡 Subject & topic examples"):
    examples = {
        "Biology":          "Photosynthesis · Cell Division · Genetics",
        "Mathematics":      "Calculus · Linear Algebra · Probability",
        "Computer Science": "Recursion · Data Structures · Algorithms",
        "History":          "The French Revolution · World War II · Cold War",
        "Physics":          "Newton's Laws · Quantum Mechanics · Thermodynamics",
        "Economics":        "Supply & Demand · Fiscal Policy · Game Theory",
        "Literature":       "Shakespeare · Narrative Structure · Literary Devices",
    }
    for sub, topics in examples.items():
        st.markdown(f"**{sub}** — {topics}")

# ── Info & Run ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
🤖 <strong>3 agents in sequence:</strong> Generator creates 6 questions →
Reviewer evaluates each one → Editor refines and finalizes.
Takes <strong>2–4 minutes</strong>.
</div>
""", unsafe_allow_html=True)

run_btn = st.button("🚀  Generate Exam Questions", use_container_width=True)

# ── Execute ───────────────────────────────────────────────────────────────────
if run_btn:
    # Validation
    if not os.getenv("GROQ_API_KEY"):
        st.error("❌ Please enter your GROQ API key in the sidebar.")
        st.stop()
    if not subject or not subject.strip():
        st.warning("⚠️ Please enter a subject name.")
        st.stop()
    if not topic or not topic.strip():
        st.warning("⚠️ Please enter a specific topic.")
        st.stop()

    subject_clean  = subject.strip()
    topic_clean    = topic.strip()
    generated_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    progress = st.empty()
    stages = [
        ("✏️", "Generator", "Creating 6 questions aligned with Bloom's taxonomy…"),
        ("🔍", "Reviewer",  "Evaluating each question for clarity and difficulty…"),
        ("✂️", "Editor",    "Refining and polishing the final question set…"),
    ]
    for icon, name, desc in stages:
        progress.markdown(f"""
        <div class="info-box">
        {icon} <strong>Agent: {name}</strong> — {desc}
        </div>""", unsafe_allow_html=True)

    with st.spinner("🤖 Crew at work — Generator → Reviewer → Editor…"):
        try:
            result = run_crew(subject_clean, topic_clean, difficulty)
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    progress.empty()
    result_text = str(result)

    # ── Stats ──────────────────────────────────────────────────────────────
    word_count = len(result_text.split())
    q_count    = result_text.lower().count("question")
    badge_cls  = f"badge-{difficulty}"

    st.markdown("---")
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-chip">
        <div class="sv">6</div>
        <div class="sl">Questions</div>
      </div>
      <div class="stat-chip">
        <div class="sv">3</div>
        <div class="sl">Agents</div>
      </div>
      <div class="stat-chip">
        <div class="sv">{word_count:,}</div>
        <div class="sl">Words</div>
      </div>
      <div class="stat-chip">
        <div class="sv"><span class="badge {badge_cls}">{difficulty}</span></div>
        <div class="sl">Difficulty</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Output ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="q-meta">
      <span>📚 {subject_clean}</span>
      <span>📌 {topic_clean}</span>
      <span>🗓️ {generated_at}</span>
      <span>🤖 CrewAI + Groq</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="q-wrap">{result_text}</div>', unsafe_allow_html=True)

    # ── Downloads ──────────────────────────────────────────────────────────
    st.markdown("")

    header = (
        f"EXAM QUESTIONS\n{'='*60}\n"
        f"Subject:    {subject_clean}\n"
        f"Topic:      {topic_clean}\n"
        f"Difficulty: {difficulty}\n"
        f"Generated:  {generated_at}\n"
        f"{'='*60}\n\n"
    )
    full_txt = header + result_text
    full_md  = (
        f"# Exam Questions — {subject_clean}\n\n"
        f"**Topic:** {topic_clean}  \n"
        f"**Difficulty:** {difficulty}  \n"
        f"**Generated:** {generated_at}\n\n---\n\n"
        + result_text
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dl_options = []
    if save_txt:
        dl_options.append(("📃 Download (.txt)", full_txt, f"exam_questions_{ts}.txt", "text/plain"))
    if save_md:
        dl_options.append(("📄 Download (.md)",  full_md,  f"exam_questions_{ts}.md",  "text/markdown"))

    if dl_options:
        cols = st.columns(len(dl_options))
        for i, (label, data, fname, mime) in enumerate(dl_options):
            with cols[i]:
                st.download_button(label, data=data, file_name=fname, mime=mime, use_container_width=True)

    st.success(f"✅ 6 exam questions generated for '{topic_clean}' ({difficulty} difficulty)")