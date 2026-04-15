import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import sys

# --------------------------------------------------
# ENVIRONMENT SETUP
# --------------------------------------------------
load_dotenv()

llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    base_url="https://api.groq.com/openai/v1"
)

# --------------------------------------------------
# AGENTS
# --------------------------------------------------
class BlogAgents:
    """Agents for AI blog creation"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def researcher(self):
        return Agent(
            role="Content Researcher",
            goal="Research the blog topic and produce structured insights and key points",
            backstory="""You are a digital content researcher skilled in online research,
            trend analysis, and idea structuring. You extract accurate, relevant,
            and engaging information suitable for blog writing.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def writer(self):
        return Agent(
            role="Blog Writer",
            goal="Write a compelling, well-structured blog post based on research input",
            backstory="""You are an experienced blog writer who crafts engaging,
            reader-friendly articles with clear structure, strong hooks,
            and smooth transitions.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def editor(self):
        return Agent(
            role="Content Editor",
            goal="Edit and polish the blog for clarity, flow, grammar, and engagement",
            backstory="""You are a professional editor. You improve clarity,
            coherence, tone, and overall writing quality while preserving meaning.
            You ensure the final content is publication-ready.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

# --------------------------------------------------
# TASKS
# --------------------------------------------------
class BlogTasks:
    def research_task(self, agent, topic):
        return Task(
            description=f"""
            Research the topic: {topic}

            Provide:
            - Background
            - Key points
            - Examples
            - Audience
            - Blog angle
            """,
            agent=agent,
            expected_output="""
            Structured research notes including:
            - Overview
            - 5–7 key points
            - Examples
            - Audience insights
            - Blog angle
            """
        )

    def writing_task(self, agent, topic, research_task):
        return Task(
            description=f"""
            Write a blog post based on the research provided.

            TOPIC:
            {topic}

            Requirements:
            - Length: 700–900 words
            - Clear introduction, body, and conclusion
            - Engaging and student-friendly tone
            - Use headings and short paragraphs
            - Maintain logical flow

            The blog should be informative, engaging, and easy to read.
            """,
            agent=agent,
            expected_output="""A complete blog draft (700–900 words) with:
            - Strong introduction
            - Well-organized sections
            - Clear conclusion""",
            context=[research_task]
        )

    def editing_task(self, agent, writing_task):
        return Task(
            description="""
            Edit the blog post for:
            - Clarity and coherence
            - Grammar and sentence structure
            - Engagement and readability
            - Consistent tone and flow

            Improve quality without changing core ideas.
            """,
            agent=agent,
            expected_output="""A polished, publication-ready blog post with:
            - Improved flow
            - Clear language
            - Professional editing""",
            context=[writing_task]
        )

# --------------------------------------------------
# CREW ORCHESTRATION
# --------------------------------------------------
class BlogCrew:
    """Orchestrates the AI blog creation workflow"""

    def __init__(self, topic):
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        if len(topic) < 3:
            raise ValueError("Topic must be at least 3 characters long")
        
        if len(topic) > 200:
            raise ValueError("Topic must be less than 200 characters long")
        
        self.topic = topic.strip()
        self.llm = llm

    def run(self):
        print("\n" + "="*60)
        print("🧠 AI CONTENT CREATION TEAM")
        print("="*60)
        print(f"✏️ Topic: {self.topic}")
        print("="*60)

        agents = BlogAgents(self.llm)
        tasks = BlogTasks()

        researcher = agents.researcher()
        writer = agents.writer()
        editor = agents.editor()

        research = tasks.research_task(researcher, self.topic)
        writing = tasks.writing_task(writer, self.topic, research)
        editing = tasks.editing_task(editor, writing)

        crew = Crew(
            agents=[researcher, writer, editor],
            tasks=[research, writing, editing],
            process=Process.sequential,
            verbose=True
        )

        print("\n🚀 Starting content creation...\n")
        result = crew.kickoff()

        print("\n" + "="*60)
        print("✅ BLOG CREATION COMPLETED")
        print("="*60)

        return result

# --------------------------------------------------
# CLI
# --------------------------------------------------
if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="AI Blog Creator (CrewAI + Groq)"
    )

    parser.add_argument("topic", help="Blog topic chosen by the student")
    parser.add_argument("--output", "-o", help="Save final blog to file")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    try:
        # Validate topic
        if not args.topic or not args.topic.strip():
            print("❌ ERROR: Topic cannot be empty")
            sys.exit(1)
        
        # Validate output path if provided
        if args.output:
            output_path = Path(args.output)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"❌ ERROR: Invalid output path: {str(e)}")
                sys.exit(1)
        
        crew = BlogCrew(args.topic)
        result = crew.run()

        print("\n📝 FINAL BLOG POST\n")
        print(result)

        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(str(result))
                print(f"\n✅ Saved to {args.output}")
            except Exception as e:
                print(f"❌ ERROR: Failed to save file: {str(e)}")
                sys.exit(1)

    except ValueError as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
