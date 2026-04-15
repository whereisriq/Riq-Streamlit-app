import os
os.environ["RICH_DISABLE"] = "true"

import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import PyPDF2

# =====================================================
# ENV + MODEL SETUP
# =====================================================

load_dotenv()

llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
    base_url="https://api.groq.com/openai/v1"
)

MEMORY_FILE = "office_memory.json"

# =====================================================
# MEMORY HANDLER (PERSISTENT JSON MEMORY)
# =====================================================

class OfficeMemory:
    def __init__(self, path=MEMORY_FILE):
        self.path = path
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return {
                "documents": {},
                "questions": [],
                "summaries": []
            }
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def store_document(self, name, content):
        self.data["documents"][name] = content[:20000]
        self.save()

    def log_question(self, question):
        self.data["questions"].append(question)
        self.save()

    def log_summary(self, summary):
        self.data["summaries"].append(summary)
        self.save()


# =====================================================
# FILE TOOLS
# =====================================================

def read_pdf(path):
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        return f"ERROR: {str(e)}"


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {str(e)}"


# =====================================================
# AGENTS
# =====================================================

class OfficeAgents:
    def __init__(self, llm):
        self.llm = llm

    def document_reader(self):
        return Agent(
            role="Document Reader",
            goal="Accurately read and extract content from office documents",
            backstory="You are a meticulous office assistant skilled in reading official documents.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def summarizer(self):
        return Agent(
            role="Document Summarizer",
            goal="Produce clear, professional summaries of documents",
            backstory="You summarize documents clearly for busy professionals.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def qa_agent(self):
        return Agent(
            role="Office Q&A Assistant",
            goal="Answer user questions using uploaded documents",
            backstory="You answer questions strictly grounded in office documents.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def reliability_agent(self):
        return Agent(
            role="Reliability Monitor",
            goal="Detect errors, missing data, or uncertainty and respond safely",
            backstory="You ensure reliability, flag missing info, and prevent hallucination.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# =====================================================
# TASKS
# =====================================================

class OfficeTasks:

    def read_task(self, agent, content, name):
        return Task(
            description=f"""
            Read the following office document:

            DOCUMENT NAME: {name}

            CONTENT:
            {content[:15000]}

            Ensure accurate understanding.
            """,
            agent=agent,
            expected_output="Confirmation that the document has been read and understood."
        )

    def summarize_task(self, agent, content):
        return Task(
            description="""
            Summarize this document for office use.

            Requirements:
            - Professional tone
            - Bullet points
            - Clear sections
            - 150–250 words
            """,
            agent=agent,
            expected_output="A professional document summary."
        )

    def qa_task(self, agent, content, question):
        return Task(
            description=f"""
            Answer the following question using ONLY the document content.

            QUESTION:
            {question}

            DOCUMENT CONTENT:
            {content[:15000]}

            If the answer is not found, clearly say so.
            """,
            agent=agent,
            expected_output="A grounded, accurate answer."
        )

    def reliability_task(self, agent, previous_task):
        return Task(
            description="""
            Review the previous output.
            - Check for unsupported claims
            - Flag uncertainty
            - Suggest safer wording if needed
            """,
            agent=agent,
            context=[previous_task],
            expected_output="Reliability validation or correction."
        )


# =====================================================
# CREW ORCHESTRATOR
# =====================================================

class OfficeAssistantCrew:
    def __init__(self, file_path, question=None):
        self.file_path = file_path
        self.question = question
        self.memory = OfficeMemory()

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print("\n📂 Loading document...")
        if file_path.endswith(".pdf"):
            self.content = read_pdf(file_path)
        else:
            self.content = read_text(file_path)

        if self.content.startswith("ERROR"):
            raise Exception(self.content)

        self.memory.store_document(Path(file_path).name, self.content)
        print("✅ Document loaded successfully")

    def run(self):
        agents = OfficeAgents(llm)
        tasks = OfficeTasks()

        reader = agents.document_reader()
        summarizer = agents.summarizer()
        qa = agents.qa_agent()
        reliability = agents.reliability_agent()

        read_task = tasks.read_task(reader, self.content, self.file_path)
        summary_task = tasks.summarize_task(summarizer, self.content)

        task_list = [read_task, summary_task]

        if self.question:
            self.memory.log_question(self.question)
            qa_task = tasks.qa_task(qa, self.content, self.question)
            reliability_task = tasks.reliability_task(reliability, qa_task)
            task_list.extend([qa_task, reliability_task])

        crew = Crew(
            agents=[reader, summarizer, qa, reliability],
            tasks=task_list,
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        self.memory.log_summary(str(result))
        return result


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Capstone AI Office Assistant (CrewAI + Groq)"
    )

    parser.add_argument("file", help="Office document (PDF or TXT)")
    parser.add_argument("--question", "-q", help="Ask a question about the document")
    parser.add_argument("--output", "-o", help="Save output to file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY missing")
        sys.exit(1)

    try:
        assistant = OfficeAssistantCrew(args.file, args.question)
        result = assistant.run()

        print("\n" + "="*60)
        print("🏢 AI OFFICE ASSISTANT OUTPUT")
        print("="*60 + "\n")
        print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
