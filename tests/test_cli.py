from click.testing import CliRunner
from nyaya.cli import cli

def test_cli_lookup():
    runner = CliRunner()
    result = runner.invoke(cli, ["lookup", "IPC", "420"])
    assert result.exit_code == 0
    assert "318" in result.output
    assert "Cheating" in result.output

def test_cli_translate():
    runner = CliRunner()
    result = runner.invoke(cli, ["translate", "IPC 420, 120B and CrPC 41A"])
    assert result.exit_code == 0
    assert "318" in result.output
    assert "61" in result.output

def test_cli_search():
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "theft", "--limit", "3"])
    assert result.exit_code == 0
    assert "Theft" in result.output or "theft" in result.output.lower()

def test_cli_audit():
    runner = CliRunner()
    sample = "FIR No. 50/2026. PS: Hazratganj. Accused Ramesh booked under IPC 420. Arrested without notice."
    result = runner.invoke(cli, ["audit", sample])
    assert result.exit_code == 0
    assert "Bail Favourability Score" in result.output
