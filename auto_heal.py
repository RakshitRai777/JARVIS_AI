from groq_ai import GroqAI
from health_check import run_health_check

ai = GroqAI()

def auto_heal():
    report = run_health_check()
    failed = [k for k, v in report.items() if not v]

    if not failed:
        print("✅ System healthy. No action needed.")
        return

    prompt = f"""
You are an AI system engineer.
These components failed: {failed}
Explain the cause and give step-by-step fixes.
"""

    solution = ai.ask(prompt)

    print("\n🔧 AUTO-HEAL SUGGESTION")
    print(solution)

if __name__ == "__main__":
    auto_heal()
