#!/usr/bin/env python3

import os
import platform
import subprocess
import sys
import threading
import json
import tkinter as tk
from tkinter import ttk

from . import cli
from . import backend
from . import spotify_backup
from . import ytmusic_credentials
from typing import Callable


THEMES = {
    "dark": {
        "background": "#101820",
        "surface": "#17232b",
        "text": "#d7f9e9",
        "muted": "#8fb5a4",
        "accent": "#20e3a2",
        "button": "#245847",
        "select": "#1d3d34",
        "select_text": "#d7f9e9",
        "border": "#2f765d",
    },
    "light": {
        "background": "#e8f2ec",
        "surface": "#f7fcf8",
        "text": "#10261d",
        "muted": "#426456",
        "accent": "#087f55",
        "button": "#b8e3cd",
        "select": "#cceedd",
        "select_text": "#10261d",
        "border": "#8ac5a8",
    },
}


def detect_system_theme() -> str:
    """Returns the desktop preference when it can be detected locally."""
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                check=False,
            )
            return "dark" if result.stdout.strip().lower() == "dark" else "light"
        except OSError:
            return "light"
    if platform.system() == "Windows":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                return "light" if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] else "dark"
        except (ImportError, OSError):
            return "light"
    return "dark" if os.environ.get("GTK_THEME", "").lower().endswith(":dark") else "light"


def create_label(parent: tk.Frame, text: str, theme: dict, **kwargs) -> tk.Label:
    """Create a themed label."""
    return tk.Label(
        parent,
        text=text,
        font=("Helvetica", 14),
        background=theme["surface"],
        foreground=theme["text"],
        **kwargs,
    )


def create_button(parent: tk.Frame, text: str, theme: dict, **kwargs) -> ttk.Button:
    """Create a themed ttk button."""
    return ttk.Button(parent, text=text, style="Custom.TButton", **kwargs)


def create_text(parent: tk.Frame, text: str, theme: dict, **kwargs) -> tk.Text:
    """Create a themed text widget with initial content."""
    text_widget = tk.Text(
        parent,
        font=("Helvetica", 14),
        background=theme["surface"],
        foreground=theme["text"],
        borderwidth=0,
        relief="flat",
        highlightbackground=theme["border"],
        highlightcolor=theme["accent"],
        highlightthickness=1,
        selectbackground=theme["select"],
        selectforeground=theme["select_text"],
        insertbackground=theme["text"],
        **kwargs,
    )
    text_widget.insert(tk.END, text)
    return text_widget


def bind_paste(widget: tk.Entry | tk.Text) -> None:
    """Provide reliable paste shortcuts for editable Tk widgets on macOS and other platforms."""
    def paste(event=None):
        try:
            clipboard_text = widget.clipboard_get()
        except tk.TclError:
            return "break"

        try:
            if isinstance(widget, tk.Text):
                try:
                    widget.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                widget.insert("insert", clipboard_text)
            else:
                if widget.selection_present():
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", clipboard_text)
        except tk.TclError:
            return "break"
        return "break"

    for sequence in ("<Command-v>", "<Control-v>", "<Meta-v>", "<<Paste>>"):
        widget.bind(sequence, paste, add="+")

    menu = tk.Menu(widget, tearoff=False)
    menu.add_command(label="Paste", command=paste)

    def show_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    widget.bind("<Button-3>", show_menu, add="+")
    widget.bind("<Button-2>", show_menu, add="+")


