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


def test_requirements_traceability_covers_completion_matrix_phases():
    matrix = phase_statuses("docs/COMPLETION_MATRIX.md")
    traceability = phase_statuses("docs/REQUIREMENTS_TRACEABILITY.md")

    assert len(matrix) == 89
    assert set(traceability) == set(matrix)
    assert traceability == matrix
