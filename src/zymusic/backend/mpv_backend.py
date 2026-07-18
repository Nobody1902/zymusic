import atexit
import json
import os
import socket
import subprocess
import threading
import time

from zymusic.backend.constants import MPV_SOCKET_TEMPLATE


class MpvBackend:
    def __init__(
        self, on_track_end=None, on_state_change=None, on_position=None, on_error=None
    ):
        self._proc: subprocess.Popen | None = None
        self._sock_path: str | None = None
        self._sock: socket.socket | None = None
        self._reader_thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()
        self._state = "idle"
        self._position = 0.0
        self._duration = 0.0
        self._volume = 100
        self._muted = False
        self._speed = 1.0

        self._on_track_end = on_track_end
        self._on_state_change = on_state_change
        self._on_position = on_position
        self._on_error = on_error

        atexit.register(self.shutdown)

    def _make_socket_path(self):
        return MPV_SOCKET_TEMPLATE.format(pid=os.getpid())

    def start(self):
        if self._proc is not None and self._proc.poll() is None:
            return
        self._sock_path = self._make_socket_path()
        try:
            os.unlink(self._sock_path)
        except OSError:
            pass
        try:
            self._proc = subprocess.Popen(
                [
                    "mpv",
                    "--no-video",
                    "--audio-display=no",
                    "--volume=100",
                    "--keep-open=no",
                    f"--input-ipc-server={self._sock_path}",
                    "--idle=yes",
                    "--term-status-msg=",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print("mpv not found on PATH")
            raise

        for _ in range(100):
            if os.path.exists(self._sock_path):
                break
            time.sleep(0.05)
        else:
            print("mpv IPC socket did not appear")
            raise RuntimeError("mpv IPC socket did not appear")

        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.settimeout(5.0)
        self._sock.connect(self._sock_path)
        self._running = True
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

        self._command(["observe_property", 1, "time-pos"])
        self._command(["observe_property", 2, "duration"])
        self._command(["observe_property", 3, "pause"])
        self._command(["observe_property", 4, "volume"])
        self._command(["observe_property", 5, "mute"])
        self._command(["observe_property", 6, "speed"])

    def _read_loop(self):
        if not self._sock:
            return

        buf = ""
        while self._running:
            try:
                data = self._sock.recv(4096).decode()
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._handle_event(line)
            except socket.timeout:
                continue
            except OSError:
                break
        self._on_disconnect()

    def _handle_event(self, line):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            return

        event = ev.get("event")

        if event == "end-file":
            reason = ev.get("reason")
            if reason == "error":
                file_name = ev.get("file", "unknown")
                print(f"mpv playback error: {file_name}")
                if self._on_error:
                    self._on_error(file_name)
            if reason != "stop":
                self._state = "idle"
            if self._on_track_end and reason != "stop":
                self._on_track_end()

        elif event == "property-change":
            name = ev.get("name")
            data = ev.get("data")
            if name == "time-pos" and data is not None:
                self._position = float(data)
                if self._on_position:
                    self._on_position(self._position, self._duration)
            elif name == "duration" and data is not None:
                self._duration = float(data)
            elif name == "pause":
                paused = bool(data)
                prev = self._state
                self._state = "paused" if paused else "playing"
                if prev != self._state and self._on_state_change:
                    self._on_state_change(self._state)
            elif name == "volume" and data is not None:
                self._volume = int(data)
            elif name == "mute" and data is not None:
                self._muted = bool(data)
            elif name == "speed" and data is not None:
                self._speed = float(data)

    def _command(self, cmd):
        with self._lock:
            if not self._sock:
                return
            payload = json.dumps({"command": cmd}) + "\n"
            try:
                self._sock.sendall(payload.encode())
            except OSError:
                pass

    def load(self, url):
        self._command(["loadfile", url])
        self._state = "loading"

    def play(self):
        self._command(["set_property", "pause", False])

    def pause(self):
        self._command(["set_property", "pause", True])

    def stop(self):
        self._command(["stop"])
        self._state = "idle"

    def seek_absolute(self, seconds):
        self._command(["seek", seconds, "absolute"])

    def seek_relative(self, seconds):
        self._command(["seek", seconds, "relative"])

    def seek_percent(self, percent):
        self._command(["seek", percent, "absolute-percent"])

    def set_volume(self, vol):
        vol = max(0, min(100, int(vol)))
        self._command(["set_property", "volume", vol])

    def set_mute(self, muted):
        self._command(["set_property", "mute", bool(muted)])

    def toggle_mute(self):
        self._command(["cycle", "mute"])

    def set_speed(self, speed):
        speed = max(0.25, min(3.0, float(speed)))
        self._command(["set_property", "speed", speed])

    def set_audio_device(self, device):
        self._command(["set_property", "audio-device", device])

    @property
    def state(self):
        return self._state

    @property
    def position(self):
        return self._position

    @property
    def duration(self):
        return self._duration

    @property
    def progress(self):
        if self._duration > 0:
            return self._position / self._duration
        return 0.0

    @property
    def volume(self):
        return self._volume / 100.0

    @property
    def is_muted(self):
        return self._muted

    @property
    def speed(self):
        return self._speed

    @property
    def is_alive(self):
        return self._proc is not None and self._proc.poll() is None

    def _on_disconnect(self):
        self._running = False
        self._state = "idle"

    def shutdown(self):
        self._running = False
        if self._sock:
            try:
                self._command(["quit"])
            except Exception:
                pass
        if self._proc:
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        try:
            if self._sock_path:
                os.unlink(self._sock_path)
        except Exception:
            pass
