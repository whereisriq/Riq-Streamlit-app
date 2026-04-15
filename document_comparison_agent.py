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

# Initialize Groq LLaMA model
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,
    base_url="https://api.groq.com/openai/v1"
)


# -------------------- FILE HELPERS --------------------

def read_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text[:20000]
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def read_text(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()[:20000]
    except Exception as e:
        return f"Error reading file: {str(e)}"


# -------------------- AGENTS --------------------

class DocumentComparisonAgents:
    def __init__(self, llm_instance):
        self.llm = llm_instance

    def comparison_agent(self):
        return Agent(
            role="Document Comparison Analyst",
            goal="Compare two documents and identify similarities and differences",
            backstory="""You are an expert analyst skilled in comparing documents.
            You identify overlapping ideas, key differences, missing elements,
            and stylistic or conceptual contrasts clearly and objectively.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def summary_agent(self):
        return Agent(
            role="Comparison Summary Writer",
            goal="Produce a clear, structured comparison summary",
            backstory="""You specialize in summarizing comparative analyses.
            You present findings clearly with sections, bullet points,
            and concise explanations suitable for academic or professional use.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# -------------------- TASKS --------------------

class DocumentComparisonTasks:
    def analysis_task(self, agent, doc1, doc2, name1, name2):
        return Task(
            description=f"""
            Compare the following two documents:

            DOCUMENT A: {name1}
            ----------------
            {doc1}

            DOCUMENT B: {name2}
            ----------------
            {doc2}

            Analyze:
            1. Shared themes or overlapping ideas
            2. Key differences in content, emphasis, or scope
            3. Differences in tone, style, or structure
            4. Missing or unique elements in each document

            Use clear sections and bullet points.
            """,
            agent=agent,
            expected_output="""A structured comparison including:
            - Similarities
            - Differences
            - Unique elements per document
            - Overall comparison insight"""
        )

    def summary_task(self, agent, analysis_task):
        return Task(
            description="""
            Summarize the comparison analysis into a concise report.

            Structure:
            1. Overview (brief comparison context)
            2. Key Similarities
            3. Key Differences
            4. Final Comparative Insight

            Write clearly and professionally.
            """,
            agent=agent,
            context=[analysis_task],
            expected_output="""A polished comparison summary with:
            - Clear sections
            - Bullet points
            - Concise professional language"""
        )


# -------------------- CREW --------------------

class DocumentComparisonCrew:
    def __init__(self, doc1_path, doc2_path):
        self.doc1_path = doc1_path
        self.doc2_path = doc2_path
        self.llm = llm

        print("\n" + "="*60)
        print("📄 LOADING DOCUMENTS")
        print("="*60)

        self.doc1_text = self._load_file(doc1_path)
        self.doc2_text = self._load_file(doc2_path)

    def _load_file(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        print(f"\n📄 Reading: {Path(path).name}")

        if path.endswith(".pdf"):
            text = read_pdf(path)
        else:
            text = read_text(path)

        if text.startswith("Error"):
            raise Exception(text)

        print(f"   ✅ Loaded ({len(text)} characters)")
        return text

    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)

        agents = DocumentComparisonAgents(self.llm)
        analyzer = agents.comparison_agent()
        summarizer = agents.summary_agent()

        print("✓ Agents created")

        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)

        tasks = DocumentComparisonTasks()

        analysis_task = tasks.analysis_task(
            analyzer,
            self.doc1_text,
            self.doc2_text,
            Path(self.doc1_path).name,
            Path(self.doc2_path).name
        )

        summary_task = tasks.summary_task(summarizer, analysis_task)

        print("✓ Tasks created")

        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)

        crew = Crew(
            agents=[analyzer, summarizer],
            tasks=[analysis_task, summary_task],
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "="*60)
        print("🚀 STARTING COMPARISON")
        print("="*60)

        result = crew.kickoff()

        print("\n" + "="*60)
        print("✅ COMPARISON COMPLETED")
        print("="*60)

        return result


# -------------------- CLI --------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Document Comparison Agent (CrewAI + Groq)"
    )

    parser.add_argument("doc1", help="First document (PDF or TXT)")
    parser.add_argument("doc2", help="Second document (PDF or TXT)")
    parser.add_argument("--output", "-o", help="Save output to file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found")
        sys.exit(1)

    try:
        crew = DocumentComparisonCrew(args.doc1, args.doc2)
        result = crew.run()

        print("\n" + "="*60)
        print("📝 DOCUMENT COMPARISON RESULT")
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
