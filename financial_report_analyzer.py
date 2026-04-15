import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import pandas as pd
import sys
from pathlib import Path
try:
    import pypdf
except ImportError:
    pypdf = None
try:
    from docx import Document
except ImportError:
    Document = None

# Load environment variables
load_dotenv()

# Initialize Groq Llama model
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
    base_url="https://api.groq.com/openai/v1"
)

def read_csv(file_path):
    """Read CSV and return as DataFrame"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Check file size (warn if > 50MB)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:
            print(f"   ⚠️  Large file detected ({file_size_mb:.1f} MB), processing may take longer")
        
        df = pd.read_csv(file_path)
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        if len(df.columns) == 0:
            raise ValueError("CSV has no columns")
        
        return df
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception(f"Error reading CSV {file_path}: {str(e)}")


def read_pdf(file_path):
    """Read PDF and return text as string"""
    if pypdf is None:
        raise ImportError("pypdf library not installed. Install with: pip install pypdf")
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:
            print(f"   ⚠️  Large file detected ({file_size_mb:.1f} MB), processing may take longer")
        
        pdf_reader = pypdf.PdfReader(file_path)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text += f"--- Page {page_num} ---\n"
            text += page.extract_text()
            text += "\n"
        
        if not text.strip():
            raise ValueError("PDF file contains no extractable text")
        
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF {file_path}: {str(e)}")


def read_docx(file_path):
    """Read DOCX and return text as string"""
    if Document is None:
        raise ImportError("python-docx library not installed. Install with: pip install python-docx")
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found: {file_path}")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:
            print(f"   ⚠️  Large file detected ({file_size_mb:.1f} MB), processing may take longer")
        
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        if not text.strip():
            raise ValueError("DOCX file contains no extractable text")
        
        return text
    except Exception as e:
        raise Exception(f"Error reading DOCX {file_path}: {str(e)}")


def load_file(file_path):
    """Load any supported file type (CSV, PDF, DOCX) and return content with type info"""
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.csv':
        return read_csv(file_path), 'dataframe'
    elif file_ext == '.pdf':
        return read_pdf(file_path), 'text'
    elif file_ext == '.docx':
        return read_docx(file_path), 'text'
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: .csv, .pdf, .docx")

class FinancialAgents:
    """Define agents for financial report analysis"""
    
    def analyzer_agent(self):
        """Agent that analyzes numerical data"""
        return Agent(
            role='Financial Data Analyzer',
            goal='Analyze income and expense data to assess financial health',
            backstory="""You are a finance expert who can interpret company or personal 
            financial data. You identify trends, compute key ratios, and summarize 
            overall financial status clearly and accurately.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )
    
    def reporter_agent(self):
        """Agent that writes structured financial summaries"""
        return Agent(
            role='Financial Report Writer',
            goal='Create a clear, structured summary of financial health',
            backstory="""You are a professional financial writer who converts analysis 
            into readable insights. Your summaries include clear takeaways, trends, 
            and actionable points.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

class FinancialTasks:
    """Define tasks for financial report processing"""
    
    def analysis_task(self, agent, data, file_name, content_type):
        """Task to analyze the financial data"""
        if content_type == 'dataframe':
            preview = data.head(50).to_dict()  # limit preview for token safety
            data_preview = f"DATA PREVIEW:\n{preview}"
            file_info = f"CSV: {file_name}\n"
        else:  # text
            # Limit text preview to 1000 chars for token safety
            preview = data[:1000] + "..." if len(data) > 1000 else data
            data_preview = f"DOCUMENT CONTENT:\n{preview}"
            file_info = f"Document: {file_name}\n"
        
        return Task(
            description=f"""
            Analyze this financial dataset and provide a structured overview.

            {file_info}
            {data_preview}

            Compute/Identify:
            1. Total income
            2. Total expenses
            3. Net balance
            4. Key trends and anomalies
            5. Any potential risks or opportunities

            Present your analysis in bullet points or tables where appropriate.
            """,
            agent=agent,
            expected_output="""A structured financial analysis including:
            - Totals for income and expenses
            - Net balance
            - Trends and anomalies
            - Risk/Opportunity insights"""
        )
    
    def reporting_task(self, agent, analysis_task):
        """Task to write the final financial summary"""
        return Task(
            description="""
            Based on the financial analysis, create a concise report summarizing financial health.
            
            Include:
            1. Key financial metrics (income, expenses, net balance)
            2. Observed trends (positive or negative)
            3. Recommendations or notes for improvement
            4. Clear sections or bullet points

            Write professionally, clearly, and ensure it is easy to understand.
            """,
            agent=agent,
            expected_output="""A polished financial summary report (250-400 words) including:
            - Metrics overview
            - Trend analysis
            - Recommendations
            - Structured and readable format""",
            context=[analysis_task]
        )

class FinancialCrew:
    """Orchestrate the financial report analysis"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.llm = llm
        self.content_type = None  # 'dataframe' or 'text'
        self.data = None
        
        print("\n" + "="*60)
        print(f"📂 LOADING FILE: {Path(file_path).name}")
        print("="*60)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            self.data, self.content_type = load_file(file_path)
            
            if self.content_type == 'dataframe':
                if self.data.empty:
                    raise ValueError("CSV file contains no data rows")
                print(f"✅ CSV loaded successfully ({len(self.data)} rows, {len(self.data.columns)} columns)")
                print(f"   Columns: {', '.join(self.data.columns)}")
            else:  # text
                text_preview = self.data[:200] + "..." if len(self.data) > 200 else self.data
                print(f"✅ Document loaded successfully ({len(self.data)} characters)")
                print(f"   Preview: {text_preview}")
        except Exception as e:
            print(f"❌ Failed to load file: {str(e)}")
            raise
    
    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)
        
        agents = FinancialAgents()
        analyzer = agents.analyzer_agent()
        reporter = agents.reporter_agent()
        print("✓ Agents created: Analyzer & Reporter")
        
        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)
        
        tasks = FinancialTasks()
        analysis_task = tasks.analysis_task(analyzer, self.data, Path(self.file_path).name, self.content_type)
        reporting_task = tasks.reporting_task(reporter, analysis_task)
        print("✓ Tasks created: Analysis & Reporting")
        
        all_tasks = [analysis_task, reporting_task]
        
        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)
        
        crew = Crew(
            agents=[analyzer, reporter],
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )
        print(f"✓ Crew assembled with {len(all_tasks)} tasks")
        
        print("\n" + "="*60)
        print("🚀 STARTING CREW EXECUTION")
        print("="*60 + "\n")
        
        result = crew.kickoff()
        
        print("\n" + "="*60)
        print("✅ FINANCIAL ANALYSIS COMPLETED")
        print("="*60)
        
        return result

# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Financial Report Analyzer Agent (supports CSV, PDF, and DOCX)',
        epilog="""
Examples:
  python financial_analyzer.py report.csv
  python financial_analyzer.py financial_report.pdf
  python financial_analyzer.py budget.docx --output summary.txt
        """
    )
    
    parser.add_argument('file', help='Path to financial file (CSV, PDF, or DOCX)')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)
    
    # Check file extension
    file_ext = Path(args.file).suffix.lower()
    if file_ext not in ['.csv', '.pdf', '.docx']:
        print(f"❌ ERROR: Unsupported file format '{file_ext}'. Supported formats: .csv, .pdf, .docx")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("FINANCIAL REPORT ANALYZER - CrewAI + Groq")
    print("="*60)
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print(f"📁 File: {args.file} ({file_ext.upper()})")
    print("="*60)
    
    try:
        crew = FinancialCrew(args.file)
        result = crew.run()
        
        print("\n" + "="*60)
        print("📝 FINANCIAL SUMMARY")
        print("="*60 + "\n")
        print(result)
        print("\n" + "="*60)
        
        # Save to file
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("FINANCIAL SUMMARY\n")
                f.write("="*60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Saved to {args.output}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
