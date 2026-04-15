import os
os.environ["RICH_DISABLE"] = "true"


import os
import csv
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
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


def read_csv_file(file_path):
    """Read and parse CSV file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
            
            if not data:
                return "Error: CSV file is empty"
            
            return data
    except Exception as e:
        return f"Error reading CSV: {str(e)}"


def analyze_csv_structure(data):
    """Analyze CSV structure and compute basic statistics"""
    if isinstance(data, str) and data.startswith("Error"):
        return data
    
    try:
        # Get headers
        headers = list(data[0].keys())
        
        # Identify numeric columns (scores)
        numeric_cols = []
        for header in headers:
            try:
                # Try to convert first value to float
                float(data[0][header])
                numeric_cols.append(header)
            except (ValueError, KeyError):
                pass
        
        # Compute statistics for numeric columns
        stats = {}
        for col in numeric_cols:
            values = []
            for row in data:
                try:
                    values.append(float(row[col]))
                except (ValueError, KeyError):
                    pass
            
            if values:
                stats[col] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'count': len(values)
                }
        
        analysis = {
            'total_students': len(data),
            'columns': headers,
            'numeric_columns': numeric_cols,
            'statistics': stats
        }
        
        return analysis
    except Exception as e:
        return f"Error analyzing CSV: {str(e)}"


def format_data_for_agent(data, analysis):
    """Format CSV data and analysis for agent consumption"""
    
    # Create a readable summary
    summary = f"""
CSV DATA SUMMARY:
================

Total Students: {analysis['total_students']}
Columns: {', '.join(analysis['columns'])}
Score Columns: {', '.join(analysis['numeric_columns'])}

