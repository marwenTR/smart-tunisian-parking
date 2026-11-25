import customtkinter as ctk
from . import theme as T
from core import database as db

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CONTENT_BG, corner_radius=0)
        ctk.CTkLabel(self, text="Settings", font=T.FONT_H1,
                     text_color=T.TEXT_PRIMARY).pack(anchor="w",
                     padx=T.PAD_XL, pady=T.PAD_L)

        card = ctk.CTkFrame(self, fg_color=T.CARD_BG, corner_radius=T.RADIUS_CARD,
                            border_width=1, border_color=T.BORDER)
        card.pack(fill="x", padx=T.PAD_XL, pady=T.PAD_S)

        ctk.CTkLabel(card, text="Parking capacity",
                     font=T.FONT_BODY, text_color=T.TEXT_PRIMARY
                     ).grid(row=0, column=0, padx=T.PAD_M, pady=T.PAD_M, sticky="w")

        self.cap_entry = ctk.CTkEntry(card, width=100, corner_radius=8)
        self.cap_entry.insert(0, str(db.get_parking_capacity()))
        self.cap_entry.grid(row=0, column=1, padx=T.PAD_M, sticky="w")

        ctk.CTkButton(card, text="Save", width=80, corner_radius=8,
                      fg_color=T.TEAL, hover_color=T.EMERALD,
                      command=self._save).grid(row=0, column=2, padx=T.PAD_M)

    def _save(self):
        try:
            val = int(self.cap_entry.get())
            if val > 0:
                db.set_setting("parking_capacity", val)
        except ValueError:
            pass