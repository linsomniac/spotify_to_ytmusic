import tkinter as tk
from tkinter import ttk
from reverse_playlist import reverse_playlist
import spotify_backup, cli
import sys, os, logging, threading, subprocess

class LoggingToGUI(logging.Handler):
    """ Used to redirect logging output to the widget passed in parameters """
    def __init__(self, console):
        logging.Handler.__init__(self)
        self.console = console

    def emit(self, message): 
        formattedMessage = self.format(message)
        self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, formattedMessage)
        self.console.configure(state=tk.DISABLED)
        self.console.see(tk.END)
        print(message)
        
def create_label(parent, text, **kwargs):
    return tk.Label(parent, text=text, font=("Helvetica", 14), **kwargs)

def create_button(parent, text, **kwargs):
    return tk.Button(parent, text=text, font=("Helvetica", 14), **kwargs)

class Window():
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Spotify to YT Music")
        self.root.geometry("1280x720")

        # Redirect stdout to GUI
        sys.stdout.write = self.redirector
        
        self.root.after(1, lambda: self.yt_login(auto=True))

        # Create a PanedWindow with vertical orientation
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Create a Frame for the tabs
        self.tab_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tab_frame, weight=1)

        # Create the TabControl (notebook)
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Helvetica', '12'))

        self.tabControl = ttk.Notebook(self.tab_frame)
        self.tabControl.pack(fill=tk.BOTH, expand=1)

        # Create the tabs
        self.tab0 = ttk.Frame(self.tabControl)
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        self.tab3 = ttk.Frame(self.tabControl)
        self.tab4 = ttk.Frame(self.tabControl)
        self.tab5 = ttk.Frame(self.tabControl)
        self.tab6 = ttk.Frame(self.tabControl)
        
        self.tabControl.add(self.tab0, text='Login to YT Music')
        self.tabControl.add(self.tab1, text='Spotify backup')
        self.tabControl.add(self.tab2, text='Reverse playlist')
        self.tabControl.add(self.tab3, text='Load liked songs')
        self.tabControl.add(self.tab4, text='List playlists')
        self.tabControl.add(self.tab5, text='Copy all playlists')
        self.tabControl.add(self.tab6, text='Copy a specific playlist')

        # Create a Frame for the logs
        self.log_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.log_frame, weight=1)

        # Create the Text widget for the logs
        self.logs = tk.Text(self.log_frame, font=("Helvetica", 14))
        self.logs.pack(fill=tk.BOTH, expand=1)
        
        # tab 0
        create_label(self.tab0, text="Welcome to Spotify to YT Music!\nTo start, you need to login to YT Music.").pack(anchor=tk.CENTER)
        create_button(self.tab0, text="Login", command=self.yt_login).pack(anchor=tk.CENTER)

        # tab1
        create_label(self.tab1, text="First, you need to backup your spotify playlists").pack(anchor=tk.CENTER)
        create_button(self.tab1, text="Backup", command=lambda: self.call_func(spotify_backup.main, self.tab2)).pack(anchor=tk.CENTER)

        # tab2
        create_label(self.tab2, text="Since this program likes the last added song first, you need to reverse the playlist if you want to keep the exact same playlists.\nBut this step is not mandatory, you can skip it if you don't mind by clicking here.").pack(anchor=tk.CENTER)
        create_button(self.tab2, text="Skip", command=lambda: self.tabControl.select(self.tab3)).pack(anchor=tk.CENTER)
        create_button(self.tab2, text="Reverse", command=self.call_reverse).pack(anchor=tk.CENTER)

        # tab3
        create_label(self.tab3, text="Now, you can load your liked songs.").pack(anchor=tk.CENTER)
        create_button(self.tab3, text="Load", command=lambda: self.call_func(cli.load_liked, self.tab4)).pack(anchor=tk.CENTER)
        
        # tab4
        create_label(self.tab4, text="Here, you can get a list of your playlists, with their ID.").pack(anchor=tk.CENTER)
        create_button(self.tab4, text="List", command=lambda: self.call_func(cli.list_playlists, self.tab5)).pack(anchor=tk.CENTER)

        # tab5
        create_label(self.tab5, text="Here, you can copy all your playlists from Spotify to YT Music. Please note that this step can take a long time since songs are added one by one.").pack(anchor=tk.CENTER)
        create_button(self.tab5, text="Copy", command=lambda: self.call_func(cli.copy_all_playlists, self.tab6)).pack(anchor=tk.CENTER)
        
        # tab6
        create_label(self.tab6, text="Here, you can copy a specific playlist from Spotify to YT Music.").pack(anchor=tk.CENTER)
        create_label(self.tab6, text="Spotify playlist ID:").pack(anchor=tk.CENTER)
        self.spotify_playlist_id = tk.Entry(self.tab6)
        self.spotify_playlist_id.pack(anchor=tk.CENTER)
        create_label(self.tab6, text="YT Music playlist ID:").pack(anchor=tk.CENTER)
        self.yt_playlist_id = tk.Entry(self.tab6)
        self.yt_playlist_id.pack(anchor=tk.CENTER)
        create_button(self.tab6, text="Copy", command=self.call_copy_playlist).pack(anchor=tk.CENTER)


    def redirector(self, inputStr):
        self.logs.config(state=tk.NORMAL)
        self.logs.insert(tk.INSERT, inputStr)
        self.logs.config(state=tk.DISABLED)
        self.logs.see(tk.END)
        
    def call_func(self, func, next_tab):
        th = threading.Thread(target=func)
        th.start()
        while th.is_alive():
            self.root.update()
        self.tabControl.select(next_tab)
        print()
        
    def call_copy_playlist(self):
        if self.spotify_playlist_id.get() == "" or self.yt_playlist_id.get() == "":
            print("Please enter both playlist IDs")
            return
        th = threading.Thread(target=cli.copy_playlist, args=(self.spotify_playlist_id.get(), self.yt_playlist_id.get()))
        th.start()
        while th.is_alive():
            self.root.update()
            
        self.tabControl.select(self.tab6)
        print()

    def call_reverse(self):
        result = [None]  # Shared data structure

        def target():
            result[0] = reverse_playlist(replace=True)  # Call the function with specific arguments

        th = threading.Thread(target=target)
        th.start()
        while th.is_alive():
            self.root.update()

        if result[0] == 0:  # Access the return value
            self.tabControl.select(self.tab3)
            print()


    def yt_login(self, auto=False):
        def run_in_thread():
            if os.path.exists("oauth.json"):
                print("File detected, auto login")
            elif auto:
                print("No file detected. Manual login required")
                return
            else:
                print("File not detected, login required")
                command = ["ytmusicapi", "oauth"]

                # Open a new console window to run the command
                if os.name == 'nt':  # If the OS is Windows
                    process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:  # For Unix and Linux
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                process.communicate()
                
                print("Login successful")
                
            self.tabControl.select(self.tab1)
            print()


        # Run the function in a separate thread
        th = threading.Thread(target=run_in_thread)
        th.start()

if __name__ == "__main__":
    ui = Window()
    ui.root.mainloop()