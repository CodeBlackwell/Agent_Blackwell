#!/usr/bin/env python3
"""Client for interacting with the Flagship TDD Orchestrator Server"""

import asyncio
import json
import sys
from typing import Optional
import aiohttp
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table


console = Console()


class FlagshipClient:
    """Client for the Flagship TDD Orchestrator Server"""
    
    def __init__(self, base_url: str = "http://localhost:8100"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def start_workflow(self, requirements: str, config_type: str = "default") -> str:
        """Start a new TDD workflow"""
        async with self.session.post(
            f"{self.base_url}/tdd/start",
            json={
                "requirements": requirements,
                "config_type": config_type
            }
        ) as response:
            data = await response.json()
            return data["session_id"]
    
    async def get_status(self, session_id: str) -> dict:
        """Get workflow status"""
        async with self.session.get(f"{self.base_url}/tdd/status/{session_id}") as response:
            return await response.json()
    
    async def stream_output(self, session_id: str):
        """Stream workflow output"""
        async with self.session.get(f"{self.base_url}/tdd/stream/{session_id}") as response:
            async for line in response.content:
                if line:
                    yield json.loads(line.decode())
    
    async def list_workflows(self) -> dict:
        """List all workflows"""
        async with self.session.get(f"{self.base_url}/workflows") as response:
            return await response.json()
    
    async def get_phases(self) -> dict:
        """Get TDD phase information"""
        async with self.session.get(f"{self.base_url}/phases") as response:
            return await response.json()


def format_phase(phase: str) -> str:
    """Format phase with emoji"""
    phase_emojis = {
        "RED": "🔴 RED",
        "YELLOW": "🟡 YELLOW",
        "GREEN": "🟢 GREEN"
    }
    return phase_emojis.get(phase, phase)


@click.group()
def cli():
    """Flagship TDD Orchestrator Client"""
    pass


@cli.command()
@click.argument('requirements')
@click.option('--config', '-c', default='default', help='Configuration type (quick/default/comprehensive)')
def start(requirements: str, config: str):
    """Start a new TDD workflow"""
    async def run():
        async with FlagshipClient() as client:
            try:
                # Start workflow
                console.print(f"[bold blue]Starting TDD workflow with config: {config}[/bold blue]")
                session_id = await client.start_workflow(requirements, config)
                console.print(f"[green]✓ Workflow started: {session_id}[/green]\n")
                
                # Stream output
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("[cyan]Running TDD workflow...", total=None)
                    
                    current_phase = "RED"
                    async for event in client.stream_output(session_id):
                        if event.get("type") == "status":
                            # Final status
                            progress.stop()
                            console.print()
                            
                            if event["status"] == "completed":
                                results = event.get("results", {})
                                
                                # Create results table
                                table = Table(title="TDD Workflow Results", show_header=True)
                                table.add_column("Metric", style="cyan")
                                table.add_column("Value", style="green")
                                
                                table.add_row("Status", "✅ Completed")
                                table.add_row("All Tests Passing", 
                                            "✅ Yes" if results.get("all_tests_passing") else "❌ No")
                                table.add_row("Iterations", str(results.get("iterations", 0)))
                                table.add_row("Duration", f"{results.get('duration', 0):.1f}s")
                                
                                test_summary = results.get("test_summary", {})
                                table.add_row("Total Tests", str(test_summary.get("total", 0)))
                                table.add_row("Passed Tests", str(test_summary.get("passed", 0)))
                                table.add_row("Failed Tests", str(test_summary.get("failed", 0)))
                                
                                console.print(table)
                                console.print(f"\n[green]✓ Workflow completed successfully![/green]")
                            else:
                                console.print(f"[red]✗ Workflow failed[/red]")
                            break
                        else:
                            # Output event
                            text = event.get("text", "")
                            
                            # Update phase if detected
                            if "Phase:" in text and "Entering" in text:
                                for phase in ["RED", "YELLOW", "GREEN"]:
                                    if phase in text:
                                        current_phase = phase
                                        progress.update(task, 
                                            description=f"[cyan]Running TDD workflow... Current phase: {format_phase(current_phase)}")
                            
                            # Print output (skip empty lines and separators)
                            if text.strip() and not text.strip().startswith("="):
                                # Syntax highlight code blocks
                                if text.strip().startswith("```python"):
                                    console.print()  # Add spacing
                                elif text.strip() == "```":
                                    console.print()  # Add spacing
                                else:
                                    console.print(text.rstrip())
                
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run())


