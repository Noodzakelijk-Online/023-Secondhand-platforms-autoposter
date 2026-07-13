from pathlib import Path


def test_progressive_stabilization_gates_reference_release_gate_status():
    content = Path("docs/PROGRESSIVE_STABILIZATION_GATES.md").read_text(encoding="utf-8")

    required_phrases = [
        "`python scripts/release_gate.py` reports `ready`",
        "`python scripts/release_gate.py` reports `blocked`",
        "Gate 5 | Blocked",
        "final release evidence records are incomplete",
    ]
    for phrase in required_phrases:
        assert phrase in content
