import os
os.environ["RICH_DISABLE"] = "true"

import csv
import sys
from pathlib import Path
from statistics import mean, median, stdev
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# Load environment variables
load_dotenv()

# Initialize Groq LLM
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
    base_url="https://api.groq.com/openai/v1"
)

# -------------------------------
# Data Utilities
# -------------------------------

def read_csv_file(file_path):
    """Read CSV and return rows + headers"""
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            return reader.fieldnames, data
    except Exception as e:
        return f"Error reading CSV: {str(e)}"


def compute_descriptive_stats(headers, rows):
    """Compute descriptive stats for numeric columns"""
    stats = {}
    for header in headers:
        values = []
        for row in rows:
            try:
                values.append(float(row[header]))
            except:
                pass
        
        if len(values) >= 2:
            stats[header] = {
                "count": len(values),
                "mean": round(mean(values), 2),
                "median": round(median(values), 2),
                "min": min(values),
                "max": max(values),
                "std_dev": round(stdev(values), 2)
            }
    
    return stats


def format_dataset_summary(headers, rows, stats):
    """Prepare dataset summary for agents"""
    summary = f"""
DATASET OVERVIEW
================
Total Rows: {len(rows)}
Total Columns: {len(headers)}

COLUMNS:
{', '.join(headers)}

DESCRIPTIVE STATISTICS:
"""

    for col, s in stats.items():
        summary += f"""
{col}:
- Count: {s['count']}
- Mean: {s['mean']}
- Median: {s['median']}
- Min: {s['min']}
- Max: {s['max']}
- Std Dev: {s['std_dev']}
"""

    summary += "\nSAMPLE ROWS (First 5):\n"
    summary += "=" * 40 + "\n"

    for i, row in enumerate(rows[:5], 1):
        summary += f"\nRow {i}:\n"
        for k, v in row.items():
            summary += f"  {k}: {v}\n"

    return summary


# -------------------------------
# Agents
# -------------------------------

class DatasetInsightAgents:
    """Define agents for dataset analysis"""

    def __init__(self, llm_instance):
        self.llm = llm_instance

    def data_analyst_agent(self):
        return Agent(
            role="Data Analyst",
            goal="Analyze dataset statistics and identify patterns, trends, and anomalies",
            backstory="""You are an experienced data analyst with strong statistical 
            reasoning skills. You interpret numerical data, detect trends, 
            identify outliers, and explain patterns clearly.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def insight_writer_agent(self):
        return Agent(
            role="Insight Report Writer",
            goal="Write a clear, structured dataset insight report for decision-makers",
            backstory="""You specialize in translating data analysis into clear 
            written insights. You focus on interpretation, implications, 
            and actionable understanding.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


# -------------------------------
# Tasks
# -------------------------------

class DatasetInsightTasks:
    """Define tasks for dataset analysis"""

    def analysis_task(self, agent, dataset_summary):
        return Task(
            description=f"""
            Analyze the dataset summary below.

            {dataset_summary}

            Perform the following:
            1. Identify key patterns and trends
            2. Highlight unusually high or low values
            3. Identify variability and consistency
            4. Note any potential data quality issues
            5. Explain what the statistics suggest about the dataset

            Use clear reasoning and reference the statistics explicitly.
            """,
            agent=agent,
            expected_output="""Analytical findings including:
            - Major patterns and trends
            - Notable anomalies or extremes
            - Interpretation of variability
            - Key observations supported by data"""
        )

    def reporting_task(self, agent, analysis_task):
        return Task(
            description="""
            Write a professional Dataset Insight Report based on the analysis.

            Structure:
            1. EXECUTIVE SUMMARY (100–150 words)
            2. DESCRIPTIVE STATISTICS INTERPRETATION
            3. KEY PATTERNS & TRENDS
            4. NOTABLE INSIGHTS & IMPLICATIONS
            5. LIMITATIONS & DATA CONSIDERATIONS
            6. CONCLUSION

            Writing Guidelines:
            - Clear and professional tone
            - Explain what the data means, not just numbers
            - Suitable for non-technical stakeholders
            """,
            agent=agent,
            expected_output="""A structured dataset insight report with:
            - Clear sections
            - Data-backed reasoning
            - Actionable interpretation
            - Professional reporting tone""",
            context=[analysis_task]
        )


# -------------------------------
# Crew Orchestration
# -------------------------------

class DatasetInsightCrew:
    """Orchestrates the dataset insight workflow"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.llm = llm

        print("\n" + "=" * 60)
        print("📊 LOADING DATASET")
        print("=" * 60)

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"File not found: {csv_path}")

        headers, rows = read_csv_file(csv_path)
        if isinstance(headers, str):
            raise Exception(headers)

        self.headers = headers
        self.rows = rows
        self.stats = compute_descriptive_stats(headers, rows)
        self.dataset_summary = format_dataset_summary(headers, rows, self.stats)

        print(f"✅ Loaded dataset with {len(rows)} rows and {len(headers)} columns")

    def run(self):
        print("\n" + "=" * 60)
        print("🔧 SETTING UP AGENTS")
        print("=" * 60)

        agents = DatasetInsightAgents(self.llm)
        analyst = agents.data_analyst_agent()
        writer = agents.insight_writer_agent()

        print("✓ Agents created: Data Analyst, Insight Writer")

        print("\n" + "=" * 60)
        print("📋 CREATING TASKS")
        print("=" * 60)

        tasks = DatasetInsightTasks()
        analysis_task = tasks.analysis_task(analyst, self.dataset_summary)
        reporting_task = tasks.reporting_task(writer, analysis_task)

        print("✓ Tasks created: Analysis & Reporting")

        print("\n" + "=" * 60)
        print("👥 ASSEMBLING CREW")
        print("=" * 60)

        crew = Crew(
            agents=[analyst, writer],
            tasks=[analysis_task, reporting_task],
            process=Process.sequential,
            verbose=True
        )

        print("✓ Crew assembled")

        print("\n" + "=" * 60)
        print("🚀 STARTING ANALYSIS")
        print("=" * 60)

        result = crew.kickoff()

        print("\n" + "=" * 60)
        print("✅ DATASET INSIGHT REPORT COMPLETED")
        print("=" * 60)

        return result


# -------------------------------
# CLI Interface
# -------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Dataset Insight Reporter (CrewAI + Groq)",
        epilog="""
Examples:
  python dataset_insight_reporter.py data.csv
  python dataset_insight_reporter.py sales.csv --output report.txt
        """
    )

    parser.add_argument("csv_file", help="Path to CSV dataset")
    parser.add_argument("--output", "-o", help="Output report file (optional)")

    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file")
        sys.exit(1)

    try:
        crew = DatasetInsightCrew(args.csv_file)
        result = crew.run()

        print("\n" + "=" * 60)
        print("📝 DATASET INSIGHT REPORT")
        print("=" * 60 + "\n")
        print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(str(result))
            print(f"\n✅ Report saved to {args.output}")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