@cli.command()
@click.argument('session_id')
def status(session_id: str):
    """Check workflow status"""
    async def run():
        async with FlagshipClient() as client:
            try:
                status = await client.get_status(session_id)
                
                panel = Panel(
                    f"Status: {status['status']}\n"
                    f"Phase: {format_phase(status.get('phase', 'N/A'))}\n"
                    f"Message: {status['message']}",
                    title=f"Workflow {session_id}",
                    border_style="blue"
                )
                console.print(panel)
                
                if status.get("results"):
                    console.print("\n[bold]Results:[/bold]")
                    console.print(json.dumps(status["results"], indent=2))
                    
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run())


@cli.command()
def list():
    """List all workflows"""
    async def run():
        async with FlagshipClient() as client:
            try:
                data = await client.list_workflows()
                
                if data["total"] == 0:
                    console.print("[yellow]No workflows found[/yellow]")
                    return
                
                table = Table(title=f"Workflows ({data['total']} total)")
                table.add_column("Session ID", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Phase")
                table.add_column("Config")
                table.add_column("Requirements", style="dim")
                
                for workflow in data["workflows"]:
                    table.add_row(
                        workflow["session_id"],
                        workflow["status"],
                        format_phase(workflow.get("phase", "N/A")),
                        workflow["config_type"],
                        workflow["requirements"]
                    )
                
                console.print(table)
                
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run())


@cli.command()
def phases():
    """Show TDD phase information"""
    async def run():
        async with FlagshipClient() as client:
            try:
                data = await client.get_phases()
                
                console.print("[bold]TDD Phases:[/bold]\n")
                
                for phase in data["phases"]:
                    console.print(f"{phase['emoji']} [bold]{phase['name']}[/bold]: {phase['description']}")
                
                console.print(f"\n[dim]Flow: {data['flow']}[/dim]")
                
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run())


@cli.command()
def interactive():
    """Interactive mode"""
    console.print("[bold blue]Flagship TDD Orchestrator - Interactive Mode[/bold blue]")
    console.print("Enter 'help' for commands or 'exit' to quit\n")
    
    async def run():
        async with FlagshipClient() as client:
            while True:
                try:
                    command = console.input("[bold]> [/bold]").strip()
                    
                    if command == "exit":
                        break
                    elif command == "help":
                        console.print("""
Commands:
  new <requirements>  - Start new workflow
  status <id>        - Check workflow status  
  list              - List all workflows
  phases            - Show TDD phases
  exit              - Exit interactive mode
                        """)
                    elif command.startswith("new "):
                        requirements = command[4:]
                        session_id = await client.start_workflow(requirements)
                        console.print(f"[green]Started workflow: {session_id}[/green]")
                    elif command.startswith("status "):
                        session_id = command[7:]
                        status = await client.get_status(session_id)
                        console.print(f"Status: {status['status']}, Phase: {status.get('phase', 'N/A')}")
                    elif command == "list":
                        data = await client.list_workflows()
                        console.print(f"Total workflows: {data['total']}")
                    elif command == "phases":
                        data = await client.get_phases()
                        console.print(data['flow'])
                    else:
                        console.print("[red]Unknown command. Type 'help' for commands.[/red]")
                        
                except Exception as e:
                    console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run())


if __name__ == "__main__":
    cli()