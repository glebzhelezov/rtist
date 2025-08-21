#!/usr/bin/env python
"""
Modern Textual UI for mtrip - A fun, colorful interface for phylogenetic tree analysis.
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import timedelta
from time import time

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, Input, Select, Checkbox, 
    Log, ProgressBar, Label, Rule, Tree, DirectoryTree
)
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from textual import on
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Import mtrip functionality
try:
    from mtrip import __version__
    from mtrip.median_tree_reconstruction import median_triplet_trees
except ImportError:
    __version__ = "dev"
    # For development when package isn't installed
    median_triplet_trees = None


class WelcomeScreen(Screen):
    """Welcome screen with colorful introduction."""
    
    BINDINGS = [
        Binding("enter", "start", "Start Analysis"),
        Binding("q", "quit", "Quit", priority=True),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(
                "[bold magenta]🧬 RTIST - Phylogenetic Tree Analysis[/bold magenta]\n\n"
                "[cyan]Welcome to the modern interface for median triplet tree analysis![/cyan]\n\n"
                "[yellow]Features:[/yellow]\n"
                "• 🎨 [green]Colorful and intuitive interface[/green]\n"
                "• 📁 [blue]Easy file selection[/blue]\n"
                "• ⚙️ [yellow]Simple parameter configuration[/yellow]\n"
                "• 📊 [magenta]Real-time progress tracking[/magenta]\n"
                "• 🎯 [red]Beautiful results visualization[/red]\n\n"
                f"[dim]Version {__version__}[/dim]\n\n"
                "[bold green]Press ENTER to begin or Q to quit[/bold green]",
                id="welcome-text"
            ),
            id="welcome-container"
        )
        yield Footer()
    
    def action_start(self) -> None:
        """Start the analysis workflow."""
        self.app.push_screen("main")
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class FileSelectScreen(ModalScreen[str]):
    """File selection modal with directory browser."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, title: str = "Select Input File", file_types: List[str] = None):
        super().__init__()
        self.title = title
        self.file_types = file_types or [".nwk", ".txt"]
    
    def compose(self) -> ComposeResult:
        with Container(id="file-select-dialog"):
            yield Static(f"[bold cyan]{self.title}[/bold cyan]", id="file-select-title")
            yield DirectoryTree("./", id="file-tree")
            with Horizontal():
                yield Button("Cancel", variant="error", id="cancel-btn")
                yield Button("Select", variant="success", id="select-btn")
    
    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection."""
        file_path = str(event.path)
        if any(file_path.endswith(ext) for ext in self.file_types):
            self.dismiss(file_path)
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self) -> None:
        self.dismiss(None)
    
    @on(Button.Pressed, "#select-btn")
    def select_pressed(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        if tree.cursor_node and tree.cursor_node.data and tree.cursor_node.data.is_file():
            self.dismiss(str(tree.cursor_node.data.path))
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class ParametersScreen(Screen):
    """Parameter configuration screen."""
    
    BINDINGS = [
        Binding("ctrl+b", "back", "Back"),
        Binding("enter", "run", "Run Analysis"),
    ]
    
    def __init__(self, input_file: str):
        super().__init__()
        self.input_file = input_file
    
    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():
            yield Static(
                f"[bold green]📋 Analysis Parameters[/bold green]\n"
                f"[cyan]Input file:[/cyan] {os.path.basename(self.input_file)}",
                id="params-header"
            )
            yield Rule()
            
            # Thread selection
            yield Label("[yellow]Number of threads:[/yellow]")
            yield Select(
                [("Auto (recommended)", -1)] + [(f"{i} threads", i) for i in range(1, 17)],
                value=-1,
                id="threads-select"
            )
            
            # Output options
            yield Label("[yellow]Output options:[/yellow]")
            with Horizontal():
                yield Checkbox("Save to file", value=True, id="save-checkbox")
                yield Checkbox("Print to screen", value=False, id="print-checkbox")
            
            # Validation options
            yield Label("[yellow]Validation:[/yellow]")
            yield Checkbox("Validate Newick strings", value=True, id="validate-checkbox")
            
            # Binary output
            yield Label("[yellow]Advanced options:[/yellow]")
            yield Checkbox("Save weights to binary file", value=False, id="binary-checkbox")
            
            yield Rule()
            
            # Action buttons
            with Horizontal():
                yield Button("🔙 Back", variant="error", id="back-btn")
                yield Button("🚀 Run Analysis", variant="success", id="run-btn")
        
        yield Footer()
    
    @on(Button.Pressed, "#back-btn")
    def back_pressed(self) -> None:
        self.action_back()
    
    @on(Button.Pressed, "#run-btn")
    def run_pressed(self) -> None:
        self.action_run()
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()
    
    def action_run(self) -> None:
        """Start the analysis."""
        # Collect parameters
        threads = self.query_one("#threads-select", Select).value
        save_file = self.query_one("#save-checkbox", Checkbox).value
        print_screen = self.query_one("#print-checkbox", Checkbox).value
        validate = self.query_one("#validate-checkbox", Checkbox).value
        save_binary = self.query_one("#binary-checkbox", Checkbox).value
        
        params = {
            "input_file": self.input_file,
            "threads": threads,
            "save_file": save_file,
            "print_screen": print_screen,
            "validate": validate,
            "save_binary": save_binary
        }
        
        self.app.push_screen(AnalysisScreen(params))


class AnalysisScreen(Screen):
    """Analysis execution screen with progress tracking."""
    
    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel Analysis"),
    ]
    
    progress = reactive(0.0)
    status = reactive("Initializing...")
    
    def __init__(self, params: dict):
        super().__init__()
        self.params = params
        self.results = None
        self.start_time = None
        
    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static(
                "[bold magenta]🔬 Running Analysis[/bold magenta]",
                id="analysis-header"
            )
            yield Rule()
            
            yield Label(self.status, id="status-label")
            yield ProgressBar(total=100, show_eta=True, id="progress-bar")
            
            yield Rule()
            yield Log(id="analysis-log", auto_scroll=True)
            
            yield Rule()
            with Horizontal():
                yield Button("❌ Cancel", variant="error", id="cancel-btn", disabled=False)
                yield Button("📊 View Results", variant="success", id="results-btn", disabled=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Start analysis when screen is mounted."""
        self.start_analysis()
    
    def watch_progress(self, progress: float) -> None:
        """Update progress bar when progress changes."""
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(progress=progress)
    
    def watch_status(self, status: str) -> None:
        """Update status label when status changes."""
        status_label = self.query_one("#status-label", Label)
        status_label.update(f"[cyan]{status}[/cyan]")
    
    def log_message(self, message: str, style: str = "white") -> None:
        """Add a message to the analysis log."""
        log = self.query_one("#analysis-log", Log)
        log.write_line(f"[{style}]{message}[/{style}]")
    
    async def start_analysis(self) -> None:
        """Run the median triplet tree analysis."""
        if median_triplet_trees is None:
            self.log_message("❌ Analysis function not available (package not installed)", "red")
            self.status = "Error: Package not installed"
            return
            
        try:
            self.start_time = time()
            self.log_message("🚀 Starting median triplet tree analysis...", "green")
            self.status = "Reading input file..."
            self.progress = 10
            
            # Read input file
            input_file = self.params["input_file"]
            self.log_message(f"📖 Reading Newick strings from: {os.path.basename(input_file)}", "blue")
            
            with open(input_file, "r") as f:
                nwks = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
            # Remove semicolons if present (as required by the function)
            nwks = [nwk.rstrip(";") for nwk in nwks]
            
            self.log_message(f"✅ Found {len(nwks)} Newick strings", "green")
            self.progress = 20
            
            if self.params["validate"]:
                self.status = "Validating Newick strings..."
                self.log_message("🔍 Validating Newick strings...", "yellow")
                # Basic validation
                for i, nwk in enumerate(nwks):
                    if nwk.count("(") != nwk.count(")"):
                        raise ValueError(f"Mismatched parentheses in line {i+1}")
                self.log_message("✅ All Newick strings validated", "green")
                self.progress = 30
            
            self.status = "Running median triplet tree analysis..."
            self.log_message("🧬 Computing median triplet trees...", "magenta")
            self.progress = 40
            
            # Run the analysis
            threads = self.params["threads"] if self.params["threads"] != -1 else None
            
            # Simulate progress updates during analysis
            self.set_timer(1.0, self.update_analysis_progress)
            
            results = median_triplet_trees(nwks, n_threads=threads)
            self.results = results
            
            self.progress = 100
            self.status = "Analysis complete!"
            
            elapsed = time() - self.start_time
            self.log_message(f"🎉 Analysis completed in {elapsed:.2f} seconds!", "green")
            self.log_message(f"📊 Found {len(results)} median triplet trees", "cyan")
            
            # Enable results button
            results_btn = self.query_one("#results-btn", Button)
            results_btn.disabled = False
            
            # Save results if requested
            if self.params["save_file"]:
                await self.save_results()
                
        except FileNotFoundError:
            self.log_message(f"❌ Input file not found: {input_file}", "red")
            self.status = "Error: File not found"
        except Exception as e:
            self.log_message(f"❌ Analysis failed: {str(e)}", "red")
            self.status = f"Error: {str(e)}"
    
    def update_analysis_progress(self) -> None:
        """Update progress during analysis."""
        if self.progress < 90:
            self.progress = min(90, self.progress + 10)
            self.set_timer(2.0, self.update_analysis_progress)
    
    async def save_results(self) -> None:
        """Save analysis results to file."""
        try:
            input_file = self.params["input_file"]
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"out_{base_name}.nwk"
            
            with open(output_file, "w") as f:
                for result in self.results:
                    f.write(f"{result}\n")
            
            self.log_message(f"💾 Results saved to: {output_file}", "green")
            
        except Exception as e:
            self.log_message(f"❌ Failed to save results: {str(e)}", "red")
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self) -> None:
        self.action_cancel()
    
    @on(Button.Pressed, "#results-btn")  
    def results_pressed(self) -> None:
        if self.results:
            self.app.push_screen(ResultsScreen(self.results))
    
    def action_cancel(self) -> None:
        """Cancel analysis and return to main screen."""
        self.app.pop_screen()


