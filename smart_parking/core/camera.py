
import os
import threading
import time
import cv2


class CameraError(Exception):
    pass


class CameraSource:
    
    def __init__(self, label=""):
        self.label = label
        self._cap = None
        self._last_frame = None

    # Public API --------------------------------------------------------
    def open(self):
        return self._open()

    def read(self):
        
        ok, frame = self._read()
        if ok and frame is not None:
            self._last_frame = frame
        return ok, frame

    def release(self):
        self._release()
        self._cap = None

    @property
    def last_frame(self):
        return self._last_frame

    def is_open(self):
        return self._cap is not None and getattr(self._cap, "isOpened", lambda: False)()

    def fps(self):
        return 0.0

    # Subclass hooks ----------------------------------------------------
    def _open(self):   raise NotImplementedError
    def _read(self):   raise NotImplementedError
    def _release(self):raise NotImplementedError


class WebcamSource(CameraSource):
    def __init__(self, index=0):
        super().__init__(f"Webcam {index}")
        self.index = index

    def _open(self):
        cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)  # DSHOW on Windows is fastest
        if not cap.isOpened():
            # Try default backend as fallback
            cap.release()
            cap = cv2.VideoCapture(self.index)
        if not cap.isOpened():
            raise CameraError(
                f"No webcam detected at index {self.index}. "
                "Use Simulation mode instead."
            )
        self._cap = cap
        return True

    def _read(self):
        if self._cap is None:
            return False, None
        return self._cap.read()

    def _release(self):
        if self._cap is not None:
            self._cap.release()

    def fps(self):
        return self._cap.get(cv2.CAP_PROP_FPS) if self._cap else 0.0


class VideoFileSource(CameraSource):
    def __init__(self, path, loop=False):
        super().__init__(f"Video: {os.path.basename(path)}")
        self.path = path
        self.loop = loop
        self._frame_count = 0
        self._fps = 0.0

    def _open(self):
        if not os.path.exists(self.path):
            raise CameraError(
                f"Video file not found: {self.path}\n"
                "Drop an MP4 into assets/videos/ or use Load Video."
            )
        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            raise CameraError(f"Cannot open video: {self.path}")
        self._cap = cap
        self._frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        return True

    def _read(self):
        if self._cap is None:
            return False, None
        ok, frame = self._cap.read()
        if not ok and self.loop:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return ok, frame

    def _release(self):
        if self._cap is not None:
            self._cap.release()

    def fps(self):
        return self._fps

    def frame_count(self):
        return self._frame_count


class ImageSource(CameraSource):
    def __init__(self, path):
        super().__init__(f"Image: {os.path.basename(path)}")
        self.path = path
        self._sent = False

    def _open(self):
        if not os.path.exists(self.path):
            raise CameraError(
                f"Image not found: {self.path}\n"
                "Drop a JPG into assets/images/ or use Load Image."
            )
        # Don't store via cv2.VideoCapture — read directly
        self._cap = True  # marker: is_open() will return True
        return True

    def _read(self):
        if self._sent:
            return False, self._last_frame
        img = cv2.imread(self.path)
        if img is None:
            raise CameraError(f"Cannot read image: {self.path}")
        self._sent = True
        return True, img

    def _release(self):
        self._sent = False
        self._cap = None

    def is_open(self):
        return self._cap is True


class FrameGrabber:
    
    def __init__(self, source: CameraSource, loop_video=True):
        self.source = source
        self.loop_video = loop_video
        self._thread = None
        self._running = False
        self._paused = False
        self._lock = threading.Lock()
        self._latest = None
        self._error = None
        self._fps = 0.0

    # Controls ----------------------------------------------------------
    def start(self):
        self.source.open()
        self._running = True
        self._paused = False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        try:
            self.source.release()
        except Exception:
            pass

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    @property
    def is_running(self):
        return self._running

    @property
    def is_paused(self):
        return self._paused

    def get_latest(self):
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    def get_error(self):
        return self._error

    def fps(self):
        return self._fps

    # Internal ----------------------------------------------------------
    def _loop(self):
        fps = self.source.fps() or 25.0
        delay = 1.0 / fps
        try:
            while self._running:
                if self._paused:
                    time.sleep(0.05)
                    continue
                ok, frame = self.source.read()
                if not ok:
                    if isinstance(self.source, VideoFileSource) and self.loop_video:
                        self.source._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    if isinstance(self.source, ImageSource):
                        time.sleep(0.1)  # image: hold last frame
                        continue
                    self._error = "Stream ended or unreadable."
                    break
                with self._lock:
                    self._latest = frame
                self._fps = fps
                time.sleep(delay)
        except CameraError as e:
            self._error = str(e)
        except Exception as e:
            self._error = f"Grabber crashed: {e}"
        finally:
            self._running = False


def probe_webcam(index=0):
    
    try:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(index)
        ok = cap.isOpened()
        if ok:
            ret, _ = cap.read()
            ok = ret
        cap.release()
        return ok
    except Exception:
        return False