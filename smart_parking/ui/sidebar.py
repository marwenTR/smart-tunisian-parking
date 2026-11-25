
import customtkinter as ctk
from . import theme as T


NAV_ITEMS = [
    ("dashboard",       "Dashboard"),
    ("live_monitoring", "Live Monitoring"),
    ("vehicles",        "Vehicle Management"),
    ("history",         "Parking History"),
    ("reports",         "Reports & Statistics"),
    ("settings",        "Settings"),
    ("about",           "About"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate):
        super().__init__(master, fg_color=T.SIDEBAR_BG, corner_radius=0, width=250)
        self.grid_propagate(False)
        self.on_navigate = on_navigate
        self.buttons = {}
        self.active = None

        # Brand
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=T.PAD_M, pady=(T.PAD_L, T.PAD_S))
        ctk.CTkLabel(brand, text="Smart Parking",
                     font=T.FONT_BRAND, text_color=T.WHITE, anchor="w"
                     ).pack(anchor="w")
        ctk.CTkLabel(brand, text="Tunisia",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED_DARK, anchor="w"
                     ).pack(anchor="w")

        # Mode badge
        self.mode_badge = ctk.CTkLabel(
            self, text="  SIMULATION MODE  ",
            fg_color=T.ORANGE, text_color=T.WHITE,
            corner_radius=8, font=(T.FONT_FAMILY, 10, "bold")
        )
        self.mode_badge.pack(anchor="w", padx=T.PAD_M, pady=(0, T.PAD_L))

        # Nav
        for key, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self, text="   " + label, anchor="w",
                height=42, corner_radius=8,
                fg_color="transparent", hover_color=T.SIDEBAR_HOVER,
                text_color=T.TEXT_ON_DARK, font=T.FONT_NAV,
                command=lambda k=key: self.on_navigate(k),
            )
            btn.pack(fill="x", padx=T.PAD_S, pady=2)
            self.buttons[key] = btn

        # Footer status
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=T.PAD_M, pady=T.PAD_M)
        self.cam_status = ctk.CTkLabel(
            footer, text="●  Camera: not checked",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED_DARK, anchor="w"
        )
        self.cam_status.pack(anchor="w")
        ctk.CTkLabel(footer, text="  © 2026 Smart Parking Tunisia",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED_DARK, anchor="w"
                     ).pack(anchor="w", pady=(4, 0))

    def set_active(self, key):
        if self.active and self.active in self.buttons:
            self.buttons[self.active].configure(
                fg_color="transparent", font=T.FONT_NAV)
        self.active = key
        if key in self.buttons:
            self.buttons[key].configure(
                fg_color=T.SIDEBAR_ACTIVE, font=T.FONT_NAV_ACT)

    def set_camera_status(self, text, ok=None):
        color = T.TEXT_MUTED_DARK
        if ok is True:
            color = T.EMERALD
        elif ok is False:
            color = T.ORANGE
        self.cam_status.configure(text="●  " + text, text_color=color)