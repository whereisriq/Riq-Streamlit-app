import os
os.environ["RICH_DISABLE"] = "true"

import sys
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# ===============================
# ENV SETUP
# ===============================
load_dotenv()

BASE_MODEL = "llama-3.1-8b-instant"

# ===============================
# SAFE FILE READ
# ===============================
def read_input_text(file_path):
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError("Input file is empty")

    return content[:12000]


# ===============================
# AGENTS
# ===============================
class ToneAdaptiveAgents:
    def academic_agent(self):
        return Agent(
            role="Academic Writing Specialist",
            goal="Rewrite content in formal academic tone",
            backstory="""You are a university-level academic writer.
You use formal language, third person, precise terminology,
and avoid conversational phrasing.""",
            verbose=True,
            allow_delegation=False,
            llm=LLM(
                model=BASE_MODEL,
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.2,  # LOW = precision
                base_url="https://api.groq.com/openai/v1"
            )
        )

    def conversational_agent(self):
        return Agent(
            role="Conversational Writing Assistant",
            goal="Rewrite content in a friendly, conversational tone",
            backstory="""You write as if explaining to a peer.
You are engaging, clear, and approachable,
using simple language and natural flow.""",
            verbose=True,
            allow_delegation=False,
            llm=LLM(
                model=BASE_MODEL,
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.7,  # HIGHER = expressive
                base_url="https://api.groq.com/openai/v1"
            )
        )

    def corporate_agent(self):
        return Agent(
            role="Corporate Communications Writer",
            goal="Rewrite content in a professional corporate tone",
            backstory="""You are a corporate communications expert.
You write concisely, professionally, and strategically,
suitable for reports, briefings, and stakeholders.""",
            verbose=True,
            allow_delegation=False,
            llm=LLM(
                model=BASE_MODEL,
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.4,  # BALANCED
                base_url="https://api.groq.com/openai/v1"
            )
        )


# ===============================
# TASKS
# ===============================
class ToneAdaptiveTasks:
    def rewrite_task(self, agent, content, tone_label):
        return Task(
            description=f"""
Rewrite the following content in **{tone_label} tone**.

CONTENT:
{content}

Guidelines:
- Preserve original meaning
- Adjust language, style, and structure to match the tone
- Do not add new facts
""",
            agent=agent,
            expected_output=f"""A rewritten version of the content in {tone_label} tone,
maintaining clarity, coherence, and intent."""
        )


# ===============================
# CREW
# ===============================
class ToneAdaptiveCrew:
    def __init__(self, input_file):
        self.input_file = input_file
        self.content = read_input_text(input_file)

        print("\n" + "=" * 60)
        print("✍️ TONE-ADAPTIVE WRITING AGENT")
        print("=" * 60)
        print(f"📄 Input file: {Path(input_file).name}")
        print("=" * 60)

    def run(self):
        agents = ToneAdaptiveAgents()
        tasks_builder = ToneAdaptiveTasks()

        academic = agents.academic_agent()
        conversational = agents.conversational_agent()
        corporate = agents.corporate_agent()

        academic_task = tasks_builder.rewrite_task(
            academic, self.content, "ACADEMIC"
        )
        conversational_task = tasks_builder.rewrite_task(
            conversational, self.content, "CONVERSATIONAL"
        )
        corporate_task = tasks_builder.rewrite_task(
            corporate, self.content, "CORPORATE"
        )

        crew = Crew(
            agents=[academic, conversational, corporate],
            tasks=[academic_task, conversational_task, corporate_task],
            process=Process.sequential,
            verbose=True
        )

        print("\n" + "=" * 60)
        print("🚀 STARTING TONE ADAPTATION")
        print("=" * 60)

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ WRITING COMPLETED")
        print("=" * 60)

        return result


# ===============================
# CLI
# ===============================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Tone-Adaptive Writing Agent (CrewAI + Groq)"
    )
    parser.add_argument("input", help="Path to input text file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found")
        sys.exit(1)

    try:
        crew = ToneAdaptiveCrew(args.input)
        output = crew.run()

        print("\n" + "=" * 60)
        print("📝 FINAL OUTPUT")
        print("=" * 60 + "\n")
        print(output)
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
