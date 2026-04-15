import os

os.environ["RICH_DISABLE"] = "1"
os.environ["CREWAI_DISABLE_RICH"] = "1"

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import PyPDF2
import requests
import sys

# Load environment variables
load_dotenv()

# Initialize Groq with Llama model
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
    base_url="https://api.groq.com/openai/v1" # <- REQUIRED
)


def read_pdf(file_path):
    """Helper function to read PDF files"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text[:15000]
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


def read_text_file(file_path):
    """Helper function to read text files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()[:15000]
    except Exception as e:
        return f"Error reading file: {str(e)}"


def fetch_url(url):
    """Helper function to fetch URL content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text[:15000]
    except Exception as e:
        return f"Error fetching URL: {str(e)}"


class TechNewsAgents:
    """Define the agents for tech news processing"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def researcher_agent(self):
        return Agent(
            role='Tech News Researcher',
            goal='Extract and analyze key information from tech news articles and PDFs',
            backstory="""You are an expert tech news analyst with years of experience 
            in identifying critical information, trends, and implications in technology news. 
            You excel at breaking down complex technical content into structured insights.
            You are thorough, detail-oriented, and always extract the most important facts.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def writer_agent(self, tone='professional'):
        tone_descriptions = {
            'professional': 'formal business tone suitable for corporate communications',
            'casual': 'conversational and friendly tone as if explaining to a friend',
            'technical': 'in-depth technical analysis suitable for engineers and developers',
            'executive': 'concise executive summary focusing on strategic implications'
        }
        
        return Agent(
            role='Tech News Writer',
            goal=f'Create well-structured summaries in a {tone} tone',
            backstory=f"""You are a skilled technology writer who specializes in crafting 
            engaging summaries. You write in a {tone_descriptions.get(tone, 'professional')} 
            and ensure content is clear, compelling, and appropriately formatted.
            You transform complex research into readable, insightful content.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class TechNewsTasks:
    """Define the tasks for the crew"""
    
    def research_task(self, agent, content):
        return Task(
            description=f"""
            Analyze the following tech news content and extract key information:
            
            CONTENT:
            {content}
            
            Your analysis should include:
            1. Main topic/technology discussed
            2. Key facts and figures (be specific with numbers, dates, statistics)
            3. Important companies, people, or organizations mentioned
            4. Implications and potential impact on the industry
            5. Technical details and innovations (if applicable)
            
            Structure your findings clearly with proper categorization.
            Be thorough and extract all important details.
            Format your response with clear sections and bullet points.
            """,
            agent=agent,
            expected_output="""A structured analysis containing:
            - Main topic (1-2 sentences)
            - Key facts (bulleted list with at least 3-5 facts)
            - Entities mentioned (companies, people, organizations)
            - Implications (2-3 key implications)
            - Technical details (if applicable)
            
            Format should be clear and well-organized."""
        )
    
    def writing_task(self, agent, tone, research_task):
        return Task(
            description=f"""
            Based on the research analysis provided, create a comprehensive summary 
            of the tech news article.
            
            Requirements:
            - Write in a {tone} tone
            - Length: 250-400 words
            - Include clear sections/paragraphs
            - Highlight key insights and takeaways
            - Make it engaging and informative
            - Use appropriate formatting
            
            Structure your summary with:
            1. Opening paragraph introducing the main topic
            2. Body paragraphs covering key details and implications
            3. Closing paragraph with insights or future outlook
            
            Write naturally and make the content flow well.
            """,
            agent=agent,
            expected_output=f"""A polished {tone} summary (250-400 words) with:
            - Clear introduction
            - Well-organized body content
            - Insightful conclusion
            - Proper formatting and structure
            
            The summary should be engaging and easy to read.""",
            context=[research_task]
        )


class TechNewsCrew:
    """Orchestrate the entire crew"""
    
    def __init__(self, content_source, tone='professional', llm_instance=None):
        self.content_source = content_source
        self.tone = tone
        self.llm = llm_instance if llm_instance else llm
        
        # Determine source type and read content
        print(f"\n📂 Processing source: {content_source}")
        
        if content_source.startswith('http'):
            print(f"📡 Fetching content from URL...")
            self.content = fetch_url(content_source)
            self.source_type = 'url'
        elif content_source.endswith('.pdf'):
            print(f"📄 Reading PDF file...")
            self.content = read_pdf(content_source)
            self.source_type = 'pdf'
        else:
            print(f"📝 Reading text file...")
            self.content = read_text_file(content_source)
            self.source_type = 'file'
        
        if self.content.startswith("Error"):
            raise Exception(self.content)
        
        print(f"✅ Content loaded successfully ({len(self.content)} characters)")
        
    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)
        
        # Initialize agents
        agents = TechNewsAgents(self.llm)
        researcher = agents.researcher_agent()
        writer = agents.writer_agent(self.tone)
        print("✓ Agents created: Researcher & Writer")
        
        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)
        
        # Initialize tasks
        tasks = TechNewsTasks()
        research_task = tasks.research_task(researcher, self.content)
        writing_task = tasks.writing_task(writer, self.tone, research_task)
        print("✓ Tasks created: Research & Writing")
        
        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)
        
        # Create crew
        crew = Crew(
            agents=[researcher, writer],
            tasks=[research_task, writing_task],
            process=Process.sequential,
            verbose=True
        )
        print("✓ Crew assembled")
        
        print("\n" + "="*60)
        print("🚀 STARTING CREW EXECUTION")
        print("="*60 + "\n")
        
        # Execute
        result = crew.kickoff()
        
        print("\n" + "="*60)
        print("✅ CREW EXECUTION COMPLETED!")
        print("="*60)
        
        return result


# CLI Interface 
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Tech News Summarizer with CrewAI + Groq',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py article.txt --tone professional
  python main.py article.pdf --tone casual
  python main.py https://example.com/news --tone technical
  python main.py article.txt --tone executive --output summary.txt
        """
    )
    
    parser.add_argument('source', help='Path to PDF/text file or URL')
    parser.add_argument('--tone', 
                       choices=['professional', 'casual', 'technical', 'executive'],
                       default='professional',
                       help='Tone for the summary (default: professional)')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("\n❌ ERROR: GROQ_API_KEY not found in .env file!")
        print("Please create a .env file and add: GROQ_API_KEY=your_key_here")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("TECH NEWS SUMMARIZER - CrewAI + Groq")
    print("="*60)
    print("📊 Model: groq/llama-3.1-8b-instant")
    print(f"📁 Source: {args.source}")
    print(f"🎨 Tone: {args.tone}")
    print("="*60)
    
    try:
        # Process based on source
        crew = TechNewsCrew(args.source, args.tone)
        result = crew.run()
        
        print("\n" + "="*60)
        print("📝 FINAL SUMMARY")
        print("="*60 + "\n")
        print(result)
        print("\n" + "="*60)
        
        # Save to file if specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(str(result))
            print(f"\n✅ Summary saved to {args.output}")
    
    except Exception as e:
        print(f"\n❌ ERROR OCCURRED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)