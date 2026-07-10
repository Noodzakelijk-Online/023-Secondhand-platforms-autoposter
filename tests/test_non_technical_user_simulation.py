from pathlib import Path


def test_non_technical_user_simulation_requires_real_user_evidence():
    content = Path("docs/NON_TECHNICAL_USER_SIMULATION.md").read_text(encoding="utf-8")

    required_phrases = [
        "proxy simulation",
        "not a substitute for observing a real non-technical user",
        "Queue publish",
        "sounds too automatic",
        "real non-technical user walkthrough must be executed",
        "remains partial until external user evidence exists",
    ]
    for phrase in required_phrases:
        assert phrase in content