STATISTICS:
"""
    
    for col, stats in analysis['statistics'].items():
        summary += f"\n{col}:"
        summary += f"\n  - Average: {stats['avg']:.2f}"
        summary += f"\n  - Minimum: {stats['min']:.2f}"
        summary += f"\n  - Maximum: {stats['max']:.2f}"
    
    summary += "\n\nSAMPLE DATA (First 10 students):\n"
    summary += "="*50 + "\n"
    
    for i, row in enumerate(data[:10], 1):
        summary += f"\nStudent {i}:\n"
        for key, value in row.items():
            summary += f"  {key}: {value}\n"
    
    if len(data) > 10:
        summary += f"\n... and {len(data) - 10} more students"
    
    return summary


class StudentAnalyzerAgents:
    """Define agents for student result analysis"""
    
    def __init__(self, llm_instance):
        self.llm = llm_instance
    
    def data_analyst_agent(self):
        """Agent that analyzes student performance data"""
        return Agent(
            role='Student Performance Data Analyst',
            goal='Analyze student scores, identify patterns, trends, and performance insights',
            backstory="""You are an experienced educational data analyst with expertise 
            in interpreting student performance metrics. You excel at identifying patterns, 
            trends, strengths, and weaknesses in student data. You use statistical thinking 
            and educational psychology to derive meaningful insights.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def educator_agent(self):
        """Agent that provides educational insights"""
        return Agent(
            role='Educational Advisor',
            goal='Provide actionable recommendations for improving student performance',
            backstory="""You are a seasoned educator with 15 years of teaching experience. 
            You understand learning challenges and effective intervention strategies. You 
            provide practical, evidence-based recommendations that teachers can implement 
            to help students improve.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def report_writer_agent(self):
        """Agent that writes comprehensive reports"""
        return Agent(
            role='Educational Report Writer',
            goal='Create clear, comprehensive reports that explain findings to teachers and administrators',
            backstory="""You are an expert at communicating data insights to educators. 
            You write clear, jargon-free reports that explain complex data in accessible 
            language. Your reports are actionable and help educators make informed decisions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class StudentAnalyzerTasks:
    """Define tasks for student analysis"""
    
    def analysis_task(self, agent, data_summary):
        """Task to analyze student performance data"""
        return Task(
            description=f"""
            Analyze the following student performance data and provide comprehensive insights:
            
            {data_summary}
            
            Your analysis should include:
            
            1. OVERALL PERFORMANCE ASSESSMENT
               - General performance level across all subjects
               - Distribution of scores (how many high/average/low performers)
            
            2. SUBJECT-SPECIFIC INSIGHTS
               - Which subjects have highest/lowest average scores
               - Which subjects show most variation in performance
               - Identify subjects where students struggle most
            
            3. PATTERNS AND TRENDS
               - Are there consistent patterns across subjects?
               - Which students are high performers vs struggling?
               - Any correlations between different subjects?
            
            4. KEY CONCERNS
               - Students at risk (very low scores)
               - Subjects needing urgent attention
               - Achievement gaps
            
            Be specific with numbers and cite actual data from the statistics.
            """,
            agent=agent,
            expected_output="""Comprehensive analysis containing:
            - Overall performance assessment
            - Subject-specific insights with actual numbers
            - Identified patterns and trends
            - Key concerns and at-risk students
            
            Format with clear sections and bullet points."""
        )
    
    def recommendations_task(self, agent, analysis_task):
        """Task to generate recommendations"""
        return Task(
            description="""
            Based on the data analysis provided, generate actionable recommendations 
            for improving student performance.
            
            Your recommendations should include:
            
            1. IMMEDIATE INTERVENTIONS
               - What actions should be taken right away?
               - Which students need immediate support?
               - Priority subjects to focus on
            
            2. INSTRUCTIONAL STRATEGIES
               - Teaching methods to improve weak subjects
               - Differentiation strategies for different performance levels
               - Specific techniques for struggling students
            
            3. ASSESSMENT IMPROVEMENTS
               - Are current assessments appropriate?
               - Suggestions for better evaluation methods
            
            4. STUDENT SUPPORT PROGRAMS
               - Tutoring recommendations
               - Peer learning opportunities
               - Additional resources needed
            
            5. MONITORING PLAN
               - How to track improvement
               - Timeline for reassessment
            
            Make recommendations practical and implementable.
            """,
            agent=agent,
            expected_output="""Actionable recommendations with:
            - Immediate interventions needed
            - Instructional strategies
            - Assessment improvements
            - Student support programs
            - Monitoring plan
            
            Each recommendation should be specific and practical.""",
            context=[analysis_task]
        )
    
    def report_writing_task(self, agent, analysis_task, recommendations_task):
        """Task to write final report"""
        return Task(
            description="""
            Write a comprehensive Student Performance Report (800-1000 words) based on 
            the analysis and recommendations provided.
            
            Structure the report as follows:
            
            1. EXECUTIVE SUMMARY (100-150 words)
               - Overall performance snapshot
               - Key findings in 3-4 bullet points
               - Critical action items
            
            2. PERFORMANCE ANALYSIS (300-400 words)
               - Detailed breakdown of performance across subjects
               - Statistical insights with specific numbers
               - Identified strengths and weaknesses
               - Student performance distribution
            
            3. KEY INSIGHTS (150-200 words)
               - Most important patterns discovered
               - Concerning trends
               - Positive achievements to highlight
            
            4. RECOMMENDATIONS (250-300 words)
               - Immediate actions needed
               - Short-term strategies (1-3 months)
               - Long-term improvements (3-6 months)
               - Resource requirements
            
            5. CONCLUSION (50-100 words)
               - Summary of priorities
               - Expected outcomes if recommendations implemented
            
            Writing guidelines:
            - Use clear, jargon-free language
            - Include specific data points and percentages
            - Make it actionable for teachers and administrators
            - Be constructive and solution-focused
            - Use professional but accessible tone
            """,
            agent=agent,
            expected_output="""A polished report (800-1000 words) with:
            - Clear structure and sections
            - Specific data-backed insights
            - Actionable recommendations
            - Professional formatting
            - Accessible language for educators
            
            The report should be ready to share with teachers and school leadership.""",
            context=[analysis_task, recommendations_task]
        )


class StudentAnalyzerCrew:
    """Orchestrate the student analysis process"""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.llm = llm
        
        print("\n" + "="*60)
        print("📊 LOADING STUDENT DATA")
        print("="*60)
        
        # Check file exists
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"\n📄 Reading: {Path(csv_path).name}")
        
        # Read CSV
        self.data = read_csv_file(csv_path)
        if isinstance(self.data, str) and self.data.startswith("Error"):
            raise Exception(self.data)
        
        print(f"✅ Loaded {len(self.data)} student records")
        
        # Analyze structure
        print("\n📈 Analyzing data structure...")
        self.analysis = analyze_csv_structure(self.data)
        if isinstance(self.analysis, str) and self.analysis.startswith("Error"):
            raise Exception(self.analysis)
        
        print(f"✅ Found {len(self.analysis['numeric_columns'])} score columns")
        print(f"   Subjects: {', '.join(self.analysis['numeric_columns'])}")
        
        # Format for agents
        self.data_summary = format_data_for_agent(self.data, self.analysis)
    
    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)
        
        agents = StudentAnalyzerAgents(self.llm)
        analyst = agents.data_analyst_agent()
        educator = agents.educator_agent()
        writer = agents.report_writer_agent()
        print("✓ Agents created: Analyst, Educator, Writer")
        
        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)
        
        tasks = StudentAnalyzerTasks()
        analysis_task = tasks.analysis_task(analyst, self.data_summary)
        print("✓ Task 1: Analyze performance data")
        
        recommendations_task = tasks.recommendations_task(educator, analysis_task)
        print("✓ Task 2: Generate recommendations")
        
        report_task = tasks.report_writing_task(writer, analysis_task, recommendations_task)
        print("✓ Task 3: Write comprehensive report")
        
        all_tasks = [analysis_task, recommendations_task, report_task]
        
        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)
        
        crew = Crew(
            agents=[analyst, educator, writer],
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )
        print(f"✓ Crew assembled with {len(all_tasks)} tasks")
        
        print("\n" + "="*60)
        print("🚀 STARTING ANALYSIS")
        print("="*60)
        print("This may take 3-5 minutes...")
        print("You will see the analysis process below:\n")
        
        # Execute
        result = crew.kickoff()
        
        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETED!")
        print("="*60)
        
        return result


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Student Result CSV Analyzer - AI-powered student performance analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python student_analyzer.py students.csv
  python student_analyzer.py results.csv --output report.txt
  
