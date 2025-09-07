from __future__ import annotations
import os, json, asyncio, sys
from pathlib import Path
from typing import Optional
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
import pandas as pd

from .logging import get_logger, set_correlation_id, setup_development_logging, setup_production_logging
from .errors import (
    map_exception,
    NotFoundError,
    ValidationError,
    UsageError,
)
from .config import settings
from .provenance import ProvenanceStore
from .lineage import LineageStore
from .chemistry import fit_parameters
from .rule_engine import evaluate_permit
from .permits import load_permit
from .reports.certificate import generate_certificate
from .utils.io import ensure_dir
from . import streaming as streaming_mod
from . import rules as rules_mod
from .dashboard import build_app as build_dashboard_app

console = Console()
app = typer.Typer(add_completion=False, help="OpenWorld Specialty Chemicals CLI - Environmental compliance monitoring and reporting")
log = get_logger("openworld-chem")

def _log_event(event: str, **fields) -> None:
    try:
        log.info(event, extra={"event": event, "fields": fields})
    except Exception:
        pass
DRY_RUN = False
QUIET = False

def _validate_file_exists(file_path: str, file_type: str = "file") -> Path:
    """Validate that a file exists and is readable."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red][ERROR] {file_type.title()} not found: {file_path}[/red]")
        raise NotFoundError(f"{file_type} not found: {file_path}")
    if not path.is_file():
        console.print(f"[red][ERROR] Path is not a file: {file_path}[/red]")
        raise ValidationError(f"Path is not a file: {file_path}")
    return path

def _validate_csv_format(df: pd.DataFrame, required_columns: list[str], file_path: str) -> None:
    """Validate CSV has required columns."""
    missing = set(required_columns) - set(df.columns)
    if missing:
        console.print(f"[red][ERROR] CSV file {file_path} is missing required columns: {', '.join(sorted(missing))}[/red]")
        console.print(f"[yellow]Available columns: {', '.join(df.columns)}[/yellow]")
        raise ValidationError(f"CSV missing columns: {', '.join(sorted(missing))}")

def _handle_error(operation: str, error: Exception) -> None:
    """Standardized error handling."""
    info = map_exception(error)
    console.print(f"[red][ERROR] Error during {operation}: {info.message}[/red]")
    log.error(f"Operation '{operation}' failed: {info.message}", exc_info=True)
    raise typer.Exit(int(info.code))

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error console output"),
    log_format: str = typer.Option("text", "--log-format", help="Log format: text or json", metavar="{text|json}"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Do not modify files or make network calls; print planned actions"),
    config_file: Optional[str] = typer.Option(None, "--config", help="Path to configuration file")
) -> None:
    """OpenWorld Specialty Chemicals CLI - Environmental compliance monitoring and reporting."""
    load_dotenv()
    global DRY_RUN, QUIET
    DRY_RUN = dry_run
    QUIET = quiet

    # Configure logging with correlation id and format
    from uuid import uuid4
    corr_id = uuid4().hex[:8]
    set_correlation_id(corr_id)
    json_fmt = (log_format.lower() == "json")
    # Expose chosen format to child processes/uvicorn
    os.environ["LOG_FORMAT"] = "json" if json_fmt else "text"
    if verbose and not quiet:
        setup_development_logging(json_format=json_fmt)
        log.setLevel("DEBUG")
        console.print(f"[blue][CONFIG] Verbose logging enabled | corr_id={corr_id} | format={log_format}[/blue]")
    else:
        setup_production_logging(json_format=json_fmt)
        if quiet:
            log.setLevel("ERROR")
        console.print(f"[blue][CONFIG] corr_id={corr_id} | format={log_format} | quiet={quiet} | dry_run={dry_run}[/blue]")
    
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            console.print(f"[red][ERROR] Configuration file not found: {config_file}[/red]")
            raise NotFoundError(f"Configuration file not found: {config_file}")
        if not QUIET:
            console.print(f"[blue][CONFIG] Using configuration: {config_file}[/blue]")

@app.command(name="process-chemistry")
def process_chemistry(
    input: str = typer.Option(..., "--input", "-i", help="Input CSV file with time-series concentration data"),
    species: str = typer.Option(..., "--species", "-s", help="Chemical species code (e.g., SO4, As, Ni)"),
    out: str = typer.Option("artifacts/fit.json", "--out", "-o", help="Output JSON file path for calibration results"),
):
    """
    Process chemistry data and fit sorption/decay parameters for a specific chemical species.
    
    Accepts CSV input in either wide format (time, SO4_mgL, As_mgL, ...) or 
    tidy format (time, species, concentration).
    """
    try:
        # Validate input file
        input_path = _validate_file_exists(input, "CSV input file")
        _log_event("chemistry_process_start", species=species, input=str(input_path), out=out)
        
        if not QUIET:
            console.print(f"[blue][CHEMISTRY] Processing chemistry data for species: {species}[/blue]")
        
        # Load and validate CSV
        df = pd.read_csv(input_path)
        if df.empty:
            console.print("[red][ERROR] Error: Input CSV file is empty[/red]")
            raise ValidationError("Input CSV file is empty")
            
        # Auto-detect format and convert if needed
        species_col = f"{species}_mgL"
        if species_col in df.columns:
            # Wide format - convert to tidy
            if len(df.columns) < 2:
                console.print("[red][ERROR] Error: Wide format CSV must have at least time and concentration columns[/red]")
                raise ValidationError("Wide format CSV requires time and concentration columns")
                
            time_col = df.columns[0]  # Assume first column is time
            tidy = pd.DataFrame({
                "time": df[time_col].to_numpy(),
                "species": [species] * len(df),
                "concentration": df[species_col].to_numpy(),
            })
            if not QUIET:
                console.print(f"[yellow][CONVERT] Converted wide format to tidy (time column: {time_col})[/yellow]")
        else:
            # Assume tidy format
            _validate_csv_format(df, ["time", "species", "concentration"], input)
            tidy = df
            
        # Fit parameters
        if not QUIET:
            console.print("[blue][PROCESS] Fitting sorption/decay parameters...[/blue]")
        res = fit_parameters(tidy, species)
        payload = res.to_dict()
        _log_event("chemistry_fit_completed", species=species, k=payload.get("k"), Kd=payload.get("Kd"))
        
        # Ensure output directory and write results
        if DRY_RUN:
            if not QUIET:
                console.print(f"[yellow][DRY-RUN] Would write calibration to: {out}[/yellow]")
        else:
            ensure_dir(os.path.dirname(out))
            with open(out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        _log_event("chemistry_process_end", out=out, dry_run=DRY_RUN)
            
        # Display results
        if not QUIET:
            console.print(Panel.fit(
            f"[green][SUCCESS] Chemistry processing completed successfully![/green]\n\n"
            f"Species: [bold]{species}[/bold]\n"
            f"Sorption rate (k): [bold]{payload['k']:.6f}[/bold]\n"  
            f"Distribution coeff (Kd): [bold]{payload['Kd']:.6f}[/bold]\n"
            f"Output: [bold]{out}[/bold]",
            title="[DATA] Chemistry Results"
            ))
        
        # Log provenance
        if not DRY_RUN:
            ProvenanceStore(settings.provenance_ledger).log(
            "process_chemistry", 
            {"species": species}, 
            [input], 
            [out]
            )
            LineageStore(settings.lineage_ledger).log_sample(
            sample_id="batch_fit", 
            source="lab_csv", 
            species=species, 
            method="fit_parameters", 
            calibration=payload, 
            file=input
            )
        
    except Exception as e:
        _handle_error("chemistry processing", e)

@app.command(name="monitor-batch")
def monitor_batch(
    input: str = typer.Option(..., "--input", "-i", help="Input CSV with monitoring data"),
    permit: str = typer.Option("", "--permit", "-p", help="Permit JSON file (uses default limits if not specified)"),
    out: str = typer.Option("artifacts/alerts.json", "--out", "-o", help="Output JSON file for compliance alerts"),
):
    """
    Monitor batch data against permit limits and generate compliance alerts.
    
    Analyzes concentration data for regulatory compliance, detecting both instantaneous 
    exceedances and rolling average trends.
    """
    try:
        # Validate input file
        input_path = _validate_file_exists(input, "monitoring CSV file")
        _log_event("monitor_batch_start", input=str(input_path), out=out, has_permit=bool(permit))
        
        if not QUIET:
            console.print(f"[blue][MONITOR] Monitoring batch data for compliance...[/blue]")
        
        # Load and validate data
        df = pd.read_csv(input_path)
        if df.empty:
            console.print("[red][ERROR] Error: Input CSV file is empty[/red]")
            raise ValidationError("Input CSV file is empty")
            
        # Load permit configuration
        if permit and not os.path.exists(permit):
            console.print(f"[red][ERROR] Error: Permit file not found: {permit}[/red]")
            raise NotFoundError(f"Permit file not found: {permit}")
            
        p = load_permit(permit if permit else None)
        if not QUIET:
            console.print(f"[blue][INFO] Using {'custom permit' if permit else 'default permit limits'}[/blue]")
        
        # Display permit limits
        limits = p.get("limits_mgL", p.get("limits", {}))
        if limits and not QUIET:
            table = Table(title="[DATA] Regulatory Limits (mg/L)")
            table.add_column("Species", style="bold")
            table.add_column("Limit", justify="right", style="cyan")
            for species, limit in limits.items():
                table.add_row(species, f"{float(limit):.3f}")
            console.print(table)
        
        # Run compliance evaluation
        if not QUIET:
            console.print("[blue][COMPLIANCE] Evaluating permit compliance...[/blue]")
        alerts = evaluate_permit(df, p)
        _log_event("monitor_batch_evaluated", alert_count=len(alerts))
        
        payload = {"count": len(alerts), "alerts": alerts}
        
        # Save results
        if DRY_RUN:
            if not QUIET:
                console.print(f"[yellow][DRY-RUN] Would write alerts to: {out}[/yellow]")
        else:
            ensure_dir(os.path.dirname(out))
            with open(out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        _log_event("monitor_batch_end", out=out, dry_run=DRY_RUN)
            
        # Display results summary
        if alerts and not QUIET:
            console.print(Panel.fit(
                f"[yellow][WARNING] Non-Compliant: {len(alerts)} alert(s) detected[/yellow]\n\n"
                f"Critical: [bold red]{len([a for a in alerts if a.get('level') == 'critical'])}[/bold red]\n"
                f"Warning: [bold yellow]{len([a for a in alerts if a.get('level') == 'warning'])}[/bold yellow]\n"  
                f"Watch: [bold blue]{len([a for a in alerts if a.get('level') == 'watch'])}[/bold blue]\n"
                f"Info: [bold]{len([a for a in alerts if a.get('level') == 'info'])}[/bold]\n\n"
                f"Report: [bold]{out}[/bold]",
                title="[ALERT] Compliance Status",
                border_style="yellow"
            ))
            
            # Show alert details
            alert_table = Table(title="Alert Details")
            alert_table.add_column("Species", style="bold")
            alert_table.add_column("Type")
            alert_table.add_column("Level") 
            alert_table.add_column("Value", justify="right")
            alert_table.add_column("Limit", justify="right")
            
            for alert in alerts[:10]:  # Show first 10 alerts
                level_style = {
                    "critical": "bold red", 
                    "warning": "bold yellow", 
                    "watch": "bold blue", 
                    "info": "dim"
                }.get(alert.get("level", "info"), "dim")
                
                alert_table.add_row(
                    alert.get("species", ""),
                    alert.get("type", ""),
                    f"[{level_style}]{alert.get('level', '').upper()}[/{level_style}]",
                    f"{alert.get('value', 0):.3f}",
                    f"{alert.get('limit', 0):.3f}"
                )
            console.print(alert_table)
            
            if len(alerts) > 10:
                console.print(f"[dim]... and {len(alerts) - 10} more alerts (see {out})[/dim]")
        elif not QUIET:
            console.print(Panel.fit(
                f"[green][SUCCESS] Compliant: No limit exceedances detected[/green]\n\n"
                f"All monitored species are within regulatory limits.\n"
                f"Report: [bold]{out}[/bold]",
                title="[SUCCESS] Compliance Status",
                border_style="green"
            ))
        
        # Log provenance
        if not DRY_RUN:
            ProvenanceStore(settings.provenance_ledger).log(
            "monitor_batch", 
            {"permit": bool(permit)}, 
            [input] + ([permit] if permit else []), 
            [out]
            )
        
    except Exception as e:
        _handle_error("batch monitoring", e)

@app.command(name="simulate-stream")
def simulate_stream_cmd(
    source: Path = typer.Option(..., "--source", "-s", help="Source CSV with time,species,concentration columns"),
    delay: float = typer.Option(0.1, "--delay", "-d", help="Delay between records in seconds"),
    publish_ws: Optional[str] = typer.Option(None, "--publish-ws", help="WebSocket URL to publish stream data"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="JSONL output file (prints to stdout if not specified)"),
):
    """
    Simulate real-time data streaming from historical CSV data.
    
    Reads CSV data and emits records with configurable delay, optionally publishing
    to WebSocket endpoint or saving to JSONL file.
    """
    try:
        # Validate input file
        if not source.exists():
            console.print(f"[red][ERROR] Error: Source CSV file not found: {source}[/red]")
            raise NotFoundError(f"Source CSV file not found: {source}")
            
        if not QUIET:
            console.print(f"[blue][STREAM] Starting stream simulation from: {source}[/blue]")
        _log_event("simulate_stream_start", source=str(source), out=str(out) if out else None, publish_ws=publish_ws)
        
        # Validate CSV format
        df = pd.read_csv(source)
        required_cols = ["time", "species", "concentration"] 
        _validate_csv_format(df, required_cols, str(source))
        
        if not QUIET:
            console.print(f"[blue]Delay: {delay}s per record | Records: {len(df)}[/blue]")
        
        # Generate streaming data
        rows = list(streaming_mod.simulate_stream(source, delay=delay))
        
        if publish_ws and not DRY_RUN:
            console.print(f"[blue][PUBLISH] Publishing to WebSocket: {publish_ws}[/blue]")
            import websockets
            
            async def _publish_stream() -> None:
                try:
                    async with websockets.connect(publish_ws) as ws:
                        for i, record in enumerate(rows):
                            try:
                                await ws.send_json(record)
                            except AttributeError:
                                # Fallback if send_json not available
                                await ws.send(json.dumps(record))
                            except Exception as e:
                                console.print(f"[yellow][WARNING] WebSocket send error: {e}[/yellow]")
                                continue
                                
                            if i % 10 == 0 and not QUIET:  # Progress every 10 records
                                console.print(f"[dim][SENT] Sent {i+1}/{len(rows)} records[/dim]")
                                
                    console.print(f"[green][SUCCESS] Published {len(rows)} records to WebSocket[/green]")
                    _log_event("simulate_stream_publish_done", count=len(rows))
                except Exception as e:
                    console.print(f"[red][ERROR] WebSocket connection failed: {e}[/red]")
                    _handle_error("websocket publish", e)
                    
            asyncio.run(_publish_stream())
            
        elif out and not DRY_RUN:
            # Write to JSONL file
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as f:
                for record in rows:
                    f.write(json.dumps(record) + "\n")
            _log_event("simulate_stream_file_done", count=len(rows), out=str(out))
                    
            if not QUIET:
                console.print(Panel.fit(
                f"[green][SUCCESS] Stream simulation completed![/green]\n\n"
                f"Records: [bold]{len(rows)}[/bold]\n"
                f"Output: [bold]{out}[/bold]\n"
                f"Format: JSONL (one JSON record per line)",
                title="[REPORT] File Output"
                ))
        elif out and DRY_RUN:
            if not QUIET:
                console.print(f"[yellow][DRY-RUN] Would write stream JSONL to: {out}[/yellow]")
        else:
            # Print to stdout
            if not QUIET:
                console.print("[blue][DISPLAY] Streaming to stdout (use --out to save or --publish-ws to stream)[/blue]")
            for record in rows:
                print(json.dumps(record))
            _log_event("simulate_stream_stdout_done", count=len(rows))
                
    except Exception as e:
        _handle_error("stream simulation", e)

@app.command(name="cert")
def cert(
    alerts: str = typer.Option(..., "--alerts", "-a", help="Alerts JSON file from monitor-batch command"),
    site: str = typer.Option(..., "--site", "-s", help="Site name for the compliance certificate"),
    out: str = typer.Option("reports/compliance.html", "--out", "-o", help="Output HTML certificate file"),
    period: Optional[str] = typer.Option(None, "--period", help="Reporting period description"),
):
    """
    Generate a professional HTML compliance certificate from alert data.
    
    Creates a formatted compliance report suitable for regulatory submission,
    showing alert details, compliance status, and recommended actions.
    """
    try:
        # Validate alerts file
        alerts_path = _validate_file_exists(alerts, "alerts JSON file")
        
        if not QUIET:
            console.print(f"[blue][INFO] Generating compliance certificate for site: {site}[/blue]")
        
        # Load and validate alerts data
        with open(alerts_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            
        # Handle different JSON formats (direct array vs wrapped object)
        if isinstance(payload, dict) and "alerts" in payload:
            alert_list = payload["alerts"]
            console.print(f"[blue][DATA] Found {len(alert_list)} alerts in wrapped format[/blue]")
        elif isinstance(payload, list):
            alert_list = payload
            console.print(f"[blue][DATA] Found {len(alert_list)} alerts in array format[/blue]")
        else:
            console.print("[red][ERROR] Error: Invalid alerts file format - expected array or object with 'alerts' key[/red]")
            raise ValidationError("Invalid alerts file format")
            
        # Generate certificate
        if not QUIET:
            console.print("[blue][GENERATE] Generating compliance certificate...[/blue]")
        cert_path = generate_certificate(
            alert_list, 
            site=site, 
            out_path=out,
            report_period=period
        )
        
        # Display results
        status = "NON-COMPLIANT" if alert_list else "COMPLIANT"
        status_color = "red" if alert_list else "green"
        status_icon = "[ERROR]" if alert_list else "[SUCCESS]"
        
        if not QUIET:
            console.print(Panel.fit(
            f"[{status_color}]{status_icon} {status}[/{status_color}]\n\n"
            f"Site: [bold]{site}[/bold]\n"
            f"Alerts: [bold]{len(alert_list)}[/bold]\n"
            f"Certificate: [bold]{cert_path}[/bold]\n"
            f"Period: [bold]{period or 'Current'}[/bold]",
            title="[INFO] Compliance Certificate Generated",
            border_style=status_color
            ))
        
        # Log provenance
        if not DRY_RUN:
            ProvenanceStore(settings.provenance_ledger).log(
            "certificate", 
            {"site": site, "period": period}, 
            [alerts], 
            [out]
            )
        
    except Exception as e:
        _handle_error("certificate generation", e)

@app.command(name="advise")
def advise(
    alerts: str = typer.Option(..., "--alerts", "-a", help="Alerts JSON file from monitor-batch command"),
    site: str = typer.Option("", "--site", "-s", help="Site name for remediation recommendations"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, or text"),
):
    """
    Generate remediation recommendations based on compliance alerts.
    
    Analyzes alert data and provides specific, actionable remediation steps
    for each detected exceedance based on chemical species and severity.
    """
    try:
        # Validate alerts file
        alerts_path = _validate_file_exists(alerts, "alerts JSON file")
        
        console.print(f"[blue][ADVICE] Generating remediation advice{'for site: ' + site if site else ''}[/blue]")
        
        # Load alerts data
        with open(alerts_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            
        # Handle different JSON formats
        if isinstance(payload, dict) and "alerts" in payload:
            alert_list = payload["alerts"]
        elif isinstance(payload, list):
            alert_list = payload
        else:
            console.print("[red][ERROR] Error: Invalid alerts file format[/red]")
            raise typer.Exit(2)
            
        if not alert_list:
            console.print(Panel.fit(
                "[green][SUCCESS] No alerts detected - no remediation required[/green]\n\n"
                "All monitored parameters are within acceptable limits.",
                title="[NOALERTS] No Action Needed"
            ))
            return
            
        console.print(f"[blue][INFO] Analyzing {len(alert_list)} alerts for remediation strategies[/blue]")
        
        # Generate recommendations
        actions = rules_mod.suggest_remediation(alert_list)
        
        if output_format == "json":
            # JSON output
            result = {
                "site": site or "Unknown", 
                "alert_count": len(alert_list),
                "actions": [a["suggestion"] for a in actions],
                "detailed_recommendations": actions
            }
            print(json.dumps(result, indent=2))
            
        elif output_format == "text":
            # Plain text output
            print(f"REMEDIATION RECOMMENDATIONS{' FOR ' + site.upper() if site else ''}")
            print("=" * 50)
            print(f"Alerts processed: {len(alert_list)}")
            print(f"Recommendations: {len(actions)}")
            print()
            for i, action in enumerate(actions, 1):
                print(f"{i}. {action['species']}: {action['suggestion']}")
                
        else:
            # Rich table output (default)
            if actions:
                table = Table(title=f"[ADVICE] Remediation Recommendations{' - ' + site if site else ''}")
                table.add_column("Species", style="bold cyan")
                table.add_column("Recommended Action", style="white")
                table.add_column("Priority", justify="center")
                
                # Group by species to avoid duplicates
                species_actions = {}
                for action in actions:
                    species = action["species"]
                    if species not in species_actions:
                        species_actions[species] = action["suggestion"]
                
                # Determine priority based on species criticality
                priority_map = {"As": "[HIGH] HIGH", "Ni": "[MEDIUM] MED", "SO4": "[MEDIUM] MED"}
                
                for species, suggestion in species_actions.items():
                    priority = priority_map.get(species, "[LOW] LOW")
                    table.add_row(species, suggestion, priority)
                    
                console.print(table)
                
                console.print(Panel.fit(
                    f"[yellow][INFO] Summary[/yellow]\n\n"
                    f"Total Alerts: [bold]{len(alert_list)}[/bold]\n"
                    f"Species Affected: [bold]{len(species_actions)}[/bold]\n"
                    f"Actions Required: [bold]{len(species_actions)}[/bold]\n\n"
                    f"[dim]Use --format=json for machine-readable output[/dim]",
                    title="Remediation Summary"
                ))
            
    except Exception as e:
        _handle_error("remediation advice generation", e)

@app.command(name="dashboard") 
def dashboard(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host address to bind the dashboard server"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number for the dashboard server"),
    serve: bool = typer.Option(True, "--serve/--no-serve", help="Start the dashboard server (use --no-serve to just validate config)"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """
    Start the web-based monitoring dashboard.
    
    Launches a FastAPI-based dashboard for real-time monitoring, WebSocket streaming,
    and interactive compliance visualization.
    """
    try:
        if not QUIET:
            console.print(f"[blue][WEB] Dashboard configuration[/blue]")
            console.print(f"  Host: [bold]{host}[/bold]")
            console.print(f"  Port: [bold]{port}[/bold]")
            console.print(f"  URL: [bold blue]http://{host}:{port}[/bold blue]")
        
        if not serve:
            if not QUIET:
                console.print(Panel.fit(
                "[green][SUCCESS] Configuration validated successfully[/green]\n\n"
                f"Dashboard would run at: http://{host}:{port}\n"
                "Use --serve to actually start the server.",
                title="[ADVICE] Configuration Check"
                ))
            return
            
        console.print(f"[blue][START] Starting dashboard server{'with auto-reload' if reload else ''}...[/blue]")
        
        try:
            import uvicorn
            from .logging import uvicorn_log_config
            
            # Build the app
            app_instance = build_dashboard_app()
            
            if not QUIET:
                console.print(Panel.fit(
                f"[green][WEB] Dashboard server starting...[/green]\n\n"
                f"[WEB] Web Interface: [bold blue]http://{host}:{port}[/bold blue]\n"
                f"[DATA] API Docs: [bold blue]http://{host}:{port}/docs[/bold blue]\n"
                f"[WEBSOCKET] WebSocket: [bold blue]ws://{host}:{port}/ws/effluent[/bold blue]\n\n"
                f"[dim]Press Ctrl+C to stop the server[/dim]",
                title="[WEB] OpenWorld Dashboard",
                border_style="blue"
                ))
            
            # Run the server
            json_fmt = (os.getenv("LOG_FORMAT", "text").lower() == "json")
            uvicorn.run(
                app_instance, 
                host=host, 
                port=port, 
                reload=reload,
                log_level="info" if not reload else "debug",
                access_log=True,
                log_config=uvicorn_log_config(json_fmt) or None,
            )
            
        except ImportError as e:
            console.print("[red][ERROR] Error: uvicorn not available. Install with: pip install uvicorn[/red]")
            _handle_error("dashboard dependency", e)
        except OSError as e:
            if "Address already in use" in str(e):
                console.print(f"[red][ERROR] Error: Port {port} is already in use. Try a different port with --port[/red]")
            else:
                console.print(f"[red][ERROR] Network error: {e}[/red]")
            _handle_error("dashboard network", e)
            
    except KeyboardInterrupt:
        console.print("\n[yellow][STOPPED] Dashboard server stopped by user[/yellow]")
    except Exception as e:
        _handle_error("dashboard startup", e)

@app.command(name="version")
def version():
    """Display version and system information."""
    from . import __version__
    
    console.print(Panel.fit(
        f"[bold cyan]OpenWorld Specialty Chemicals[/bold cyan]\n"
        f"Version: [bold]{__version__}[/bold]\n"
        f"Python: [bold]{sys.version.split()[0]}[/bold]\n"
        f"Platform: [bold]{sys.platform}[/bold]",
        title="[VERSION] Version Information"
    ))

if __name__ == "__main__":
    app()
