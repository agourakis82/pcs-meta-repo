#!/usr/bin/env python3
"""
PCS AI Research Suite - Demo GUI
Simplified demonstration version of the graphical interface.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
from pathlib import Path
from datetime import datetime


class PCSDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("PCS AI Research Suite - Demo v4.3")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")

        # Paths
        self.base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        self.ai_suite_path = self.base_path / "pcs_ai_suite.sh"

        self.create_interface()

    def create_interface(self):
        """Create the demo interface."""
        # Header
        header_frame = tk.Frame(self.root, bg="#2E86AB", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🧠 PCS AI Research Suite v4.3 - Demo",
            font=("Arial", 18, "bold"),
            bg="#2E86AB",
            fg="white",
        )
        title_label.pack(pady=15)

        # Main frame
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = tk.LabelFrame(
            main_frame,
            text="🧠 AI Research Controls",
            font=("Arial", 12, "bold"),
            bg="white",
        )
        left_panel.pack(side="left", fill="y", padx=(0, 5))

        # Search section
        tk.Label(
            left_panel, text="Research Topic:", font=("Arial", 10, "bold"), bg="white"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        self.search_entry = tk.Entry(left_panel, width=35, font=("Arial", 10))
        self.search_entry.pack(padx=10, pady=5)
        self.search_entry.insert(0, "semantic networks computational psychiatry")

        # Buttons
        tk.Button(
            left_panel,
            text="🔍 AI Search & Analysis",
            command=self.run_ai_search,
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            width=25,
        ).pack(padx=10, pady=5)

        tk.Button(
            left_panel,
            text="🎯 Generate Strategy",
            command=self.generate_strategy,
            font=("Arial", 10, "bold"),
            bg="#9b59b6",
            fg="white",
            width=25,
        ).pack(padx=10, pady=5)

        tk.Button(
            left_panel,
            text="🚀 Complete Pipeline",
            command=self.run_pipeline,
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            width=25,
        ).pack(padx=10, pady=5)

        tk.Button(
            left_panel,
            text="🔍 Analyze Gaps",
            command=self.analyze_gaps,
            font=("Arial", 10, "bold"),
            bg="#f39c12",
            fg="white",
            width=25,
        ).pack(padx=10, pady=5)

        # Status section
        status_frame = tk.LabelFrame(
            left_panel, text="⚙️ System Status", font=("Arial", 10, "bold"), bg="white"
        )
        status_frame.pack(fill="x", padx=10, pady=10)

        self.status_labels = {}
        components = [
            ("Python 3", "python"),
            ("Gemini AI", "gemini"),
            ("AI Assistant", "ai"),
            ("MCP Memory", "mcp"),
        ]

        for name, key in components:
            frame = tk.Frame(status_frame, bg="white")
            frame.pack(fill="x", padx=5, pady=2)

            status_label = tk.Label(frame, text="🟢", font=("Arial", 12), bg="white")
            status_label.pack(side="left")

            name_label = tk.Label(frame, text=name, font=("Arial", 9), bg="white")
            name_label.pack(side="left", padx=5)

            self.status_labels[key] = status_label

        tk.Button(
            status_frame,
            text="🔄 Refresh Status",
            command=self.update_status,
            font=("Arial", 9),
            width=20,
        ).pack(pady=5)

        # Right panel - Output
        right_panel = tk.LabelFrame(
            main_frame,
            text="📋 Research Output",
            font=("Arial", 12, "bold"),
            bg="white",
        )
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Output text
        self.output_text = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Controls
        controls_frame = tk.Frame(right_panel, bg="white")
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(
            controls_frame, text="🗑️ Clear", command=self.clear_output, font=("Arial", 9)
        ).pack(side="left", padx=5)

        tk.Button(
            controls_frame,
            text="📊 View Memories",
            command=self.view_memories,
            font=("Arial", 9),
        ).pack(side="left", padx=5)

        # Initial status
        self.log_output("🚀 PCS AI Research Suite Demo Initialized", "SUCCESS")
        self.log_output("Ready for AI-enhanced research automation!", "INFO")
        self.update_status()

    def log_output(self, message, level="INFO"):
        """Add message to output."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Emoji mapping
        emojis = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}

        emoji = emojis.get(level, "•")
        formatted_message = f"[{timestamp}] {emoji} {message}\n"

        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def run_command_async(self, command, description):
        """Run command asynchronously."""

        def run():
            try:
                self.log_output(f"Running: {description}")

                # Simulate the command for demo
                if not self.ai_suite_path.exists():
                    self.log_output(
                        "Demo Mode: Simulating AI command execution", "WARNING"
                    )
                    self.log_output(f"Would execute: {' '.join(command)}", "INFO")
                    self.log_output("✅ Demo execution completed", "SUCCESS")
                    return

                result = subprocess.run(
                    command,
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    self.log_output("Command completed successfully", "SUCCESS")
                    if result.stdout:
                        self.log_output(result.stdout[:500], "INFO")
                else:
                    self.log_output(f"Command failed: {result.stderr[:200]}", "ERROR")

            except subprocess.TimeoutExpired:
                self.log_output("Command timed out", "ERROR")
            except Exception as e:
                self.log_output(f"Error: {e}", "ERROR")

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def run_ai_search(self):
        """Run AI search."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a research topic")
            return

        command = [str(self.ai_suite_path), "ai-search", query]
        self.run_command_async(command, f"AI Search: {query}")

    def generate_strategy(self):
        """Generate research strategy."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a research topic")
            return

        command = [str(self.ai_suite_path), "ai-strategy", query]
        self.run_command_async(command, f"Strategy Generation: {query}")

    def run_pipeline(self):
        """Run complete pipeline."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a research topic")
            return

        if messagebox.askyesno(
            "Confirm Pipeline",
            f"Run complete AI pipeline for: '{query}'?\n\n"
            "This includes literature search, strategy generation,\n"
            "gap analysis, and manuscript outline.",
        ):
            command = [str(self.ai_suite_path), "ai-pipeline", query]
            self.run_command_async(command, f"Complete Pipeline: {query}")

    def analyze_gaps(self):
        """Analyze research gaps."""
        command = [str(self.ai_suite_path), "ai-gaps"]
        self.run_command_async(command, "Research Gap Analysis")

    def view_memories(self):
        """View MCP memories."""
        try:
            memory_manager = self.base_path / "scripts" / "memory_manager.py"
            if memory_manager.exists():
                command = ["python3", str(memory_manager), "list"]
                result = subprocess.run(
                    command, capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    self.log_output("📚 MCP Memories:", "SUCCESS")
                    lines = result.stdout.split("\n")[:10]  # Show first 10 lines
                    for line in lines:
                        if line.strip():
                            self.log_output(line, "INFO")
                    if len(result.stdout.split("\n")) > 10:
                        self.log_output("... (showing first 10 entries)", "INFO")
                else:
                    self.log_output("Error retrieving memories", "ERROR")
            else:
                self.log_output(
                    "Memory manager not found - running in demo mode", "WARNING"
                )
        except Exception as e:
            self.log_output(f"Error viewing memories: {e}", "ERROR")

    def update_status(self):
        """Update system status."""

        def check():
            # Check Python
            try:
                result = subprocess.run(["python3", "--version"], capture_output=True)
                self.status_labels["python"].config(
                    text="🟢" if result.returncode == 0 else "🔴"
                )
            except:
                self.status_labels["python"].config(text="🔴")

            # Check Gemini
            gemini_config = Path.home() / ".gemini" / "settings.json"
            self.status_labels["gemini"].config(
                text="🟢" if gemini_config.exists() else "🟡"
            )

            # Check AI Assistant
            ai_assistant = self.base_path / "scripts" / "ai_research_assistant.py"
            self.status_labels["ai"].config(
                text="🟢" if ai_assistant.exists() else "🔴"
            )

            # Check MCP
            memory_file = Path.home() / ".pcs-memory.json"
            self.status_labels["mcp"].config(
                text="🟢" if memory_file.exists() else "🟡"
            )

            self.log_output("System status updated", "INFO")

        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()

    def clear_output(self):
        """Clear output text."""
        self.output_text.delete(1.0, tk.END)
        self.log_output("Output cleared", "INFO")


def main():
    """Launch the demo GUI."""
    root = tk.Tk()

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (900 // 2)
    y = (root.winfo_screenheight() // 2) - (600 // 2)
    root.geometry(f"900x600+{x}+{y}")

    app = PCSDemo(root)

    # Handle window close
    def on_close():
        if messagebox.askokcancel("Quit", "Close PCS AI Research Suite Demo?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
