"""
JARVIS SYSTEM SELF-TEST
Run with: python test_jarvis.py
"""

import time
import queue
import traceback

# ===================== RESULTS =====================
results = []

def test(name, fn):
    try:
        fn()
        results.append((name, True, "OK"))
    except Exception as e:
        results.append((name, False, str(e)))

# ===================== TESTS =====================

def test_config():
    from config import Config
    assert Config.GROQ_API_KEY, "GROQ_API_KEY missing"

def test_imports():
    import main
    import healing_arbiter
    import vision_module
    import brain_manager

def test_queues():
    import main
    assert isinstance(main.command_queue, queue.Queue)
    assert isinstance(main.stream_queue, queue.Queue)

def test_brain_manager():
    from brain_manager import BrainManager
    assert hasattr(BrainManager, "start")
    assert hasattr(BrainManager, "restart")

def test_groq_connectivity():
    import main
    reply = main.groq("Say OK")
    assert isinstance(reply, str)
    assert len(reply) > 0

def test_healing_snapshot():
    import healing_arbiter
    snap = healing_arbiter.snapshot("test")
    assert "cpu" in snap
    assert "ram" in snap
    assert "queue" in snap

def test_healing_think():
    import healing_arbiter
    snap = healing_arbiter.snapshot("test")
    decision = healing_arbiter.think(snap)
    assert "action" in decision
    assert "confidence" in decision

def test_streaming_pipeline():
    import main
    main.stream_queue.put("hello ")
    main.stream_queue.put("__END__")
    token = main.stream_queue.get(timeout=1)
    assert token == "hello "

def test_tts_pipeline():
    import main
    # Dry test: ensure function exists and does not crash on empty text
    main.speak("")

def test_vision_module():
    import vision_module
    assert hasattr(vision_module, "get_vision_analysis")

# ===================== RUN ALL =====================

if __name__ == "__main__":
    print("\n🔍 Running JARVIS system self-test...\n")

    test("Config loaded", test_config)
    test("Imports valid", test_imports)
    test("Queues initialized", test_queues)
    test("Brain manager OK", test_brain_manager)
    test("Groq connectivity", test_groq_connectivity)
    test("Healing snapshot", test_healing_snapshot)
    test("Healing decision", test_healing_think)
    test("Streaming pipeline", test_streaming_pipeline)
    test("TTS pipeline", test_tts_pipeline)
    test("Vision module", test_vision_module)

    print("\n📋 Test Results:\n")

    failed = False
    for name, ok, info in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} — {name}")
        if not ok:
            print(f"    ↳ {info}")
            failed = True

    print("\n==============================\n")

    if failed:
        print("❌ JARVIS has issues. Please fix the failed tests above.")
    else:
        print("🟢 Everything is working properly without any type of errors.")
