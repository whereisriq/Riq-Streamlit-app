import os
os.environ["RICH_DISABLE"] = "true"

import sys
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import PyPDF2

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,
    base_url="https://api.groq.com/openai/v1"
)

# -------------------------------
# Document Utilities
# -------------------------------

def read_pdf(file_path):
    """Extract text from PDF document"""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for i, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                text += f"\n--- Page {i} ---\n{page_text}\n"
                if len(text) > 50000:
                    break
            return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def read_text(file_path):
    """Read text document"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


# -------------------------------
# Agents
# -------------------------------

class SchoolAdminAgents:
    """Define agents for school administration assistance"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def admin_assistant_agent(self):
        return Agent(
            role="School Administration Assistant",
            goal="Answer administrative questions using only the provided school documents",
            backstory="""You are a professional school administration assistant.
            You help students, staff, and parents understand policies, procedures,
            deadlines, and administrative processes.

            You strictly base your answers on the provided documents.
            If information is missing, you clearly state that it is not available.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            memory=True
        )


# -------------------------------
# Tasks
# -------------------------------

class SchoolAdminTasks:
    """Define tasks for administrative Q&A"""

    def admin_question_task(self, agent, documents, question):
        return Task(
            description=f"""
            You are given official school administrative documents and a user question.

            DOCUMENTS:
            ====================
            {documents[:20000]}
            ====================

            USER QUESTION:
            "{question}"

            Instructions:
            - Answer ONLY using the information from the documents
            - Do NOT guess or hallucinate
            - If the answer is not found, clearly state that
            - Use clear, professional administrative language
            - Cite which section/page the answer comes from if possible
            """,
            agent=agent,
            expected_output="""A clear administrative answer that:
            - Is grounded in the provided documents
            - Uses professional tone
            - Clearly states limitations if information is missing"""
        )


# -------------------------------
# Crew Orchestration
# -------------------------------

class SchoolAdminCrew:
    """Orchestrates the school admin assistant workflow"""

    def __init__(self, document_paths, question):
        self.document_paths = document_paths
        self.question = question
        self.llm = llm
        self.documents_text = ""

        print("\n" + "=" * 60)
        print("📂 LOADING ADMINISTRATIVE DOCUMENTS")
        print("=" * 60)

        for i, path in enumerate(document_paths, 1):
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

            print(f"\n{i}. {Path(path).name}")

            if path.endswith(".pdf"):
                content = read_pdf(path)
            else:
                content = read_text(path)

            if content.startswith("Error"):
                raise Exception(content)

            self.documents_text += f"\n\n### DOCUMENT: {Path(path).name}\n{content}"
            print(f"   ✅ Loaded ({len(content)} characters)")

        print(f"\n✅ Loaded {len(document_paths)} administrative documents")

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENT")
        print("=" * 60)

        agents = SchoolAdminAgents(self.llm)
        admin_agent = agents.admin_assistant_agent()
        print("✓ School Administration Assistant ready")

        print("\n" + "=" * 60)
        print("📋 CREATING TASK")
        print("=" * 60)

        tasks = SchoolAdminTasks()
        admin_task = tasks.admin_question_task(
            admin_agent,
            self.documents_text,
            self.question
        )

        print("✓ Administrative Q&A task created")

        print("\n" + "=" * 60)
        print("👥 ASSEMBLING CREW")
        print("=" * 60)

        crew = Crew(
            agents=[admin_agent],
            tasks=[admin_task],
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "=" * 60)
        print("🚀 ANSWERING QUESTION")
        print("=" * 60)

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ QUESTION ANSWERED")
        print("=" * 60)

        return result


# -------------------------------
# CLI Interface
# -------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="School Administration Assistant (CrewAI + Groq)",
        epilog="""
Examples:
  python school_admin_assistant.py handbook.pdf "What is the attendance policy?"
  python school_admin_assistant.py policy.pdf calendar.txt "When is course registration?"
        """
    )

    parser.add_argument("documents", nargs="+", help="School policy PDFs or text files")
    parser.add_argument("--question", "-q", required=True, help="Administrative question")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🏫 SCHOOL ADMINISTRATION ASSISTANT")
    print("=" * 60)
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print(f"📄 Documents: {len(args.documents)}")
    print(f"❓ Question: {args.question}")
    print("=" * 60)

    try:
        crew = SchoolAdminCrew(args.documents, args.question)
        result = crew.run()

        print("\n" + "=" * 60)
        print("📝 ADMINISTRATIVE RESPONSE")
        print("=" * 60 + "\n")
        print(result)
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
