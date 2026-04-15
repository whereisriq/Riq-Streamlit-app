import os
import streamlit as st
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import PyPDF2
from pathlib import Path
import tempfile
import datetime

# Load environment variables
load_dotenv()

# Disable rich output
os.environ["RICH_DISABLE"] = "true"

# Initialize LLM
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,
    base_url="https://api.groq.com/openai/v1"
)

# ---------------- PDF Extraction ---------------- #
def extract_pdf_text(file_path):
    try:
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            if len(reader.pages) == 0:
                return None
            
            text = ""
            for i, page in enumerate(reader.pages, 1):
                text += f"\n--- Page {i} ---\n"
                text += page.extract_text() or ""

                if len(text) > 50000:
                    break

            return text if text.strip() else None
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

# ---------------- Agents ---------------- #
class PolicyExplainerAgents:
    def __init__(self, llm_instance):
        self.llm = llm_instance

    def policy_analyst_agent(self):
        return Agent(
            role="University Policy Analyst",
            goal="Analyze policy documents",
            backstory="Expert in interpreting academic policies.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

    def simplifier_agent(self):
        return Agent(
            role="Policy Simplifier",
            goal="Explain policies in simple terms",
            backstory="Expert in simplifying complex content.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

    def faq_agent(self):
        return Agent(
            role="FAQ Generator",
            goal="Generate FAQs from policy",
            backstory="Creates helpful student-focused FAQs.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

# ---------------- Tasks ---------------- #
class PolicyExplainerTasks:
    def analysis_task(self, agent, policy_text):
        return Task(
            description=f"""
            Analyze this policy:

            {policy_text[:15000]}

            Extract:
            - Purpose
            - Scope
            - Rules
            - Responsibilities
            - Consequences
            """,
            agent=agent,
            expected_output="""
            Structured analysis including:
            - Policy purpose
            - Scope and applicability
            - Key rules
            - Responsibilities
            - Enforcement or consequences
            """
        )

    def simplification_task(self, agent, analysis_task):
        return Task(
            description="""
            Simplify the policy for students using plain language.
            Explain what students must do and why it matters.
            """,
            agent=agent,
            context=[analysis_task],
            expected_output="""
            Plain-language explanation including:
            - What the policy is about
            - Why it matters
            - What students should do
            """
        )

    def faq_task(self, agent, analysis_task):
        return Task(
            description="""
            Generate FAQs based on the policy.
            Include 8–12 realistic student questions and answers.
            """,
            agent=agent,
            context=[analysis_task],
            expected_output="""
            FAQ section with:
            - At least 8 questions
            - Clear, concise answers
            """
        )

# ---------------- Crew Runner ---------------- #
def run_crew(pdf_path):
    policy_text = extract_pdf_text(pdf_path)

    agents = PolicyExplainerAgents(llm)
    tasks = PolicyExplainerTasks()

    analyst = agents.policy_analyst_agent()
    simplifier = agents.simplifier_agent()
    faq_writer = agents.faq_agent()

    analysis = tasks.analysis_task(analyst, policy_text)
    simplified = tasks.simplification_task(simplifier, analysis)
    faq = tasks.faq_task(faq_writer, analysis)

    crew = Crew(
        agents=[analyst, simplifier, faq_writer],
        tasks=[analysis, simplified, faq],
        process=Process.sequential,
        verbose=False
    )

    return crew.kickoff()

# ---------------- Streamlit UI ---------------- #
st.set_page_config(page_title="Policy Explainer", layout="wide")

st.title("📘 University Policy Explainer")
st.markdown("Upload a policy PDF and get a simplified explanation + FAQs.")

# API key check
if not os.getenv("GROQ_API_KEY"):
    st.error("⚠️ GROQ_API_KEY not found in .env file")
    st.stop()

uploaded_file = st.file_uploader("Upload Policy PDF", type=["pdf"])

if uploaded_file:
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    st.success("✅ File uploaded successfully")
    st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")

    if st.button("🚀 Analyze Policy"):
        with st.spinner("Processing policy..."):
            try:
                # Extract and validate PDF
                policy_text = extract_pdf_text(temp_path)
                if not policy_text:
                    st.error("❌ Could not extract text from PDF. Please ensure the PDF contains readable text.")
                else:
                    result = run_crew(temp_path)

                    st.subheader("📝 Policy Explanation")
                    
                    # Format result as markdown
                    result_text = str(result)
                    st.markdown(result_text)
                    
                    # Add metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Document", uploaded_file.name.replace(".pdf", ""))
                    with col2:
                        st.metric("Status", "Analyzed")
                    
                    # Create timestamped download
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    st.download_button(
                        label="📥 Download Result (Text)",
                        data=result_text,
                        file_name=f"policy_explanation_{timestamp}.txt",
                        mime="text/plain",
                        key="download_txt"
                    )
                    
                    st.download_button(
                        label="📥 Download Result (Markdown)",
                        data=result_text,
                        file_name=f"policy_explanation_{timestamp}.md",
                        mime="text/markdown",
                        key="download_md"
                    )
                    
                    # Copy area
                    st.text_area("Copy Explanation:", value=result_text, height=300, disabled=True)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                # Clean up temp file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass