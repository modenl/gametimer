import os
import sys
import time
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

try:
    import psutil
except ImportError:
    psutil = None


ADMIN_PASSWORD_DEFAULT = "123456"
COOLDOWN_SECONDS = 60 * 60
DEFAULT_SESSION_MINUTES = 40.0


def platform_name():
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "mac"
    return "other"


def now_ts():
    return time.time()


class GameConfig:
    def __init__(
        self,
        name,
        identifiers,
        path_candidates,
        kill_process_on_timeout=True,
        track_process_state=True,
    ):
        self.name = name
        self.identifiers = identifiers
        self.path_candidates = path_candidates
        self.kill_process_on_timeout = kill_process_on_timeout
        self.track_process_state = track_process_state


class GameState:
    def __init__(self, config):
        self.config = config
        self.path_var = tk.StringVar(value="")
        self.time_var = tk.StringVar(value=f"{DEFAULT_SESSION_MINUTES:.2f}")
        self.status_var = tk.StringVar(value="Ready")
        self.remaining_var = tk.StringVar(value="--:--")
        self.running = False
        self.popen = None
        self.pid = None
        self.end_ts = None
        self.start_ts = None
        self.path_entry = None
        self.time_entry = None
        self.browse_btn = None
        self.start_btn = None
        self.stop_btn = None

    def reset_session(self):
        self.running = False
        self.popen = None
        self.pid = None
        self.end_ts = None
        self.start_ts = None
        self.remaining_var.set("--:--")


class CanvasButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command,
        bg,
        fg,
        active_bg,
        active_fg,
        disabled_bg="#4b5563",
        disabled_fg="#9ca3af",
    ):
        font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        text_w = font.measure(text)
        width = max(90, text_w + 24)
        height = 34

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg"),
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.default_bg = bg
        self.default_fg = fg
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.disabled_bg = disabled_bg
        self.disabled_fg = disabled_fg
        self.command = command
        self.text = text
        self.font = font
        self.enabled = True

        self.rect = self.create_rectangle(
            0, 0, width, height, fill=self.default_bg, outline=self.default_bg
        )
        self.text_id = self.create_text(
            width / 2,
            height / 2,
            text=self.text,
            fill=self.default_fg,
            font=self.font,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, _event=None):
        if not self.enabled:
            return
        self.itemconfigure(self.rect, fill=self.active_bg, outline=self.active_bg)
        self.itemconfigure(self.text_id, fill=self.active_fg)

    def _on_leave(self, _event=None):
        self._apply_default_style()

    def _on_press(self, _event=None):
        if not self.enabled:
            return
        self.itemconfigure(self.rect, fill=self.default_bg, outline=self.default_bg)
        self.itemconfigure(self.text_id, fill=self.default_fg)

    def _on_release(self, event=None):
        if not self.enabled:
            return
        self.itemconfigure(self.rect, fill=self.active_bg, outline=self.active_bg)
        self.itemconfigure(self.text_id, fill=self.active_fg)
        if self.command is None:
            return
        if event is None:
            self.command()
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is self:
            self.command()

    def _apply_default_style(self):
        if self.enabled:
            self.itemconfigure(self.rect, fill=self.default_bg, outline=self.default_bg)
            self.itemconfigure(self.text_id, fill=self.default_fg)
            self.configure(cursor="hand2")
        else:
            self.itemconfigure(self.rect, fill=self.disabled_bg, outline=self.disabled_bg)
            self.itemconfigure(self.text_id, fill=self.disabled_fg)
            self.configure(cursor="arrow")

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._apply_default_style()


