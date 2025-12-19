from groq_ai import GroqAI
from health_check import run_health_check
from logger import info, warn

ai = GroqAI()

def auto_heal():
    info("Running auto-heal system")
    report = run_health_check()
    failed = [k for k, v in report.items() if not v]

    if not failed:
        info("System healthy. No auto-heal required.")
        return

    warn(f"Auto-heal triggered for components: {failed}")

    prompt = f"""
You are an AI system engineer.
These components failed: {failed}
Explain the cause and give step-by-step fixes.
"""

    solution = ai.ask(prompt)
    info("Auto-heal solution generated")
    print("\n🔧 AUTO-HEAL SUGGESTION\n", solution)

if __name__ == "__main__":
    auto_heal()
