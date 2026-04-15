import os
os.environ["RICH_DISABLE"] = "true"

import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# ===============================
# ENVIRONMENT SETUP
# ===============================
load_dotenv()

llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
    base_url="https://api.groq.com/openai/v1"
)

MEMORY_FILE = "student_memory.json"

# ===============================
# MEMORY UTILITIES
# ===============================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "student_name": None,
            "preferences": {
                "explanation_style": "simple",
                "difficulty": "medium"
            },
            "topics_studied": [],
            "progress_notes": []
        }
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)


def update_memory(memory, topic, note):
    if topic not in memory["topics_studied"]:
        memory["topics_studied"].append(topic)

    memory["progress_notes"].append(note)
    save_memory(memory)

# ===============================
# AGENTS
# ===============================
class StudyAssistantAgents:
    def __init__(self, llm_instance):
        self.llm = llm_instance

    def tutor_agent(self):
        return Agent(
            role="AI Study Tutor",
            goal="Teach topics clearly while adapting to the student's preferences and learning history",
            backstory="""You are a reliable AI tutor who remembers what the student has learned before.
You adapt explanations based on difficulty preference and past progress.
You never contradict earlier learning unless correcting misconceptions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# ===============================
# TASKS
# ===============================
class StudyAssistantTasks:
    def study_task(self, agent, topic, memory):
        return Task(
            description=f"""
You are tutoring a student.

STUDENT MEMORY:
- Preferred explanation style: {memory['preferences']['explanation_style']}
- Difficulty level: {memory['preferences']['difficulty']}
- Topics already studied: {', '.join(memory['topics_studied']) if memory['topics_studied'] else 'None'}

CURRENT TOPIC:
{topic}

TASK:
1. Explain the topic clearly and accurately
2. Adapt to the student's difficulty and style preferences
3. Build on prior knowledge if relevant
4. Include:
   - Simple explanation
   - Key concepts (bulleted)
   - One short example
5. End with a brief progress note
""",
            agent=agent,
            expected_output="""A personalized study explanation with:
- Clear explanation
- Key points
- Example
- Progress note"""
        )


# ===============================
# CREW
# ===============================
class StudyAssistantCrew:
    def __init__(self, topic):
        self.topic = topic
        self.llm = llm
        self.memory = load_memory()

        print("\n" + "=" * 60)
        print("📘 AI STUDY ASSISTANT WITH MEMORY")
        print("=" * 60)

        if not self.memory["student_name"]:
            self.memory["student_name"] = "Student"
            save_memory(self.memory)

        print(f"👤 Student: {self.memory['student_name']}")
        print(f"📚 Topics studied: {len(self.memory['topics_studied'])}")

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENT")
        print("=" * 60)

        agents = StudyAssistantAgents(self.llm)
        tutor = agents.tutor_agent()

        print("\n" + "=" * 60)
        print("📋 CREATING STUDY TASK")
        print("=" * 60)

        tasks = StudyAssistantTasks()
        study_task = tasks.study_task(tutor, self.topic, self.memory)

        crew = Crew(
            agents=[tutor],
            tasks=[study_task],
            process=Process.sequential,
            verbose=True
        )

        print("\n" + "=" * 60)
        print("🚀 STARTING STUDY SESSION")
        print("=" * 60)

        result = crew.kickoff()

        # Update memory
        update_memory(
            self.memory,
            self.topic,
            f"Studied topic '{self.topic}' with {self.memory['preferences']['difficulty']} difficulty."
        )

        print("\n" + "=" * 60)
        print("✅ STUDY SESSION COMPLETED")
        print("=" * 60)

        return result


# ===============================
# CLI
# ===============================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Study Assistant with Persistent Memory (CrewAI + Groq)"
    )
    parser.add_argument("topic", help="Topic the student wants to study")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY missing")
        sys.exit(1)

    try:
        crew = StudyAssistantCrew(args.topic)
        output = crew.run()

        print("\n" + "=" * 60)
        print("📝 STUDY OUTPUT")
        print("=" * 60 + "\n")
        print(output)
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
