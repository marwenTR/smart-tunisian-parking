"""Reusable premium widgets: Card, StatCard, StatusPill, Table, SectionTitle."""
import customtkinter as ctk
from . import theme as T

class Card(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=T.CARD_BG, corner_radius=T.RADIUS_CARD,
                         border_width=1, border_color=T.BORDER, **kw)

class StatCard(Card):
    def __init__(self, master, title, value, accent=T.TEAL, icon="●", **kw):
        super().__init__(master, **kw)
        self.grid_columnconfigure(1, weight=1)
        icon_box = ctk.CTkFrame(self, width=52, height=52, fg_color=accent, corner_radius=12)
        icon_box.grid(row=0, column=0, rowspan=2, padx=(T.PAD_M, T.PAD_M), pady=T.PAD_M, sticky="n")
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=(T.FONT_FAMILY, 22, "bold"), text_color=T.WHITE).place(relx=0.5, rely=0.5, anchor="center")
        self.value_lbl = ctk.CTkLabel(self, text=str(value), font=T.FONT_CARD_NUM, text_color=T.TEXT_PRIMARY, anchor="w")
        self.value_lbl.grid(row=0, column=1, sticky="sw", pady=(T.PAD_M, 0))
        ctk.CTkLabel(self, text=title, font=T.FONT_CARD_LBL, text_color=T.TEXT_SECONDARY, anchor="w").grid(row=1, column=1, sticky="nw", pady=(0, T.PAD_M))

    def set_value(self, value):
        self.value_lbl.configure(text=str(value))

class StatusPill(ctk.CTkLabel):
    def __init__(self, master, status):
        color = T.STATUS_PARKED if status == "Parked" else T.STATUS_COMPLETED
        super().__init__(master, text=f"  {status}  ", fg_color=color, text_color=T.WHITE, corner_radius=8, font=T.FONT_SMALL)

class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text):
        super().__init__(master, text=text, font=T.FONT_H2, text_color=T.TEXT_PRIMARY, anchor="w")

class DataTable(ctk.CTkFrame):
    def __init__(self, master, columns, **kw):
        # The height=350 is critical! It prevents the table from disappearing.
        super().__init__(master, fg_color=T.CARD_BG, corner_radius=T.RADIUS_CARD,
                         border_width=1, border_color=T.BORDER, height=350, **kw)
        self.columns = columns
        self._build_header()
        self.row_container = ctk.CTkFrame(self, fg_color="transparent")
        self.row_container.pack(fill="both", expand=True, padx=T.PAD_M, pady=(0, T.PAD_M))

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=T.PAD_M, pady=(T.PAD_M, T.PAD_S))
        for i, (key, label, width) in enumerate(self.columns):
            hdr.grid_columnconfigure(i, weight=width)
            ctk.CTkLabel(hdr, text=label, font=(T.FONT_FAMILY, 11, "bold"),
                         text_color=T.TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=i, sticky="ew", padx=4)

    def clear(self):
        for w in self.row_container.winfo_children():
            w.destroy()

    def set_rows(self, rows):
        self.clear()
        if not rows:
            ctk.CTkLabel(self.row_container, text="No records yet. Data will appear here as vehicles enter.", font=T.FONT_BODY, text_color=T.TEXT_SECONDARY).pack(pady=T.PAD_L)
            return

        for r_idx, row in enumerate(rows):
            rf = ctk.CTkFrame(self.row_container, fg_color="transparent")
            rf.pack(fill="x", pady=1)
            for i, (key, _, width) in enumerate(self.columns):
                rf.grid_columnconfigure(i, weight=width)
                value = row.get(key, "")
                if key == "status":
                    cell = StatusPill(rf, value)
                    cell.grid(row=0, column=i, sticky="w", padx=4, pady=6)
                else:
                    ctk.CTkLabel(rf, text=str(value), font=T.FONT_BODY,
                                 text_color=T.TEXT_PRIMARY, anchor="w"
                                 ).grid(row=0, column=i, sticky="ew", padx=4, pady=6)
            if r_idx < len(rows) - 1:
                ctk.CTkFrame(self.row_container, height=1, fg_color=T.BORDER).pack(fill="x")