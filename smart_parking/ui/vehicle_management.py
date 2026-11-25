"""Vehicle Management: list of all known vehicles, last seen, visits, status."""
import customtkinter as ctk
from . import theme as T
from .widgets import DataTable, SectionTitle
from core import database as db
from datetime import datetime

TABLE_COLUMNS = [
    ("plate",       "Registration", 2),
    ("status",      "Status",       1),
    ("last_entry",  "Last Entry",   2),
    ("last_exit",   "Last Exit",    2),
    ("visits",      "Total Visits", 1),
]

class VehicleManagementPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CONTENT_BG, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=T.PAD_XL, pady=(T.PAD_L, T.PAD_M))
        ctk.CTkLabel(header, text="Vehicle Management", font=T.FONT_H1, text_color=T.TEXT_PRIMARY).pack(side="left")

        # Manual Action Buttons
        ctk.CTkButton(header, text="Manual Exit", width=110, height=34, corner_radius=8, fg_color=T.DEEP_BLUE, hover_color=T.NAVY, command=self._manual_exit).pack(side="right", padx=(T.PAD_S, 0))
        ctk.CTkButton(header, text="Manual Entry", width=110, height=34, corner_radius=8, fg_color=T.TEAL, hover_color=T.EMERALD, command=self._manual_entry).pack(side="right")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=T.PAD_XL, pady=(0, T.PAD_S))
        SectionTitle(toolbar, "Known vehicles").pack(side="left")

        self.search_var = ctk.StringVar()
        ctk.CTkEntry(toolbar, textvariable=self.search_var, placeholder_text="Search plate…", width=200, height=32, corner_radius=8, border_color=T.BORDER).pack(side="right", padx=(T.PAD_S, 0))
        ctk.CTkButton(toolbar, text="Search", width=70, height=32, corner_radius=8, fg_color=T.TEAL, hover_color=T.EMERALD, command=self.refresh).pack(side="right", padx=(T.PAD_S, 0))

        self.table = DataTable(self, TABLE_COLUMNS)
        self.table.grid(row=2, column=0, sticky="nsew", padx=T.PAD_XL, pady=(0, T.PAD_L))

        self.refresh()

    def refresh(self):
        rows = db.fetch_vehicle_summary(self.search_var.get().strip())
        self.table.set_rows(rows)

    def _manual_entry(self):
        self._prompt_plate("Manual Entry", "Enter plate number:", self._do_entry)

    def _manual_exit(self):
        self._prompt_plate("Manual Exit", "Enter plate number:", self._do_exit)

    def _prompt_plate(self, title, text, callback):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("300x150")
        popup.configure(fg_color=T.CARD_BG)
        popup.transient(self.winfo_toplevel())
        
        ctk.CTkLabel(popup, text=text, font=T.FONT_BODY, text_color=T.TEXT_PRIMARY).pack(pady=(T.PAD_M, 5))
        entry = ctk.CTkEntry(popup, width=200, corner_radius=8)
        entry.pack(pady=5)
        entry.focus_set()
        
        def submit():
            plate = entry.get().strip().upper()
            if plate:
                popup.destroy()
                callback(plate)
                
        ctk.CTkButton(popup, text="Confirm", width=100, corner_radius=8, fg_color=T.TEAL, hover_color=T.EMERALD, command=submit).pack(pady=T.PAD_S)

    def _do_entry(self, plate):
        try:
            # Check if already parked
            with db._connect() as conn:
                active = conn.execute("SELECT id FROM parking_records WHERE plate=? AND status='Parked'", (plate,)).fetchone()
                if active:
                    self._show_msg("Error", f"{plate} is already parked!")
                    return
                
                now = datetime.now().isoformat(sep=' ', timespec='seconds')
                conn.execute("INSERT INTO parking_records(plate, entry_ts, status) VALUES(?,?, 'Parked')", (plate, now))
                conn.commit()
            self._show_msg("Success", f"Entry recorded for {plate}.")
            self.refresh()
        except Exception as e:
            self._show_msg("Error", str(e))

    def _do_exit(self, plate):
        try:
            with db._connect() as conn:
                active = conn.execute("SELECT id, entry_ts FROM parking_records WHERE plate=? AND status='Parked'", (plate,)).fetchone()
                if not active:
                    self._show_msg("Error", f"No active parking record found for {plate}.")
                    return
                
                now = datetime.now()
                entry_dt = datetime.fromisoformat(active["entry_ts"])
                duration = int((now - entry_dt).total_seconds())
                
                conn.execute("UPDATE parking_records SET exit_ts=?, duration_sec=?, status='Completed' WHERE id=?",
                             (now.isoformat(sep=' ', timespec='seconds'), duration, active["id"]))
                conn.commit()
            self._show_msg("Success", f"Exit recorded for {plate}. Duration: {duration//60} mins.")
            self.refresh()
        except Exception as e:
            self._show_msg("Error", str(e))

    def _show_msg(self, title, msg):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("350x120")
        popup.configure(fg_color=T.CARD_BG)
        popup.transient(self.winfo_toplevel())
        ctk.CTkLabel(popup, text=msg, font=T.FONT_BODY, text_color=T.TEXT_PRIMARY, wraplength=300).pack(pady=T.PAD_L)
        ctk.CTkButton(popup, text="OK", width=80, corner_radius=8, fg_color=T.TEAL, hover_color=T.EMERALD, command=popup.destroy).pack()