def create_scrollable_tab(parent: ttk.Notebook) -> tuple[ttk.Frame, ttk.Frame]:
    """Create a notebook page with a vertically scrollable content frame."""
    page = ttk.Frame(parent)
    canvas = tk.Canvas(page, highlightthickness=0, borderwidth=0)
    scrollbar = ttk.Scrollbar(page, orient=tk.VERTICAL, command=canvas.yview)
    content = ttk.Frame(canvas)
    content_window = canvas.create_window((0, 0), window=content, anchor=tk.NW)

    def update_scroll_region(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))

    def resize_content(event) -> None:
        canvas.itemconfigure(content_window, width=event.width)

    content.bind("<Configure>", update_scroll_region)
    canvas.bind("<Configure>", resize_content)
    root = parent.winfo_toplevel()
    if not hasattr(root, "_scroll_bindings_ready"):
        root._scroll_bindings_ready = True
        root._active_scroll_canvas = None

        def scroll_canvas(event) -> None:
            active_canvas = root._active_scroll_canvas
            if active_canvas is None:
                return
            scrollregion = active_canvas.bbox("all")
            if scrollregion is None or scrollregion[3] - scrollregion[1] <= active_canvas.winfo_height():
                return
            if event.num == 4:
                amount = -3
            elif event.num == 5:
                amount = 3
            else:
                amount = -int(event.delta / 120) or (-1 if event.delta > 0 else 1)
            active_canvas.yview_scroll(amount, "units")

        root.bind_all("<MouseWheel>", scroll_canvas, add="+")
        root.bind_all("<Button-4>", scroll_canvas, add="+")
        root.bind_all("<Button-5>", scroll_canvas, add="+")

    def activate_scroll_canvas(_event) -> None:
        root._active_scroll_canvas = canvas

    def deactivate_scroll_canvas(_event) -> None:
        if root._active_scroll_canvas is canvas:
            root._active_scroll_canvas = None

    page.bind("<Enter>", activate_scroll_canvas)
    page.bind("<Leave>", deactivate_scroll_canvas)
    canvas.bind("<Enter>", activate_scroll_canvas)
    content.bind("<Enter>", activate_scroll_canvas)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return page, content



