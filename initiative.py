from awareness import is_idle

def should_speak(importance="low"):
    score = 0
    if importance == "high":
        score += 3
    if is_idle(240):
        score += 2
    return score >= 4
