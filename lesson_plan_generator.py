import os

os.environ["RICH_DISABLE"] = "1"
os.environ["CREWAI_DISABLE_RICH"] = "1"

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import sys
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Groq with Llama model
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    base_url="https://api.groq.com/openai/v1"
)


class LessonPlanAgents:
    """Define agents for lesson plan generation"""
    
    def __init__(self, llm_instance):
        self.llm = llm_instance
    
    def researcher_agent(self):
        """Agent that researches the topic"""
        return Agent(
            role='Educational Content Researcher',
            goal='Research topic thoroughly to identify key concepts, learning objectives, and age-appropriate content',
            backstory="""You are an experienced curriculum researcher with expertise in 
            educational content development. You excel at breaking down complex topics into 
            teachable components, identifying prerequisite knowledge, and understanding how 
            students learn at different grade levels. You always consider pedagogical best 
            practices and learning theory when researching content.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def curriculum_designer_agent(self):
        """Agent that designs the lesson plan structure"""
        return Agent(
            role='Curriculum Designer',
            goal='Create comprehensive, well-structured 4-week lesson plans with clear progression',
            backstory="""You are a master curriculum designer with 15 years of experience 
            creating engaging lesson plans. You understand learning progressions, Bloom's 
            taxonomy, and differentiation strategies. You design lessons that build upon each 
            other, incorporate various teaching methods, and include formative assessments. 
            Your lesson plans are detailed, practical, and aligned with educational standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def reviewer_agent(self):
        """Agent that reviews and refines the lesson plan"""
        return Agent(
            role='Instructional Coach',
            goal='Review lesson plans for clarity, feasibility, and effectiveness, then refine them',
            backstory="""You are an instructional coach who helps teachers improve their 
            lesson plans. You have a keen eye for clarity, practical implementation, and 
            student engagement. You identify gaps, unclear instructions, missing materials, 
            or unrealistic timeframes. You refine lesson plans to be crystal clear, actionable, 
            and effective for actual classroom use.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class LessonPlanTasks:
    """Define tasks for lesson plan generation"""
    
    def research_task(self, agent, topic, grade_level, subject):
        """Task to research the topic"""
        return Task(
            description=f"""
            Research the following topic for lesson planning:
            
            TOPIC: {topic}
            GRADE LEVEL: {grade_level}
            SUBJECT: {subject}
            
            Your research should cover:
            
            1. KEY CONCEPTS AND CONTENT
               - What are the essential concepts students must learn?
               - What are the foundational ideas they need to understand first?
               - What vocabulary or terminology is important?
            
            2. LEARNING OBJECTIVES
               - What should students know by the end of 4 weeks?
               - What skills should they be able to demonstrate?
               - How does this align with {grade_level} capabilities?
            
            3. PREREQUISITE KNOWLEDGE
               - What should students already know before starting?
               - What gaps might need to be addressed?
            
            4. COMMON MISCONCEPTIONS
               - What do students typically misunderstand about this topic?
               - What challenging concepts need extra attention?
            
            5. TEACHING APPROACHES
               - What teaching methods work best for this topic?
               - What hands-on activities could reinforce learning?
               - What real-world connections can be made?
            
            6. ASSESSMENT STRATEGIES
               - How can we check for understanding?
               - What types of assessments are appropriate?
            
            Be thorough and consider age-appropriateness for {grade_level} students.
            """,
            agent=agent,
            expected_output=f"""Comprehensive research report on {topic} containing:
            - 5-7 key concepts to teach
            - 3-5 clear learning objectives
            - Prerequisite knowledge required
            - 2-3 common misconceptions
            - Suggested teaching approaches
            - Assessment strategy ideas
            
            All content appropriate for {grade_level} level."""
        )
    
    def design_task(self, agent, research_task):
        """Task to design the 4-week lesson plan"""
        return Task(
            description="""
            Based on the research provided, design a comprehensive 4-week lesson plan.
            
            Structure the plan as follows:
            
            WEEK 1: INTRODUCTION AND FOUNDATIONS
            For each day (Day 1-5):
            - Learning Objective (what students will learn today)
            - Materials Needed (specific items required)
            - Introduction/Hook (5-10 min) - engaging activity to start
            - Main Instruction (20-30 min) - core teaching activities
            - Guided Practice (15-20 min) - students practice with support
            - Independent Practice (10-15 min) - students work alone
            - Closure/Assessment (5-10 min) - check understanding
            - Homework/Extension (optional activities)
            
            WEEK 2: SKILL DEVELOPMENT
            Follow same daily structure, building on Week 1
            
            WEEK 3: APPLICATION AND DEEPENING
            Follow same daily structure, applying concepts
            
            WEEK 4: SYNTHESIS AND ASSESSMENT
            Follow same daily structure, culminating project/assessment
            
            Requirements:
            - Each day should have clear, measurable objectives
            - Include variety of teaching methods (direct instruction, group work, 
              hands-on activities, discussions, technology integration)
            - Incorporate formative assessments throughout
            - Build complexity progressively across 4 weeks
            - Include differentiation notes for struggling and advanced students
            - Specify exact materials needed for each activity
            - Provide realistic time estimates
            - Include a summative assessment in Week 4
            
            Make it detailed enough that a teacher could implement it directly.
            """,
            agent=agent,
            expected_output="""A complete 4-week lesson plan with:
            - 20 daily lessons (5 days × 4 weeks)
            - Each day with all required components
            - Clear learning progression
            - Variety of activities and assessments
            - Specific materials lists
            - Realistic time allocations
            - Differentiation strategies
            
            Plan should be 2000-2500 words total.""",
            context=[research_task]
        )
    
    def review_task(self, agent, design_task):
        """Task to review and refine the lesson plan"""
        return Task(
            description="""
            Review the lesson plan for clarity, feasibility, and effectiveness. 
            Then refine it to be crystal clear and immediately usable.
            
            REVIEW CHECKLIST:
            
            1. CLARITY
               - Are objectives written in clear, student-friendly language?
               - Are instructions specific enough for a new teacher?
               - Is the progression logical and easy to follow?
            
            2. FEASIBILITY
               - Are time estimates realistic?
               - Are materials commonly available or easy to obtain?
               - Can activities actually be completed in allocated time?
               - Is the workload appropriate for the grade level?
            
            3. EFFECTIVENESS
               - Do activities align with learning objectives?
               - Is there enough variety to maintain engagement?
               - Are assessments meaningful and actionable?
               - Does each week build logically on the previous?
            
            4. COMPLETENESS
               - Are any materials or steps missing?
               - Are there gaps in the learning progression?
               - Is differentiation adequately addressed?
            
            REFINEMENT TASKS:
            
            - Rewrite unclear objectives to be specific and measurable
            - Add missing materials or preparation steps
            - Adjust time allocations if unrealistic
            - Enhance activities that seem dull or ineffective
            - Improve transitions between days and weeks
            - Add more specific differentiation strategies
            - Clarify any vague instructions
            - Ensure consistent formatting throughout
            
            Produce a REFINED version that is polished and ready for classroom use.
            """,
            agent=agent,
            expected_output="""A refined, polished 4-week lesson plan with:
            - Crystal clear objectives and instructions
            - Realistic, tested time estimates
            - Complete materials lists with no gaps
            - Engaging, varied activities
            - Smooth transitions and logical flow
            - Specific differentiation guidance
            - Professional formatting
            - Ready for immediate classroom implementation
            
            Include a brief summary of improvements made.""",
            context=[design_task]
        )


class LessonPlanCrew:
    """Orchestrate the lesson plan generation process"""
    
    def __init__(self, topic, grade_level, subject):
        self.topic = topic
        self.grade_level = grade_level
        self.subject = subject
        self.llm = llm
        
        print("\n" + "="*60)
        print("📚 LESSON PLAN GENERATOR")
        print("="*60)
        print(f"\n📖 Topic: {topic}")
        print(f"🎓 Grade Level: {grade_level}")
        print(f"📝 Subject: {subject}")
        print("⏱️  Duration: 4 weeks")
    
    def run(self):
        print("\n" + "="*60)
        print("🔧 SETTING UP AGENTS")
        print("="*60)
        
        agents = LessonPlanAgents(self.llm)
        researcher = agents.researcher_agent()
        designer = agents.curriculum_designer_agent()
        reviewer = agents.reviewer_agent()
        print("✓ Agents created: Researcher, Designer, Reviewer")
        
        print("\n" + "="*60)
        print("📋 CREATING TASKS")
        print("="*60)
        
        tasks = LessonPlanTasks()
        research_task = tasks.research_task(researcher, self.topic, 
                                           self.grade_level, self.subject)
        print("✓ Task 1: Research topic and learning objectives")
        
        design_task = tasks.design_task(designer, research_task)
        print("✓ Task 2: Design 4-week lesson plan")
        
        review_task = tasks.review_task(reviewer, design_task)
        print("✓ Task 3: Review and refine for clarity")
        
        all_tasks = [research_task, design_task, review_task]
        
        print("\n" + "="*60)
        print("👥 ASSEMBLING CREW")
        print("="*60)
        
        crew = Crew(
            agents=[researcher, designer, reviewer],
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )
        print(f"✓ Crew assembled with {len(all_tasks)} tasks")
        
        print("\n" + "="*60)
        print("🚀 STARTING LESSON PLAN GENERATION")
        print("="*60)
        print("This may take 5-8 minutes...")
        print("The crew will:")
        print("  1. Research the topic thoroughly")
        print("  2. Design a comprehensive 4-week plan")
        print("  3. Review and refine for clarity")
        print("\nYou will see the process below:\n")
        
        # Execute
        result = crew.kickoff()
        
        print("\n" + "="*60)
        print("✅ LESSON PLAN COMPLETED!")
        print("="*60)
        
        return result


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI Lesson Plan Generator - Create comprehensive 4-week lesson plans',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lesson_plan_generator.py "Photosynthesis" "Grade 7" "Science"
  python lesson_plan_generator.py "The Water Cycle" "Grade 5" "Science" --output plan.txt
  python lesson_plan_generator.py "Fractions" "Grade 4" "Mathematics" -o fractions_plan.txt
  python lesson_plan_generator.py "The American Revolution" "Grade 8" "History"
  python lesson_plan_generator.py "Creative Writing" "Grade 6" "English"
  
Grade Level Options:
  - Elementary: Grade 1, Grade 2, Grade 3, Grade 4, Grade 5
  - Middle School: Grade 6, Grade 7, Grade 8
  - High School: Grade 9, Grade 10, Grade 11, Grade 12
  
Common Subjects:
  - Science, Mathematics, English, History, Geography
  - Art, Music, Physical Education, Computer Science
        """
    )
    
    parser.add_argument('topic', help='Topic for the lesson plan (e.g., "Photosynthesis")')
    parser.add_argument('grade_level', help='Grade level (e.g., "Grade 7")')
    parser.add_argument('subject', help='Subject area (e.g., "Science")')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not found in .env file!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("AI LESSON PLAN GENERATOR")
    print("="*60)
    print(f"📊 Model: groq/llama-3.1-8b-instant")
    print(f"📖 Topic: {args.topic}")
    print(f"🎓 Grade: {args.grade_level}")
    print(f"📚 Subject: {args.subject}")
    print("="*60)
    
    try:
        crew = LessonPlanCrew(args.topic, args.grade_level, args.subject)
        result = crew.run()
        
        print("\n" + "="*60)
        print("📝 4-WEEK LESSON PLAN")
        print("="*60 + "\n")
        print(result)
        print("\n" + "="*60)
        
        # Save to file
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(f"4-WEEK LESSON PLAN\n")
                f.write("="*60 + "\n\n")
                f.write(f"Topic: {args.topic}\n")
                f.write(f"Grade Level: {args.grade_level}\n")
                f.write(f"Subject: {args.subject}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n" + "="*60 + "\n\n")
                f.write(str(result))
            print(f"\n✅ Lesson plan saved to {args.output}")
        
        # Create a quick reference file
        quick_ref = args.output.replace('.txt', '_quick_ref.txt') if args.output else 'lesson_plan_quick_ref.txt'
        with open(quick_ref, 'w', encoding='utf-8') as f:
            f.write("LESSON PLAN QUICK REFERENCE\n")
            f.write("="*60 + "\n\n")
            f.write(f"Topic: {args.topic}\n")
            f.write(f"Grade: {args.grade_level}\n")
            f.write(f"Subject: {args.subject}\n")
            f.write(f"Duration: 4 weeks (20 lessons)\n\n")
            f.write("Weekly Overview:\n")
            f.write("  Week 1: Introduction and Foundations\n")
            f.write("  Week 2: Skill Development\n")
            f.write("  Week 3: Application and Deepening\n")
            f.write("  Week 4: Synthesis and Assessment\n\n")
            f.write(f"Full plan available in: {args.output if args.output else 'console output'}\n")
        print(f"✅ Quick reference saved to {quick_ref}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)