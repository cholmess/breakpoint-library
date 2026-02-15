from pathlib import Path


ROOT = Path(__file__).parent.parent
CI_DIR = ROOT / "examples" / "ci"


def test_ci_template_files_exist():
    assert (CI_DIR / "github-actions-breakpoint.yml").is_file()
    assert (CI_DIR / "run-breakpoint-gate.sh").is_file()


def test_ci_shell_template_is_executable():
    shell_template = CI_DIR / "run-breakpoint-gate.sh"
    assert shell_template.stat().st_mode & 0o111


def test_github_actions_template_has_copy_paste_gate_contract():
    workflow = (CI_DIR / "github-actions-breakpoint.yml").read_text(encoding="utf-8")
    assert "BREAKPOINT_FAIL_ON: warn" in workflow
    assert "continue-on-error: true" in workflow
    assert 'echo "exit_code=$code" >> "$GITHUB_OUTPUT"' in workflow
    assert "Enforce gate result" in workflow
