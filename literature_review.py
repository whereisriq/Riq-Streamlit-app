import os
os.environ["RICH_DISABLE"] = "true"



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
                page_text = page.extract_text()
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


class LiteratureReviewAgents:
    """Define agents for literature review process"""
    
    def __init__(self, llm_instance):
        self.llm = llm_instance
    
    def extractor_agent(self):
        """Agent that extracts key information from papers"""
        return Agent(
            role='Research Paper Analyzer',
            goal='Extract key themes, methodologies, findings, and contributions from academic papers',
            backstory="""You are an expert research analyst with a PhD in your field. 
            You excel at reading academic papers and identifying core themes, research gaps, 
            methodologies, key findings, and theoretical contributions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def synthesizer_agent(self):
        """Agent that synthesizes findings across papers"""
        return Agent(
            role='Research Synthesizer',
            goal='Identify common themes, contrasts, and research gaps across multiple papers',
            backstory="""You are a senior academic researcher specializing in research synthesis. 
            You identify patterns, commonalities, and contradictions across studies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def writer_agent(self):
        """Agent that writes the literature review"""
        return Agent(
            role='Academic Writer',
            goal='Write a comprehensive, well-structured literature review in academic style',
            backstory="""You are an accomplished academic writer with expertise in crafting 
            literature reviews. You write in clear, formal academic prose.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class LiteratureReviewTasks:
    """Define tasks for the literature review process"""
    
    def extraction_task(self, agent, paper_content, paper_name):
        """Task to extract information from a single paper"""
        return Task(
            description=f"""
            Analyze this research paper and extract key information:
            
            PAPER: {paper_name}
            
            CONTENT:
            {paper_content[:15000]}
            
            Extract:
            1. Main research question
            2. Methodology used
            3. Key findings (list 3-5)
            4. Core themes (list 3-5)
            5. Limitations mentioned
            
            Be specific and thorough.
            """,
            agent=agent,
            expected_output=f"""Structured extraction for {paper_name} with:
            - Research question
            - Methodology
            - Key findings (3-5 points)
            - Core themes (3-5 themes)
            - Limitations"""
        )
    
    def synthesis_task(self, agent, extraction_tasks):
        """Task to synthesize findings across all papers"""
        return Task(
            description="""
            Synthesize the research from all papers:
            
            1. Identify COMMON THEMES across papers
            2. Compare METHODOLOGICAL APPROACHES
            3. Note CONVERGING and DIVERGING findings
            4. Highlight RESEARCH GAPS
            5. Identify any CONTRADICTIONS
            
            Organize thematically, not by individual papers.
            """,
            agent=agent,
            expected_output="""Thematic synthesis with:
            - 3-5 major themes
            - Methodological comparison
            - Research gaps
            - Key contradictions or debates""",
            context=extraction_tasks
        )
    
    def writing_task(self, agent, synthesis_task):
        """Task to write the final literature review"""
        return Task(
            description="""
            Write a mini literature review (600-800 words) based on the synthesis.
            
            Structure:
            1. INTRODUCTION (100-150 words)
               - Context and importance
               - Scope of review
            
            2. THEMATIC ANALYSIS (350-450 words)
               - Organize by themes, NOT by papers
               - Compare and contrast approaches
               - Cite papers naturally
            
            3. RESEARCH GAPS (100-150 words)
               - What hasn't been studied
               - Future directions
            
            4. CONCLUSION (50-100 words)
               - Main insights
            
            Use formal academic tone and third person.
            """,
            agent=agent,
            expected_output="""A polished literature review (600-800 words) with:
            - Clear structure
            - Thematic organization
            - Critical analysis
            - Identified research gaps""",
            context=[synthesis_task]
        )


class LiteratureReviewCrew:
    """Orchestrate the literature review process"""
    
    def __init__(self, pdf_paths):
        self.pdf_paths = pdf_paths
        self.llm = llm
        self.papers_content = {}
        
        print("\n" + "="*60)
        print("📚 LOADING RESEARCH PAPERS")
        print("="*60)
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"File not found: {pdf_path}")
            
            print(f"\n{i}. {Path(pdf_path).name}")
            
            # Read file based on extension
            if pdf_path.endswith('.pdf'):
                content = extract_pdf_text(pdf_path)
            else:
                content = read_text_file(pdf_path)
            
            if content.startswith("Error"):
                raise Exception(content)
            
            self.papers_content[pdf_path] = content
            print(f"   ✅ Loaded ({len(content)} characters)")
        
        print(f"\n✅ All {len(pdf_paths)} papers loaded successfully")
    
    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)
        
        agents = LiteratureReviewAgents(self.llm)
        extractor = agents.extractor_agent()
        synthesizer = agents.synthesizer_agent()
        writer = agents.writer_agent()
        print("✓ Agents created: Extractor, Synthesizer, Writer")
        
        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)
        
        tasks = LiteratureReviewTasks()
        extraction_tasks = []
        
        for i, (pdf_path, content) in enumerate(self.papers_content.items(), 1):
            paper_name = Path(pdf_path).stem
            print(f"✓ Task {i}: Extract from '{paper_name}'")
            extraction_tasks.append(
                tasks.extraction_task(extractor, content, paper_name)
            )
        
        synthesis_task = tasks.synthesis_task(synthesizer, extraction_tasks)
        print(f"✓ Task {len(extraction_tasks) + 1}: Synthesize findings")
        
        writing_task = tasks.writing_task(writer, synthesis_task)
        print(f"✓ Task {len(extraction_tasks) + 2}: Write literature review")
        
        all_tasks = extraction_tasks + [synthesis_task, writing_task]
        
        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)
        
        crew = Crew(
            agents=[extractor, synthesizer, writer],
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )
        print(f"✓ Crew assembled with {len(all_tasks)} tasks")
        
        print("\n" + "="*60)
        print("🚀 STARTING EXECUTION")
        print("="*60)
        print("This may take 3-5 minutes...")
        print("You will see agent thinking process below:\n")
        
        # Execute
        result = crew.kickoff()
        
        print("\n" + "="*60)
        print("✅ LITERATURE REVIEW COMPLETED!")
        print("="*60)
        
        return result


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Academic Literature Review Agent',
        epilog="""
Examples:
  python literature_review.py paper1.txt paper2.txt
  python literature_review.py paper1.pdf paper2.pdf --output review.txt
        """
    )
    
    parser.add_argument('papers', nargs='+', help='Paths to 2-3 research papers')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Validate
    if len(args.papers) < 2:
        print("❌ ERROR: Please provide at least 2 papers")
        sys.exit(1)
    
    if len(args.papers) > 3:
        print("⚠️  Using first 3 papers only")
        args.papers = args.papers[:3]
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("ACADEMIC LITERATURE REVIEW AGENT")
    print("="*60)
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print(f"📚 Papers: {len(args.papers)}")
    for i, paper in enumerate(args.papers, 1):
        print(f"   {i}. {Path(paper).name}")
    print("="*60)
    
    try:
        crew = LiteratureReviewCrew(args.papers)
        result = crew.run()
        
        print("\n" + "="*60)
        print("📝 LITERATURE REVIEW")
        print("="*60 + "\n")
        print(result)
        print("\n" + "="*60)
        
        # Save to file
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("LITERATURE REVIEW\n")
                f.write("="*60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)