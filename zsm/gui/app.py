from __future__ import annotations

import json
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from ..config import Config
from ..core.audit import run_audit
from ..core.manager import StorageManager
from ..reports.generator import write_reports


class NavButton(ctk.CTkButton):
    def __init__(self, master, text: str, command):
        super().__init__(
            master,
            text=text,
            command=command,
            width=210,
            height=44,
            corner_radius=9,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color=("#dbeafe", "#24324a"),
            text_color=("#172033", "#e8eef9"),
        )

    def active(self, enabled: bool) -> None:
        self.configure(fg_color=("#bfdbfe", "#1d4ed8") if enabled else "transparent")


class App(ctk.CTk):
    def __init__(self) -> None:
        self.config_data = Config.load()
        ctk.set_appearance_mode(self.config_data.theme)
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("Zima Storage Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.manager = StorageManager(self.config_data)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.side = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.side.grid(row=0, column=0, sticky="nsew")
        self.side.grid_propagate(False)
        ctk.CTkLabel(
            self.side,
            text="ZIMA\nSTORAGE MANAGER",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left",
        ).pack(padx=20, pady=(28, 24), anchor="w")

        self.buttons: dict[str, NavButton] = {}
        for name in ["Dashboard", "Dischi", "Rinomina", "Audit", "Backup", "Log"]:
            button = NavButton(self.side, name, lambda selected=name: self.show(selected))
            button.pack(padx=20, pady=5)
            self.buttons[name] = button

        ctk.CTkButton(
            self.side,
            text="Esci",
            command=self.destroy,
            width=210,
            height=44,
            corner_radius=9,
            fg_color="#991b1b",
            hover_color="#b91c1c",
        ).pack(side="bottom", padx=20, pady=22)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        self.title_label = ctk.CTkLabel(
            self.content, text="", font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 18))
        self.body = ctk.CTkScrollableFrame(self.content)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.show("Dashboard")

    def clear(self) -> None:
        for widget in self.body.winfo_children():
            widget.destroy()

    def show(self, name: str) -> None:
        for button_name, button in self.buttons.items():
            button.active(button_name == name)
        self.title_label.configure(text=name)
        self.clear()
        getattr(self, f"page_{name.lower()}")()

    def card(self, title: str, value: str, sub: str = "") -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.body)
        frame.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(
            frame, text=title, font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=18, pady=(14, 3))
        ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=20)).pack(
            anchor="w", padx=18
        )
        ctk.CTkLabel(frame, text=sub).pack(anchor="w", padx=18, pady=(3, 14))
        return frame

    def page_dashboard(self) -> None:
        self.card(
            "Servizio local-storage",
            self.manager.system.service_state(self.config_data.service_name),
            self.config_data.service_name,
        )
        self.card(
            "Database",
            str(self.config_data.database_path),
            "Esistente" if self.config_data.database_path.exists() else "Non trovato",
        )
        try:
            self.card("Dischi registrati", str(len(self.manager.disks())), "Record attivi")
        except Exception as exc:
            self.card("Errore", str(exc))

    def page_dischi(self) -> None:
        try:
            for disk in self.manager.disks():
                active = ", ".join(disk.active_mounts) or "-"
                self.card(
                    disk.label or disk.uuid,
                    disk.device or "Non collegato",
                    f"{disk.size} • {disk.fs_type} • DB: {disk.mount_point} • Attivi: {active}",
                )
        except Exception as exc:
            self.card("Errore", str(exc))

    def page_rinomina(self) -> None:
        ctk.CTkLabel(self.body, text="UUID del disco").pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        uuid_entry = ctk.CTkEntry(self.body, height=42)
        uuid_entry.pack(fill="x", padx=12)
        ctk.CTkLabel(self.body, text="Nuovo nome").pack(
            anchor="w", padx=12, pady=(14, 4)
        )
        name_entry = ctk.CTkEntry(self.body, height=42)
        name_entry.pack(fill="x", padx=12)
        dry_run = ctk.CTkCheckBox(self.body, text="Simula senza modificare")
        dry_run.select()
        dry_run.pack(anchor="w", padx=12, pady=18)
        output = ctk.CTkTextbox(self.body, height=180)
        output.pack(fill="both", expand=True, padx=12, pady=8)

        def execute() -> None:
            try:
                manager = StorageManager(self.config_data, bool(dry_run.get()))
                result = manager.rename(uuid_entry.get(), name_entry.get())
                output.delete("1.0", "end")
                output.insert("end", json.dumps(result, indent=2))
                messagebox.showinfo("ZSM", "Operazione completata")
            except Exception as exc:
                messagebox.showerror("ZSM", str(exc))

        ctk.CTkButton(
            self.body,
            text="Esegui rinomina",
            command=execute,
            height=44,
            corner_radius=9,
            hover_color="#1d4ed8",
        ).pack(fill="x", padx=12, pady=12)

    def page_audit(self) -> None:
        output = ctk.CTkTextbox(self.body)
        output.pack(fill="both", expand=True, padx=12, pady=12)

        def work() -> None:
            try:
                items = run_audit(self.manager)
                paths = write_reports(items, self.config_data.report_dir)
                text = "\n".join(
                    f"[{item.level.upper()}] {item.title}: {item.detail}" for item in items
                )
                text += "\n\nReport:\n" + "\n".join(map(str, paths.values()))
                self.after(0, lambda: self._set_text(output, text))
            except Exception as exc:
                error_message = str(exc)
                self.after(0, lambda msg=error_message: messagebox.showerror("ZSM", msg))

        ctk.CTkButton(
            self.body,
            text="Avvia audit",
            command=lambda: threading.Thread(target=work, daemon=True).start(),
            height=44,
            corner_radius=9,
        ).pack(fill="x", padx=12, pady=12)

    @staticmethod
    def _set_text(widget: ctk.CTkTextbox, text: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("end", text)

    def page_backup(self) -> None:
        def create() -> None:
            try:
                messagebox.showinfo("Backup creato", str(self.manager.create_backup()))
                self.show("Backup")
            except Exception as exc:
                messagebox.showerror("ZSM", str(exc))

        ctk.CTkButton(
            self.body, text="Crea backup", command=create, height=44, corner_radius=9
        ).pack(fill="x", padx=12, pady=12)
        for path in self.manager.backups():
            self.card(path.name, str(path))

    def page_log(self) -> None:
        path = self.config_data.log_dir / "timeline.jsonl"
        text = ctk.CTkTextbox(self.body)
        text.pack(fill="both", expand=True, padx=12, pady=12)
        try:
            text.insert(
                "end",
                path.read_text(encoding="utf-8") if path.exists() else "Nessuna operazione.",
            )
        except Exception as exc:
            text.insert("end", str(exc))


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