CSV Format:
  The CSV should have:
  - Student identifier column (Name, ID, etc.)
  - Score columns (Math, English, Science, etc.)
  
  Example:
    Name,Math,English,Science,History
    Alice,85,92,78,88
    Bob,72,68,75,80
        """
    )
    
    parser.add_argument('csv_file', help='Path to student results CSV file')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("STUDENT PERFORMANCE ANALYZER")
    print("="*60)
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print(f"📄 File: {Path(args.csv_file).name}")
    print("="*60)
    
    try:
        crew = StudentAnalyzerCrew(args.csv_file)
        result = crew.run()
        
        print("\n" + "="*60)
        print("📝 STUDENT PERFORMANCE REPORT")
        print("="*60 + "\n")
        print(result)
        print("\n" + "="*60)
        
        # Save to file
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("STUDENT PERFORMANCE REPORT\n")
                f.write("="*60 + "\n\n")
                f.write(str(result))
                f.write("\n\n" + "="*60 + "\n")
                f.write(f"Generated by Student Performance Analyzer\n")
                f.write(f"Source: {args.csv_file}\n")
            print(f"\n✅ Report saved to {args.output}")
        
        # Save summary statistics
        stats_file = args.output.replace('.txt', '_stats.txt') if args.output else 'analysis_stats.txt'
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("QUICK STATISTICS\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total Students: {crew.analysis['total_students']}\n")
            f.write(f"Subjects Analyzed: {', '.join(crew.analysis['numeric_columns'])}\n\n")
            f.write("Subject Averages:\n")
            for col, stats in crew.analysis['statistics'].items():
                f.write(f"  {col}: {stats['avg']:.2f} (Range: {stats['min']:.0f}-{stats['max']:.0f})\n")
        print(f"✅ Statistics saved to {stats_file}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)