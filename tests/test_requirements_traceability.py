from pathlib import Path

STATUSES = {"Done", "Partial", "Not started"}


def phase_statuses(path: str) -> dict[int, str]:
    statuses: dict[int, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not cells[0].isdigit():
            continue
        status = next((cell for cell in cells[1:] if cell in STATUSES), None)
        if status:
            statuses[int(cells[0])] = status
    return statuses


def summary_counts(path: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        for status in STATUSES:
            prefix = f"- {status}: "
            if stripped.startswith(prefix):
                counts[status] = int(stripped.removeprefix(prefix).removesuffix("."))
    return counts


def test_requirements_traceability_covers_completion_matrix_phases():
    matrix = phase_statuses("docs/COMPLETION_MATRIX.md")
    traceability = phase_statuses("docs/REQUIREMENTS_TRACEABILITY.md")

    assert len(matrix) == 89
    assert set(traceability) == set(matrix)
    assert traceability == matrix


def test_completion_matrix_summary_matches_phase_rows():
    matrix = phase_statuses("docs/COMPLETION_MATRIX.md")
    summary = summary_counts("docs/COMPLETION_MATRIX.md")

    assert summary == {status: list(matrix.values()).count(status) for status in sorted(STATUSES)}
