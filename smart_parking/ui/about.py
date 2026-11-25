import customtkinter as ctk
from . import theme as T

class AboutPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CONTENT_BG, corner_radius=0)
        ctk.CTkLabel(self, text="About", font=T.FONT_H1,
                     text_color=T.TEXT_PRIMARY).pack(anchor="w",
                     padx=T.PAD_XL, pady=T.PAD_L)
        ctk.CTkLabel(self, justify="left", font=T.FONT_BODY,
                     text_color=T.TEXT_SECONDARY,
                     text=("Smart Tunisian Parking Management System\n"
                           "University project n"
                           "Stack: Python · CustomTkinter · OpenCV · SQLite\n"
                           "Later phases: YOLO detection, Tesseract OCR")
        ).pack(anchor="w", padx=T.PAD_XL)