import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import PyPDF2
import sys
from pathlib import Path

# --------------------------------------------------
# ENVIRONMENT SETUP
# --------------------------------------------------
load_dotenv()

llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,
    base_url="https://api.groq.com/openai/v1"
)

# --------------------------------------------------
# FILE TOOLS
# --------------------------------------------------
def extract_pdf_text(file_path):
    """Extract text from resume PDF"""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""

            print(f"   📄 Extracting {len(reader.pages)} page(s)...")

            for i, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i} ---\n{page_text}"

                if len(text) > 30000:
                    print("   ⚠️ Content truncated to avoid token overflow")
                    break

            return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# --------------------------------------------------
# AGENTS
# --------------------------------------------------
class ResumeAgents:
    """Agents for resume analysis"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def analyzer_agent(self):
        return Agent(
            role="Resume Analyst",
            goal="Analyze resume content and identify strengths and weaknesses",
            backstory="""You are an experienced hiring manager and career advisor.
            You analyze resumes critically, identifying strong qualifications,
            gaps, clarity issues, and alignment with professional standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def advisor_agent(self):
        return Agent(
            role="Career Advisor",
            goal="Provide actionable, professional improvement suggestions for resumes",
            backstory="""You are a professional career coach who helps candidates
            improve resumes for clarity, impact, and competitiveness.
            Your advice is practical, constructive, and encouraging.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

# --------------------------------------------------
# TASKS
# --------------------------------------------------
class ResumeTasks:
    """Tasks for resume feedback"""

    def analysis_task(self, agent, resume_text):
        return Task(
            description=f"""
            Analyze the following resume content:

            RESUME:
            {resume_text[:15000]}

            Identify:
            1. Overall impression
            2. Key strengths (skills, experience, formatting, achievements)
            3. Weaknesses or gaps (clarity, missing info, structure, impact)
            4. Tone and professionalism assessment

            Be objective and professional.
            """,
            agent=agent,
            expected_output="""Structured resume analysis including:
            - Overall impression
            - Strengths (bulleted)
            - Weaknesses (bulleted)
            - Professional tone assessment"""
        )

    def feedback_task(self, agent, analysis_task):
        return Task(
            description="""
            Based on the resume analysis, provide clear improvement suggestions.

            Include:
            1. Content improvements (skills, experience, achievements)
            2. Structure and formatting suggestions
            3. Language and tone refinements
            4. General career advice (optional)

            Keep feedback constructive and actionable.
            """,
            agent=agent,
            expected_output="""Professional improvement feedback including:
            - Specific suggestions
            - Actionable examples
            - Clear prioritization""",
            context=[analysis_task]
        )

# --------------------------------------------------
# CREW ORCHESTRATION
# --------------------------------------------------
class ResumeAnalyzerCrew:
    """Orchestrates resume analysis workflow"""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.llm = llm

        print("\n" + "=" * 60)
        print("📄 LOADING RESUME")
        print("=" * 60)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")

        print(f"\n📄 Reading: {Path(pdf_path).name}")
        self.resume_text = extract_pdf_text(pdf_path)

        if self.resume_text.startswith("Error"):
            raise Exception(self.resume_text)

        print(f"✅ Resume loaded ({len(self.resume_text)} characters)")

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENTS")
        print("=" * 60)

        agents = ResumeAgents(self.llm)
        analyzer = agents.analyzer_agent()
        advisor = agents.advisor_agent()

        print("✓ Agents created: Analyzer & Advisor")

        print("\n" + "=" * 60)
        print("📋 CREATING TASKS")
        print("=" * 60)

        tasks = ResumeTasks()
        analysis = tasks.analysis_task(analyzer, self.resume_text)
        feedback = tasks.feedback_task(advisor, analysis)

        print("✓ Tasks created: Analysis & Feedback")

        print("\n" + "=" * 60)
        print("👥 ASSEMBLING CREW")
        print("=" * 60)

        crew = Crew(
            agents=[analyzer, advisor],
            tasks=[analysis, feedback],
            process=Process.sequential,
            verbose=True
        )

        print("\n🚀 STARTING RESUME ANALYSIS...\n")
        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ RESUME ANALYSIS COMPLETED")
        print("=" * 60)

        return result

# --------------------------------------------------
# CLI
# --------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Resume Analyzer & Feedback Agent (CrewAI + Groq)"
    )

    parser.add_argument("resume_pdf", help="Path to resume/CV PDF file")
    parser.add_argument("--output", "-o", help="Save feedback to file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    try:
        crew = ResumeAnalyzerCrew(args.resume_pdf)
        result = crew.run()

        print("\n" + "=" * 60)
        print("📝 RESUME FEEDBACK")
        print("=" * 60 + "\n")
        print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("RESUME FEEDBACK\n")
                f.write("=" * 60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