class ResultsScreen(Screen):
    """Results display screen."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+s", "save", "Save Results"),
    ]
    
    def __init__(self, results: List[str]):
        super().__init__()
        self.results = results
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static(
                f"[bold green]🎯 Analysis Results[/bold green]\n"
                f"[cyan]Found {len(self.results)} median triplet trees[/cyan]",
                id="results-header"
            )
            yield Rule()
            
            with ScrollableContainer():
                for i, tree in enumerate(self.results, 1):
                    yield Static(
                        f"[yellow]Tree {i}:[/yellow] [white]{tree}[/white]",
                        classes="result-tree"
                    )
            
            yield Rule()
            with Horizontal():
                yield Button("🔙 Back", variant="primary", id="back-btn")
                yield Button("💾 Save Results", variant="success", id="save-btn")
        
        yield Footer()
    
    @on(Button.Pressed, "#back-btn")
    def back_pressed(self) -> None:
        self.action_back()
    
    @on(Button.Pressed, "#save-btn")
    def save_pressed(self) -> None:
        self.action_save()
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_save(self) -> None:
        """Save results to file."""
        # TODO: Implement file save dialog
        pass


class MainScreen(Screen):
    """Main application screen."""
    
    BINDINGS = [
        Binding("ctrl+o", "open_file", "Open File"),
        Binding("q", "quit", "Quit"),
        Binding("ctrl+h", "help", "Help"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static(
                "[bold cyan]🧬 RTIST - Phylogenetic Analysis[/bold cyan]\n"
                "[dim]Select a Newick file to begin analysis[/dim]",
                id="main-header"
            )
            yield Rule()
            
            with Vertical():
                yield Button(
                    "📁 [bold]Select Input File[/bold]",
                    variant="primary",
                    id="select-file-btn",
                    classes="large-button"
                )
                yield Static("")
                yield Button(
                    "📖 [bold]Load Example[/bold]", 
                    variant="default",
                    id="load-example-btn",
                    classes="large-button"
                )
                yield Static("")
                yield Button(
                    "❓ [bold]Help & Documentation[/bold]",
                    variant="warning", 
                    id="help-btn",
                    classes="large-button"
                )
                yield Static("")
                yield Button(
                    "❌ [bold]Exit[/bold]",
                    variant="error",
                    id="exit-btn", 
                    classes="large-button"
                )
        
        yield Footer()
    
    @on(Button.Pressed, "#select-file-btn")
    def select_file_pressed(self) -> None:
        self.action_open_file()
    
    @on(Button.Pressed, "#load-example-btn")
    def load_example_pressed(self) -> None:
        # Look for example files
        example_files = []
        for example_dir in ["./examples", "../examples", "../../examples"]:
            if os.path.exists(example_dir):
                for file in os.listdir(example_dir):
                    if file.endswith(('.nwk', '.txt')):
                        example_files.append(os.path.join(example_dir, file))
        
        if example_files:
            # Use the first example file found
            self.app.push_screen(ParametersScreen(example_files[0]))
        else:
            # No examples found, ask user to select file
            self.action_open_file()
    
    @on(Button.Pressed, "#help-btn")
    def help_pressed(self) -> None:
        self.action_help()
    
    @on(Button.Pressed, "#exit-btn")
    def exit_pressed(self) -> None:
        self.action_quit()
    
    def action_open_file(self) -> None:
        """Open file selection dialog."""
        def file_selected(file_path: Optional[str]) -> None:
            if file_path:
                self.app.push_screen(ParametersScreen(file_path))
        
        self.app.push_screen(FileSelectScreen(), file_selected)
    
    def action_help(self) -> None:
        """Show help information."""
        # TODO: Implement help screen
        pass
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class RTistApp(App):
    """Main RTIST Textual application."""
    
    CSS_PATH = None
    CSS = """
    #welcome-container {
        align: center middle;
        text-align: center;
        padding: 2;
    }
    
    #welcome-text {
        width: 80%;
        height: auto;
        margin: 1;
        border: solid $primary;
        padding: 2;
    }
    
    .large-button {
        width: 60%;
        height: 3;
        margin: 1;
        text-align: center;
    }
    
    #main-header {
        text-align: center;
        padding: 1;
    }
    
    #file-select-dialog {
        align: center middle;
        width: 80%;
        height: 80%;
        border: solid $primary;
        background: $background;
        padding: 1;
    }
    
    #file-select-title {
        text-align: center;
        margin-bottom: 1;
    }
    
    #params-header {
        text-align: center;
        padding: 1;
    }
    
    #analysis-header {
        text-align: center;
        padding: 1;
    }
    
    #results-header {
        text-align: center;
        padding: 1;
    }
    
    .result-tree {
        margin: 1 0;
        padding: 1;
        border-left: solid $primary;
    }
    
    #analysis-log {
        height: 20;
        border: solid $primary;
        margin: 1 0;
    }
    
    Label {
        margin: 1 0;
    }
    
    Select {
        margin: 0 0 1 0;
    }
    
    Checkbox {
        margin: 0 1;
    }
    """
    
    TITLE = "RTIST - Phylogenetic Tree Analysis"
    SUB_TITLE = "Modern UI for median triplet tree analysis"
    
    SCREENS = {
        "welcome": WelcomeScreen,
        "main": MainScreen,
    }
    
    def on_mount(self) -> None:
        """Initialize the application."""
        self.push_screen("welcome")


def main():
    """Main entry point for the RTIST UI."""
    app = RTistApp()
    app.run()


if __name__ == "__main__":
    main()