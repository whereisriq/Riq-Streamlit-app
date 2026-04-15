import os

os.environ["RICH_DISABLE"] = "1"
os.environ["CREWAI_DISABLE_RICH"] = "1"


import os
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
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            num_pages = len(pdf_reader.pages)
            
            print(f"   📄 Extracting from {num_pages} pages...")
            
            for i, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text() or ""
                text += f"\n--- Page {i} ---\n{page_text}\n"
                
                # Limit to prevent token overflow
                if len(text) > 50000:
                    print(f"   ⚠️  Truncated at page {i} (content too large)")
                    break
            
            return text
    except Exception as e:
        return f"Error reading PDF {file_path}: {str(e)}"


def read_text_file(file_path):
    """Read text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


class CourseOutlineAgents:
    """Define agents for course outline review"""
    
    def __init__(self, llm_instance):
        self.llm = llm_instance
    
    def analyzer_agent(self):
        """Agent that analyzes the course outline"""
        return Agent(
            role='Course Outline Analyst',
            goal='Analyze course outlines for structure, content, and learning objectives',
            backstory="""You are an expert curriculum designer. 
            You can detect gaps in course content, evaluate alignment of objectives with outcomes, 
            and suggest improvements to make the course well-structured and coherent.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def reviewer_agent(self):
        """Agent that critiques and suggests improvements"""
        return Agent(
            role='Course Outline Reviewer',
            goal='Provide structured feedback, detect gaps, and rewrite learning objectives',
            backstory="""You are an experienced educational consultant. 
            You provide actionable feedback on course outlines, identify missing elements, 
            and rewrite objectives in a clear and measurable way.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def writer_agent(self):
        """Agent that rewrites objectives and final summary"""
        return Agent(
            role='Course Outline Writer',
            goal='Rewrite learning objectives and summarize improvements in a structured format',
            backstory="""You are skilled at transforming analysis into clear, actionable outputs.
            You rewrite objectives in a measurable and student-friendly manner.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class CourseOutlineTasks:
    """Define tasks for course outline review"""
    
    def analysis_task(self, agent, content, outline_name):
        """Task to analyze course outline"""
        return Task(
            description=f"""
            Analyze the following course outline:

            OUTLINE: {outline_name}

            CONTENT:
            {content[:15000]}

            Assess the following:
            1. Completeness of topics
            2. Alignment of objectives with course content
            3. Logical flow of modules
            4. Detect any missing elements or gaps

            Provide structured feedback with clear categories.
            """,
            agent=agent,
            expected_output="""Structured analysis including:
            - Completeness of topics
            - Alignment of objectives
            - Logical flow of modules
            - Gaps or missing elements"""
        )
    
    def critique_task(self, agent, analysis_task):
        """Task to provide critique and improvement suggestions"""
        return Task(
            description="""
            Based on the analysis, critique the course outline:
            1. Suggest improvements for content coverage
            2. Recommend adjustments to module sequencing
            3. Identify weak or unclear objectives
            4. Suggest actionable recommendations

            Structure feedback clearly and provide examples where possible.
            """,
            agent=agent,
            expected_output="""Structured critique including:
            - Content improvements
            - Module sequencing recommendations
            - Weak objectives identified
            - Actionable suggestions""",
            context=[analysis_task]
        )
    
    def rewrite_task(self, agent, critique_task):
        """Task to rewrite objectives and summarize"""
        return Task(
            description="""
            Rewrite the course objectives and provide a final summary:
            1. Rewrite all learning objectives to be measurable and clear
            2. Summarize key improvements
            3. Present a concise, structured report suitable for faculty review
            """,
            agent=agent,
            expected_output="""Final output including:
            - Rewritten, measurable learning objectives
            - Summary of key improvements
            - Structured faculty-ready report""",
            context=[critique_task]
        )


class CourseOutlineCrew:
    """Orchestrate the course outline review process"""
    
    def __init__(self, outline_path):
        self.outline_path = outline_path
        self.llm = llm
        
        print("\n" + "="*60)
        print("📄 LOADING COURSE OUTLINE")
        print("="*60)
        
        if not os.path.exists(outline_path):
            raise FileNotFoundError(f"File not found: {outline_path}")
        
        if outline_path.endswith('.pdf'):
            self.outline_text = extract_pdf_text(outline_path)
        else:
            self.outline_text = read_text_file(outline_path)
        
        if self.outline_text.startswith("Error"):
            raise Exception(self.outline_text)
        
        print(f"✅ Loaded '{Path(outline_path).name}' ({len(self.outline_text)} characters)")
    
    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)
        
        agents = CourseOutlineAgents(self.llm)
        analyzer = agents.analyzer_agent()
        reviewer = agents.reviewer_agent()
        writer = agents.writer_agent()
        print("✓ Agents created: Analyzer, Reviewer, Writer")
        
        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)
        
        tasks = CourseOutlineTasks()
        analysis_task = tasks.analysis_task(analyzer, self.outline_text, Path(self.outline_path).stem)
        critique_task = tasks.critique_task(reviewer, analysis_task)
        rewrite_task = tasks.rewrite_task(writer, critique_task)
        print("✓ Tasks created: Analysis, Critique, Rewrite")
        
        all_tasks = [analysis_task, critique_task, rewrite_task]
        
        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)
        
        crew = Crew(
            agents=[analyzer, reviewer, writer],
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )
        print(f"✓ Crew assembled with {len(all_tasks)} tasks")
        
        print("\n" + "="*60)
        print("🚀 STARTING EXECUTION")
        print("="*60)
        print("You will see agent thinking process below...\n")
        
        result = crew.kickoff()
        
        print("\n" + "="*60)
        print("✅ COURSE OUTLINE REVIEW COMPLETED!")
        print("="*60)
        
        return result


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='University Course Outline Reviewer Agent',
        epilog="""
Examples:
  python course_reviewer.py syllabus.pdf
  python course_reviewer.py syllabus.txt --output improved_syllabus.txt
        """
    )
    
    parser.add_argument('outline', help='Path to course outline PDF or text file')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("COURSE OUTLINE REVIEWER AGENT")
    print("="*60)
    print(f"📄 Outline: {Path(args.outline).name}")
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print("="*60)
    
    try:
        crew = CourseOutlineCrew(args.outline)
        result = crew.run()
        
        print("\n" + "="*60)
        print("📝 FINAL REVIEW & REWRITTEN OBJECTIVES")
        print("="*60 + "\n")
        print(result)
        print("\n" + "="*60)
        
        # Save output if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("COURSE OUTLINE REVIEW\n")
                f.write("="*60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
