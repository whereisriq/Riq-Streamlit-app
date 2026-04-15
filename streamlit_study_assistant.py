import os
os.environ["RICH_DISABLE"] = "true"

import json
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import time

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# CUSTOM CSS
# ===============================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .memory-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# ENVIRONMENT SETUP
# ===============================
load_dotenv()

MEMORY_FILE = "student_memory.json"

# ===============================
# INITIALIZE SESSION STATE
# ===============================
if 'memory' not in st.session_state:
    st.session_state.memory = None
if 'study_output' not in st.session_state:
    st.session_state.study_output = None
if 'is_studying' not in st.session_state:
    st.session_state.is_studying = False

# ===============================
# MEMORY UTILITIES
# ===============================
def load_memory():
    """Load student memory from JSON file"""
    if not os.path.exists(MEMORY_FILE):
        return {
            "student_name": "Student",
            "preferences": {
                "explanation_style": "simple",
                "difficulty": "medium"
            },
            "topics_studied": [],
            "progress_notes": []
        }
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    """Save student memory to JSON file"""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)
        return True
    except Exception as e:
        st.error(f"❌ Failed to save memory: {str(e)}")
        return False


def update_memory(memory, topic, note):
    """Update memory with new topic and progress note"""
    if not topic or not topic.strip():
        return memory
    
    topic = topic.strip()
    if topic not in memory["topics_studied"]:
        memory["topics_studied"].append(topic)
    
    memory["progress_notes"].append({
        "topic": topic,
        "note": note,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_memory(memory)
    return memory


def reset_memory():
    """Reset student memory to defaults"""
    default_memory = {
        "student_name": "Student",
        "preferences": {
            "explanation_style": "simple",
            "difficulty": "medium"
        },
        "topics_studied": [],
        "progress_notes": []
    }
    save_memory(default_memory)
    return default_memory


# ===============================
# CREWAI SETUP
# ===============================
@st.cache_resource
def get_llm():
    """Initialize and cache LLM instance"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not found in environment variables!")
        st.stop()
    
    return LLM(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0.5,
        base_url="https://api.groq.com/openai/v1"
    )


class StudyAssistantAgents:
    """Agent definitions for the study assistant"""
    def __init__(self, llm_instance):
        self.llm = llm_instance

    def tutor_agent(self):
        return Agent(
            role="AI Study Tutor",
            goal="Teach topics clearly while adapting to the student's preferences and learning history",
            backstory="""You are a reliable AI tutor who remembers what the student has learned before.
You adapt explanations based on difficulty preference and past progress.
You never contradict earlier learning unless correcting misconceptions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )


class StudyAssistantTasks:
    """Task definitions for the study assistant"""
    def study_task(self, agent, topic, memory):
        return Task(
            description=f"""
You are tutoring {memory['student_name']}.

STUDENT MEMORY:
- Preferred explanation style: {memory['preferences']['explanation_style']}
- Difficulty level: {memory['preferences']['difficulty']}
- Topics already studied: {', '.join(memory['topics_studied']) if memory['topics_studied'] else 'None'}

CURRENT TOPIC:
{topic}

TASK:
1. Explain the topic clearly and accurately
2. Adapt to the student's difficulty and style preferences
3. Build on prior knowledge if relevant topics have been studied
4. Include:
   - Clear explanation tailored to their level
   - Key concepts (bulleted list)
   - One concrete example
   - Practice suggestion
5. End with a brief progress note

Make the explanation engaging and appropriate for the {memory['preferences']['difficulty']} difficulty level.
""",
            agent=agent,
            expected_output="""A personalized study explanation with:
- Clear explanation
- Key points (bulleted)
- Concrete example
- Practice suggestion
- Progress note"""
        )


def run_study_session(topic, memory, llm):
    """Execute a study session using CrewAI"""
    # Create agents
    agents = StudyAssistantAgents(llm)
    tutor = agents.tutor_agent()
    
    # Create tasks
    tasks = StudyAssistantTasks()
    study_task = tasks.study_task(tutor, topic, memory)
    
    # Create crew
    crew = Crew(
        agents=[tutor],
        tasks=[study_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    result = crew.kickoff()
    
    # Update memory
    updated_memory = update_memory(
        memory,
        topic,
        f"Studied '{topic}' with {memory['preferences']['difficulty']} difficulty using {memory['preferences']['explanation_style']} style."
    )
    
    return result, updated_memory


# ===============================
# STREAMLIT APP
# ===============================
def main():
    # Header
    st.markdown('<p class="main-header">📚 AI Study Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Personalized learning powered by CrewAI & Groq</p>', unsafe_allow_html=True)
    
    # Load memory
    if st.session_state.memory is None:
        st.session_state.memory = load_memory()
    
    memory = st.session_state.memory
    
    # ===============================
    # SIDEBAR - SETTINGS & STATS
    # ===============================
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Student name
        new_name = st.text_input(
            "Student Name",
            value=memory["student_name"],
            key="student_name_input"
        )
        if new_name != memory["student_name"]:
            memory["student_name"] = new_name
            save_memory(memory)
            st.session_state.memory = memory
        
        st.divider()
        
        # Preferences
        st.subheader("Learning Preferences")
        
        new_style = st.selectbox(
            "Explanation Style",
            options=["simple", "detailed", "technical", "visual"],
            index=["simple", "detailed", "technical", "visual"].index(
                memory["preferences"]["explanation_style"]
            ),
            key="style_select"
        )
        
        new_difficulty = st.selectbox(
            "Difficulty Level",
            options=["beginner", "medium", "advanced"],
            index=["beginner", "medium", "advanced"].index(
                memory["preferences"]["difficulty"]
            ),
            key="difficulty_select"
        )
        
        # Update preferences if changed
        if (new_style != memory["preferences"]["explanation_style"] or 
            new_difficulty != memory["preferences"]["difficulty"]):
            memory["preferences"]["explanation_style"] = new_style
            memory["preferences"]["difficulty"] = new_difficulty
            save_memory(memory)
            st.session_state.memory = memory
            st.success("✅ Preferences updated!")
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Learning Stats")
        st.metric("Topics Studied", len(memory["topics_studied"]))
        st.metric("Total Sessions", len(memory["progress_notes"]))
        
        st.divider()
        
        # Reset button
        if st.button("🔄 Reset Memory", type="secondary", use_container_width=True):
            st.session_state.show_reset_confirm = True
        
        # Show confirmation if needed
        if st.session_state.get("show_reset_confirm", False):
            st.warning("⚠️ This will delete all your learning history!")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("✅ Yes, Reset", use_container_width=True):
                    st.session_state.memory = reset_memory()
                    st.session_state.study_output = None
                    st.session_state.show_reset_confirm = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_reset_confirm = False
                    st.rerun()
    
    # ===============================
    # MAIN CONTENT
    # ===============================
    
    # Study Input Section
    st.header("📖 Start Learning")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        topic = st.text_input(
            "What would you like to study today?",
            placeholder="e.g., Photosynthesis, Quadratic Equations, World War II...",
            key="topic_input"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        study_button = st.button(
            "🚀 Start Learning",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_studying or not topic.strip()
        )
    
    # Execute study session
    if study_button and topic and topic.strip():
        # Validate topic
        topic = topic.strip()
        if len(topic) < 2:
            st.error("❌ Topic must be at least 2 characters long.")
            st.stop()
        if len(topic) > 200:
            st.error("❌ Topic must be less than 200 characters long.")
            st.stop()
        
        st.session_state.is_studying = True
        
        with st.spinner("🤖 Your AI tutor is preparing the lesson..."):
            try:
                llm = get_llm()
                result, updated_memory = run_study_session(topic, memory, llm)
                
                st.session_state.study_output = str(result)
                st.session_state.memory = updated_memory
                st.session_state.is_studying = False
                st.success("✅ Lesson completed!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.is_studying = False
    
    # Display study output
    if st.session_state.study_output:
        st.divider()
        st.header("📝 Lesson")
        
        st.markdown(f"""
        <div class="success-box">
            <strong>✅ Lesson completed successfully!</strong>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(st.session_state.study_output)
    
    # ===============================
    # LEARNING HISTORY
    # ===============================
    if memory["topics_studied"]:
        st.divider()
        st.header("📚 Learning History")
        
        # Display topics in a grid
        cols = st.columns(3)
        for idx, topic in enumerate(memory["topics_studied"]):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="memory-card">
                    📌 {topic}
                </div>
                """, unsafe_allow_html=True)
        
        # Progress notes expander
        with st.expander("📋 View Detailed Progress Notes"):
            for note in reversed(memory["progress_notes"][-10:]):  # Last 10 notes
                timestamp = note.get("timestamp", "Unknown time")
                topic = note.get("topic", "Unknown topic")
                note_text = note.get("note", note if isinstance(note, str) else "")
                
                st.markdown(f"""
                **{timestamp}** - {topic}  
                _{note_text}_
                """)
                st.divider()


# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    main()