class Window:
    """The main window of the application. It contains the tabs and the logs."""

    def __init__(self) -> None:
        """Initializes the main window of the application. It contains the tabs and the logs."""
        self.root = tk.Tk()
        self.root.title("Spotify to YT Music")
        self.root.geometry("1280x720")
        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.worker_thread: threading.Thread | None = None
        self.operation_active = False
        self.root.config(background=self.theme["background"])

        style = ttk.Style()
        style.theme_use("default")
        self.apply_theme()

        # Redirect stdout to GUI
        sys.stdout.write = self.redirector

        self.root.after(1, lambda: self.yt_login(auto=True))

        # Create a PanedWindow with vertical orientation
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Create a Frame for the tabs
        self.tab_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tab_frame, weight=2)

        # Create the TabControl (notebook)
        self.tabControl = ttk.Notebook(self.tab_frame)
        self.tabControl.pack(fill=tk.BOTH, expand=1)

        # Create the tabs
        tab1_page, tab1_content = create_scrollable_tab(self.tabControl)
        tab2_page, tab2_content = create_scrollable_tab(self.tabControl)
        tab3_page, tab3_content = create_scrollable_tab(self.tabControl)
        tab4_page, tab4_content = create_scrollable_tab(self.tabControl)
        tab5_page, tab5_content = create_scrollable_tab(self.tabControl)
        tab6_page, tab6_content = create_scrollable_tab(self.tabControl)
        tab7_page, tab7_content = create_scrollable_tab(self.tabControl)

        self.tab1 = tab1_content
        self.tab2 = tab2_content
        self.tab3 = tab3_content
        self.tab4 = tab4_content
        self.tab5 = tab5_content
        self.tab6 = tab6_content
        self.tab7 = tab7_content
        self.tab_pages = {
            self.tab1: tab1_page,
            self.tab2: tab2_page,
            self.tab3: tab3_page,
            self.tab4: tab4_page,
            self.tab5: tab5_page,
            self.tab6: tab6_page,
            self.tab7: tab7_page,
        }

        self.tabControl.add(tab1_page, text="Login to YT Music")
        self.tabControl.add(tab2_page, text="Spotify backup")
        self.tabControl.add(tab3_page, text="Load liked songs")
        self.tabControl.add(tab4_page, text="List playlists")
        self.tabControl.add(tab5_page, text="Copy all playlists")
        self.tabControl.add(tab6_page, text="Copy a specific playlist")
        self.tabControl.add(tab7_page, text="Settings")

        # Create a Frame for the logs
        self.log_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.log_frame, weight=1)
        self.root.after_idle(self.set_initial_pane_sizes)

        # Create operation controls and the Text widget for the logs
        self.operation_controls = ttk.Frame(self.log_frame)
        self.operation_controls.pack(fill=tk.X, padx=6, pady=4)
        create_button(
            self.operation_controls, text="Stop", theme=self.theme, command=self.stop_operation
        ).pack(side=tk.LEFT, padx=3)
        create_button(
            self.operation_controls, text="Continue", theme=self.theme, command=self.continue_operation
        ).pack(side=tk.LEFT, padx=3)
        create_button(
            self.operation_controls, text="Reset", theme=self.theme, command=self.reset_operation
        ).pack(side=tk.LEFT, padx=3)
        self.operation_status = create_label(
            self.operation_controls, text="Ready", theme=self.theme
        )
        self.operation_status.pack(side=tk.LEFT, padx=12)
        self.logs = tk.Text(self.log_frame, font=("Helvetica", 14))
        self.logs.pack(fill=tk.BOTH, expand=1)
        self.logs.config(background=self.theme["surface"], foreground=self.theme["text"])

        # tab1
        create_label(
            self.tab1,
            text="Welcome to Spotify to YT Music!\nTo start, you need to login to YT Music.",
            theme=self.theme,
        ).pack(anchor=tk.N, expand=False, pady=12)
        create_button(self.tab1, text="Login", theme=self.theme, command=self.yt_login).pack(
            anchor=tk.N, expand=False, pady=12
        )

        create_label(
            self.tab1,
            text="If login fails or credentials expire, paste raw request headers below\n"
            "(from music.youtube.com, a POST to /youtubei/v1/browse, must include 'authorization').",
            theme=self.theme,
        ).pack(anchor=tk.CENTER)
        self.raw_headers_text = tk.Text(self.tab1, height=8, width=100)
        bind_paste(self.raw_headers_text)
        self.raw_headers_text.pack(anchor=tk.CENTER, pady=5)
        create_button(
            self.tab1,
            text="Save credentials",
            theme=self.theme,
            command=self.save_ytmusic_credentials,
        ).pack(anchor=tk.N, expand=False, pady=12)

        # tab2
        create_label(
            self.tab2, text="First, you need to backup your spotify playlists", theme=self.theme
        ).pack(anchor=tk.N, expand=False, pady=12)
        self.var_force_backup = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.tab2,
            text="Force new backup (re-authenticate even if playlists.json exists)",
            variable=self.var_force_backup,
            background=self.theme["surface"],
            foreground=self.theme["text"],
            selectcolor=self.theme["select"],
        ).pack(anchor=tk.CENTER)
        create_button(
            self.tab2,
            text="Backup",
            theme=self.theme,
            command=self.run_spotify_backup,
        ).pack(anchor=tk.N, expand=False, pady=12)

        # tab3
        create_label(self.tab3, text="Now, you can load your liked songs.", theme=self.theme).pack(
            anchor=tk.N, expand=False, pady=12
        )
        create_button(
            self.tab3,
            theme=self.theme,
            text="Load",
            command=lambda: self.call_func(
                func=backend.copier,
                args=(
                    backend.iter_spotify_playlist(),
                    None,
                    False,
                    0,
                    self.var_algo.get(),
                ),
                next_tab=self.tab4,
                controllable=True,
            ),
        ).pack(anchor=tk.N, expand=False, pady=12)

        # tab4
        create_label(
            self.tab4, text="Here, you can get a list of your playlists, with their ID.", theme=self.theme
        ).pack(anchor=tk.N, expand=False, pady=12)
        create_button(
            self.tab4,
            text="Load",
            theme=self.theme,
            command=self.run_list_playlists,
        ).pack(anchor=tk.N, expand=False, pady=12)
        create_label(
            self.tab4,
            text="Click a column header to sort. Click a row to copy its ID to the clipboard.",
            theme=self.theme,
        ).pack(anchor=tk.CENTER)

        tables_frame = ttk.Frame(self.tab4)
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.playlist_tables_frame = tables_frame
        tables_frame.grid_columnconfigure(0, weight=1, uniform="playlist-pane")
        tables_frame.grid_columnconfigure(1, weight=1, uniform="playlist-pane")
        tables_frame.grid_rowconfigure(0, weight=1)

        spotify_frame = ttk.Frame(tables_frame)
        self.spotify_playlist_frame = spotify_frame
        spotify_frame.grid_rowconfigure(1, weight=1)
        spotify_frame.grid_columnconfigure(0, weight=1)
        create_label(spotify_frame, text="Spotify", theme=self.theme).grid(row=0, column=0, sticky="w")
        self.spotify_tree = ttk.Treeview(
            spotify_frame, columns=("id", "name", "tracks"), show="headings"
        )
        self.setup_playlist_tree(self.spotify_tree)
        self.spotify_tree.grid(row=1, column=0, sticky="nsew")

        yt_frame = ttk.Frame(tables_frame)
        self.yt_playlist_frame = yt_frame
        yt_frame.grid_rowconfigure(1, weight=1)
        yt_frame.grid_columnconfigure(0, weight=1)
        create_label(yt_frame, text="YTMusic", theme=self.theme).grid(row=0, column=0, sticky="w")
        self.yt_tree = ttk.Treeview(
            yt_frame, columns=("id", "name", "tracks"), show="headings"
        )
        self.setup_playlist_tree(self.yt_tree)
        self.yt_tree.grid(row=1, column=0, sticky="nsew")
        self.layout_playlist_tables()

        # tab5
        create_label(
            self.tab5,
            text="Here, you can copy all your playlists from Spotify to YT Music. Please note that this step "
            "can take a long time since songs are added one by one.",
            theme=self.theme,
        ).pack(anchor=tk.N, expand=False, pady=12)
        create_button(
            self.tab5,
            text="Copy",
            theme=self.theme,
            command=lambda: self.call_func(
                func=backend.copy_all_playlists,
                args=(0, False, "utf-8", self.var_algo.get()),
                next_tab=self.tab6,
                controllable=True,
            ),
        ).pack(anchor=tk.N, expand=False, pady=12)

        # tab6
        create_label(
            self.tab6,
            text="Here, you can copy a specific playlist from Spotify to YT Music.",
            theme=self.theme,
        ).pack(anchor=tk.N, expand=False, pady=12)
        create_label(self.tab6, text="Spotify playlist ID:", theme=self.theme).pack(
            anchor=tk.N, expand=False, pady=8
        )
        self.spotify_playlist_id = tk.Entry(self.tab6)
        bind_paste(self.spotify_playlist_id)
        self.spotify_playlist_id.pack(anchor=tk.N, expand=False, pady=8)
        create_label(self.tab6, text="YT Music playlist ID:", theme=self.theme).pack(
            anchor=tk.N, expand=False, pady=8
        )
        self.yt_playlist_id = tk.Entry(self.tab6)
        bind_paste(self.yt_playlist_id)
        self.yt_playlist_id.pack(anchor=tk.N, expand=False, pady=8)
        create_button(
            self.tab6,
            text="Copy",
            theme=self.theme,
            command=lambda: self.call_func(
                func=backend.copy_playlist,
                args=(
                    self.spotify_playlist_id.get(),
                    self.yt_playlist_id.get(),
                    "utf-8",
                    False,
                    0,
                    self.var_algo.get(),
                ),
                next_tab=self.tab6,
                controllable=True,
            ),
        ).pack(anchor=tk.N, expand=False, pady=12)

        # tab7
        self.var_scroll = tk.BooleanVar()

        auto_scroll = tk.Checkbutton(
            self.tab7,
            text="Auto scroll",
            variable=self.var_scroll,
            command=lambda: self.load_write_settings(1),
            background=self.theme["button"],
            foreground=self.theme["text"],
            selectcolor=self.theme["select"],
            border=1,
        )
        auto_scroll.pack(anchor=tk.N, expand=False, pady=8)
        auto_scroll.select()

        self.var_algo = tk.IntVar()
        self.var_algo.set(0)

        self.algo_label = create_label(self.tab7, text=f"Algorithm: ", theme=self.theme)
        self.algo_label.pack(anchor=tk.N, expand=False, pady=8)

        menu_algo = tk.OptionMenu(
            self.tab7,
            self.var_algo,
            0,
            *[1, 2],
            command=lambda x: self.load_write_settings(1),
        )
        menu_algo.pack(anchor=tk.N, expand=False, pady=8)
        menu_algo.config(
            background=self.theme["button"], foreground=self.theme["text"], border=1
        )

        self.theme_var = tk.StringVar(value="system")
        theme_label = create_label(self.tab7, text="Theme", theme=self.theme)
        theme_label.pack(anchor=tk.N, expand=False, pady=8)
        theme_controls = tk.Frame(self.tab7, background=self.theme["surface"])
        theme_controls.pack(anchor=tk.N, expand=False, pady=8)
        for theme_name, text in (("system", "System"), ("light", "Light"), ("dark", "Dark")):
            create_button(
                theme_controls,
                text=text,
                theme=self.theme,
                command=lambda name=theme_name: self.set_theme(name),
            ).pack(side=tk.LEFT, padx=3)

        self.root.after_idle(lambda: self.load_write_settings(0))
        self.apply_theme()

    def set_initial_pane_sizes(self) -> None:
        """Keep the log pane compact without removing the draggable divider."""
        self.root.update_idletasks()
        height = self.paned_window.winfo_height()
        if height > 0:
            self.paned_window.sashpos(0, max(180, int(height * 0.82)))

    def apply_theme(self) -> None:
        """Applies the selected palette to the root and all existing widgets."""
        palette = self.theme
        if platform.system() == "Darwin":
            try:
                appearance = "dark" if self.theme_name == "dark" else "light"
                self.root.tk.call("::tk::mac::setAppearance", appearance)
            except tk.TclError:
                pass
        self.root.config(background=palette["background"])
        style = ttk.Style(self.root)
        style.configure("TFrame", background=palette["surface"])
        style.configure("TNotebook", background=palette["background"], borderwidth=0)
        style.configure(
            "TNotebook.Tab", background=palette["background"], foreground=palette["muted"]
        )
        style.configure(
            "Custom.TButton",
            font=("Helvetica", 14),
            background=palette["button"],
            foreground=palette["text"],
            bordercolor=palette["border"],
            lightcolor=palette["border"],
            darkcolor=palette["border"],
            relief="flat",
        )
        style.map(
            "Custom.TButton",
            background=[
                ("pressed", palette["accent"]),
                ("active", palette["select"]),
                ("!disabled", palette["button"]),
            ],
            foreground=[
                ("pressed", palette["surface"]),
                ("active", palette["accent"]),
                ("!disabled", palette["text"]),
            ],
            bordercolor=[("focus", palette["accent"]), ("!focus", palette["border"])],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", palette["surface"])],
            foreground=[("selected", palette["accent"])],
        )
        style.configure(
            "Treeview",
            background=palette["surface"],
            fieldbackground=palette["surface"],
            foreground=palette["text"],
        )
        style.map("Treeview", background=[("selected", palette["select"])])
        self._theme_widget(self.root)

    def _theme_widget(self, widget: tk.Misc) -> None:
        palette = self.theme
        options = widget.keys()
        if isinstance(widget, (tk.Frame, tk.LabelFrame, tk.Label, tk.Canvas, tk.Text, tk.Entry, tk.Listbox)):
            if "background" in options:
                widget.configure(background=palette["surface"])
            if "foreground" in options:
                widget.configure(foreground=palette["text"])
        if isinstance(widget, (tk.Text, tk.Entry, tk.Listbox)):
            selection_options = {
                "selectbackground": palette["select"],
                "selectforeground": palette["select_text"],
                "insertbackground": palette["text"],
            }
            if "inactiveselectbackground" in options:
                selection_options["inactiveselectbackground"] = palette["select"]
            widget.configure(
                borderwidth=0,
                relief="flat",
                highlightbackground=palette["border"],
                highlightcolor=palette["accent"],
                highlightthickness=1,
                **selection_options,
            )
        if isinstance(widget, tk.OptionMenu):
            widget.configure(
                background=palette["button"],
                foreground=palette["text"],
                activebackground=palette["select"],
                activeforeground=palette["accent"],
                highlightbackground=palette["border"],
                highlightcolor=palette["accent"],
                highlightthickness=1,
                relief="flat",
            )
        if isinstance(widget, (tk.Checkbutton, tk.Radiobutton)):
            widget.configure(
            background=palette["surface"],
                foreground=palette["text"],
                activebackground=palette["surface"],
                activeforeground=palette["accent"],
                highlightbackground=palette["border"],
                highlightcolor=palette["accent"],
                highlightthickness=1,
                selectcolor=palette["select"],
            )
        for child in widget.winfo_children():
            self._theme_widget(child)

    def set_theme(self, theme_name: str) -> None:
        self.theme_var.set(theme_name)
        self.theme_name = detect_system_theme() if theme_name == "system" else theme_name
        self.theme = THEMES[self.theme_name]
        self.apply_theme()
        self.load_write_settings(1)

    def redirector(self, input_str="") -> None:
        """
        Inserts the input string into the logs widget and disables editing.

        Args:
            self: The instance of the class.
            input_str (str): The string to be inserted into the logs' widget.
        """
        self.logs.config(state=tk.NORMAL)
        self.logs.insert(tk.END, input_str)
        self.logs.config(state=tk.DISABLED)
        if self.var_scroll.get():
            self.logs.see(tk.END)

    def call_func(
        self, func: Callable, args: tuple, next_tab: ttk.Frame, controllable: bool = False
    ) -> None:
        """Calls the given function in a separate thread and switches to the next tab when the function is done.

        Args:
            func (Callable): The function to be called.
            args (tuple): The arguments to be passed to the function. If no arguments are needed, pass an empty tuple.
            next_tab (ttk.Frame): The tab to switch to when the function is done. If no switch needed, pass the current one.
        """
        if self.operation_active:
            print("An operation is already running.")
            return

        self.stop_event.clear()
        self.pause_event.set()
        self.operation_active = controllable
        self.operation_status.config(text="Running" if controllable else "Busy")

        worker = lambda: func(*args)
        if controllable:
            worker = lambda: func(
                *args, stop_event=self.stop_event, pause_event=self.pause_event
            )

        th = threading.Thread(target=worker)
        self.worker_thread = th
        th.start()
        while th.is_alive():
            self.root.update()
        self.worker_thread = None
        was_reset = self.stop_event.is_set()
        self.operation_active = False
        self.stop_event.clear()
        self.pause_event.set()
        self.operation_status.config(text="Ready")
        if not was_reset:
            self.tabControl.select(self.tab_pages.get(next_tab, next_tab))
        print()

    def stop_operation(self) -> None:
        """Pause the current copy operation at its next track checkpoint."""
        if self.operation_active:
            self.pause_event.clear()
            self.operation_status.config(text="Stopped")

    def continue_operation(self) -> None:
        """Continue a paused copy operation."""
        if self.operation_active and not self.stop_event.is_set():
            self.pause_event.set()
            self.operation_status.config(text="Running")

    def reset_operation(self) -> None:
        """Cancel the current copy operation at its next track checkpoint."""
        if self.operation_active:
            self.stop_event.set()
            self.pause_event.set()
            self.operation_status.config(text="Resetting")

    def save_ytmusic_credentials(self) -> None:
        """Saves pasted raw headers to raw_headers.txt, regenerates oauth.json, and validates it."""
        headers_raw = self.raw_headers_text.get("1.0", tk.END).strip()
        if not headers_raw:
            print("ERROR: Paste the raw request headers into the box first.")
            return

        def worker():
            with open("raw_headers.txt", "w", encoding="utf-8") as f:
                f.write(headers_raw)
            try:
                ytmusic_credentials.setup_ytmusic_with_raw_headers()
            except Exception as e:
                print(f"ERROR: Failed to save credentials: {e}")
                return
            try:
                backend.get_ytmusic()
                print("Credentials saved and verified successfully!")
            except SystemExit:
                print("Credentials were saved but still fail to authenticate, see errors above.")

        self.call_func(func=worker, args=(), next_tab=self.tab1)

    def run_spotify_backup(self) -> None:
        """Runs the Spotify backup, skipping re-authentication if playlists.json already exists
        and the user hasn't requested a forced re-backup."""
        if os.path.exists("playlists.json") and not self.var_force_backup.get():
            print("playlists.json already exists, skipping backup (check 'Force new backup' to redo it).")
            self.tabControl.select(self.tab_pages[self.tab3])
            return
        self.call_func(func=spotify_backup.main, args=(), next_tab=self.tab3)

    def layout_playlist_tables(self, _event=None) -> None:
        """Keep both playlist tables side by side without any adaptive collapsing."""
        self.playlist_tables_frame.grid_columnconfigure(0, weight=1, uniform="playlist-pane")
        self.playlist_tables_frame.grid_columnconfigure(1, weight=1, uniform="playlist-pane")
        self.playlist_tables_frame.grid_rowconfigure(0, weight=1, uniform="playlist-pane")
        self.playlist_tables_frame.grid_rowconfigure(1, weight=0)

        self.spotify_playlist_frame.grid_columnconfigure(0, weight=1)
        self.yt_playlist_frame.grid_columnconfigure(0, weight=1)
        self.spotify_playlist_frame.grid_rowconfigure(1, weight=1)
        self.yt_playlist_frame.grid_rowconfigure(1, weight=1)

        self.spotify_playlist_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        self.yt_playlist_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)

    def setup_playlist_tree(self, tree: ttk.Treeview) -> None:
        """Configures sortable headings and click-to-copy-ID behavior on a playlist Treeview."""
        for col, text in (("id", "ID"), ("name", "Name"), ("tracks", "Tracks")):
            tree.heading(
                col, text=text, command=lambda c=col: self.sort_tree(tree, c, False)
            )
        tree.bind("<<TreeviewSelect>>", self.copy_selected_id_to_clipboard)

    def sort_tree(self, tree: ttk.Treeview, col: str, reverse: bool) -> None:
        """Sorts a Treeview's rows by the given column, toggling direction on repeated clicks."""
        rows = [(tree.set(item, col), item) for item in tree.get_children("")]

        def sort_key(row):
            value = row[0]
            try:
                return (0, int(value))
            except (TypeError, ValueError):
                return (1, str(value).lower())

        rows.sort(key=sort_key, reverse=reverse)
        for index, (_, item) in enumerate(rows):
            tree.move(item, "", index)
        tree.heading(col, command=lambda: self.sort_tree(tree, col, not reverse))

    def copy_selected_id_to_clipboard(self, event: tk.Event) -> None:
        """Copies the ID column of the selected row to the clipboard."""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
        playlist_id = tree.set(selection[0], "id")
        self.root.clipboard_clear()
        self.root.clipboard_append(playlist_id)
        print(f"Copied ID to clipboard: {playlist_id}")

    def run_list_playlists(self) -> None:
        """Fetches playlists in a background thread and populates the Spotify/YTMusic tables."""
        result: dict = {}

        def worker():
            try:
                result["spotify"], result["yt"] = backend.get_playlists_overview()
            except SystemExit:
                #  get_ytmusic() prints details via print() and exits on fatal errors
                print("Failed to list playlists, see the errors above.")
            except Exception as e:
                print(f"ERROR: Failed to list playlists: {e}")

        self.call_func(func=worker, args=(), next_tab=self.tab4)

        for tree in (self.spotify_tree, self.yt_tree):
            tree.delete(*tree.get_children())

        for src_pl in result.get("spotify", []):
            self.spotify_tree.insert(
                "", tk.END, values=(src_pl.get("id"), src_pl["name"], len(src_pl["tracks"]))
            )
        for pl in result.get("yt", []):
            self.yt_tree.insert(
                "", tk.END, values=(pl["playlistId"], pl["title"], pl.get("count", "?"))
            )

    def yt_login(self, auto=False) -> None:
        """Logs in to YT Music. If the oauth.json file is not found, it opens a new console window to run the 'ytmusicapi oauth' command.

        Args:
            auto (bool, optional): Weather to automatically login using the oauth.json file. Defaults to False.
        """

        def run_in_thread():
            if os.path.exists("oauth.json"):
                try:
                    backend.get_ytmusic()
                    print("File detected, auto login")
                except SystemExit:
                    print("'oauth.json' exists but is invalid or expired.")
                    print("Paste fresh raw headers above and click 'Save credentials'.")
                    return
            elif auto:
                print("No file detected. Manual login required")
                return
            else:
                print("File not detected, login required")

                # Open a new console window to run the command
                if os.name == "nt":  # If the OS is Windows
                    try:
                        process = subprocess.Popen(
                            ["ytmusicapi", "oauth"],
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                        )
                    except FileNotFoundError as e:
                        print(
                            f"ERROR: Unable to run 'ytmusicapi oauth'.  Is ytmusicapi installed?  Perhaps try running 'pip install ytmusicapi' Exception: {e}"
                        )
                        sys.exit(1)
                    process.communicate()
                else:  # For Unix and Linux
                    try:
                        subprocess.call(
                            "python3 -m ytmusicapi oauth",
                            shell=True,
                            stdout=subprocess.PIPE,
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")


            self.tabControl.select(self.tab_pages[self.tab2])
            print()

        # Run the function in a separate thread
        th = threading.Thread(target=run_in_thread)
        th.start()

    def load_write_settings(self, action: int) -> None:
        """Loads or writes the settings to the settings.json file.

        Args:
            action (int): 0 to load the settings, 1 to write the settings.
        """
        texts = {0: "Exact match", 1: "Fuzzy match", 2: "Fuzzy match with videos"}

        exist = True
        if action == 0:
            with open("settings.json", "a+"):
                pass
            with open("settings.json", "r+") as f:
                value = f.read()
                if value == "":
                    exist = False
            if exist:
                with open("settings.json", "r+") as f:
                    settings = json.load(f)
                    self.var_scroll.set(settings["auto_scroll"])
                    self.var_algo.set(settings["algo_number"])
                    theme_name = settings.get("theme", "system")
                    self.theme_var.set(theme_name)
                    self.theme_name = (
                        detect_system_theme() if theme_name == "system" else theme_name
                    )
                    self.theme = THEMES.get(self.theme_name, THEMES["dark"])
                    self.apply_theme()
        else:
            with open("settings.json", "w+") as f:
                settings = {
                    "auto_scroll": self.var_scroll.get(),
                    "algo_number": self.var_algo.get(),
                    "theme": self.theme_var.get(),
                }
                json.dump(settings, f)

        self.algo_label.config(text=f"Algorithm: {texts[self.var_algo.get()]}")
        self.root.update()


def main() -> None:
    ui = Window()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