class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Timer")
        self.root.configure(bg="#0f1115")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<F11>", self.toggle_fullscreen)

        self.admin_password = ADMIN_PASSWORD_DEFAULT
        self.cooldown_until = None

        self.games = self.build_games()
        self.game_states = [GameState(cfg) for cfg in self.games]

        self.overlay = None
        self.overlay_label = None

        self.build_ui()
        self.detect_paths()
        self.tick()

    def build_games(self):
        system = platform_name()
        chrome_paths = []
        minecraft_paths = []

        if system == "windows":
            chrome_paths = [
                r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
            minecraft_paths = [
                r"C:\\Program Files (x86)\\Minecraft Launcher\\MinecraftLauncher.exe",
                r"C:\\Program Files\\Minecraft Launcher\\MinecraftLauncher.exe",
            ]
        elif system == "mac":
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
            minecraft_paths = [
                "/Applications/Minecraft.app/Contents/MacOS/Minecraft",
                "/Applications/Minecraft Launcher.app/Contents/MacOS/Minecraft Launcher",
            ]

        games = [
            GameConfig(
                name="Minecraft",
                identifiers=["minecraft", "javaw", "minecraftlauncher"],
                path_candidates=minecraft_paths,
                kill_process_on_timeout=True,
                track_process_state=True,
            ),
            GameConfig(
                name="Chrome",
                identifiers=["chrome", "google chrome"],
                path_candidates=chrome_paths,
                kill_process_on_timeout=False,
                track_process_state=False,
            ),
        ]

        return games

    def make_button(self, parent, text, command, bg, fg, active_bg, active_fg):
        return CanvasButton(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            active_bg=active_bg,
            active_fg=active_fg,
        )

    def build_ui(self):
        header = tk.Frame(self.root, bg="#0f1115")
        header.pack(fill="x", padx=24, pady=16)

        title = tk.Label(
            header,
            text="PC Timer",
            fg="#ffffff",
            bg="#0f1115",
            font=("Helvetica", 28, "bold"),
        )
        title.pack(side="left")

        self.cooldown_label = tk.Label(
            header,
            text="Cooldown: None",
            fg="#94a3b8",
            bg="#0f1115",
            font=("Helvetica", 14),
        )
        self.cooldown_label.pack(side="right")

        button_row = tk.Frame(self.root, bg="#0f1115")
        button_row.pack(fill="x", padx=24)

        self.rescan_btn = self.make_button(
            button_row,
            text="Rescan Paths",
            command=self.detect_paths,
            bg="#1f2937",
            fg="#e2e8f0",
            active_bg="#334155",
            active_fg="#f8fafc",
        )
        self.rescan_btn.pack(side="left")

        self.admin_btn = self.make_button(
            button_row,
            text="Admin Reset Cooldown",
            command=self.prompt_admin_reset,
            bg="#3b0764",
            fg="#fdf4ff",
            active_bg="#581c87",
            active_fg="#fdf4ff",
        )
        self.admin_btn.pack(side="right")

        list_frame = tk.Frame(self.root, bg="#0f1115")
        list_frame.pack(fill="both", expand=True, padx=24, pady=16)

        headers = [
            "Game",
            "Path",
            "Session (min)",
            "Status",
            "Remaining",
            "Actions",
        ]
        for col, text in enumerate(headers):
            label = tk.Label(
                list_frame,
                text=text,
                fg="#94a3b8",
                bg="#0f1115",
                font=("Helvetica", 12, "bold"),
            )
            label.grid(row=0, column=col, sticky="w", padx=6, pady=4)

        for idx, state in enumerate(self.game_states, start=1):
            name_label = tk.Label(
                list_frame,
                text=state.config.name,
                fg="#f8fafc",
                bg="#0f1115",
                font=("Helvetica", 14),
            )
            name_label.grid(row=idx, column=0, sticky="w", padx=6, pady=8)

            path_entry = tk.Entry(
                list_frame,
                textvariable=state.path_var,
                width=56,
                bg="#111827",
                fg="#e2e8f0",
                insertbackground="#e2e8f0",
                relief="flat",
            )
            path_entry.grid(row=idx, column=1, sticky="w", padx=6, pady=8)
            state.path_entry = path_entry

            time_entry = tk.Entry(
                list_frame,
                textvariable=state.time_var,
                width=10,
                bg="#111827",
                fg="#e2e8f0",
                insertbackground="#e2e8f0",
                relief="flat",
                justify="center",
            )
            time_entry.grid(row=idx, column=2, sticky="w", padx=6, pady=8)
            state.time_entry = time_entry
            state.path_var.trace_add("write", lambda *_: self.refresh_controls())
            state.time_var.trace_add("write", lambda *_: self.refresh_controls())

            status_label = tk.Label(
                list_frame,
                textvariable=state.status_var,
                fg="#e2e8f0",
                bg="#0f1115",
                font=("Helvetica", 12),
            )
            status_label.grid(row=idx, column=3, sticky="w", padx=6, pady=8)

            remaining_label = tk.Label(
                list_frame,
                textvariable=state.remaining_var,
                fg="#fef08a",
                bg="#0f1115",
                font=("Helvetica", 12),
            )
            remaining_label.grid(row=idx, column=4, sticky="w", padx=6, pady=8)

            action_frame = tk.Frame(list_frame, bg="#0f1115")
            action_frame.grid(row=idx, column=5, sticky="w", padx=6, pady=8)

            browse_btn = self.make_button(
                action_frame,
                text="Set Path",
                command=lambda s=state: self.choose_path(s),
                bg="#1f2937",
                fg="#e2e8f0",
                active_bg="#334155",
                active_fg="#f8fafc",
            )
            browse_btn.pack(side="left", padx=2)
            state.browse_btn = browse_btn

            start_btn = self.make_button(
                action_frame,
                text="Start",
                command=lambda s=state: self.start_game(s),
                bg="#065f46",
                fg="#ecfdf5",
                active_bg="#047857",
                active_fg="#ecfdf5",
            )
            start_btn.pack(side="left", padx=2)
            state.start_btn = start_btn

            stop_btn = self.make_button(
                action_frame,
                text="Stop",
                command=lambda s=state: self.stop_game(s, manual=True),
                bg="#7f1d1d",
                fg="#fef2f2",
                active_bg="#991b1b",
                active_fg="#fef2f2",
            )
            stop_btn.pack(side="left", padx=2)
            state.stop_btn = stop_btn

        footer = tk.Label(
            self.root,
            text="F11 toggles fullscreen for testing.",
            fg="#475569",
            bg="#0f1115",
            font=("Helvetica", 10),
        )
        footer.pack(side="bottom", pady=8)

        if psutil is None:
            messagebox.showwarning(
                "Missing Dependency",
                "psutil is required for process detection. Install it with: pip install psutil",
            )
        self.refresh_controls()

    def toggle_fullscreen(self, _event=None):
        current = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current)

    def detect_paths(self):
        for state in self.game_states:
            found = ""
            for path in state.config.path_candidates:
                if path and os.path.exists(path):
                    found = path
                    break
            if found:
                state.path_var.set(found)
                state.status_var.set("Ready")
            else:
                if not state.path_var.get().strip():
                    state.status_var.set("Path not found")
        self.refresh_controls()

    def choose_path(self, state):
        initial_dir = os.path.dirname(state.path_var.get()) if state.path_var.get() else None
        selected = filedialog.askopenfilename(initialdir=initial_dir or None)
        if selected:
            state.path_var.set(selected)
            state.status_var.set("Ready")
        self.refresh_controls()

    def parse_minutes(self, value):
        try:
            minutes = float(value)
        except ValueError:
            return None
        if minutes <= 0:
            return None
        return round(minutes, 2)

    def cooldown_active(self):
        return self.cooldown_until is not None and now_ts() < self.cooldown_until

    def cooldown_remaining(self):
        if not self.cooldown_until:
            return 0
        return max(0, int(self.cooldown_until - now_ts()))

    def any_game_running(self):
        return any(state.running for state in self.game_states)

    def refresh_controls(self):
        cooldown_on = self.cooldown_active()
        any_running = self.any_game_running()

        for state in self.game_states:
            has_valid_time = self.parse_minutes(state.time_var.get()) is not None
            has_valid_path = bool(state.path_var.get().strip()) and os.path.exists(
                state.path_var.get().strip()
            )
            can_start = (
                (not state.running)
                and (not cooldown_on)
                and has_valid_time
                and has_valid_path
                and (psutil is not None)
            )
            can_stop = state.running
            can_browse = not state.running

            if state.path_entry is not None:
                state.path_entry.config(state="normal" if can_browse else "disabled")
            if state.time_entry is not None:
                state.time_entry.config(state="normal" if can_browse else "disabled")
            if state.start_btn is not None:
                state.start_btn.set_enabled(can_start)
            if state.stop_btn is not None:
                state.stop_btn.set_enabled(can_stop)
            if state.browse_btn is not None:
                state.browse_btn.set_enabled(can_browse)

        if hasattr(self, "admin_btn"):
            self.admin_btn.set_enabled(cooldown_on and (not any_running))
        if hasattr(self, "rescan_btn"):
            self.rescan_btn.set_enabled(not any_running)

    def start_cooldown_if_idle(self):
        if not self.any_game_running():
            self.start_cooldown()

    def start_game(self, state):
        if psutil is None:
            state.status_var.set("psutil required")
            self.refresh_controls()
            return
        if self.cooldown_active():
            remaining = self.cooldown_remaining()
            state.status_var.set(f"Cooldown {self.format_seconds(remaining)}")
            self.refresh_controls()
            return

        if state.running:
            state.status_var.set("Already running")
            self.refresh_controls()
            return

        path = state.path_var.get().strip()
        if not path or not os.path.exists(path):
            state.status_var.set("Invalid path")
            self.refresh_controls()
            return

        minutes = self.parse_minutes(state.time_var.get())
        if minutes is None:
            state.status_var.set("Invalid time")
            self.refresh_controls()
            return

        duration = minutes * 60
        popen = None
        pid = None

        try:
            if platform_name() == "mac" and path.endswith(".app"):
                popen = subprocess.Popen(["open", "-a", path])
            else:
                popen = subprocess.Popen([path])
            pid = popen.pid
        except Exception:
            state.status_var.set("Launch failed")
            self.refresh_controls()
            return

        state.running = True
        state.popen = popen
        state.pid = pid
        state.start_ts = now_ts()
        state.end_ts = state.start_ts + duration
        state.status_var.set("Running")
        state.remaining_var.set(self.format_seconds(int(duration)))
        self.refresh_controls()

    def stop_game(self, state, manual=False):
        if not state.running:
            state.status_var.set("Not running")
            self.refresh_controls()
            return

        if state.config.kill_process_on_timeout:
            self.kill_game_process(state)
        state.status_var.set("Stopped")
        state.reset_session()

        if manual:
            self.start_cooldown_if_idle()
        self.refresh_controls()

    def start_cooldown(self):
        self.cooldown_until = now_ts() + COOLDOWN_SECONDS

    def kill_game_process(self, state):
        if psutil is None:
            return
        if not state.config.kill_process_on_timeout:
            return

        targets = []
        if state.pid and psutil.pid_exists(state.pid):
            try:
                targets.append(psutil.Process(state.pid))
            except psutil.Error:
                pass

        identifiers = [i.lower() for i in state.config.identifiers]
        for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
            try:
                name = (proc.info.get("name") or "").lower()
                exe = (proc.info.get("exe") or "").lower()
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                haystack = f"{name} {exe} {cmd}"
                if any(token in haystack for token in identifiers):
                    targets.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for proc in targets:
            try:
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        gone, alive = psutil.wait_procs(targets, timeout=2)
        for proc in alive:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def format_seconds(self, seconds):
        minutes = seconds // 60
        remaining = seconds % 60
        return f"{minutes:02d}:{remaining:02d}"

    def update_overlay(self, remaining_seconds):
        if remaining_seconds is None:
            if self.overlay is not None:
                self.overlay.destroy()
                self.overlay = None
                self.overlay_label = None
            return

        if self.overlay is None:
            self.overlay = tk.Toplevel(self.root)
            self.overlay.overrideredirect(True)
            self.overlay.attributes("-topmost", True)
            self.overlay.attributes("-alpha", 0.75)
            self.overlay.configure(bg="#0b0f1a")
            self.overlay_label = tk.Label(
                self.overlay,
                text="",
                fg="#f8fafc",
                bg="#0b0f1a",
                font=("Helvetica", 24, "bold"),
                padx=16,
                pady=10,
            )
            self.overlay_label.pack()

        self.overlay_label.configure(text=self.format_seconds(int(remaining_seconds)))
        self.overlay.update_idletasks()
        width = self.overlay.winfo_width()
        height = self.overlay.winfo_height()
        screen_w = self.overlay.winfo_screenwidth()
        x = max(0, screen_w - width - 24)
        y = 24
        self.overlay.geometry(f"{width}x{height}+{x}+{y}")

    def ensure_fullscreen(self):
        self.root.attributes("-fullscreen", True)
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(200, lambda: self.root.attributes("-topmost", False))

    def prompt_admin_reset(self):
        if self.any_game_running():
            return
        if not self.cooldown_active():
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Admin Reset")
        dialog.configure(bg="#0f1115")
        dialog.geometry("320x160")
        dialog.transient(self.root)
        dialog.grab_set()

        label = tk.Label(
            dialog,
            text="Enter admin password",
            fg="#e2e8f0",
            bg="#0f1115",
            font=("Helvetica", 12),
        )
        label.pack(pady=12)

        entry = tk.Entry(dialog, show="*", bg="#111827", fg="#f8fafc", relief="flat")
        entry.pack(pady=6)
        entry.focus_set()

        status = tk.Label(dialog, text="", fg="#f87171", bg="#0f1115")
        status.pack(pady=4)

        def submit():
            if entry.get() == self.admin_password:
                self.cooldown_until = None
                self.refresh_controls()
                dialog.destroy()
            else:
                status.config(text="Wrong password")

        submit_btn = self.make_button(
            dialog,
            text="Reset Cooldown",
            command=submit,
            bg="#065f46",
            fg="#ecfdf5",
            active_bg="#047857",
            active_fg="#ecfdf5",
        )
        submit_btn.pack(pady=8)

    def tick(self):
        now = now_ts()
        soonest = None

        for state in self.game_states:
            if state.running and state.end_ts:
                if state.config.track_process_state and (not self.is_process_running(state)):
                    state.status_var.set("Process closed")
                    state.reset_session()
                    self.start_cooldown_if_idle()
                    continue
                remaining = int(state.end_ts - now)
                if remaining <= 0:
                    still_running = (
                        self.is_process_running(state)
                        if state.config.kill_process_on_timeout
                        else False
                    )
                    if still_running and state.config.kill_process_on_timeout:
                        self.kill_game_process(state)
                    state.status_var.set("Session ended")
                    state.reset_session()
                    self.start_cooldown_if_idle()
                    self.ensure_fullscreen()
                else:
                    state.remaining_var.set(self.format_seconds(remaining))
                    if soonest is None or remaining < soonest:
                        soonest = remaining
            elif not state.running:
                if state.remaining_var.get() == "--:--":
                    pass

        if self.cooldown_active():
            remaining_cd = self.cooldown_remaining()
            self.cooldown_label.config(
                text=f"Cooldown: {self.format_seconds(remaining_cd)}"
            )
        else:
            self.cooldown_label.config(text="Cooldown: None")

        if soonest is not None and soonest <= 60:
            self.update_overlay(soonest)
        else:
            self.update_overlay(None)

        self.refresh_controls()
        self.root.after(500, self.tick)

    def is_process_running(self, state):
        if psutil is None:
            return True

        if state.pid and psutil.pid_exists(state.pid):
            try:
                proc = psutil.Process(state.pid)
                if proc.is_running():
                    return True
            except psutil.Error:
                pass

        identifiers = [i.lower() for i in state.config.identifiers]
        for proc in psutil.process_iter(["name", "exe", "cmdline"]):
            try:
                name = (proc.info.get("name") or "").lower()
                exe = (proc.info.get("exe") or "").lower()
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                haystack = f"{name} {exe} {cmd}"
                if any(token in haystack for token in identifiers):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return False


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()
