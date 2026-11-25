"""Dashboard page: KPI cards + toolbar + recent activity table."""
import customtkinter as ctk
from . import theme as T
from .widgets import StatCard, DataTable, SectionTitle
from core import database as db


TABLE_COLUMNS = [
    ("id",          "ID",           1),
    ("plate",       "Registration", 2),
    ("entry_date",  "Entry Date",   2),
    ("entry_time",  "Entry Time",   1),
    ("exit_time",   "Exit Time",    1),
    ("duration",    "Duration",     1),
    ("status",      "Status",       1),
]


def _fmt_duration(sec):
    if not sec:
        return "—"
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h {m:02d}m"


def _prepare_row(r):
    entry_ts = r.get("entry_ts") or ""
    exit_ts = r.get("exit_ts") or ""
    return {
        "id":         r["id"],
        "plate":      r["plate"],
        "entry_date": entry_ts[:10] if entry_ts else "—",
        "entry_time": entry_ts[11:19] if len(entry_ts) >= 19 else "—",
        "exit_time":  exit_ts[11:19] if len(exit_ts) >= 19 else "—",
        "duration":   _fmt_duration(r.get("duration_sec")),
        "status":     r["status"],
    }


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CONTENT_BG, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)

        # --- Header ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=T.PAD_XL, pady=(T.PAD_L, T.PAD_M))
        ctk.CTkLabel(header, text="Dashboard", font=T.FONT_H1,
                     text_color=T.TEXT_PRIMARY).pack(side="left")

        # --- KPI row ---
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.grid(row=1, column=0, sticky="ew", padx=T.PAD_XL)
        for c in range(4):
            kpi_row.grid_columnconfigure(c, weight=1, uniform="kpi")

        self.card_parked    = StatCard(kpi_row, "Currently parked", 0, T.TEAL,    "P")
        self.card_entries   = StatCard(kpi_row, "Entries today",    0, T.EMERALD, "↓")
        self.card_exits     = StatCard(kpi_row, "Exits today",      0, T.DEEP_BLUE, "↑")
        self.card_available = StatCard(kpi_row, "Available spaces", 0, T.ORANGE,  "A")
        for i, c in enumerate((self.card_parked, self.card_entries,
                               self.card_exits, self.card_available)):
            c.grid(row=0, column=i, sticky="nsew",
                   padx=(0 if i == 0 else T.PAD_M, 0), pady=0)

        # --- Toolbar ---
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=2, column=0, sticky="ew",
                     padx=T.PAD_XL, pady=(T.PAD_L, T.PAD_S))
        SectionTitle(toolbar, "Recent activity").pack(side="left")

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(toolbar, textvariable=self.search_var,
                                    placeholder_text="Search plate…",
                                    width=180, height=32,
                                    corner_radius=8, border_color=T.BORDER)
        search_entry.pack(side="right", padx=(T.PAD_S, 0))

        self.date_to = ctk.CTkEntry(toolbar, placeholder_text="To YYYY-MM-DD",
                                    width=130, height=32, corner_radius=8,
                                    border_color=T.BORDER)
        self.date_to.pack(side="right", padx=(T.PAD_S, 0))

        self.date_from = ctk.CTkEntry(toolbar, placeholder_text="From YYYY-MM-DD",
                                      width=130, height=32, corner_radius=8,
                                      border_color=T.BORDER)
        self.date_from.pack(side="right", padx=(T.PAD_S, 0))

        ctk.CTkButton(toolbar, text="Apply", width=70, height=32,
                      corner_radius=8, fg_color=T.TEAL, hover_color=T.EMERALD,
                      command=self.refresh
                      ).pack(side="right", padx=(T.PAD_S, 0))

        # --- Table ---
        self.table = DataTable(self, TABLE_COLUMNS)
        self.table.grid(row=3, column=0, sticky="nsew",
                        padx=T.PAD_XL, pady=(0, T.PAD_L))
        self.grid_rowconfigure(3, weight=1)

        self.refresh()

    def refresh(self):
        """Pull real numbers + rows from DB. Called on show and on demand."""
        self.card_parked.set_value(db.count_currently_parked())
        self.card_entries.set_value(db.count_entries_today())
        self.card_exits.set_value(db.count_exits_today())
        self.card_available.set_value(db.count_available_spaces())

        rows = db.fetch_recent_records(
            limit=50,
            search=self.search_var.get().strip(),
            date_from=self.date_from.get().strip(),
            date_to=self.date_to.get().strip(),
        )
        self.table.set_rows([_prepare_row(r) for r in rows])