"""Live Monitoring: real camera OR simulation (entry/exit video, image test)."""
import os
import customtkinter as ctk
from PIL import Image
from . import theme as T
from .widgets import Card, SectionTitle
from core.camera import WebcamSource, FrameGrabber, CameraError, probe_webcam
from core.simulation import SimulationSession
from core.vehicle_detection import VehicleDetector
import cv2


class LiveMonitoringPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CONTENT_BG, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # State ----------------------------------------------------------
        self.mode = "none"
        self.grabber = None
        self.sim = None
        self._preview_job = None
        self._ctk_preview_img = None
        
        # Initialize Detector
        self.detector = VehicleDetector()

        # ================= HEADER ======================================
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=T.PAD_XL, pady=(T.PAD_L, T.PAD_S))

        ctk.CTkLabel(header, text="Live Monitoring", font=T.FONT_H1,
                     text_color=T.TEXT_PRIMARY).pack(side="left")

        self.mode_badge = ctk.CTkLabel(
            header, text="  MODE: NONE  ", fg_color=T.TEXT_SECONDARY,
            text_color=T.WHITE, corner_radius=8,
            font=(T.FONT_FAMILY, 10, "bold"))
        self.mode_badge.pack(side="right")

        # ================= MODE SELECTOR ===============================
        modes_row = ctk.CTkFrame(self, fg_color="transparent")
        modes_row.grid(row=1, column=0, sticky="ew",
                       padx=T.PAD_XL, pady=(0, T.PAD_M))
        self._mode_btn(modes_row, "Real Camera",      "real",  T.EMERALD)
        self._mode_btn(modes_row, "Entry Simulation", "entry", T.TEAL)
        self._mode_btn(modes_row, "Exit Simulation",  "exit",  T.DEEP_BLUE)
        self._mode_btn(modes_row, "Image Test",       "image", T.ORANGE)

        # ================= CONTENT (2 columns) =========================
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew",
                     padx=T.PAD_XL, pady=(0, T.PAD_L))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)

        # ---------- Preview card (left) --------------------------------
        preview_card = Card(content)
        preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, T.PAD_M))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)

        prev_head = ctk.CTkFrame(preview_card, fg_color="transparent")
        prev_head.grid(row=0, column=0, sticky="ew",
                       padx=T.PAD_M, pady=(T.PAD_M, T.PAD_S))
        SectionTitle(prev_head, "Preview").pack(side="left")
        self.status_lbl = ctk.CTkLabel(
            prev_head, text="Idle", font=T.FONT_SMALL,
            text_color=T.TEXT_SECONDARY)
        self.status_lbl.pack(side="right")

        self.preview = ctk.CTkLabel(
            preview_card, text="No source selected.\nPick a mode above.",
            fg_color=T.NAVY, corner_radius=8,
            text_color=T.TEXT_MUTED_DARK)
        self.preview.grid(row=1, column=0, sticky="nsew",
                          padx=T.PAD_M, pady=(0, T.PAD_S))

        controls = ctk.CTkFrame(preview_card, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew",
                      padx=T.PAD_M, pady=(0, T.PAD_M))
        self._ctrl_btn(controls, "Play/Pause", self._toggle_play, T.TEAL)
        self._ctrl_btn(controls, "Stop",       self._stop_all,   T.RED)
        self._ctrl_btn(controls, "Capture",    self._capture,    T.ORANGE)
        self._ctrl_btn(controls, "Load File…", self._load_custom, T.DEEP_BLUE)

        # ---------- Right column (capture + info) ----------------------
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        cap_card = Card(right)
        cap_card.grid(row=0, column=0, sticky="new", pady=(0, T.PAD_M))
        cap_card.grid_columnconfigure(0, weight=1)
        SectionTitle(cap_card, "Captured frame").grid(
            row=0, column=0, sticky="w", padx=T.PAD_M, pady=(T.PAD_M, T.PAD_S))
        self.capture_lbl = ctk.CTkLabel(
            cap_card, text="No frame captured yet.",
            fg_color=T.OFF_WHITE, text_color=T.TEXT_SECONDARY,
            corner_radius=8, height=200)
        self.capture_lbl.grid(row=1, column=0, sticky="ew",
                              padx=T.PAD_M, pady=(0, T.PAD_M))

        info_card = Card(right)
        info_card.grid(row=1, column=0, sticky="nsew")
        info_card.grid_columnconfigure(0, weight=1)
        SectionTitle(info_card, "Detection status").grid(
            row=0, column=0, sticky="nw", padx=T.PAD_M, pady=(T.PAD_M, T.PAD_S))
        
        # We will update this label dynamically
        self.info_lbl = ctk.CTkLabel(
            info_card,
            text="Waiting for stream...",
            font=T.FONT_BODY, text_color=T.TEXT_SECONDARY,
            justify="left", anchor="nw")
        self.info_lbl.grid(row=1, column=0, sticky="nw",
                           padx=T.PAD_M, pady=(0, T.PAD_M))

        self.after(200, self._refresh_sidebar_status)

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------
    def _mode_btn(self, parent, label, mode, color):
        btn = ctk.CTkButton(parent, text=label, width=160, height=38,
                            corner_radius=8, fg_color=color,
                            hover_color=T.NAVY, font=T.FONT_BODY,
                            command=lambda m=mode: self._select_mode(m))
        btn.pack(side="left", padx=(0, T.PAD_S))
        return btn

    def _ctrl_btn(self, parent, label, cmd, color):
        b = ctk.CTkButton(parent, text=label, width=110, height=34,
                          corner_radius=8, fg_color=color, hover_color=T.NAVY,
                          font=T.FONT_SMALL, command=cmd)
        b.pack(side="left", padx=(0, T.PAD_S))
        return b

    # ------------------------------------------------------------------
    # Mode selection
    # ------------------------------------------------------------------
    def _select_mode(self, mode):
        self._stop_all()
        self.mode = mode
        self._set_badge(mode)

        # Check detector status
        if not self.detector.is_ready():
            self._update_detection_ui(error=self.detector.error)
        else:
            self._update_detection_ui(waiting=True)

        try:
            if mode == "real":
                if not probe_webcam(0):
                    self._set_status("No webcam detected", error=True)
                    self._show_preview_message(
                        "No physical webcam found.\n"
                        "Switch to Entry/Exit Simulation or Image Test.")
                    return
                src = WebcamSource(0)
                self.grabber = FrameGrabber(src, loop_video=False)
                self.grabber.start()
                self._start_preview_loop()

            elif mode in ("entry", "exit"):
                self.sim = SimulationSession(f"{mode}_video")
                self.sim.load()
                self._start_preview_loop()

            elif mode == "image":
                self.sim = SimulationSession("image")
                self.sim.load()
                self._start_preview_loop()

        except CameraError as e:
            self._set_status("Error", error=True)
            self._show_preview_message(str(e))

    def _set_badge(self, mode):
        labels = {"real": ("LIVE CAMERA", T.EMERALD),
                  "entry": ("SIMULATION — ENTRY", T.ORANGE),
                  "exit": ("SIMULATION — EXIT", T.ORANGE),
                  "image": ("SIMULATION — IMAGE", T.ORANGE),
                  "none": ("MODE: NONE", T.TEXT_SECONDARY)}
        text, color = labels.get(mode, ("MODE: NONE", T.TEXT_SECONDARY))
        self.mode_badge.configure(text=f"  {text}  ", fg_color=color)

    # ------------------------------------------------------------------
    # Preview loop
    # ------------------------------------------------------------------
    def _start_preview_loop(self):
        self._cancel_preview()
        self._preview_job = self.after(30, self._preview_tick)

    def _cancel_preview(self):
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
            self._preview_job = None

    def _preview_tick(self):
        frame = None
        err = None
        if self.mode == "real" and self.grabber:
            frame = self.grabber.get_latest()
            err = self.grabber.get_error()
        elif self.sim and self.sim.grabber:
            frame = self.sim.get_frame()
            err = self.sim.error()

        if err:
            self._set_status(f"Error: {err}", error=True)
            self._cancel_preview()
            return

        if frame is not None:
            # Run detection if model is loaded
            if self.detector.is_ready():
                annotated, detections = self.detector.detect(frame)
                self._render_frame(annotated, self.preview)
                self._update_detection_ui(detections=detections)
            else:
                self._render_frame(frame, self.preview)
                self._update_detection_ui(error=self.detector.error)

        still_running = (
            (self.mode == "real" and self.grabber and self.grabber.is_running)
            or (self.sim and self.sim.grabber and self.sim.grabber.is_running)
        )
        if still_running:
            self._preview_job = self.after(30, self._preview_tick)
        else:
            self._preview_job = None

    def _render_frame(self, frame, target_label, max_w=760, max_h=480):
        target_label.update_idletasks()
        avail_w = max(target_label.winfo_width(), 320)
        avail_h = max(target_label.winfo_height(), 200)
        max_w = min(max_w, avail_w - 8)
        max_h = min(max_h, avail_h - 8)

        h, w = frame.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).resize((new_w, new_h), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil,
                                size=(new_w, new_h))
        target_label.configure(image=ctk_img, text="")
        if target_label is self.preview:
            self._ctk_preview_img = ctk_img
        else:
            target_label._ctk_img = ctk_img

    def _show_preview_message(self, msg):
        self.preview.configure(image="", text=msg,
                               text_color=T.TEXT_MUTED_DARK)

    # ------------------------------------------------------------------
    # UI Updates
    # ------------------------------------------------------------------
    def _update_detection_ui(self, detections=None, error=None, waiting=False):
        if error:
            self.info_lbl.configure(text=f"⚠️ {error}", text_color=T.RED)
        elif waiting:
            self.info_lbl.configure(text="Waiting for vehicle...", text_color=T.TEXT_SECONDARY)
        elif detections is not None:
            if not detections:
                self.info_lbl.configure(text="No vehicles detected.", text_color=T.TEXT_SECONDARY)
            else:
                # Build a text summary of detected vehicles
                lines = [f"Detected {len(detections)} vehicle(s):"]
                for d in detections:
                    lines.append(f" • {d['class_name']} ({d['confidence']*100:.1f}%)")
                lines.append("\n*(Plate OCR arrives in Phase 5)*")
                self.info_lbl.configure(text="\n".join(lines), text_color=T.TEXT_PRIMARY)

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------
    def _toggle_play(self):
        if self.sim and self.sim.grabber:
            if self.sim.is_playing():
                self.sim.pause()
                self._set_status("Paused")
            else:
                self.sim.play()
                self._set_status("Playing")
                if self._preview_job is None:
                    self._start_preview_loop()
        elif self.mode == "real":
            self._set_status("Real camera is always live (no pause).")

    def _stop_all(self):
        self._cancel_preview()
        if self.grabber:
            self.grabber.stop()
            self.grabber = None
        if self.sim:
            self.sim.stop()
            self.sim = None
        self._set_status("Stopped")
        self._show_preview_message("Stopped. Pick a mode above.")
        self._set_badge("none")
        self.mode = "none"
        self._update_detection_ui(waiting=True)

    def _capture(self):
        frame = None
        if self.sim:
            frame = self.sim.capture()
        elif self.mode == "real" and self.grabber:
            frame = self.grabber.get_latest()

        if frame is None:
            self._set_status("Nothing to capture", error=True)
            return
        
        # Annotate the captured frame too, so the user sees the boxes
        if self.detector.is_ready():
            annotated, _ = self.detector.detect(frame)
            self._render_frame(annotated, self.capture_lbl, max_w=340, max_h=200)
        else:
            self._render_frame(frame, self.capture_lbl, max_w=340, max_h=200)
            
        self._set_status("Frame captured")

    def _load_custom(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Load video or image",
            filetypes=[("Video", "*.mp4 *.avi *.mov"),
                       ("Image", "*.jpg *.jpeg *.png"),
                       ("All files", "*.*")])
        if not path:
            return
        self._stop_all()
        try:
            if path.lower().endswith((".mp4", ".avi", ".mov")):
                self.mode = "entry"
                self.sim = SimulationSession("entry_video", path=path)
                self.sim.load()
                self._set_badge("entry")
                self._start_preview_loop()
            else:
                self.mode = "image"
                self.sim = SimulationSession("image", path=path)
                self.sim.load()
                self._set_badge("image")
                self._start_preview_loop()
            self._set_status(f"Loaded: {os.path.basename(path)}")
        except CameraError as e:
            self._set_status("Load failed", error=True)
            self._show_preview_message(str(e))

    def _set_status(self, text, error=False):
        color = T.RED if error else T.TEXT_SECONDARY
        self.status_lbl.configure(text=text, text_color=color)

    def _refresh_sidebar_status(self):
        try:
            app = self.winfo_toplevel()
            if hasattr(app, "sidebar"):
                ok = probe_webcam(0)
                app.sidebar.set_camera_status(
                    "Camera detected" if ok else "No camera — use simulation",
                    ok=ok)
        except Exception:
            pass