from core.engine import ArkaEngine
from core.modes.planning import PlanningMode
import os
import time

def run_grand_challenge():
    print("🚀 STARTING GRAND CHALLENGE: The 8 Trials of ARKA")
    engine = ArkaEngine()
    planner = PlanningMode(engine)
    
    # 1. Apple Music
    print("\n[1] Hardware Control: Apple Music")
    try:
        # We start with open_app since 'music' tool assumes app is running or handles it via osascript
        # But let's just ask the agent directly.
        res = engine.run("Open Apple Music and play the song 'Navior'.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 2. Open Comet Browser & Play Youtube
    print("\n[2] Process Control: Comet & Youtube")
    try:
        # 'Comet' might not exist, but let's try opening it. If not, open Safari/Chrome.
        # User asked for 'Comet'. 
        res = engine.run("Open the application 'Comet'. Then open a new tab with 'youtube.com' and search for 'Punkrocker song'.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 3. Web Search
    print("\n[3] Web Search")
    try:
        res = engine.run("Do a web search for 'Latest AI Agent frameworks 2025'.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 4. Deep Research (Simulated)
    print("\n[4] Deep Research")
    try:
        res = engine.run("Research the history of 'Antigravity' propulsion theories. Provide a summary.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 5. Planning (Navigation)
    print("\n[5] Planning: Navigation")
    try:
        res = planner.start_plan("Plan a trip from New York to London using sustainable transport methods.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 6. Build Portfolio & Test
    print("\n[6] Coding & Verification: Portfolio")
    try:
        task = """
        1. Create a file 'portfolio.html' with a simple personal portfolio template.
        2. Open this file in a browser to verify it loads.
        """
        res = engine.run(task)
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 7. Resume Analysis
    print("\n[7] Resume Analysis")
    resume_path = "/Users/xyx/Documents/DESKTOP/Resumes/my_ai_resume.pdf"
    try:
        if not os.path.exists(resume_path):
            print(f"⚠️ Resume not found at {resume_path}. Creating a dummy text resume for testing.")
            resume_path = "dummy_resume.pdf"
            # We can't easily make a PDF, let's make a txt and pretend or skip pdf specific test if not found.
            # Actually, `read_file` supports text too. usage of .pdf extension implies pdf parser trigger.
            # Let's skip creating dummy if pypdf is expected.
            print("Skipping PDF creation. Asking agent to check path.")
            
        task = f"Read the file at '{resume_path}' and identify three weak points."
        res = engine.run(task)
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 8. Internship Search
    print("\n[8] Job Search")
    try:
        task = "Find 3 relevant internship postings based on the skills in the resume I just analyzed. Provide links."
        res = engine.run(task)
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n🎉 Grand Challenge Completed.")

if __name__ == "__main__":
    run_grand_challenge()
