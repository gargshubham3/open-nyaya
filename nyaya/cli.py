import os
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from nyaya.mapper import LawMapper
from nyaya.auditor import CaseAuditor
from nyaya.parser import FIRParser
from nyaya.drafter import BailDrafter

console = Console()

@click.group()
@click.version_option(version="0.1.0", prog_name="open-nyaya")
def cli():
    """⚖️ open-nyaya: AI & Legal Computing Toolkit for Modern Indian Law."""
    pass

@cli.command()
@click.argument("act")
@click.argument("section")
def lookup(act: str, section: str):
    """Lookup statutory mapping for a section (e.g. 'IPC 420' or 'BNS 103')."""
    mapper = LawMapper()
    res = mapper.lookup(act, section)

    if not res:
        console.print(f"[bold red]No mapping found for {act.upper()} Section {section}.[/bold red]")
        sys.exit(1)

    table = Table(title=f"Statutory Mapping: {act.upper()} {section}", show_header=True, header_style="bold cyan")
    table.add_column("Attribute", style="bold yellow", width=20)
    table.add_column("Details", style="white")

    table.add_row("Status", f"[bold green]{res.status}[/bold green]")
    table.add_row("Source", f"{res.source.act} Section {res.source.section} ({res.source.title})")
    
    if res.target:
        table.add_row("Target", f"[bold cyan]{res.target.act} Section {res.target.section}[/bold cyan] ({res.target.title})")
        if res.target.sub_section:
            table.add_row("Sub-Section", res.target.sub_section)
        table.add_row("Target Chapter", res.target.chapter or "N/A")
    else:
        table.add_row("Target", "[italic red]Repealed / No Direct Equivalent[/italic red]")

    table.add_row("Statement", res.mapping_statement)

    console.print(table)

    if res.full_text:
        console.print(Panel(res.full_text[:500] + "...", title="Statute Excerpt", border_style="dim"))

@cli.command()
@click.argument("charges")
def translate(charges: str):
    """Translate arbitrary charges string (e.g. 'IPC 420, 120B and CrPC 41A')."""
    mapper = LawMapper()
    results = mapper.translate_string(charges)

    if not results:
        console.print(f"[bold yellow]No recognized sections found in: '{charges}'[/bold yellow]")
        return

    table = Table(title="Parsed & Translated Charges", show_header=True, header_style="bold magenta")
    table.add_column("Source Law", style="yellow")
    table.add_column("Target Modern Law", style="bold green")
    table.add_column("Title / Offence", style="white")

    for r in results:
        src_str = f"{r.source.act} Sec {r.source.section}" if r.source else r.lookup_key
        tgt_str = f"{r.target.act} Sec {r.target.section}" if r.target else "Repealed"
        title = r.target.title if r.target else (r.source.title if r.source else "")
        table.add_row(src_str, tgt_str, title)

    console.print(table)

@cli.command()
@click.argument("query")
@click.option("--act", default=None, help="Filter by Act (IPC, BNS, CrPC, BNSS, IEA, BSA)")
@click.option("--limit", default=10, help="Maximum results to return")
def search(query: str, act: str, limit: int):
    """Keyword search across all Indian criminal statutes."""
    mapper = LawMapper()
    results = mapper.search(query, act=act, limit=limit)

    if not results:
        console.print(f"[yellow]No results matching '{query}'.[/yellow]")
        return

    table = Table(title=f"Search Results for '{query}' ({len(results)} found)", show_header=True, header_style="bold blue")
    table.add_column("Act", style="cyan", width=12)
    table.add_column("Section", style="bold yellow", width=10)
    table.add_column("Title", style="white")
    table.add_column("Mapped Modern Equivalent", style="green")

    for r in results:
        src_act = r.source.act.split(",")[0] if r.source else ""
        src_sec = r.source.section if r.source else ""
        src_title = r.source.title if r.source else ""
        tgt_str = f"{r.target.act.split(',')[0]} Sec {r.target.section}" if r.target else "-"
        table.add_row(src_act, src_sec, src_title, tgt_str)

    console.print(table)

