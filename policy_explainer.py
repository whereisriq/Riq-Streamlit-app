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

# Initialize Groq with Llama model
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,
    base_url="https://api.groq.com/openai/v1"
)


def extract_pdf_text(file_path):
    """Extract text from a policy PDF"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Check file size (warn if > 10MB)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 10:
            print(f"   ⚠️  Large file detected ({file_size_mb:.1f} MB), processing may take longer")
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            if len(reader.pages) == 0:
                raise ValueError("PDF contains no pages")
            
            text = ""
            print(f"   📄 Extracting {len(reader.pages)} pages...")

            for i, page in enumerate(reader.pages, 1):
                extracted = page.extract_text()
                if extracted:
                    text += f"\n--- Page {i} ---\n"
                    text += extracted

                if len(text) > 50000:
                    print("   ⚠️  Content truncated to prevent token overflow")
                    break

            if not text.strip():
                raise ValueError("No readable text found in PDF")
            
            return text
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


class PolicyExplainerAgents:
    """Agents for policy understanding and explanation"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def policy_analyst_agent(self):
        return Agent(
            role="University Policy Analyst",
            goal="Understand and interpret complex university policy documents accurately",
            backstory="""You are a policy specialist experienced in analyzing academic
            and institutional policies. You extract intent, obligations, rules, and scope
            from formal policy language.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def simplifier_agent(self):
        return Agent(
            role="Student-Focused Policy Explainer",
            goal="Translate university policies into simple, student-friendly language",
            backstory="""You specialize in audience-aware writing. You explain complex
            policies clearly to students, parents, and non-legal audiences without
            losing accuracy.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def faq_agent(self):
        return Agent(
            role="Policy FAQ Writer",
            goal="Create clear and practical FAQs based on policy rules and implications",
            backstory="""You anticipate common questions students ask about policies
            and answer them clearly, accurately, and reassuringly.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class PolicyExplainerTasks:
    """Tasks for explaining university policies"""

    def analysis_task(self, agent, policy_text):
        return Task(
            description=f"""
            Analyze the following university policy document:

            POLICY CONTENT:
            {policy_text[:15000]}

            Extract:
            1. Purpose of the policy
            2. Who it applies to
            3. Key rules and requirements
            4. Rights and responsibilities
            5. Consequences of non-compliance

            Be precise and faithful to the policy language.
            """,
            agent=agent,
            expected_output="""Structured analysis including:
            - Policy purpose
            - Scope and applicability
            - Key rules
            - Responsibilities
            - Enforcement or consequences"""
        )

    def simplification_task(self, agent, analysis_task):
        return Task(
            description="""
            Using the policy analysis, write a simplified explanation
            suitable for undergraduate students.

            Requirements:
            - Plain language
            - Short paragraphs
            - No legal jargon
            - Explain what students MUST do and SHOULD know

            Tone: clear, supportive, and informative.
            """,
            agent=agent,
            expected_output="""Plain-language explanation including:
            - What the policy is about
            - Why it matters to students
            - What students need to do""",
            context=[analysis_task]
        )

    def faq_task(self, agent, analysis_task):
        return Task(
            description="""
            Create a FAQ section based on the policy analysis.

            Include:
            - 8–12 realistic student questions
            - Clear, concise answers
            - Practical scenarios where helpful

            Assume the reader has NOT read the policy.
            """,
            agent=agent,
            expected_output="""FAQ section with:
            - At least 8 questions
            - Clear student-focused answers""",
            context=[analysis_task]
        )


class PolicyExplainerCrew:
    """Orchestrates the policy explanation workflow"""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.llm = llm

        print("\n" + "=" * 60)
        print("📘 LOADING UNIVERSITY POLICY")
        print("=" * 60)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")

        print(f"\n📄 Reading: {Path(pdf_path).name}")
        
        try:
            self.policy_text = extract_pdf_text(pdf_path)
            print(f"✅ Loaded policy ({len(self.policy_text)} characters)")
        except Exception as e:
            print(f"❌ Failed to extract PDF: {str(e)}")
            raise

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENTS")
        print("=" * 60)

        agents = PolicyExplainerAgents(self.llm)
        analyst = agents.policy_analyst_agent()
        simplifier = agents.simplifier_agent()
        faq_writer = agents.faq_agent()

        print("✓ Agents created: Analyst, Simplifier, FAQ Writer")

        print("\n" + "=" * 60)
        print("📋 CREATING TASKS")
        print("=" * 60)

        tasks = PolicyExplainerTasks()
        analysis = tasks.analysis_task(analyst, self.policy_text)
        simplified = tasks.simplification_task(simplifier, analysis)
        faq = tasks.faq_task(faq_writer, analysis)

        all_tasks = [analysis, simplified, faq]

        print("\n" + "=" * 60)
        print("👥 ASSEMBLING CREW")
        print("=" * 60)

        crew = Crew(
            agents=[analyst, simplifier, faq_writer],
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "=" * 60)
        print("🚀 STARTING EXECUTION")
        print("=" * 60)

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ POLICY EXPLANATION COMPLETED!")
        print("=" * 60)

        return result


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="University Policy Document Explainer (CrewAI + Groq)",
        epilog="""
Examples:
  python policy_explainer.py policy.pdf
  python policy_explainer.py policy.pdf --output explanation.txt
        """
    )

    parser.add_argument("policy_pdf", help="Path to university policy PDF")
    parser.add_argument("--output", "-o", help="Output file path (optional)")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("UNIVERSITY POLICY EXPLAINER")
    print("=" * 60)
    print("📊 Model: groq/llama-3.1-8b-instant")
    print(f"📄 Policy: {Path(args.policy_pdf).name}")
    print("=" * 60)

    try:
        crew = PolicyExplainerCrew(args.policy_pdf)
        result = crew.run()

        print("\n" + "=" * 60)
        print("📝 POLICY EXPLANATION OUTPUT")
        print("=" * 60 + "\n")
        print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("UNIVERSITY POLICY EXPLANATION\n")
                f.write("=" * 60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
