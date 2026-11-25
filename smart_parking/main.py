"""App entry point: sets up window, sidebar, page router."""
import customtkinter as ctk
import traceback
import tkinter.messagebox
from ui import theme as T
from ui.sidebar import Sidebar
from ui.dashboard import DashboardPage
from ui.live_monitoring import LiveMonitoringPage
from ui.vehicle_management import VehicleManagementPage
from ui.parking_history import ParkingHistoryPage
from ui.reports import ReportsPage
from ui.settings import SettingsPage
from ui.about import AboutPage
from core import database as db

ctk.set_appearance_mode("light")

PAGES = {
    "dashboard": DashboardPage,
    "live_monitoring": LiveMonitoringPage,
    "vehicles": VehicleManagementPage,
    "history": ParkingHistoryPage,
    "reports": ReportsPage,
    "settings": SettingsPage,
    "about": AboutPage,
}

def global_exception_handler(exc, val, tb):
    error_msg = "".join(traceback.format_exception(exc, val, tb))
    print("\n--- CRITICAL UI ERROR ---\n", error_msg)
    tkinter.messagebox.showerror("UI Crash", f"An error occurred:\n\n{val}\n\nCheck terminal for details.")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Force window to front
        self.lift()
        self.focus_force()
        
        self.title("Smart Tunisian Parking Management")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.configure(fg_color=T.CONTENT_BG)
        
        # Attach error catcher
        self.report_callback_exception = global_exception_handler

        db.init_db()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color=T.CONTENT_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self.current_key = None
        
        # Start on Dashboard
        self.show_page("dashboard")

    def show_page(self, key):
        if key not in PAGES: return
        if self.current_key == key:
            page = self.pages.get(key)
            if hasattr(page, "refresh"): page.refresh()
            return

        if self.current_key and self.current_key in self.pages:
            old_page = self.pages[self.current_key]
            if hasattr(old_page, "_stop_all"):
                try: old_page._stop_all()
                except: pass
            old_page.grid_forget()

        if key not in self.pages:
            self.pages[key] = PAGES[key](self.content)
        self.pages[key].grid(row=0, column=0, sticky="nsew")
        self.current_key = key
        self.sidebar.set_active(key)
        
        page = self.pages[key]
        if hasattr(page, "refresh"): page.refresh()

def _on_close():
    for page in app.pages.values():
        if hasattr(page, "_stop_all"):
            try: page._stop_all()
            except: pass
    app.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", _on_close)
    app.mainloop()