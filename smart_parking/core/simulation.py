
import os
from .camera import VideoFileSource, ImageSource, FrameGrabber, CameraError
from core import database as db


DEFAULT_ENTRY_VIDEO = "assets/videos/entry_demo.mp4"
DEFAULT_EXIT_VIDEO  = "assets/videos/exit_demo.mp4"
DEFAULT_IMAGE_1     = "assets/images/nn.png"
DEFAULT_IMAGE_2     = "assets/images/car_sample_2.jpg"
DEFAULT_PLATE_IMG   = "assets/images/plate_sample_1.jpg"


def _resolve(path):
    """Resolve relative to project root (this file lives in core/)."""
    if os.path.isabs(path):
        return path
    root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root, path)


class SimulationSession:
    """
    One simulation panel's state: video or image, playing or paused, plus
    the last captured frame. Does NOT fake detection — that's Phase 4's job.
    """
    def __init__(self, kind, path=None):
        """kind: 'entry_video' | 'exit_video' | 'image'."""
        self.kind = kind
        self.path = _resolve(path) if path else self._default_path(kind)
        self.source = None
        self.grabber = None
        self.captured_frame = None
        self.captured_meta = {}

    @staticmethod
    def _default_path(kind):
        mapping = {
            "entry_video": DEFAULT_ENTRY_VIDEO,
            "exit_video":  DEFAULT_EXIT_VIDEO,
            "image":       DEFAULT_IMAGE_1,
        }
        return _resolve(mapping.get(kind, ""))

    # Lifecycle ---------------------------------------------------------
    def load(self):
        """Open the source. Raises CameraError if file missing/broken."""
        self.stop()
        if self.kind in ("entry_video", "exit_video"):
            self.source = VideoFileSource(self.path, loop=True)
        elif self.kind == "image":
            self.source = ImageSource(self.path)
        else:
            raise CameraError(f"Unknown simulation kind: {self.kind}")

        self.grabber = FrameGrabber(self.source, loop_video=True)
        self.grabber.start()
        return True

    def play(self):
        if self.grabber:
            self.grabber.resume()

    def pause(self):
        if self.grabber:
            self.grabber.pause()

    def stop(self):
        if self.grabber:
            self.grabber.stop()
            self.grabber = None
        self.source = None

    # Capture -----------------------------------------------------------
    def capture(self):
        """Save the current frame in memory. Returns ndarray or None."""
        if self.grabber is None:
            return None
        frame = self.grabber.get_latest()
        if frame is not None:
            self.captured_frame = frame.copy()
            self.captured_meta = {"kind": self.kind, "path": self.path}
        return self.captured_frame

    # Info --------------------------------------------------------------
    def get_frame(self):
        return self.grabber.get_latest() if self.grabber else None

    def error(self):
        return self.grabber.get_error() if self.grabber else None

    def is_playing(self):
        return bool(self.grabber and self.grabber.is_running
                    and not self.grabber.is_paused)


def probe_assets():
    """Report which default assets exist. Used to warn the user."""
    report = {}
    for label, rel in [
        ("entry_demo.mp4",     DEFAULT_ENTRY_VIDEO),
        ("exit_demo.mp4",      DEFAULT_EXIT_VIDEO),
        ("car_sample_1.jpg",   DEFAULT_IMAGE_1),
        ("car_sample_2.jpg",   DEFAULT_IMAGE_2),
        ("plate_sample_1.jpg", DEFAULT_PLATE_IMG),
    ]:
        report[label] = os.path.exists(_resolve(rel))
    return report