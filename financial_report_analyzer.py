import os
os.environ["RICH_DISABLE"] = "true"

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import pandas as pd
import sys
from pathlib import Path

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
    
    def analysis_task(self, agent, df, file_name):
        """Task to analyze the CSV data"""
        preview = df.head(50).to_dict()  # limit preview for token safety
        return Task(
            description=f"""
            Analyze this financial dataset and provide a structured overview.

            CSV: {file_name}

            DATA PREVIEW:
            {preview}

            Compute:
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
    
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.llm = llm
        
        print("\n" + "="*60)
        print("📂 LOADING FINANCIAL CSV")
        print("="*60)
        
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"File not found: {csv_file}")
        
        try:
            self.df = read_csv(csv_file)
            
            if self.df.empty:
                raise ValueError("CSV file contains no data rows")
            
            print(f"✅ CSV loaded successfully ({len(self.df)} rows, {len(self.df.columns)} columns)")
            print(f"   Columns: {', '.join(self.df.columns)}")
        except Exception as e:
            print(f"❌ Failed to load CSV: {str(e)}")
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
        analysis_task = tasks.analysis_task(analyzer, self.df, Path(self.csv_file).name)
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
        description='Financial Report Analyzer Agent',
        epilog="""
Examples:
  python financial_analyzer.py report.csv
  python financial_analyzer.py report.csv --output summary.txt
        """
    )
    
    parser.add_argument('csv_file', help='Path to financial CSV (income/expenses)')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("FINANCIAL REPORT ANALYZER - CrewAI + Groq")
    print("="*60)
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print(f"📁 CSV: {args.csv_file}")
    print("="*60)
    
    try:
        crew = FinancialCrew(args.csv_file)
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
