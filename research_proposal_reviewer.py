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
    temperature=0.6,
    base_url="https://api.groq.com/openai/v1"
)

# -------------------- FILE HANDLING --------------------

def extract_pdf_text(file_path):
    """Extract text from PDF"""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for i, page in enumerate(reader.pages, 1):
                text += f"\n--- Page {i} ---\n{page.extract_text()}\n"
                if len(text) > 50000:
                    break
            return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def read_text_file(file_path):
    """Read text file"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


# -------------------- AGENTS --------------------

class ProposalReviewAgents:
    """Agents for proposal review"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def analyzer_agent(self):
        return Agent(
            role="Research Proposal Analyst",
            goal="Critically analyze research aims, objectives, gaps, and feasibility",
            backstory="""You are an experienced academic reviewer with expertise in 
            evaluating research proposals for funding and ethics approval.
            You assess clarity, rigor, feasibility, and scholarly contribution.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def feasibility_agent(self):
        return Agent(
            role="Research Feasibility Expert",
            goal="Assess methodological, timeline, and resource feasibility",
            backstory="""You specialize in evaluating whether proposed research designs 
            are realistic, ethical, and achievable within constraints.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def writer_agent(self):
        return Agent(
            role="Academic Reviewer",
            goal="Write a structured, professional proposal review",
            backstory="""You write formal academic evaluations used by supervisors,
            ethics committees, and funding panels.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# -------------------- TASKS --------------------

class ProposalReviewTasks:
    """Tasks for proposal evaluation"""

    def analysis_task(self, agent, proposal_text):
        return Task(
            description=f"""
            Analyze the following research proposal:

            {proposal_text[:15000]}

            Critically evaluate:
            1. Research AIM(S): clarity, focus, relevance
            2. Research OBJECTIVES: alignment with aims, measurability
            3. PROBLEM STATEMENT: significance and justification
            4. LITERATURE POSITIONING: implied gaps or novelty

            Use critical academic reasoning.
            """,
            agent=agent,
            expected_output="""Structured analysis covering:
            - Evaluation of aims
            - Evaluation of objectives
            - Identified research gaps
            - Conceptual strengths and weaknesses"""
        )

    def feasibility_task(self, agent, analysis_task):
        return Task(
            description="""
            Evaluate the feasibility of the proposed research:

            1. Methodological feasibility
            2. Time and scope realism
            3. Resource and data availability
            4. Ethical or practical risks

            Be constructive and specific.
            """,
            agent=agent,
            expected_output="""Feasibility assessment including:
            - Method feasibility
            - Timeline realism
            - Risks and constraints
            - Overall viability judgement""",
            context=[analysis_task]
        )

    def review_writing_task(self, agent, analysis_task, feasibility_task):
        return Task(
            description="""
            Write a formal research proposal review (700–900 words).

            Structure:
            1. EXECUTIVE SUMMARY
            2. ANALYSIS OF AIMS & OBJECTIVES
            3. IDENTIFIED GAPS & CONTRIBUTION
            4. FEASIBILITY ASSESSMENT
            5. STRENGTHS
            6. AREAS FOR IMPROVEMENT
            7. OVERALL RECOMMENDATION

            Tone:
            - Professional
            - Constructive
            - Academic
            """,
            agent=agent,
            expected_output="""A polished academic proposal review with:
            - Clear headings
            - Critical evaluation
            - Constructive feedback
            - Recommendation (revise / approve / major revisions)""",
            context=[analysis_task, feasibility_task]
        )


# -------------------- CREW --------------------

class ProposalReviewCrew:
    """Orchestrates proposal review"""

    def __init__(self, proposal_path):
        self.proposal_path = proposal_path
        self.llm = llm

        print("\n" + "=" * 60)
        print("📄 LOADING RESEARCH PROPOSAL")
        print("=" * 60)

        if not os.path.exists(proposal_path):
            raise FileNotFoundError(f"File not found: {proposal_path}")

        print(f"\n📄 Reading: {Path(proposal_path).name}")

        if proposal_path.endswith(".pdf"):
            self.proposal_text = extract_pdf_text(proposal_path)
        else:
            self.proposal_text = read_text_file(proposal_path)

        if self.proposal_text.startswith("Error"):
            raise Exception(self.proposal_text)

        print(f"✅ Loaded proposal ({len(self.proposal_text)} characters)")

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENTS")
        print("=" * 60)

        agents = ProposalReviewAgents(self.llm)
        analyzer = agents.analyzer_agent()
        feasibility = agents.feasibility_agent()
        writer = agents.writer_agent()

        print("✓ Agents created")

        print("\n" + "=" * 60)
        print("📋 CREATING TASKS")
        print("=" * 60)

        tasks = ProposalReviewTasks()
        analysis_task = tasks.analysis_task(analyzer, self.proposal_text)
        feasibility_task = tasks.feasibility_task(feasibility, analysis_task)
        review_task = tasks.review_writing_task(writer, analysis_task, feasibility_task)

        print("✓ Tasks created")

        print("\n" + "=" * 60)
        print("👥 ASSEMBLING CREW")
        print("=" * 60)

        crew = Crew(
            agents=[analyzer, feasibility, writer],
            tasks=[analysis_task, feasibility_task, review_task],
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "=" * 60)
        print("🚀 STARTING REVIEW")
        print("=" * 60 + "\n")

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ REVIEW COMPLETED")
        print("=" * 60)

        return result


# -------------------- CLI --------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Research Proposal Reviewer (CrewAI + Groq)"
    )

    parser.add_argument("proposal", help="Path to proposal PDF or text file")
    parser.add_argument("--output", "-o", help="Save review to file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("RESEARCH PROPOSAL REVIEWER")
    print("=" * 60)
    print("📊 Model: groq/llama-3.1-8b-instant")
    print(f"📄 Proposal: {Path(args.proposal).name}")
    print("=" * 60)

    try:
        crew = ProposalReviewCrew(args.proposal)
        result = crew.run()

        print("\n" + "=" * 60)
        print("📝 PROPOSAL REVIEW")
        print("=" * 60 + "\n")
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
