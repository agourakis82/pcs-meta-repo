#!/usr/bin/env python3
"""
Teste simples de GUI - apenas caracteres ASCII
"""

import tkinter as tk
from tkinter import scrolledtext


def main():
    root = tk.Tk()
    root.title("PCS Test GUI - ASCII Only")
    root.geometry("600x400")

    # Frame principal
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Título
    title_label = tk.Label(
        main_frame, text="PCS AI Research Suite v4.3", font=("Arial", 16, "bold")
    )
    title_label.pack(pady=10)

    # Área de entrada
    entry_frame = tk.Frame(main_frame)
    entry_frame.pack(fill="x", pady=5)

    tk.Label(entry_frame, text="Research Topic:", font=("Arial", 10)).pack(anchor="w")
    search_entry = tk.Entry(entry_frame, width=50, font=("Arial", 10))
    search_entry.pack(fill="x", pady=5)
    search_entry.insert(0, "semantic networks computational psychiatry")

    # Botões
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)

    tk.Button(
        button_frame,
        text="AI Search",
        font=("Arial", 10),
        bg="#3498db",
        fg="white",
        width=15,
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame,
        text="Generate Strategy",
        font=("Arial", 10),
        bg="#9b59b6",
        fg="white",
        width=15,
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame,
        text="Exit",
        command=root.quit,
        font=("Arial", 10),
        bg="#e74c3c",
        fg="white",
        width=15,
    ).pack(side="right", padx=5)

    # Área de output
    output_label = tk.Label(main_frame, text="Output:", font=("Arial", 10, "bold"))
    output_label.pack(anchor="w", pady=(10, 5))

    output_text = scrolledtext.ScrolledText(
        main_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#f8f8f8"
    )
    output_text.pack(fill="both", expand=True)

    # Mensagem inicial
    output_text.insert(tk.END, "PCS AI Research Suite Initialized\n")
    output_text.insert(tk.END, "Ready for AI-enhanced research automation!\n")
    output_text.insert(tk.END, "No emojis or special characters - pure ASCII\n")

    # Status
    status_label = tk.Label(
        root,
        text="Status: Ready | Python 3 | Tkinter OK | No encoding issues",
        relief=tk.SUNKEN,
        anchor="w",
    )
    status_label.pack(side="bottom", fill="x")

    print("GUI Test Started - Check for any strange characters")
    root.mainloop()
    print("GUI Test Completed")


if __name__ == "__main__":
    main()
