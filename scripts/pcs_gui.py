#!/usr/bin/env python3
"""
PCS AI Research Suite - Graphical User Interface
Modern and user-friendly interface for AI-enhanced research automation.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import queue
import os
from pathlib import Path
import json
from datetime import datetime
import webbrowser


class PCSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCS AI Research Suite v4.3")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Paths
        self.base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        self.scripts_path = self.base_path / "scripts"
        self.ai_suite_path = self.base_path / "pcs_ai_suite.sh"

        # Queue for thread communication
        self.output_queue = queue.Queue()

        # Setup GUI
        self.setup_styles()
        self.create_header()
        self.create_main_frame()
        self.create_status_bar()

        # Start checking for output updates
        self.check_output_queue()

        # Load initial status
        self.update_system_status()

    def setup_styles(self):
        """Configure modern styling."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure colors
        self.colors = {
            "primary": "#2E86AB",
            "secondary": "#A23B72",
            "success": "#2ECC71",
            "warning": "#F39C12",
            "danger": "#E74C3C",
            "light": "#ECF0F1",
            "dark": "#2C3E50",
        }

        # Configure styles
        style.configure(
            "Header.TLabel",
            font=("Arial", 16, "bold"),
            background=self.colors["primary"],
            foreground="white",
        )

        style.configure("Action.TButton", font=("Arial", 10, "bold"), padding=(10, 5))

        style.configure("Status.TLabel", font=("Arial", 9), padding=(5, 2))

    def create_header(self):
        """Create the header section."""
        header_frame = tk.Frame(self.root, bg=self.colors["primary"], height=80)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        # Title
        title_label = tk.Label(
            header_frame,
            text="🧠 PCS AI Research Suite v4.3",
            font=("Arial", 20, "bold"),
            bg=self.colors["primary"],
            fg="white",
        )
        title_label.pack(pady=15)

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Computational-Symbolic Psychiatry • AI-Enhanced Research Automation",
            font=("Arial", 12),
            bg=self.colors["primary"],
            fg="white",
        )
        subtitle_label.pack()

    def create_main_frame(self):
        """Create the main content area."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.create_research_tab()
        self.create_analysis_tab()
        self.create_system_tab()
        self.create_results_tab()

    def create_research_tab(self):
        """Create the main research automation tab."""
        research_frame = ttk.Frame(self.notebook)
        self.notebook.add(research_frame, text="🔬 AI Research")

        # Left panel - Controls
        left_panel = tk.Frame(research_frame, bg="white", relief="raised", bd=1)
        left_panel.pack(side="left", fill="y", padx=(0, 5), pady=0)

        # Research controls
        controls_label = tk.Label(
            left_panel,
            text="🧠 AI Research Controls",
            font=("Arial", 14, "bold"),
            bg="white",
        )
        controls_label.pack(pady=10)

        # Search section
        search_frame = tk.LabelFrame(
            left_panel,
            text="🔍 Intelligent Search",
            font=("Arial", 11, "bold"),
            bg="white",
        )
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="Research Topic:", bg="white").pack(
            anchor="w", padx=5
        )
        self.search_entry = tk.Entry(search_frame, width=30, font=("Arial", 10))
        self.search_entry.pack(fill="x", padx=5, pady=2)

        ttk.Button(
            search_frame,
            text="🔍 AI Search & Analysis",
            command=self.run_ai_search,
            style="Action.TButton",
        ).pack(fill="x", padx=5, pady=5)

        # Strategy section
        strategy_frame = tk.LabelFrame(
            left_panel,
            text="📊 Research Strategy",
            font=("Arial", 11, "bold"),
            bg="white",
        )
        strategy_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(strategy_frame, text="Research Goal:", bg="white").pack(
            anchor="w", padx=5
        )
        self.strategy_entry = tk.Entry(strategy_frame, width=30, font=("Arial", 10))
        self.strategy_entry.pack(fill="x", padx=5, pady=2)

        ttk.Button(
            strategy_frame,
            text="🎯 Generate AI Strategy",
            command=self.generate_strategy,
            style="Action.TButton",
        ).pack(fill="x", padx=5, pady=5)

        # Pipeline section
        pipeline_frame = tk.LabelFrame(
            left_panel,
            text="🚀 Complete Pipeline",
            font=("Arial", 11, "bold"),
            bg="white",
        )
        pipeline_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(pipeline_frame, text="Research Objective:", bg="white").pack(
            anchor="w", padx=5
        )
        self.pipeline_entry = tk.Entry(pipeline_frame, width=30, font=("Arial", 10))
        self.pipeline_entry.pack(fill="x", padx=5, pady=2)

        ttk.Button(
            pipeline_frame,
            text="🚀 Run Complete AI Pipeline",
            command=self.run_complete_pipeline,
            style="Action.TButton",
        ).pack(fill="x", padx=5, pady=5)

        # Quick actions
        quick_frame = tk.LabelFrame(
            left_panel, text="⚡ Quick Actions", font=("Arial", 11, "bold"), bg="white"
        )
        quick_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            quick_frame,
            text="🔍 Analyze Research Gaps",
            command=self.analyze_gaps,
            style="Action.TButton",
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            quick_frame,
            text="📝 Create Manuscript Outline",
            command=self.create_outline_dialog,
            style="Action.TButton",
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            quick_frame,
            text="📊 Generate Dashboard",
            command=self.generate_dashboard,
            style="Action.TButton",
        ).pack(fill="x", padx=5, pady=2)

        # Right panel - Output
        right_panel = tk.Frame(research_frame, bg="white", relief="raised", bd=1)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        output_label = tk.Label(
            right_panel,
            text="📋 Research Output & Logs",
            font=("Arial", 14, "bold"),
            bg="white",
        )
        output_label.pack(pady=10)

        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Output controls
        output_controls = tk.Frame(right_panel, bg="white")
        output_controls.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            output_controls, text="🗑️ Clear Output", command=self.clear_output
        ).pack(side="left", padx=5)

        ttk.Button(
            output_controls, text="💾 Save Output", command=self.save_output
        ).pack(side="left", padx=5)

    def create_analysis_tab(self):
        """Create the analysis and results tab."""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="📊 Analysis")

        # Memory status
        memory_frame = tk.LabelFrame(
            analysis_frame, text="🧠 MCP Research Memory", font=("Arial", 12, "bold")
        )
        memory_frame.pack(fill="x", padx=10, pady=5)

        memory_controls = tk.Frame(memory_frame)
        memory_controls.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            memory_controls, text="📋 View All Memories", command=self.view_memories
        ).pack(side="left", padx=5)

        ttk.Button(
            memory_controls,
            text="🔍 Search Memories",
            command=self.search_memories_dialog,
        ).pack(side="left", padx=5)

        ttk.Button(
            memory_controls,
            text="📊 Research Context",
            command=self.view_research_context,
        ).pack(side="left", padx=5)

        # Memory display
        self.memory_text = scrolledtext.ScrolledText(
            memory_frame, height=15, wrap=tk.WORD, font=("Arial", 10)
        )
        self.memory_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Analysis results
        results_frame = tk.LabelFrame(
            analysis_frame, text="📈 Analysis Results", font=("Arial", 12, "bold")
        )
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.results_text = scrolledtext.ScrolledText(
            results_frame, wrap=tk.WORD, font=("Arial", 10)
        )
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_system_tab(self):
        """Create the system status and configuration tab."""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="⚙️ System")

        # System status
        status_frame = tk.LabelFrame(
            system_frame, text="🔧 System Status", font=("Arial", 12, "bold")
        )
        status_frame.pack(fill="x", padx=10, pady=5)

        # Status indicators
        self.status_indicators = {}
        indicators = [
            ("Python", "python"),
            ("Node.js", "nodejs"),
            ("MCP Server", "mcp"),
            ("Gemini AI", "gemini"),
            ("AI Assistant", "ai_assistant"),
            ("Research Hub", "research_hub"),
        ]

        indicators_frame = tk.Frame(status_frame)
        indicators_frame.pack(fill="x", padx=10, pady=10)

        for i, (name, key) in enumerate(indicators):
            row = i // 3
            col = i % 3

            indicator_frame = tk.Frame(indicators_frame)
            indicator_frame.grid(row=row, column=col, padx=10, pady=5, sticky="w")

            status_label = tk.Label(indicator_frame, text="⚪", font=("Arial", 16))
            status_label.pack(side="left")

            name_label = tk.Label(indicator_frame, text=name, font=("Arial", 10))
            name_label.pack(side="left", padx=5)

            self.status_indicators[key] = status_label

        # System controls
        controls_frame = tk.Frame(status_frame)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            controls_frame, text="🔄 Refresh Status", command=self.update_system_status
        ).pack(side="left", padx=5)

        ttk.Button(
            controls_frame,
            text="🧪 Test AI Components",
            command=self.test_ai_components,
        ).pack(side="left", padx=5)

        ttk.Button(
            controls_frame, text="📂 Open Workspace", command=self.open_workspace
        ).pack(side="left", padx=5)

        # Configuration
        config_frame = tk.LabelFrame(
            system_frame, text="⚙️ Configuration", font=("Arial", 12, "bold")
        )
        config_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Gemini API configuration
        gemini_frame = tk.Frame(config_frame)
        gemini_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(
            gemini_frame, text="Gemini API Status:", font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.gemini_status_label = tk.Label(
            gemini_frame, text="Checking...", font=("Arial", 10)
        )
        self.gemini_status_label.pack(anchor="w", padx=20)

        ttk.Button(
            gemini_frame,
            text="🔑 Configure Gemini API",
            command=self.configure_gemini_api,
        ).pack(anchor="w", pady=5)

        # System info
        info_frame = tk.Frame(config_frame)
        info_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.system_info_text = scrolledtext.ScrolledText(
            info_frame, height=10, wrap=tk.WORD, font=("Consolas", 9)
        )
        self.system_info_text.pack(fill="both", expand=True)

    def create_results_tab(self):
        """Create the results and export tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📁 Results")

        # Export options
        export_frame = tk.LabelFrame(
            results_frame, text="📤 Export Options", font=("Arial", 12, "bold")
        )
        export_frame.pack(fill="x", padx=10, pady=5)

        export_controls = tk.Frame(export_frame)
        export_controls.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            export_controls,
            text="📊 Export Research Dashboard",
            command=self.export_dashboard,
        ).pack(side="left", padx=5)

        ttk.Button(
            export_controls,
            text="📝 Export Research Summary",
            command=self.export_summary,
        ).pack(side="left", padx=5)

        ttk.Button(
            export_controls, text="💾 Export MCP Memories", command=self.export_memories
        ).pack(side="left", padx=5)

        # Recent results
        recent_frame = tk.LabelFrame(
            results_frame, text="📋 Recent Results", font=("Arial", 12, "bold")
        )
        recent_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Results tree
        self.results_tree = ttk.Treeview(
            recent_frame, columns=("Type", "Timestamp", "Status"), show="tree headings"
        )
        self.results_tree.heading("#0", text="Research Item")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Timestamp", text="Timestamp")
        self.results_tree.heading("Status", text="Status")

        self.results_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Results details
        details_frame = tk.Frame(recent_frame)
        details_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            details_frame, text="👁️ View Details", command=self.view_result_details
        ).pack(side="left", padx=5)

        ttk.Button(
            details_frame, text="🔄 Refresh Results", command=self.refresh_results
        ).pack(side="left", padx=5)

    def create_status_bar(self):
        """Create the status bar."""
        self.status_frame = tk.Frame(self.root, relief="sunken", bd=1)
        self.status_frame.pack(side="bottom", fill="x")

        self.status_label = tk.Label(
            self.status_frame, text="Ready", font=("Arial", 9), anchor="w"
        )
        self.status_label.pack(side="left", padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.status_frame, mode="indeterminate", length=200
        )
        self.progress.pack(side="right", padx=5, pady=2)

    def log_output(self, message, level="INFO"):
        """Add message to output area."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding
        colors = {
            "INFO": "#00ff00",
            "WARNING": "#ffaa00",
            "ERROR": "#ff0000",
            "SUCCESS": "#00ff00",
        }

        color = colors.get(level, "#ffffff")

        formatted_message = f"[{timestamp}] {level}: {message}\n"

        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def run_command_async(self, command, callback=None):
        """Run command in background thread."""

        def run_command():
            try:
                self.log_output(f"Running: {' '.join(command)}")
                self.progress.start()

                result = subprocess.run(
                    command,
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                self.progress.stop()

                if result.returncode == 0:
                    self.log_output("Command completed successfully", "SUCCESS")
                    self.log_output(result.stdout)
                else:
                    self.log_output(
                        f"Command failed with code {result.returncode}", "ERROR"
                    )
                    self.log_output(result.stderr, "ERROR")

                if callback:
                    callback(result)

            except subprocess.TimeoutExpired:
                self.progress.stop()
                self.log_output("Command timed out", "ERROR")
            except Exception as e:
                self.progress.stop()
                self.log_output(f"Error running command: {e}", "ERROR")

        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()

    def run_ai_search(self):
        """Run AI-enhanced search."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a research topic")
            return

        self.status_label.config(text="Running AI search...")
        command = [str(self.ai_suite_path), "ai-search", query]
        self.run_command_async(command)

    def generate_strategy(self):
        """Generate research strategy."""
        goal = self.strategy_entry.get().strip()
        if not goal:
            messagebox.showwarning("Warning", "Please enter a research goal")
            return

        self.status_label.config(text="Generating AI strategy...")
        command = [str(self.ai_suite_path), "ai-strategy", goal]
        self.run_command_async(command)

    def run_complete_pipeline(self):
        """Run complete AI pipeline."""
        objective = self.pipeline_entry.get().strip()
        if not objective:
            messagebox.showwarning("Warning", "Please enter a research objective")
            return

        if messagebox.askyesno(
            "Confirm",
            f"Run complete AI pipeline for: '{objective}'?\n\n"
            "This will take 10-15 minutes and include:\n"
            "• Literature search & AI analysis\n"
            "• Strategy generation\n"
            "• Gap analysis\n"
            "• Manuscript outline",
        ):
            self.status_label.config(text="Running complete AI pipeline...")
            command = [str(self.ai_suite_path), "ai-pipeline", objective]
            self.run_command_async(command)

    def analyze_gaps(self):
        """Analyze research gaps."""
        self.status_label.config(text="Analyzing research gaps...")
        command = [str(self.ai_suite_path), "ai-gaps"]
        self.run_command_async(command)

    def create_outline_dialog(self):
        """Show dialog for manuscript outline creation."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Manuscript Outline")
        dialog.geometry("400x200")
        dialog.configure(bg="white")

        tk.Label(
            dialog, text="Manuscript Focus:", font=("Arial", 12, "bold"), bg="white"
        ).pack(pady=10)

        focus_entry = tk.Entry(dialog, width=50, font=("Arial", 10))
        focus_entry.pack(pady=5)
        focus_entry.focus()

        tk.Label(
            dialog,
            text="Target Journal: Nature Human Behaviour",
            font=("Arial", 10),
            bg="white",
            fg="gray",
        ).pack(pady=5)

        def create_outline():
            focus = focus_entry.get().strip()
            if focus:
                dialog.destroy()
                self.status_label.config(text="Creating manuscript outline...")
                command = [str(self.ai_suite_path), "ai-outline", focus]
                self.run_command_async(command)
            else:
                messagebox.showwarning("Warning", "Please enter a manuscript focus")

        ttk.Button(dialog, text="📝 Create Outline", command=create_outline).pack(
            pady=20
        )

    def generate_dashboard(self):
        """Generate research dashboard."""
        self.status_label.config(text="Generating research dashboard...")
        command = ["python3", str(self.scripts_path / "research_dashboard.py")]

        def on_complete(result):
            if result.returncode == 0:
                dashboard_path = self.base_path / "research_dashboard.html"
                if dashboard_path.exists():
                    if messagebox.askyesno(
                        "Dashboard Created",
                        "Research dashboard created successfully!\n\n"
                        "Would you like to open it in your browser?",
                    ):
                        webbrowser.open(f"file://{dashboard_path}")

        self.run_command_async(command, on_complete)

    def update_system_status(self):
        """Update system status indicators."""

        def check_status():
            # Check Python
            try:
                result = subprocess.run(
                    ["python3", "--version"], capture_output=True, text=True
                )
                self.status_indicators["python"].config(
                    text="🟢" if result.returncode == 0 else "🔴"
                )
            except:
                self.status_indicators["python"].config(text="🔴")

            # Check Node.js
            try:
                result = subprocess.run(
                    ["node", "--version"], capture_output=True, text=True
                )
                self.status_indicators["nodejs"].config(
                    text="🟢" if result.returncode == 0 else "🔴"
                )
            except:
                self.status_indicators["nodejs"].config(text="🔴")

            # Check MCP
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "mcp-memory-server"], capture_output=True
                )
                self.status_indicators["mcp"].config(
                    text="🟢" if result.returncode == 0 else "🟡"
                )
            except:
                self.status_indicators["mcp"].config(text="🔴")

            # Check Gemini API
            gemini_config = Path.home() / ".gemini" / "settings.json"
            if gemini_config.exists():
                try:
                    with open(gemini_config, "r") as f:
                        config = json.load(f)
                        if config.get("apiKey"):
                            self.status_indicators["gemini"].config(text="🟢")
                            self.gemini_status_label.config(
                                text="✅ API Key Configured", fg="green"
                            )
                        else:
                            self.status_indicators["gemini"].config(text="🔴")
                            self.gemini_status_label.config(
                                text="❌ API Key Missing", fg="red"
                            )
                except:
                    self.status_indicators["gemini"].config(text="🔴")
                    self.gemini_status_label.config(text="❌ Config Error", fg="red")
            else:
                self.status_indicators["gemini"].config(text="🔴")
                self.gemini_status_label.config(text="❌ Not Configured", fg="red")

            # Check AI Assistant
            ai_assistant = self.scripts_path / "ai_research_assistant.py"
            self.status_indicators["ai_assistant"].config(
                text="🟢" if ai_assistant.exists() else "🔴"
            )

            # Check Research Hub
            research_hub = self.scripts_path / "intelligent_research_hub.py"
            self.status_indicators["research_hub"].config(
                text="🟢" if research_hub.exists() else "🔴"
            )

            self.status_label.config(text="System status updated")

        thread = threading.Thread(target=check_status)
        thread.daemon = True
        thread.start()

    def test_ai_components(self):
        """Test AI components."""
        self.status_label.config(text="Testing AI components...")
        command = [str(self.ai_suite_path), "test"]
        self.run_command_async(command)

    def view_memories(self):
        """View MCP memories."""
        self.status_label.config(text="Loading memories...")
        command = ["python3", str(self.scripts_path / "memory_manager.py"), "list"]

        def on_complete(result):
            if result.returncode == 0:
                self.memory_text.delete(1.0, tk.END)
                self.memory_text.insert(1.0, result.stdout)
            else:
                self.memory_text.delete(1.0, tk.END)
                self.memory_text.insert(
                    1.0, f"Error loading memories:\n{result.stderr}"
                )

        self.run_command_async(command, on_complete)

    def view_research_context(self):
        """View research context."""
        self.status_label.config(text="Loading research context...")
        command = ["python3", str(self.scripts_path / "memory_manager.py"), "context"]

        def on_complete(result):
            if result.returncode == 0:
                self.memory_text.delete(1.0, tk.END)
                self.memory_text.insert(1.0, result.stdout)
            else:
                self.memory_text.delete(1.0, tk.END)
                self.memory_text.insert(1.0, f"Error loading context:\n{result.stderr}")

        self.run_command_async(command, on_complete)

    def search_memories_dialog(self):
        """Show memory search dialog."""
        query = tk.simpledialog.askstring("Search Memories", "Enter search query:")
        if query:
            self.status_label.config(text="Searching memories...")
            command = [
                "python3",
                str(self.scripts_path / "memory_manager.py"),
                "search",
                "--query",
                query,
            ]

            def on_complete(result):
                if result.returncode == 0:
                    self.memory_text.delete(1.0, tk.END)
                    self.memory_text.insert(1.0, result.stdout)
                else:
                    self.memory_text.delete(1.0, tk.END)
                    self.memory_text.insert(1.0, f"Search error:\n{result.stderr}")

            self.run_command_async(command, on_complete)

    def configure_gemini_api(self):
        """Configure Gemini API."""
        messagebox.showinfo(
            "Gemini API Configuration",
            "Please configure your Gemini API key in:\n\n"
            "~/.gemini/settings.json\n\n"
            "Format:\n"
            '{"apiKey": "your-api-key-here"}',
        )

    def open_workspace(self):
        """Open workspace in file manager."""
        if os.name == "posix":
            subprocess.Popen(["xdg-open", str(self.base_path)])
        elif os.name == "nt":
            subprocess.Popen(["explorer", str(self.base_path)])

    def clear_output(self):
        """Clear output text."""
        self.output_text.delete(1.0, tk.END)

    def save_output(self):
        """Save output to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            try:
                with open(filename, "w") as f:
                    f.write(self.output_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save output: {e}")

    def export_dashboard(self):
        """Export research dashboard."""
        self.generate_dashboard()

    def export_summary(self):
        """Export research summary."""
        self.status_label.config(text="Exporting research summary...")
        command = [
            "python3",
            str(self.scripts_path / "intelligent_research_hub.py"),
            "status",
        ]

        def on_complete(result):
            if result.returncode == 0:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    initialname="research_summary.txt",
                )
                if filename:
                    try:
                        with open(filename, "w") as f:
                            f.write(result.stdout)
                        messagebox.showinfo(
                            "Success", f"Research summary exported to {filename}"
                        )
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to export summary: {e}")

        self.run_command_async(command, on_complete)

    def export_memories(self):
        """Export MCP memories."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialname="mcp_memories.json",
        )
        if filename:
            try:
                memory_file = Path.home() / ".pcs-memory.json"
                if memory_file.exists():
                    import shutil

                    shutil.copy2(memory_file, filename)
                    messagebox.showinfo("Success", f"Memories exported to {filename}")
                else:
                    messagebox.showwarning("Warning", "Memory file not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export memories: {e}")

    def refresh_results(self):
        """Refresh results list."""
        # This would populate the results tree with recent research results
        self.results_tree.delete(*self.results_tree.get_children())

        # Add sample results (in real implementation, would load from MCP)
        sample_results = [
            ("AI Search", "Search", "2025-09-10 16:44:10", "✅ Success"),
            ("Pipeline", "Complete Analysis", "2025-09-10 16:43:48", "✅ Success"),
            ("Strategy", "Research Strategy", "2025-09-10 16:44:51", "✅ Success"),
            ("Gaps", "Gap Analysis", "2025-09-10 16:45:25", "✅ Success"),
        ]

        for i, (name, type_name, timestamp, status) in enumerate(sample_results):
            self.results_tree.insert(
                "", "end", iid=i, text=name, values=(type_name, timestamp, status)
            )

    def view_result_details(self):
        """View details of selected result."""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            messagebox.showinfo(
                "Result Details",
                f"Name: {item['text']}\nType: {item['values'][0]}\nTimestamp: {item['values'][1]}\nStatus: {item['values'][2]}",
            )

    def check_output_queue(self):
        """Check for output updates from threads."""
        try:
            while True:
                message = self.output_queue.get_nowait()
                self.log_output(message)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.check_output_queue)


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = PCSGUI(root)

    # Add import for dialog
    import tkinter.simpledialog

    tk.simpledialog = tkinter.simpledialog

    root.mainloop()


if __name__ == "__main__":
    main()
