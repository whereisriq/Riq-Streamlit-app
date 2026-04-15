import os
import sys
import tempfile
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tech News Summarizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}
.stApp {
    background: #0a0a0f;
    color: #e8e6f0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e30;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #c8b8ff;
}

/* ── Header banner ── */
.hero {
    background: linear-gradient(135deg, #12001f 0%, #0a0a1a 50%, #001020 100%);
    border: 1px solid #2a1a40;
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, #6e3aff22, transparent 70%);
    pointer-events: none;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #c8b8ff, #7cf7d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 .4rem;
    letter-spacing: -1px;
}
.hero p {
    color: #888;
    font-size: 1rem;
    margin: 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: .85rem;
}

/* ── Cards ── */
.card {
    background: #12121e;
    border: 1px solid #1e1e30;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
}

/* ── Tone pills ── */
.tone-grid {display:flex;gap:.6rem;flex-wrap:wrap;margin-top:.5rem;}
.tone-pill {
    padding:.35rem .9rem;
    border-radius:100px;
    font-size:.78rem;
    font-weight:600;
    letter-spacing:.04em;
    border:1px solid;
    cursor:pointer;
}
.tone-professional {background:#0d2a1a;color:#4cffaa;border-color:#1e5a35;}
.tone-casual       {background:#1a1a0d;color:#ffe84c;border-color:#5a5010;}
.tone-technical    {background:#0d1a2a;color:#4caaff;border-color:#10355a;}
.tone-executive    {background:#1f0d2a;color:#cc80ff;border-color:#5a1a8a;}

/* ── Result box ── */
.result-box {
    background: #0e0e1b;
    border: 1px solid #2a2a45;
    border-radius: 14px;
    padding: 2rem 2.2rem;
    line-height: 1.75;
    font-size: .97rem;
    color: #ddd8f5;
    white-space: pre-wrap;
}
.result-label {
    font-family:'JetBrains Mono',monospace;
    font-size:.72rem;
    color:#5a5a80;
    text-transform:uppercase;
    letter-spacing:.12em;
    margin-bottom:.7rem;
}

/* ── Buttons ── */
div.stButton > button {
    background: linear-gradient(135deg, #6e3aff, #3a8aff);
    color: white;
    border: none;
    border-radius: 10px;
    padding: .65rem 2rem;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: .02em;
    width: 100%;
    transition: opacity .2s;
}
div.stButton > button:hover { opacity: .85; }

/* ── Status tags ── */
.status-ok  {color:#4cffaa;font-weight:700;}
.status-err {color:#ff6b6b;font-weight:700;}

/* ── Inputs / textarea ── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stSelectbox > div > div {
    background: #12121e !important;
    border-color: #2a2a40 !important;
    color: #e8e6f0 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .88rem !important;
}
div[data-baseweb="select"] * { color: #e8e6f0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: .4rem;
}
.stTabs [data-baseweb="tab"] {
    background: #12121e;
    border: 1px solid #1e1e30;
    border-radius: 8px;
    color: #888;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #1e1440 !important;
    border-color: #6e3aff !important;
    color: #c8b8ff !important;
}

/* ── Misc ── */
hr {border-color:#1e1e30;}
.stSpinner > div { border-top-color: #6e3aff !important; }
</style>
""", unsafe_allow_html=True)


# ── Lazy-load heavy deps ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_deps():
    """Import heavy dependencies once and cache them."""
    from dotenv import load_dotenv
    load_dotenv()

    os.environ["RICH_DISABLE"] = "1"
    os.environ["CREWAI_DISABLE_RICH"] = "1"

    from crewai.llm import LLM

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None, "GROQ_API_KEY not found"

    llm = LLM(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0.5,
        base_url="https://api.groq.com/openai/v1",
    )
    return llm, None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    groq_key = st.text_input(
        "GROQ API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Paste your key here or add it to a .env file",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    st.markdown("---")
    st.markdown("### 🎨 Summary Tone")

    tone_info = {
        "professional": ("💼", "Formal business style"),
        "casual":       ("💬", "Friendly & conversational"),
        "technical":    ("🔧", "In-depth for engineers"),
        "executive":    ("📊", "Concise strategic brief"),
    }

    tone = st.selectbox(
        "Select tone",
        list(tone_info.keys()),
        format_func=lambda t: f"{tone_info[t][0]}  {t.capitalize()}",
        label_visibility="collapsed",
    )
    st.caption(tone_info[tone][1])

    st.markdown("---")
    st.markdown("### 💾 Export")
    save_output = st.checkbox("Save summary to file", value=False)
    output_filename = ""
    if save_output:
        output_filename = st.text_input("Filename", value="summary.txt")

    st.markdown("---")
    st.markdown(
        "<div style='color:#444;font-size:.78rem;font-family:JetBrains Mono,monospace;'>"
        "Model: llama-3.1-8b-instant<br>Provider: Groq<br>Orchestration: CrewAI"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚡ Tech News Summarizer</h1>
  <p>CrewAI · Groq · llama-3.1-8b-instant &nbsp;|&nbsp; Research → Write → Summarize</p>
</div>
""", unsafe_allow_html=True)


# ── Input tabs ────────────────────────────────────────────────────────────────
tab_url, tab_text, tab_file = st.tabs(["🌐  URL", "📝  Paste Text", "📄  Upload File"])

source_content = None   # raw text fed to the crew
source_label   = ""

with tab_url:
    url_input = st.text_input(
        "Article URL",
        placeholder="https://techcrunch.com/2024/...",
        label_visibility="collapsed",
    )
    if url_input:
        source_label = url_input

with tab_text:
    text_input = st.text_area(
        "Paste article text",
        height=240,
        placeholder="Paste any tech news article here…",
        label_visibility="collapsed",
    )
    if text_input.strip():
        source_content = text_input
        source_label   = "pasted text"

with tab_file:
    uploaded = st.file_uploader(
        "Upload a PDF or TXT file",
        type=["pdf", "txt"],
        label_visibility="collapsed",
    )
    if uploaded:
        source_label = uploaded.name

st.markdown("")

run_btn = st.button("🚀  Run Summarizer", width='stretch')


# ── Core run logic ────────────────────────────────────────────────────────────
def run_crew(content: str, tone: str):
    """Instantiate TechNewsCrew directly with pre-loaded content."""
    from crewai import Agent, Task, Crew, Process

    llm_inst, err = load_deps()
    if err:
        st.error(f"❌ {err}")
        return None

    # --- Agents ---
    researcher = Agent(
        role="Tech News Researcher",
        goal="Extract and analyze key information from tech news articles",
        backstory=(
            "You are an expert tech news analyst skilled at identifying critical "
            "information, trends, and implications. Thorough, detail-oriented, "
            "you extract the most important facts."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm_inst,
    )

    tone_desc = {
        "professional": "formal business tone suitable for corporate communications",
        "casual":       "conversational and friendly tone as if explaining to a friend",
        "technical":    "in-depth technical analysis suitable for engineers and developers",
        "executive":    "concise executive summary focusing on strategic implications",
    }

    writer = Agent(
        role="Tech News Writer",
        goal=f"Create well-structured summaries in a {tone} tone",
        backstory=(
            f"You are a skilled technology writer who crafts engaging summaries "
            f"in a {tone_desc.get(tone, 'professional')}. "
            "You transform complex research into readable, insightful content."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm_inst,
    )

    # --- Tasks ---
    research_task = Task(
        description=f"""
Analyze the following tech news content and extract key information:

CONTENT:
{content}

Your analysis should include:
1. Main topic/technology discussed
2. Key facts and figures (specific numbers, dates, statistics)
3. Important companies, people, or organizations mentioned
4. Implications and potential impact on the industry
5. Technical details and innovations (if applicable)
""",
        agent=researcher,
        expected_output=(
            "A structured analysis with main topic, key facts (3-5 bullets), "
            "entities mentioned, implications, and technical details."
        ),
    )

    writing_task = Task(
        description=f"""
Based on the research analysis, create a comprehensive summary of the tech news article.

Requirements:
- Tone: {tone}
- Length: 250-400 words
- Clear sections/paragraphs
- Highlight key insights and takeaways
- Engaging and informative

Structure:
1. Opening paragraph introducing the main topic
2. Body paragraphs covering key details and implications
3. Closing paragraph with insights or future outlook
""",
        agent=writer,
        expected_output=(
            f"A polished {tone} summary (250-400 words) with clear intro, "
            "organised body, and insightful conclusion."
        ),
        context=[research_task],
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew.kickoff()


# ── Execution ─────────────────────────────────────────────────────────────────
if run_btn:
    if not os.getenv("GROQ_API_KEY"):
        st.error("❌ Please enter your GROQ API key in the sidebar.")
        st.stop()

    # Resolve content from whichever tab has data
    final_content = None

    if uploaded:
        # Check file size
        file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        if file_size_mb > 50:
            st.error(f"❌ File too large ({file_size_mb:.1f} MB). Maximum is 50 MB.")
            st.stop()
        
        suffix = "." + uploaded.name.rsplit(".", 1)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                try:
                    import PyPDF2
                    with open(tmp_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        if len(reader.pages) == 0:
                            st.error("❌ PDF contains no pages.")
                            st.stop()
                        text = "\n".join(p.extract_text() or "" for p in reader.pages)
                    if not text.strip():
                        st.error("❌ Could not extract text from PDF. Ensure it's not image-based.")
                        st.stop()
                    final_content = text[:15000]
                except Exception as e:
                    st.error(f"❌ PDF Error: {str(e)}")
                    st.stop()
            else:
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                    final_content = f.read()[:15000]
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    elif url_input:
        # Validate URL
        if not url_input.startswith(("http://", "https://")):
            st.error("❌ Invalid URL. Must start with http:// or https://")
            st.stop()
        
        import requests
        with st.spinner("Fetching URL…"):
            try:
                r = requests.get(
                    url_input,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15,
                )
                r.raise_for_status()
                
                # Extract text from HTML or use raw content
                final_content = None
                try:
                    from bs4 import BeautifulSoup  # pyright: ignore[reportMissingImports]
                    soup = BeautifulSoup(r.text, "html.parser")
                    # Remove script and style elements
                    for script in soup.find_all(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    # Clean up whitespace
                    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
                    final_content = text[:15000]
                except (ImportError, Exception) as e:
                    # Fall back to raw text if BeautifulSoup not available or fails
                    import re
                    # Remove HTML tags and scripts
                    text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<[^>]+>', '', text)
                    text = re.sub(r'\s+', ' ', text)
                    final_content = text[:15000]
            except requests.exceptions.Timeout:
                st.error("❌ URL request timed out. Try a different URL.")
                st.stop()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Could not fetch URL: {str(e)}")
                st.stop()

    elif text_input.strip():
        final_content = text_input.strip()

    else:
        st.warning("⚠️ Please provide a URL, paste text, or upload a file.")
        st.stop()

    if not final_content or not final_content.strip():
        st.error("❌ No content extracted. Please try a different source.")
        st.stop()

    # ── Run crew ──
    st.markdown("---")

    col_info, _ = st.columns([3, 1])
    with col_info:
        st.markdown(
            f"<span class='status-ok'>▶ Running</span>&nbsp;&nbsp;"
            f"<span style='color:#555;font-size:.85rem;font-family:JetBrains Mono,monospace'>"
            f"source: {source_label} &nbsp;|&nbsp; tone: {tone}</span>",
            unsafe_allow_html=True,
        )

    with st.spinner("🤖 Crew is working — Researcher → Writer…"):
        try:
            result = run_crew(final_content, tone)
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    result_text = str(result)

    # ── Display result ──
    st.markdown("")
    st.markdown("<div class='result-label'>📝 Final Summary</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='result-box'>{result_text}</div>",
        unsafe_allow_html=True,
    )

    # ── Copy / download ──
    st.markdown("")
    col_dl, col_copy = st.columns(2)
    with col_dl:
        st.download_button(
            "⬇️  Download summary",
            data=result_text,
            file_name=output_filename if (save_output and output_filename) else "summary.txt",
            mime="text/plain",
            width='stretch',
        )
    with col_copy:
        st.code(result_text, language=None)

    # ── Save to disk if requested ──
    if save_output and output_filename:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(result_text)
        st.success(f"✅ Saved to `{output_filename}`")