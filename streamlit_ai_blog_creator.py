import os
os.environ["RICH_DISABLE"] = "true"
os.environ["CREWAI_DISABLE_RICH"] = "1"

import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Blog Creator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,600;0,800;1,300;1,600&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #faf8f5; color: #1c1917; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1c1208 !important;
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #e8dfc8 !important; }
section[data-testid="stSidebar"] h3 { color: #f5c97a !important; }
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #2a1e0e !important;
    border-color: #3d2e18 !important;
    color: #e8dfc8 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .82rem !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #1c1208 0%, #2e1c08 55%, #1a1410 100%);
    border-radius: 22px;
    padding: 3rem 3.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    bottom: -60px; right: -60px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, #f5c97a22, transparent 65%);
}
.hero::after {
    content: "✍️";
    position: absolute;
    right: 3.5rem; top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: .14;
}
.hero h1 {
    font-family: 'Fraunces', serif;
    font-size: 2.9rem;
    font-weight: 800;
    color: #faf8f5;
    margin: 0 0 .4rem;
    line-height: 1.1;
    letter-spacing: -.5px;
}
.hero h1 span { color: #f5c97a; font-style: italic; }
.hero p {
    color: #7a6a50;
    font-family: 'JetBrains Mono', monospace;
    font-size: .82rem;
    margin: 0;
}

/* ── Input card ── */
.input-card {
    background: white;
    border-radius: 18px;
    padding: 2rem 2.2rem;
    box-shadow: 0 2px 20px rgba(28,18,8,.07);
    border: 1px solid #ede8df;
    margin-bottom: 1.5rem;
}

/* ── Topic tags ── */
.tag-row { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.8rem; }
.tag {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
    border-radius: 100px;
    padding: .25rem .8rem;
    font-size: .77rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .15s;
}
.tag:hover { background: #fde68a; }

/* ── Process pipeline ── */
.pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 1.5rem 0;
    flex-wrap: wrap;
}
.pipe-step {
    background: white;
    border: 1.5px solid #ede8df;
    border-radius: 12px;
    padding: .7rem 1.1rem;
    font-size: .82rem;
    font-weight: 600;
    color: #44321a;
    display: flex;
    align-items: center;
    gap: .4rem;
    flex: 1;
    justify-content: center;
    min-width: 100px;
}
.pipe-step.active {
    background: #1c1208;
    color: #f5c97a;
    border-color: #1c1208;
}
.pipe-arrow {
    color: #c4b49a;
    font-size: 1.1rem;
    padding: 0 .2rem;
    flex-shrink: 0;
}

/* ── Word count badge ── */
.wc-badge {
    display: inline-block;
    background: #d1fae5;
    color: #065f46;
    border-radius: 100px;
    padding: .2rem .75rem;
    font-size: .75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    margin-left: .5rem;
}
.wc-badge.warn { background: #fef3c7; color: #92400e; }

/* ── Blog output ── */
.blog-wrap {
    background: white;
    border-radius: 20px;
    padding: 3rem 3.5rem;
    box-shadow: 0 4px 28px rgba(28,18,8,.09);
    border: 1px solid #ede8df;
    line-height: 1.85;
    color: #1c1917;
    font-size: 1rem;
    font-family: 'Inter', sans-serif;
    max-width: 820px;
    margin: 0 auto;
}
.blog-wrap h1, .blog-wrap h2, .blog-wrap h3 {
    font-family: 'Fraunces', serif;
    color: #1c1208;
}
.blog-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: .7rem;
    color: #a89070;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: 1rem;
    display: flex;
    gap: 1.2rem;
    flex-wrap: wrap;
}

/* ── Stats row ── */
.stat-row { display:flex; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.stat-chip {
    background: white;
    border: 1.5px solid #ede8df;
    border-radius: 12px;
    padding: .8rem 1.2rem;
    text-align: center;
    flex: 1; min-width: 110px;
    box-shadow: 0 1px 8px rgba(28,18,8,.05);
}
.stat-chip .sv { font-family:'JetBrains Mono',monospace; font-size:1.5rem; font-weight:700; color:#1c1208; }
.stat-chip .sl { font-size:.7rem; text-transform:uppercase; letter-spacing:.1em; color:#a89070; margin-top:.2rem; }

/* ── Info box ── */
.info-box {
    background: #fffbeb;
    border-left: 4px solid #f5c97a;
    border-radius: 8px;
    padding: .85rem 1.2rem;
    font-size: .87rem;
    color: #78350f;
    margin-bottom: 1rem;
}

/* ── Run button ── */
div.stButton > button {
    background: linear-gradient(135deg, #1c1208, #3d2e18);
    color: #f5c97a;
    border: none;
    border-radius: 12px;
    padding: .8rem 2rem;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    width: 100%;
    letter-spacing: .01em;
    transition: opacity .2s;
}
div.stButton > button:hover { opacity: .85; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
    background: white;
    color: #1c1208;
    border: 2px solid #d4b896;
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
    font-family: 'Inter', sans-serif;
}

/* ── Text input ── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
    background: #faf8f5 !important;
    border-color: #e0d8cc !important;
    color: #1c1917 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Char counter ── */
.char-counter {
    font-family: 'JetBrains Mono', monospace;
    font-size: .72rem;
    color: #a89070;
    text-align: right;
    margin-top: -.5rem;
    margin-bottom: .5rem;
}
.char-counter.warn { color: #d97706; }
.char-counter.error { color: #dc2626; }

hr { border-color: #ede8df; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Crew runner ───────────────────────────────────────────────────────────────
def run_crew(topic: str) -> str:
    from dotenv import load_dotenv
    load_dotenv()
    from crewai import Agent, Task, Crew, Process
    from crewai.llm import LLM

    llm = LLM(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
        base_url="https://api.groq.com/openai/v1",
    )

    researcher = Agent(
        role="Content Researcher",
        goal="Research the blog topic and produce structured insights and key points",
        backstory=(
            "You are a digital content researcher skilled in online research, trend analysis, "
            "and idea structuring. You extract accurate, relevant, and engaging information "
            "suitable for blog writing."
        ),
        llm=llm, verbose=False, allow_delegation=False,
    )

    writer = Agent(
        role="Blog Writer",
        goal="Write a compelling, well-structured blog post based on research input",
        backstory=(
            "You are an experienced blog writer who crafts engaging, reader-friendly articles "
            "with clear structure, strong hooks, and smooth transitions."
        ),
        llm=llm, verbose=False, allow_delegation=False,
    )

    editor = Agent(
        role="Content Editor",
        goal="Edit and polish the blog for clarity, flow, grammar, and engagement",
        backstory=(
            "You are a professional editor. You improve clarity, coherence, tone, and overall "
            "writing quality while preserving meaning. You ensure the final content is "
            "publication-ready."
        ),
        llm=llm, verbose=False, allow_delegation=False,
    )

    research_task = Task(
        description=f"""
Research the topic: {topic}

Provide:
- Background
- Key points
- Examples
- Audience
- Blog angle
""",
        agent=researcher,
        expected_output=(
            "Structured research notes including overview, 5-7 key points, "
            "examples, audience insights, and blog angle."
        ),
    )

    writing_task = Task(
        description=f"""
Write a blog post based on the research provided.

TOPIC: {topic}

Requirements:
- Length: 700-900 words
- Clear introduction, body, and conclusion
- Engaging and reader-friendly tone
- Use headings and short paragraphs
- Maintain logical flow
""",
        agent=writer,
        expected_output="A complete blog draft (700-900 words) with strong intro, organized sections, and clear conclusion.",
        context=[research_task],
    )

    editing_task = Task(
        description="""
Edit the blog post for:
- Clarity and coherence
- Grammar and sentence structure
- Engagement and readability
- Consistent tone and flow

Improve quality without changing core ideas.
""",
        agent=editor,
        expected_output="A polished, publication-ready blog post with improved flow, clear language, and professional editing.",
        context=[writing_task],
    )

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, writing_task, editing_task],
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
    save_md   = st.checkbox("Markdown (.md)",  value=True)
    save_txt  = st.checkbox("Plain text (.txt)", value=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:.77rem;color:#7a6a50;font-family:JetBrains Mono,monospace;line-height:1.9'>
    Model: llama-3.1-8b-instant<br>
    Provider: Groq<br>
    Orchestration: CrewAI<br>
    Agents: Researcher · Writer · Editor
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🤖 Agent Pipeline")
    st.markdown("""
    <div style='font-size:.82rem;color:#7a6a50;line-height:2'>
    1️⃣ <b>Researcher</b> — gathers insights<br>
    2️⃣ <b>Writer</b> — drafts the blog<br>
    3️⃣ <b>Editor</b> — polishes & finalizes
    </div>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>AI <span>Blog Creator</span></h1>
  <p>Type a topic → 3 AI agents research, write & edit → Publication-ready blog</p>
</div>
""", unsafe_allow_html=True)

# ── Pipeline display ──────────────────────────────────────────────────────────
st.markdown("""
<div class="pipeline">
  <div class="pipe-step">🔍 Researcher</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">✍️ Writer</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step">✂️ Editor</div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-step active">📄 Blog Post</div>
</div>
""", unsafe_allow_html=True)

# ── Input card ────────────────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)
st.markdown("#### 📝 What should the blog be about?")

topic = st.text_input(
    "Blog topic",
    placeholder="e.g. How AI is changing the way students learn in 2025",
    max_chars=200,
    label_visibility="collapsed",
)

# Character counter
if topic:
    char_count = len(topic)
    cls = "error" if char_count > 180 else "warn" if char_count > 120 else ""
    st.markdown(f'<div class="char-counter {cls}">{char_count}/200 characters</div>', unsafe_allow_html=True)

# Topic suggestions
st.markdown("**💡 Try one of these topics:**")
suggestions = [
    "The Future of Remote Work",
    "Climate Tech in 2025",
    "AI in Healthcare",
    "Beginner's Guide to Crypto",
    "Mental Health & Social Media",
    "Electric Vehicles Explained",
    "Quantum Computing Basics",
    "Space Tourism: What's Next",
]
st.markdown(
    '<div class="tag-row">' +
    "".join(f'<span class="tag">{s}</span>' for s in suggestions) +
    "</div>",
    unsafe_allow_html=True,
)
st.markdown("*Click a tag above, then paste it into the input field.*")
st.markdown('</div>', unsafe_allow_html=True)

# ── Validation & Run ──────────────────────────────────────────────────────────
st.markdown("")

col_btn, col_info = st.columns([2, 3])
with col_btn:
    run_btn = st.button("🚀  Generate Blog Post", use_container_width=True)

with col_info:
    st.markdown("""
    <div class="info-box" style="margin-bottom:0">
    ⏱️ Takes <strong>2–4 minutes</strong> · 3 agents in sequence · 700–900 word output
    </div>
    """, unsafe_allow_html=True)

# ── Run ───────────────────────────────────────────────────────────────────────
if run_btn:
    if not os.getenv("GROQ_API_KEY"):
        st.error("❌ Please enter your GROQ API key in the sidebar.")
        st.stop()

    if not topic or not topic.strip():
        st.warning("⚠️ Please enter a blog topic first.")
        st.stop()

    if len(topic.strip()) < 3:
        st.warning("⚠️ Topic must be at least 3 characters.")
        st.stop()

    if len(topic.strip()) > 200:
        st.warning("⚠️ Topic must be under 200 characters.")
        st.stop()

    topic_clean = topic.strip()

    # Animated progress
    progress_placeholder = st.empty()

    stages = [
        ("🔍", "Researcher", "Gathering insights, trends, and key points…"),
        ("✍️", "Writer",     "Drafting the 700–900 word blog post…"),
        ("✂️", "Editor",     "Polishing grammar, flow, and readability…"),
    ]

    for icon, name, desc in stages:
        progress_placeholder.markdown(f"""
        <div class="info-box">
        {icon} <strong>Agent: {name}</strong> — {desc}
        </div>
        """, unsafe_allow_html=True)

    with st.spinner("🤖 Crew at work — Researcher → Writer → Editor…"):
        try:
            result = run_crew(topic_clean)
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    progress_placeholder.empty()

    result_text = str(result)

    # ── Stats ──
    word_count = len(result_text.split())
    char_total = len(result_text)
    read_mins  = max(1, round(word_count / 200))
    wc_cls     = "" if 700 <= word_count <= 950 else "warn"

    st.markdown("---")
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-chip">
        <div class="sv">{word_count:,}</div>
        <div class="sl">Words</div>
      </div>
      <div class="stat-chip">
        <div class="sv">{char_total:,}</div>
        <div class="sl">Characters</div>
      </div>
      <div class="stat-chip">
        <div class="sv">{read_mins}</div>
        <div class="sl">Min Read</div>
      </div>
      <div class="stat-chip">
        <div class="sv">3</div>
        <div class="sl">Agents Used</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Blog output ──
    st.markdown('<div class="blog-meta">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="blog-meta">
      <span>📌 Topic: {topic_clean}</span>
      <span>🤖 AI-generated · CrewAI + Groq</span>
      <span>📖 ~{read_mins} min read</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="blog-wrap">{result_text}</div>', unsafe_allow_html=True)

    # ── Downloads ──
    st.markdown("")
    dl_cols = []
    if save_md:
        dl_cols.append(("md", "📄 Download Markdown (.md)", result_text, "blog_post.md", "text/markdown"))
    if save_txt:
        dl_cols.append(("txt", "📃 Download Plain Text (.txt)", result_text, "blog_post.txt", "text/plain"))

    if dl_cols:
        cols = st.columns(len(dl_cols))
        for i, (_, label, data, fname, mime) in enumerate(dl_cols):
            with cols[i]:
                st.download_button(label, data=data, file_name=fname, mime=mime, use_container_width=True)

    st.success(f"✅ Blog post generated! {word_count} words · ~{read_mins} min read")