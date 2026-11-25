"""Reports & Statistics: real charts from real DB data."""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from . import theme as T
from core import database as db

class ReportsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CONTENT_BG, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=T.PAD_XL, pady=(T.PAD_L, T.PAD_M))
        ctk.CTkLabel(header, text="Reports & Statistics", font=T.FONT_H1, text_color=T.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(header, text="Refresh", width=90, height=32, corner_radius=8, fg_color=T.TEAL, hover_color=T.EMERALD, command=self.refresh).pack(side="right")

        self.card1 = self._make_chart_card(self, "Entries & exits — last 7 days")
        self.card1.grid(row=1, column=0, sticky="nsew", padx=(T.PAD_XL, T.PAD_M), pady=(0, T.PAD_M))

        self.card2 = self._make_chart_card(self, "Occupancy")
        self.card2.grid(row=1, column=1, sticky="nsew", padx=(0, T.PAD_XL), pady=(0, T.PAD_M))

        self.card3 = self._make_chart_card(self, "Entries per hour — today")
        self.card3.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=T.PAD_XL, pady=(0, T.PAD_L))

        self.refresh()

    def _make_chart_card(self, master, title):
        card = ctk.CTkFrame(master, fg_color=T.CARD_BG, corner_radius=T.RADIUS_CARD, border_width=1, border_color=T.BORDER)
        ctk.CTkLabel(card, text=title, font=T.FONT_H2, text_color=T.TEXT_PRIMARY, anchor="w").pack(anchor="w", padx=T.PAD_M, pady=(T.PAD_M, 0))
        
        holder = ctk.CTkFrame(card, fg_color="transparent")
        holder.pack(fill="both", expand=True, padx=T.PAD_M, pady=T.PAD_M)
        card._holder = holder
        return card

    def _draw_chart(self, card, figure_fn):
        holder = card._holder
        for w in holder.winfo_children():
            w.destroy()
            
        # Create figure with fixed size
        fig = Figure(figsize=(6, 3), dpi=80)
        fig.patch.set_facecolor(T.CARD_BG)
        ax = fig.add_subplot(111)
        
        figure_fn(ax)
        
        ax.set_facecolor(T.CARD_BG)
        for spine in ("top", "right"): ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"): ax.spines[spine].set_color(T.BORDER)
        ax.tick_params(colors=T.TEXT_SECONDARY, labelsize=8)
        fig.tight_layout()
        
        # Force absolute rendering dimensions so Tkinter can't collapse it
        canvas = FigureCanvasTkAgg(fig, master=holder)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(width=450, height=250)
        widget.pack(fill="both", expand=True, side="top")

    def refresh(self):
        daily   = db.fetch_daily_counts(days=7)
        occ     = db.fetch_occupancy()
        hourly  = db.fetch_hourly_entries_today()

        def draw_daily(ax):
            labels = [d["date"][5:] for d in daily]
            entries = [d["entries"] for d in daily]
            exits   = [d["exits"]   for d in daily]
            x = range(len(labels))
            ax.bar([i - 0.2 for i in x], entries, width=0.4, color=T.TEAL, label="Entries")
            ax.bar([i + 0.2 for i in x], exits, width=0.4, color=T.DEEP_BLUE, label="Exits")
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels)
            ax.legend(fontsize=8, frameon=False)
        self._draw_chart(self.card1, draw_daily)

        def draw_occ(ax):
            parked = occ["parked"]
            free   = max(0, occ["capacity"] - parked)
            ax.pie([parked, free] if parked + free > 0 else [0, 1], labels=[f"Parked\n{parked}", f"Free\n{free}"], colors=[T.TEAL, T.OFF_WHITE], textprops={"color": T.TEXT_PRIMARY, "fontsize": 9}, wedgeprops={"edgecolor": T.CARD_BG, "linewidth": 2})
        self._draw_chart(self.card2, draw_occ)

        def draw_hourly(ax):
            hours = [h["hour"] for h in hourly]
            counts = [h["count"] for h in hourly]
            ax.plot(hours, counts, color=T.ORANGE, marker="o", linewidth=2)
            ax.set_xticks(range(0, 24, 3))
            ax.set_xlim(0, 23)
            ax.set_ylim(bottom=0)
        self._draw_chart(self.card3, draw_hourly)