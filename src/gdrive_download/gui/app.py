"""Simple tkinter GUI for Google Drive Download tools."""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional
import queue


def get_app_data_dir() -> Path:
    """Return platform-appropriate app data directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "gdrive-download"


class GDriveApp:
    """Main GUI application for Google Drive tools."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Google Drive Tools")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        # Queue for thread-safe logging
        self.log_queue = queue.Queue()

        # Track running operations
        self.running = False

        self._setup_ui()
        self._check_credentials()
        self._process_log_queue()

    def _setup_ui(self):
        """Set up the main UI components."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Google Drive Download Tools",
            font=("TkDefaultFont", 16, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 15), sticky="w")

        # Credentials status
        self.creds_frame = ttk.LabelFrame(main_frame, text="Credentials", padding="5")
        self.creds_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.creds_frame.columnconfigure(1, weight=1)

        self.creds_status = ttk.Label(self.creds_frame, text="Checking...")
        self.creds_status.grid(row=0, column=0, sticky="w")

        self.creds_path_var = tk.StringVar()
        ttk.Entry(
            self.creds_frame, textvariable=self.creds_path_var, state="readonly"
        ).grid(row=0, column=1, sticky="ew", padx=(10, 5))

        ttk.Button(self.creds_frame, text="Browse...", command=self._browse_credentials).grid(
            row=0, column=2
        )

        # === SEARCH SECTION ===
        search_frame = ttk.LabelFrame(main_frame, text="Search & Create Shortcuts", padding="10")
        search_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        # Pattern
        ttk.Label(search_frame, text="Search Pattern:").grid(row=0, column=0, sticky="w", pady=2)
        self.pattern_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.pattern_var).grid(
            row=0, column=1, columnspan=2, sticky="ew", pady=2
        )
        ttk.Label(search_frame, text="e.g., AAR*, *2024*, Project Brief*", font=("TkDefaultFont", 9)).grid(
            row=1, column=1, columnspan=2, sticky="w"
        )

        # Scope
        ttk.Label(search_frame, text="Search Scope:").grid(row=2, column=0, sticky="w", pady=2)
        self.scope_var = tk.StringVar(value="all")
        scope_combo = ttk.Combobox(
            search_frame,
            textvariable=self.scope_var,
            values=["all", "personal", "shared"],
            state="readonly",
            width=15,
        )
        scope_combo.grid(row=2, column=1, sticky="w", pady=2)

        # Shortcuts folder
        ttk.Label(search_frame, text="Shortcuts Folder ID:").grid(row=3, column=0, sticky="w", pady=2)
        self.shortcuts_folder_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.shortcuts_folder_var).grid(
            row=3, column=1, columnspan=2, sticky="ew", pady=2
        )
        ttk.Label(
            search_frame,
            text="Leave empty to skip shortcut creation. Find ID in folder URL after /folders/",
            font=("TkDefaultFont", 9),
        ).grid(row=4, column=1, columnspan=2, sticky="w")

        # Options
        options_frame = ttk.Frame(search_frame)
        options_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=(5, 0))

        self.download_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Download files", variable=self.download_var).pack(
            side="left", padx=(0, 15)
        )

        self.convert_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Convert to Markdown", variable=self.convert_var).pack(
            side="left", padx=(0, 15)
        )

        # Since filter
        ttk.Label(options_frame, text="Modified since:").pack(side="left")
        self.since_var = tk.StringVar()
        since_entry = ttk.Entry(options_frame, textvariable=self.since_var, width=12)
        since_entry.pack(side="left", padx=(5, 0))
        ttk.Label(options_frame, text="(e.g., 7d, 30d, 2024-01-01)", font=("TkDefaultFont", 9)).pack(
            side="left", padx=(5, 0)
        )

        # Search button
        self.search_btn = ttk.Button(
            search_frame, text="Search", command=self._run_search, style="Accent.TButton"
        )
        self.search_btn.grid(row=6, column=0, columnspan=3, pady=(10, 0))

        # === DOWNLOAD SECTION ===
        download_frame = ttk.LabelFrame(main_frame, text="Download from Folder", padding="10")
        download_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        download_frame.columnconfigure(1, weight=1)

        ttk.Label(download_frame, text="Folder URL:").grid(row=0, column=0, sticky="w", pady=2)
        self.folder_url_var = tk.StringVar()
        ttk.Entry(download_frame, textvariable=self.folder_url_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )
        ttk.Label(
            download_frame,
            text="Paste full Google Drive folder URL",
            font=("TkDefaultFont", 9),
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(download_frame, text="Output Directory:").grid(row=2, column=0, sticky="w", pady=2)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(download_frame, textvariable=self.output_dir_var).grid(
            row=2, column=1, sticky="ew", pady=2
        )
        ttk.Button(download_frame, text="Browse...", command=self._browse_output_dir).grid(
            row=2, column=2, padx=(5, 0)
        )

        self.download_btn = ttk.Button(
            download_frame, text="Download", command=self._run_download
        )
        self.download_btn.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        # === LOG OUTPUT ===
        log_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, state="disabled", wrap="word"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Clear button
        ttk.Button(log_frame, text="Clear Log", command=self._clear_log).grid(
            row=1, column=0, pady=(5, 0)
        )

    def _check_credentials(self):
        """Check for credentials file and update status."""
        # Check common locations
        locations = [
            Path.cwd() / "credentials.json",
            get_app_data_dir() / "credentials.json",
        ]

        for loc in locations:
            if loc.exists():
                self.creds_path_var.set(str(loc))
                self.creds_status.config(text="Found:", foreground="green")
                return

        self.creds_status.config(text="Not found:", foreground="red")
        app_dir = get_app_data_dir()
        self.creds_path_var.set(f"Place credentials.json in {app_dir}")

    def _browse_credentials(self):
        """Browse for credentials file."""
        path = filedialog.askopenfilename(
            title="Select credentials.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.creds_path_var.set(path)
            self.creds_status.config(text="Selected:", foreground="green")

    def _browse_output_dir(self):
        """Browse for output directory."""
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir_var.set(path)

    def _log(self, message: str):
        """Thread-safe logging to the text widget."""
        self.log_queue.put(message)

    def _process_log_queue(self):
        """Process messages from the log queue."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self._process_log_queue)

    def _clear_log(self):
        """Clear the log output."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _set_running(self, running: bool):
        """Enable/disable buttons during operations."""
        self.running = running
        state = "disabled" if running else "normal"
        self.search_btn.config(state=state)
        self.download_btn.config(state=state)

    def _get_credentials_path(self) -> Optional[Path]:
        """Get the credentials path, validating it exists."""
        path_str = self.creds_path_var.get()
        if not path_str or not Path(path_str).exists():
            messagebox.showerror(
                "Credentials Required",
                "Please select a valid credentials.json file.\n\n"
                "You can obtain this from the Google Cloud Console.",
            )
            return None
        return Path(path_str)

    def _run_search(self):
        """Run search operation in background thread."""
        pattern = self.pattern_var.get().strip()
        if not pattern:
            messagebox.showwarning("Pattern Required", "Please enter a search pattern.")
            return

        creds_path = self._get_credentials_path()
        if not creds_path:
            return

        self._set_running(True)
        self._log(f"Starting search for pattern: {pattern}")

        def search_thread():
            try:
                from gdrive_download.config import GlobalConfig
                from gdrive_download.downloader import GoogleDriveSearcher, GoogleDriveDownloader, FileConverter

                config = GlobalConfig()
                config.downloader.credentials_file = creds_path

                searcher = GoogleDriveSearcher(config.downloader)
                self._log(f"Searching in scope: {self.scope_var.get()}")

                # Parse since date if provided
                since_date = None
                since_str = self.since_var.get().strip()
                if since_str:
                    from gdrive_download.cli.search import parse_since_date
                    try:
                        since_date = parse_since_date(since_str)
                        self._log(f"Filtering files modified since: {since_date}")
                    except ValueError as e:
                        self._log(f"Warning: Invalid date format '{since_str}', ignoring filter")

                results = searcher.search_files(
                    pattern=pattern,
                    drive_scope=self.scope_var.get(),
                    modified_since=since_date,
                )

                self._log(f"Found {len(results)} files")

                # Create shortcuts if folder ID provided
                shortcuts_folder = self.shortcuts_folder_var.get().strip()
                if shortcuts_folder and results:
                    self._log(f"Creating shortcuts in folder: {shortcuts_folder}")
                    created, skipped = searcher.create_shortcuts(results, shortcuts_folder)
                    self._log(f"Created {created} shortcuts, skipped {skipped} existing")

                # Download if requested
                if self.download_var.get() and results:
                    self._log("Downloading files...")
                    downloader = GoogleDriveDownloader(config.downloader)
                    # Create output directory
                    import re
                    safe_pattern = re.sub(r'[<>:"/\\|?*]', '_', pattern)[:30]
                    output_dir = Path.cwd() / f"search_{safe_pattern}"
                    output_dir.mkdir(parents=True, exist_ok=True)

                    for i, file_info in enumerate(results, 1):
                        self._log(f"  [{i}/{len(results)}] {file_info.get('name', 'Unknown')}")
                        try:
                            downloader.download_file(
                                file_info["id"],
                                output_dir / "documents",
                                file_info.get("name", "unknown"),
                            )
                        except Exception as e:
                            self._log(f"    Error: {e}")

                    # Convert if requested
                    if self.convert_var.get():
                        self._log("Converting to markdown...")
                        converter = FileConverter(
                            input_dir=output_dir / "documents",
                            output_dir=output_dir / "markdown",
                        )
                        converted = converter.convert_all_files()
                        self._log(f"Converted {len(converted)} files")

                self._log("Search complete!")

            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=search_thread, daemon=True).start()

    def _run_download(self):
        """Run download operation in background thread."""
        folder_url = self.folder_url_var.get().strip()
        if not folder_url:
            messagebox.showwarning("URL Required", "Please enter a Google Drive folder URL.")
            return

        creds_path = self._get_credentials_path()
        if not creds_path:
            return

        self._set_running(True)
        self._log(f"Starting download from: {folder_url}")

        def download_thread():
            try:
                from gdrive_download.config import GlobalConfig
                from gdrive_download.downloader import GoogleDriveDownloader, FileConverter
                import re

                config = GlobalConfig()
                config.downloader.credentials_file = creds_path

                # Determine output directory
                output_dir = self.output_dir_var.get().strip()
                if not output_dir:
                    # Extract folder ID for default name
                    match = re.search(r'/folders/([^/?]+)', folder_url)
                    folder_id = match.group(1)[:8] if match else "download"
                    output_dir = Path.cwd() / f"gdrive_{folder_id}"
                else:
                    output_dir = Path(output_dir)

                output_dir = Path(output_dir)
                docs_dir = output_dir / "documents"
                docs_dir.mkdir(parents=True, exist_ok=True)

                self._log(f"Output directory: {output_dir}")

                downloader = GoogleDriveDownloader(config.downloader)
                files = downloader.download_folder(folder_url, docs_dir)

                self._log(f"Downloaded {len(files)} files")

                # Convert to markdown
                if self.convert_var.get() and files:
                    self._log("Converting to markdown...")
                    converter = FileConverter(
                        input_dir=docs_dir,
                        output_dir=output_dir / "markdown",
                    )
                    converted = converter.convert_all_files()
                    self._log(f"Converted {len(converted)} files")

                self._log("Download complete!")

            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: self._set_running(False))

        threading.Thread(target=download_thread, daemon=True).start()

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Entry point for the GUI application."""
    app = GDriveApp()
    app.run()


if __name__ == "__main__":
    main()
