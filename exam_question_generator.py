import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import sys

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,
    base_url="https://api.groq.com/openai/v1"
)


# =========================
# AGENTS
# =========================

class ExamAgents:
    """Agents for exam question generation and review"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def question_generator(self):
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

    def question_reviewer(self):
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

    def question_editor(self):
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

    def generation_task(self, agent, subject, topic, difficulty):
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

    def review_task(self, agent, generation_task):
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

    def refinement_task(self, agent, generation_task, review_task):
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

    def __init__(self, subject, topic, difficulty):
        self.subject = subject
        self.topic = topic
        self.difficulty = difficulty
        self.llm = llm

    def run(self):
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

        return result


# =========================
# CLI
# =========================

if __name__ == "__main__":
    import argparse

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

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    try:
        crew = ExamQuestionCrew(
            subject=args.subject,
            topic=args.topic,
            difficulty=args.difficulty
        )
        output = crew.run()
        print("\n" + str(output))

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