@cli.command()
@click.argument("input_path_or_text")
def audit(input_path_or_text: str):
    """Audit an FIR or charge-sheet for procedural defects and BNSS violations."""
    if os.path.exists(input_path_or_text):
        with open(input_path_or_text, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = input_path_or_text

    parser = FIRParser()
    fir = parser.parse_text(text)

    auditor = CaseAuditor()
    report = auditor.audit(fir)

    console.print(Panel(
        f"[bold]FIR No:[/bold] {fir.fir_number} | [bold]PS:[/bold] {fir.police_station} | [bold]Accused:[/bold] {report.accused_name}\n"
        f"[bold]Bail Favourability Score:[/bold] [bold green]{report.bail_favourability_score}/100[/bold green]",
        title="⚖️ Case Audit Summary",
        border_style="cyan"
    ))

    if report.flags:
        console.print("\n[bold red]Detected Procedural Defects & Violations:[/bold red]")
        for idx, flag in enumerate(report.flags, start=1):
            color = "red" if flag.severity == "CRITICAL" else ("yellow" if flag.severity == "HIGH" else "blue")
            console.print(Panel(
                f"[bold {color}][{flag.severity}] {flag.title}[/bold {color}]\n\n"
                f"{flag.violation_detail}\n\n"
                f"[bold cyan]Statutory Reference:[/bold cyan] {flag.statutory_reference}\n"
                f"[bold green]Judicial Precedent:[/bold green] {flag.judicial_precedent}\n\n"
                f"[bold yellow]Suggested Argument:[/bold yellow]\n{flag.suggested_defense_argument}",
                border_style=color
            ))

    if report.cross_examination_questions:
        console.print("\n[bold cyan]Recommended Cross-Examination Questions for IO:[/bold cyan]")
        for q in report.cross_examination_questions:
            console.print(f" [bold yellow]•[/bold yellow] {q}")

@cli.command(name="draft-bail")
@click.option("--accused", prompt="Accused Name", default="Ramesh Kumar")
@click.option("--fir", prompt="FIR Number/Year", default="101/2026")
@click.option("--ps", prompt="Police Station", default="Hazratganj")
@click.option("--district", prompt="District", default="Lucknow")
@click.option("--state", default="Uttar Pradesh")
@click.option("--sections", prompt="Sections Charged (e.g. 'IPC 420, 120B')", default="IPC 420, 120B")
@click.option("--custody-days", default=30, type=int)
@click.option("--output", default=None, help="Save to file path (.txt or .md)")
def draft_bail(accused, fir, ps, district, state, sections, custody_days, output):
    """Generate a court-ready District Court Regular Bail Application under Section 480 BNSS."""
    mapper = LawMapper()
    auditor = CaseAuditor(mapper)
    drafter = BailDrafter(mapper)

    # Build FIR object
    from nyaya.models import FIRDetails, AccusedPerson, SectionCharge
    translated = mapper.translate_string(sections)
    charges = [
        SectionCharge(act=t.source.act if t.source else "IPC", section=t.source.section if t.source else t.lookup_key)
        for t in translated
    ] if translated else [SectionCharge(act="IPC", section="420")]

    fir_obj = FIRDetails(
        fir_number=fir,
        year=2026,
        police_station=ps,
        district=district,
        state=state,
        accused_list=[AccusedPerson(name=accused, is_arrested=True, custody_days=custody_days)],
        sections_charged=charges,
        section_35_notice_issued=False
    )

    report = auditor.audit(fir_obj)
    draft = drafter.draft_bail(fir_obj, report)

    console.print(Panel(draft.formatted_document, title="Generated Bail Pleading (BNSS Sec 480)", border_style="green"))

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(draft.formatted_document)
        console.print(f"[bold green]Saved bail application to {output}[/bold green]")

@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface")
@click.option("--port", default=8000, help="Port to listen on")
def serve(host: str, port: int):
    """Start the interactive open-nyaya web server."""
    import uvicorn
    console.print(f"[bold green]Starting Open-Nyaya server at http://{host}:{port}[/bold green]")
    uvicorn.run("nyaya.web:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    cli()
