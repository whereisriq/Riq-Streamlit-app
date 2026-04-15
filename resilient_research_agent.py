import os
os.environ["RICH_DISABLE"] = "true"

import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# ===============================
# ENV SETUP
# ===============================
load_dotenv()

llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,
    base_url="https://api.groq.com/openai/v1"
)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# ===============================
# SAFE FILE HANDLING
# ===============================
def safe_read_text(file_path: str):
    """
    Safely read a text file with validation and controlled failure.
    """
    if not file_path:
        return None, "No file path provided"

    path = Path(file_path)

    if not path.exists():
        return None, f"File not found: {file_path}"

    if path.suffix.lower() not in [".txt", ".md"]:
        return None, f"Unsupported file type: {path.suffix}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return None, "File is empty"

        return content[:15000], None

    except Exception as e:
        return None, f"Failed to read file: {str(e)}"


# ===============================
# AGENTS
# ===============================
class ResilientResearchAgents:
    def __init__(self, llm_instance):
        self.llm = llm_instance

    def research_agent(self):
        return Agent(
            role="Resilient Research Analyst",
            goal="Analyze research input reliably while handling incomplete or faulty data safely",
            backstory="""You are a production-grade research agent.
You never hallucinate missing data.
If information is insufficient, you clearly state limitations.
You prioritize correctness, clarity, and operational safety.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# ===============================
# TASKS
# ===============================
class ResilientResearchTasks:
    def research_task(self, agent, content):
        return Task(
            description=f"""
Analyze the following research input safely and conservatively.

CONTENT:
{content}

INSTRUCTIONS:
1. Summarize the main topic
2. Extract key points (only if explicitly present)
3. Identify missing or unclear information
4. Clearly state limitations
5. DO NOT assume facts not present

If the content is weak or incomplete, explain why.
""",
            agent=agent,
            expected_output="""A safe research analysis containing:
- Main topic
- Key points (if available)
- Identified gaps or missing data
- Limitations and confidence level"""
        )


# ===============================
# CREW
# ===============================
class ResilientResearchCrew:
    def __init__(self, file_path):
        self.file_path = file_path
        self.llm = llm
        self.content = None

        print("\n" + "=" * 60)
        print("🛡️ ERROR-RESILIENT RESEARCH AGENT")
        print("=" * 60)

    def load_with_retries(self):
        """
        Retry logic for recoverable file errors.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n📄 Attempt {attempt}/{MAX_RETRIES} — Loading file")

            content, error = safe_read_text(self.file_path)

            if content:
                print("✅ File loaded successfully")
                return content

            print(f"⚠️  Load failed: {error}")

            if attempt < MAX_RETRIES:
                print(f"🔄 Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

        return None

    def run(self):
        self.content = self.load_with_retries()

        if not self.content:
            print("\n❌ SAFE FAILURE")
            print("Reason: Input could not be loaded after retries.")
            print("No agent execution performed.")
            return "Research aborted safely due to invalid or missing input."

        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENT")
        print("=" * 60)

        agents = ResilientResearchAgents(self.llm)
        researcher = agents.research_agent()

        print("\n" + "=" * 60)
        print("📋 CREATING TASK")
        print("=" * 60)

        tasks = ResilientResearchTasks()
        research_task = tasks.research_task(researcher, self.content)

        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True
        )

        print("\n" + "=" * 60)
        print("🚀 STARTING SAFE EXECUTION")
        print("=" * 60)

        try:
            result = crew.kickoff()
        except Exception as e:
            print("\n❌ AGENT FAILURE (Handled Safely)")
            print(f"Reason: {str(e)}")
            return "Agent execution failed safely."

        print("\n" + "=" * 60)
        print("✅ RESEARCH COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return result


# ===============================
# CLI
# ===============================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Error-Resilient Research Agent (CrewAI + Groq)"
    )
    parser.add_argument("file", help="Path to research input text file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found")
        sys.exit(1)

    try:
        crew = ResilientResearchCrew(args.file)
        output = crew.run()

        print("\n" + "=" * 60)
        print("📝 FINAL OUTPUT")
        print("=" * 60 + "\n")
        print(output)
        print("\n" + "=" * 60)

    except Exception as e:
        print("\n❌ UNEXPECTED FAILURE (SAFE EXIT)")
        print(str(e))
        sys.exit(1)
