import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import sys
import argparse
from typing import Optional
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Groq LLM
def get_llm(api_key: Optional[str] = None) -> LLM:
    """Initialize and return Groq LLM instance with error handling."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not found in environment or parameters")
    
    return LLM(
        model="llama-3.1-8b-instant",
        api_key=key,
        temperature=0.6,
        base_url="https://api.groq.com/openai/v1"
    )

llm = get_llm()


# =========================
# AGENTS
# =========================

class ExamAgents:
    """Agents for exam question generation and review"""

    def __init__(self, llm_instance: LLM) -> None:
        """Initialize agents with LLM instance.
        
        Args:
            llm_instance: The language model to use for agent reasoning
        """
        self.llm = llm_instance

    def question_generator(self) -> Agent:
        """Create an agent specialized in generating exam questions."""
        return Agent(
            role="Exam Question Designer",
            goal="Generate high-quality exam questions aligned with learning objectives",
            backstory="""You are an experienced educator and assessment specialist.
            You design exam questions that are clear, fair, and aligned with
            Bloom’s taxonomy and academic standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def question_reviewer(self) -> Agent:
        """Create an agent specialized in reviewing exam question quality."""
        return Agent(
            role="Assessment Quality Reviewer",
            goal="Evaluate exam questions for clarity, difficulty, and educational alignment",
            backstory="""You are a senior academic reviewer specializing in assessment
            validation. You ensure questions are unambiguous, appropriately difficult,
            and aligned with learning outcomes.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def question_editor(self) -> Agent:
        """Create an agent specialized in refining exam questions."""
        return Agent(
            role="Exam Question Editor",
            goal="Refine exam questions based on review feedback",
            backstory="""You specialize in improving assessment items. You rewrite
            questions to enhance clarity, balance difficulty, and ensure fairness
            while preserving learning intent.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# =========================
# TASKS
# =========================

class ExamTasks:
    """Tasks for question generation, review, and refinement"""

    def generation_task(self, agent: Agent, subject: str, topic: str, difficulty: str) -> Task:
        return Task(
            description=f"""
            Generate 6 exam questions for the following:

            Subject: {subject}
            Topic: {topic}
            Difficulty Level: {difficulty}

            Requirements:
            - Include a mix of question types (short answer, essay, applied)
            - Align with Bloom’s taxonomy
            - Avoid ambiguity
            - Ensure academic integrity

            Label each question with:
            - Question number
            - Question type
            - Bloom’s level
            """,
            agent=agent,
            expected_output="""6 well-structured exam questions with:
            - Clear wording
            - Labeled Bloom’s levels
            - Appropriate difficulty"""
        )

    def review_task(self, agent: Agent, generation_task: Task) -> Task:
        return Task(
            description="""
            Review the generated exam questions.

            Assess each question for:
            1. Clarity of wording
            2. Alignment with topic and difficulty
            3. Cognitive level (Bloom’s taxonomy)
            4. Potential ambiguity or bias
            5. Overall assessment quality

            Provide structured feedback per question.
            """,
            agent=agent,
            expected_output="""A structured review including:
            - Strengths of each question
            - Weaknesses or risks
            - Difficulty appropriateness
            - Suggestions for improvement""",
            context=[generation_task]
        )

    def refinement_task(self, agent: Agent, generation_task: Task, review_task: Task) -> Task:
        return Task(
            description="""
            Improve and rewrite the exam questions based on the reviewer’s feedback.

            Goals:
            - Improve clarity
            - Adjust difficulty where needed
            - Preserve learning objectives
            - Ensure fairness and consistency

            Output only the FINAL revised questions.
            """,
            agent=agent,
            expected_output="""A finalized set of polished exam questions that:
            - Are clear and unambiguous
            - Match stated difficulty
            - Meet educational assessment standards""",
            context=[generation_task, review_task]
        )


# =========================
# CREW
# =========================

class ExamQuestionCrew:
    """Orchestrates exam question generation and review"""

    def __init__(self, subject: str, topic: str, difficulty: str, output_file: Optional[str] = None) -> None:
        """Initialize the exam question crew.
        
        Args:
            subject: Course or subject name
            topic: Specific topic to generate questions for
            difficulty: Difficulty level (easy, medium, hard)
            output_file: Optional file path to save results
        """
        self.subject = subject
        self.topic = topic
        self.difficulty = difficulty
        self.llm = llm
        self.output_file = output_file

    def run(self) -> str:
        print("\n" + "=" * 60)
        print("📘 EXAM QUESTION GENERATOR & REVIEWER")
        print("=" * 60)

        agents = ExamAgents(self.llm)
        generator = agents.question_generator()
        reviewer = agents.question_reviewer()
        editor = agents.question_editor()

        tasks = ExamTasks()

        gen_task = tasks.generation_task(
            generator,
            self.subject,
            self.topic,
            self.difficulty
        )

        review_task = tasks.review_task(reviewer, gen_task)
        refine_task = tasks.refinement_task(editor, gen_task, review_task)

        crew = Crew(
            agents=[generator, reviewer, editor],
            tasks=[gen_task, review_task, refine_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ FINAL EXAM QUESTIONS")
        print("=" * 60)
        print(str(result))

        # Save to file if specified
        if self.output_file:
            self._save_results(result)

        return result

    def _save_results(self, result: str) -> None:
        """Save exam questions to a file.
        
        Args:
            result: The generated exam questions text
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_file.replace(".txt", f"_{timestamp}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Subject: {self.subject}\n")
                f.write(f"Topic: {self.topic}\n")
                f.write(f"Difficulty: {self.difficulty}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("\n" + "=" * 60 + "\n\n")
                f.write(str(result))
            print(f"\n💾 Results saved to: {filename}")
        except IOError as e:
            print(f"\n⚠️  Warning: Could not save to file: {e}")


# =========================
# CLI
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Exam Question Generator & Reviewer (CrewAI + Groq)"
    )

    parser.add_argument("--subject", required=True, help="Course or subject name")
    parser.add_argument("--topic", required=True, help="Specific topic")
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Difficulty level"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional file path to save results"
    )

    args = parser.parse_args()

    # Validate required environment variable
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    try:
        crew = ExamQuestionCrew(
            subject=args.subject,
            topic=args.topic,
            difficulty=args.difficulty,
            output_file=args.output
        )
        output = crew.run()

    except ValueError as e:
        print(f"\n❌ CONFIGURATION ERROR: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
