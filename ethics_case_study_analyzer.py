import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import PyPDF2
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
    base_url="https://api.groq.com/openai/v1"
)

# -------------------------
# File Reading Utilities
# -------------------------

def read_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for i, page in enumerate(reader.pages, 1):
                text += f"\n--- Page {i} ---\n{page.extract_text()}\n"
                if len(text) > 40000:
                    break
            return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def read_text_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# -------------------------
# Agents
# -------------------------

class EthicsCaseStudyAgents:
    def __init__(self, llm_instance):
        self.llm = llm_instance

    def analyst_agent(self):
        return Agent(
            role="AI Ethics Analyst",
            goal="Analyze ethical issues, stakeholders, risks, and moral implications",
            backstory="""You are an AI ethics expert with deep knowledge of ethical frameworks
            such as utilitarianism, deontology, virtue ethics, and responsible AI principles.
            You excel at identifying ethical risks and stakeholder impacts.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def evaluator_agent(self):
        return Agent(
            role="Ethical Reasoning Evaluator",
            goal="Apply ethical frameworks and evaluate decisions logically",
            backstory="""You specialize in structured ethical reasoning. You rigorously
            apply ethical theories and justify conclusions with clear arguments.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def writer_agent(self):
        return Agent(
            role="Ethics Report Writer",
            goal="Produce a clear, structured ethical evaluation report",
            backstory="""You are a professional ethics writer who translates complex
            ethical reasoning into clear, well-structured reports suitable for
            students, faculty, and policy audiences.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

# -------------------------
# Tasks
# -------------------------

class EthicsCaseStudyTasks:

    def analysis_task(self, agent, content):
        return Task(
            description=f"""
            Analyze the following AI ethics case study:

            CONTENT:
            {content[:15000]}

            Identify:
            1. Core ethical issue(s)
            2. Stakeholders affected
            3. Risks and harms
            4. Benefits and motivations
            5. Key ethical tensions
            """,
            agent=agent,
            expected_output="""Structured analysis including:
            - Ethical issues
            - Stakeholders
            - Risks vs benefits
            - Ethical tensions"""
        )

    def evaluation_task(self, agent, analysis_task):
        return Task(
            description="""
            Evaluate the case study using ethical frameworks:

            1. Utilitarian perspective
            2. Deontological perspective
            3. Fairness and accountability
            4. Long-term societal impact

            Clearly justify each evaluation.
            """,
            agent=agent,
            expected_output="""Ethical evaluation with:
            - Framework-based reasoning
            - Justified conclusions
            - Clear logical structure""",
            context=[analysis_task]
        )

    def writing_task(self, agent, evaluation_task):
        return Task(
            description="""
            Write a formal AI Ethics Case Study Evaluation (700–900 words).

            Structure:
            1. Introduction (context + issue)
            2. Ethical Analysis
            3. Framework-Based Evaluation
            4. Final Ethical Judgment
            5. Recommendations

            Writing requirements:
            - Clear, structured arguments
            - Professional academic tone
            - Logically reasoned conclusions
            """,
            agent=agent,
            expected_output="""A polished ethics report with:
            - Clear sections
            - Structured arguments
            - Strong ethical reasoning
            - Actionable recommendations""",
            context=[evaluation_task]
        )

# -------------------------
# Crew Orchestrator
# -------------------------

class EthicsCaseStudyCrew:

    def __init__(self, case_path):
        self.case_path = case_path
        self.llm = llm

        print("\n" + "="*60)
        print("⚖️  LOADING ETHICS CASE STUDY")
        print("="*60)

        if not os.path.exists(case_path):
            raise FileNotFoundError(f"File not found: {case_path}")

        print(f"📄 Reading: {Path(case_path).name}")

        if case_path.endswith(".pdf"):
            self.content = read_pdf(case_path)
        else:
            self.content = read_text_file(case_path)

        if self.content.startswith("Error"):
            raise Exception(self.content)

        print(f"✅ Loaded ({len(self.content)} characters)")

    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)

        agents = EthicsCaseStudyAgents(self.llm)
        analyst = agents.analyst_agent()
        evaluator = agents.evaluator_agent()
        writer = agents.writer_agent()

        print("✓ Agents created: Analyst, Evaluator, Writer")

        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)

        tasks = EthicsCaseStudyTasks()
        analysis = tasks.analysis_task(analyst, self.content)
        evaluation = tasks.evaluation_task(evaluator, analysis)
        writing = tasks.writing_task(writer, evaluation)

        print("✓ Tasks created: Analysis → Evaluation → Report")

        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)

        crew = Crew(
            agents=[analyst, evaluator, writer],
            tasks=[analysis, evaluation, writing],
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "="*60)
        print("🚀 STARTING ETHICAL ANALYSIS")
        print("="*60)

        result = crew.kickoff()

        print("\n" + "="*60)
        print("✅ ETHICS ANALYSIS COMPLETED")
        print("="*60)

        return result

# -------------------------
# CLI Interface
# -------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Ethics Case Study Analyzer"
    )

    parser.add_argument("case_file", help="Path to ethics case study PDF or text file")
    parser.add_argument("--output", "-o", help="Optional output file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found")
        sys.exit(1)

    print("\n" + "="*60)
    print("AI ETHICS CASE STUDY ANALYZER")
    print("="*60)
    print("📊 Model: groq/llama-3.1-8b-instant")
    print(f"📄 Case: {Path(args.case_file).name}")
    print("="*60)

    try:
        crew = EthicsCaseStudyCrew(args.case_file)
        result = crew.run()

        print("\n" + "="*60)
        print("📝 ETHICAL EVALUATION REPORT")
        print("="*60 + "\n")
        print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
