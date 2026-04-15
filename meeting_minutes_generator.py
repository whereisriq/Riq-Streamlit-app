import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4,
    base_url="https://api.groq.com/openai/v1"
)


def read_transcript(file_path):
    """Read meeting transcript from text file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading transcript: {str(e)}"


# =========================
# AGENTS
# =========================

class MeetingMinutesAgents:
    """Define agents for meeting minutes generation"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def analyst_agent(self):
        return Agent(
            role="Meeting Analyst",
            goal="Analyze meeting transcripts to extract key discussions, decisions, and action items",
            backstory="""You are a professional meeting analyst experienced in corporate 
            governance and documentation. You identify agenda items, key discussion points, 
            decisions made, and assigned actions accurately.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def writer_agent(self):
        return Agent(
            role="Meeting Minutes Writer",
            goal="Produce clear, formal, and well-structured meeting minutes",
            backstory="""You are an executive assistant skilled in writing formal meeting minutes.
            You follow professional standards, maintain neutrality, and ensure clarity 
            for stakeholders and leadership.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# =========================
# TASKS
# =========================

class MeetingMinutesTasks:
    """Define tasks for meeting minutes creation"""

    def analysis_task(self, agent, transcript):
        return Task(
            description=f"""
            Analyze the following meeting transcript and extract structured information.

            TRANSCRIPT:
            {transcript[:15000]}

            Extract:
            1. Meeting purpose and agenda items
            2. Key discussion points (bullet points)
            3. Decisions made
            4. Action items (with responsible person if mentioned)
            5. Any unresolved issues or follow-ups

            Be factual and concise.
            """,
            agent=agent,
            expected_output="""Structured analysis containing:
            - Agenda items
            - Discussion highlights
            - Decisions
            - Action items
            - Follow-ups"""
        )

    def writing_task(self, agent, analysis_task):
        return Task(
            description="""
            Using the analyzed meeting content, write formal meeting minutes.

            Format the minutes as follows:

            MEETING MINUTES

            1. Meeting Information
               - Date (if mentioned)
               - Participants (if mentioned)
               - Purpose

            2. Agenda Overview

            3. Discussion Summary
               - Organized by agenda item

            4. Decisions Made

            5. Action Items
               - Action | Owner | Deadline (if available)

            6. Next Steps / Follow-ups

            Writing Guidelines:
            - Use professional, neutral tone
            - Clear headings and bullet points
            - No unnecessary commentary
            - Suitable for official records
            """,
            agent=agent,
            expected_output="""A professionally formatted set of meeting minutes with:
            - Clear sections and headings
            - Concise summaries
            - Clearly listed decisions and action items""",
            context=[analysis_task]
        )


# =========================
# CREW
# =========================

class MeetingMinutesCrew:
    """Orchestrate the meeting minutes generation"""

    def __init__(self, transcript_path):
        self.transcript_path = transcript_path
        self.llm = llm

        print("\n" + "=" * 60)
        print("📄 LOADING MEETING TRANSCRIPT")
        print("=" * 60)

        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"File not found: {transcript_path}")

        print(f"📄 Reading: {Path(transcript_path).name}")
        self.transcript = read_transcript(transcript_path)

        if self.transcript.startswith("Error"):
            raise Exception(self.transcript)

        print(f"✅ Transcript loaded ({len(self.transcript)} characters)")

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENTS")
        print("=" * 60)

        agents = MeetingMinutesAgents(self.llm)
        analyst = agents.analyst_agent()
        writer = agents.writer_agent()
        print("✓ Agents created: Analyst & Writer")

        print("\n" + "=" * 60)
        print("📋 CREATING TASKS")
        print("=" * 60)

        tasks = MeetingMinutesTasks()
        analysis_task = tasks.analysis_task(analyst, self.transcript)
        writing_task = tasks.writing_task(writer, analysis_task)
        print("✓ Tasks created: Analysis & Writing")

        print("\n" + "=" * 60)
        print("👥 ASSEMBLING CREW")
        print("=" * 60)

        crew = Crew(
            agents=[analyst, writer],
            tasks=[analysis_task, writing_task],
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "=" * 60)
        print("🚀 GENERATING MEETING MINUTES")
        print("=" * 60 + "\n")

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ MEETING MINUTES COMPLETED")
        print("=" * 60)

        return result


# =========================
# CLI
# =========================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Meeting Minutes Generator (CrewAI + Groq)"
    )

    parser.add_argument("transcript", help="Path to meeting transcript (.txt)")
    parser.add_argument("--output", "-o", help="Save minutes to file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("AI MEETING MINUTES GENERATOR")
    print("=" * 60)
    print("📊 Model: groq/llama-3.1-8b-instant")
    print(f"📄 Transcript: {Path(args.transcript).name}")
    print("=" * 60)

    try:
        crew = MeetingMinutesCrew(args.transcript)
        result = crew.run()

        print("\n" + "=" * 60)
        print("📝 MEETING MINUTES")
        print("=" * 60 + "\n")
        print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("MEETING MINUTES\n")
                f.write("=" * 60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
