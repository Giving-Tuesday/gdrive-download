"""Simple tkinter GUI for Google Drive Download tools."""

import csv
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, List, Dict
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


def get_default_output_dir() -> Path:
    """Return default output directory (user's Documents folder)."""
    if sys.platform == "win32":
        # Try to get Windows Documents folder
        docs = Path(os.environ.get("USERPROFILE", Path.home())) / "Documents"
    elif sys.platform == "darwin":
        docs = Path.home() / "Documents"
    else:
        docs = Path.home() / "Documents"

    # Fall back to home if Documents doesn't exist
    if not docs.exists():
        docs = Path.home()

    return docs / "GDrive Downloads"


class GDriveApp:
    """Main GUI application for Google Drive tools."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Google Drive Tools")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # Queue for thread-safe logging
        self.log_queue = queue.Queue()

        # Track running operations
        self.running = False

        # Store search results for later actions
        self.search_results: List[Dict] = []

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

        # === CREDENTIALS SECTION ===
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

        # === OUTPUT DIRECTORY SECTION ===
        output_frame = ttk.LabelFrame(main_frame, text="Output Location", padding="5")
        output_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Save files to:").grid(row=0, column=0, sticky="w")
        self.output_dir_var = tk.StringVar(value=str(get_default_output_dir()))
        ttk.Entry(output_frame, textvariable=self.output_dir_var).grid(
            row=0, column=1, sticky="ew", padx=(10, 5)
        )
        ttk.Button(output_frame, text="Browse...", command=self._browse_output_dir).grid(
            row=0, column=2
        )

        # === SEARCH SECTION ===
        search_frame = ttk.LabelFrame(main_frame, text="Search & Create Shortcuts", padding="10")
        search_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
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

        # Scope and Since on same row
        ttk.Label(search_frame, text="Search Scope:").grid(row=2, column=0, sticky="w", pady=2)
        scope_frame = ttk.Frame(search_frame)
        scope_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=2)

        self.scope_var = tk.StringVar(value="all")
        scope_combo = ttk.Combobox(
            scope_frame,
            textvariable=self.scope_var,
            values=["all", "personal", "shared"],
            state="readonly",
            width=12,
        )
        scope_combo.pack(side="left")

        ttk.Label(scope_frame, text="   Modified since:").pack(side="left")
        self.since_var = tk.StringVar()
        ttk.Entry(scope_frame, textvariable=self.since_var, width=12).pack(side="left", padx=(5, 0))
        ttk.Label(scope_frame, text="(e.g., 7d, 30d)", font=("TkDefaultFont", 9)).pack(side="left", padx=(5, 0))

        # Shortcuts folder
        ttk.Label(search_frame, text="Shortcuts Folder ID:").grid(row=3, column=0, sticky="w", pady=2)
        self.shortcuts_folder_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.shortcuts_folder_var).grid(
            row=3, column=1, columnspan=2, sticky="ew", pady=2
        )
        ttk.Label(
            search_frame,
            text="Optional: ID from folder URL after /folders/ (leave empty to skip)",
            font=("TkDefaultFont", 9),
        ).grid(row=4, column=1, columnspan=2, sticky="w")

        # Search button
        self.search_btn = ttk.Button(
            search_frame, text="Search", command=self._run_search
        )
        self.search_btn.grid(row=5, column=0, columnspan=3, pady=(10, 0))

        # === RESULTS TABLE ===
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="5")
        results_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Treeview for results
        columns = ("name", "type", "modified", "drive")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=6)
        self.results_tree.heading("name", text="File Name")
        self.results_tree.heading("type", text="Type")
        self.results_tree.heading("modified", text="Modified")
        self.results_tree.heading("drive", text="Drive")
        self.results_tree.column("name", width=300)
        self.results_tree.column("type", width=100)
        self.results_tree.column("modified", width=100)
        self.results_tree.column("drive", width=150)

        # Scrollbar for results
        results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        results_scroll.grid(row=0, column=1, sticky="ns")

        # Results action buttons
        results_btn_frame = ttk.Frame(results_frame)
        results_btn_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))

        self.results_count_label = ttk.Label(results_btn_frame, text="No results")
        self.results_count_label.pack(side="left", padx=(0, 20))

        self.download_selected_btn = ttk.Button(
            results_btn_frame, text="Download Selected", command=self._download_selected, state="disabled"
        )
        self.download_selected_btn.pack(side="left", padx=(0, 10))

        self.download_all_btn = ttk.Button(
            results_btn_frame, text="Download All", command=self._download_all, state="disabled"
        )
        self.download_all_btn.pack(side="left", padx=(0, 10))

        self.create_shortcuts_btn = ttk.Button(
            results_btn_frame, text="Create Shortcuts", command=self._create_shortcuts_from_results, state="disabled"
        )
        self.create_shortcuts_btn.pack(side="left")

        # === DOWNLOAD FROM FOLDER SECTION ===
        download_frame = ttk.LabelFrame(main_frame, text="Download from Folder URL", padding="10")
        download_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        download_frame.columnconfigure(1, weight=1)

        ttk.Label(download_frame, text="Folder URL:").grid(row=0, column=0, sticky="w", pady=2)
        self.folder_url_var = tk.StringVar()
        ttk.Entry(download_frame, textvariable=self.folder_url_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        # Options row
        options_frame = ttk.Frame(download_frame)
        options_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

        self.convert_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Convert to Markdown", variable=self.convert_var).pack(side="left", padx=(0, 20))

        self.download_btn = ttk.Button(
            download_frame, text="Download Folder", command=self._run_download
        )
        self.download_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # === LOG OUTPUT ===
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=6, column=0, sticky="ew", pady=(0, 5))
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=5, state="disabled", wrap="word"
        )
        self.log_text.grid(row=0, column=0, sticky="ew")

        # Clear button
        ttk.Button(log_frame, text="Clear Log", command=self._clear_log).grid(
            row=1, column=0, pady=(5, 0), sticky="e"
        )

    def _check_credentials(self):
        """Check for credentials file and update status."""
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
        if running:
            self.download_selected_btn.config(state="disabled")
            self.download_all_btn.config(state="disabled")
            self.create_shortcuts_btn.config(state="disabled")

    def _update_results_buttons(self):
        """Enable/disable result action buttons based on results."""
        has_results = len(self.search_results) > 0
        state = "normal" if has_results and not self.running else "disabled"
        self.download_selected_btn.config(state=state)
        self.download_all_btn.config(state=state)
        self.create_shortcuts_btn.config(state=state)

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

    def _get_output_dir(self, subfolder: str = "") -> Path:
        """Get the output directory, creating it if needed."""
        base = Path(self.output_dir_var.get().strip())
        if not base:
            base = get_default_output_dir()
        if subfolder:
            base = base / subfolder
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _populate_results_table(self, results: List[Dict]):
        """Populate the results treeview with search results."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        self.search_results = results

        for result in results:
            name = result.get("name", "Unknown")
            mime_type = result.get("mimeType", "")
            # Simplify mime type display
            if "document" in mime_type:
                file_type = "Document"
            elif "spreadsheet" in mime_type:
                file_type = "Spreadsheet"
            elif "presentation" in mime_type:
                file_type = "Presentation"
            elif "pdf" in mime_type:
                file_type = "PDF"
            else:
                file_type = mime_type.split(".")[-1] if "." in mime_type else "File"

            modified = result.get("modifiedTime", "")[:10] if result.get("modifiedTime") else ""
            drive = result.get("drive", "My Drive")

            self.results_tree.insert("", "end", values=(name, file_type, modified, drive), tags=(result.get("id"),))

        count = len(results)
        self.results_count_label.config(text=f"{count} file{'s' if count != 1 else ''} found")
        self._update_results_buttons()

    def _save_search_results_csv(self, results: List[Dict], output_dir: Path):
        """Save search results to CSV file."""
        csv_path = output_dir / "search_results.csv"
        if not results:
            return

        fieldnames = ["name", "id", "webViewLink", "mimeType", "modifiedTime", "createdTime", "drive"]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)

        self._log(f"Saved results to: {csv_path}")

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
        self._log(f"Searching for: {pattern}")

        def search_thread():
            try:
                from gdrive_download.config import GlobalConfig
                from gdrive_download.downloader import GoogleDriveSearcher

                config = GlobalConfig()
                config.downloader.credentials_file = creds_path

                searcher = GoogleDriveSearcher(config.downloader)

                # Parse since date if provided
                since_date = None
                since_str = self.since_var.get().strip()
                if since_str:
                    from gdrive_download.cli.search import parse_since_date
                    try:
                        since_date = parse_since_date(since_str)
                        self._log(f"Filtering: modified since {since_date.strftime('%Y-%m-%d')}")
                    except ValueError:
                        self._log(f"Warning: Invalid date format '{since_str}', ignoring")

                results = searcher.search_files(
                    pattern=pattern,
                    drive_scope=self.scope_var.get(),
                    modified_since=since_date,
                )

                self._log(f"Found {len(results)} files")

                # Update UI on main thread
                self.root.after(0, lambda: self._populate_results_table(results))

                # Save CSV
                safe_pattern = re.sub(r'[<>:"/\\|?*]', '_', pattern)[:30]
                output_dir = self._get_output_dir(f"search_{safe_pattern}")
                self._save_search_results_csv(results, output_dir)

                # Create shortcuts if folder ID provided (during search)
                shortcuts_folder = self.shortcuts_folder_var.get().strip()
                if shortcuts_folder and results:
                    self._log(f"Creating shortcuts in folder...")
                    created, skipped = searcher.create_shortcuts(results, shortcuts_folder)
                    self._log(f"Created {created} shortcuts, skipped {skipped} existing")

                self._log("Search complete!")

            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: self._set_running(False))
                self.root.after(0, self._update_results_buttons)

        threading.Thread(target=search_thread, daemon=True).start()

    def _download_files(self, files: List[Dict], output_subdir: str = ""):
        """Download a list of files."""
        if not files:
            return

        creds_path = self._get_credentials_path()
        if not creds_path:
            return

        self._set_running(True)
        self._log(f"Downloading {len(files)} files...")

        def download_thread():
            try:
                from gdrive_download.config import GlobalConfig
                from gdrive_download.downloader import GoogleDriveDownloader, FileConverter

                config = GlobalConfig()
                config.downloader.credentials_file = creds_path

                output_dir = self._get_output_dir(output_subdir)
                docs_dir = output_dir / "documents"
                docs_dir.mkdir(parents=True, exist_ok=True)

                self._log(f"Output: {output_dir}")

                downloader = GoogleDriveDownloader(config.downloader)

                for i, file_info in enumerate(files, 1):
                    name = file_info.get("name", "Unknown")
                    self._log(f"  [{i}/{len(files)}] {name}")
                    try:
                        downloader.download_file(
                            file_info["id"],
                            docs_dir,
                            name,
                        )
                    except Exception as e:
                        self._log(f"    Error: {e}")

                # Convert if requested
                if self.convert_var.get():
                    self._log("Converting to markdown...")
                    converter = FileConverter(
                        input_dir=docs_dir,
                        output_dir=output_dir / "markdown",
                    )
                    converted = converter.convert_all_files()
                    self._log(f"Converted {len(converted)} files")

                self._log(f"Download complete! Files saved to:\n  {output_dir}")

            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: self._set_running(False))
                self.root.after(0, self._update_results_buttons)

        threading.Thread(target=download_thread, daemon=True).start()

    def _download_selected(self):
        """Download only selected files from results."""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select files to download from the results table.")
            return

        # Get file info for selected items
        selected_files = []
        for item in selected:
            values = self.results_tree.item(item, "values")
            # Find matching result by name
            for result in self.search_results:
                if result.get("name") == values[0]:
                    selected_files.append(result)
                    break

        pattern = self.pattern_var.get().strip()
        safe_pattern = re.sub(r'[<>:"/\\|?*]', '_', pattern)[:30] if pattern else "selected"
        self._download_files(selected_files, f"search_{safe_pattern}")

    def _download_all(self):
        """Download all files from search results."""
        if not self.search_results:
            return

        pattern = self.pattern_var.get().strip()
        safe_pattern = re.sub(r'[<>:"/\\|?*]', '_', pattern)[:30] if pattern else "results"
        self._download_files(self.search_results, f"search_{safe_pattern}")

    def _create_shortcuts_from_results(self):
        """Create shortcuts from current search results."""
        if not self.search_results:
            return

        shortcuts_folder = self.shortcuts_folder_var.get().strip()
        if not shortcuts_folder:
            messagebox.showwarning(
                "Folder ID Required",
                "Please enter a Shortcuts Folder ID.\n\n"
                "This is the part after /folders/ in a Google Drive folder URL."
            )
            return

        creds_path = self._get_credentials_path()
        if not creds_path:
            return

        self._set_running(True)
        self._log(f"Creating shortcuts for {len(self.search_results)} files...")

        def shortcuts_thread():
            try:
                from gdrive_download.config import GlobalConfig
                from gdrive_download.downloader import GoogleDriveSearcher

                config = GlobalConfig()
                config.downloader.credentials_file = creds_path

                searcher = GoogleDriveSearcher(config.downloader)
                created, skipped = searcher.create_shortcuts(self.search_results, shortcuts_folder)
                self._log(f"Created {created} shortcuts, skipped {skipped} existing")
                self._log("Shortcuts complete!")

            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: self._set_running(False))
                self.root.after(0, self._update_results_buttons)

        threading.Thread(target=shortcuts_thread, daemon=True).start()

    def _run_download(self):
        """Run download from folder URL operation."""
        folder_url = self.folder_url_var.get().strip()
        if not folder_url:
            messagebox.showwarning("URL Required", "Please enter a Google Drive folder URL.")
            return

        creds_path = self._get_credentials_path()
        if not creds_path:
            return

        self._set_running(True)
        self._log(f"Downloading from folder...")

        def download_thread():
            try:
                from gdrive_download.config import GlobalConfig
                from gdrive_download.downloader import GoogleDriveDownloader, FileConverter

                config = GlobalConfig()
                config.downloader.credentials_file = creds_path

                # Extract folder ID for subfolder name
                match = re.search(r'/folders/([^/?]+)', folder_url)
                folder_id = match.group(1)[:12] if match else "folder"

                output_dir = self._get_output_dir(f"folder_{folder_id}")
                docs_dir = output_dir / "documents"
                docs_dir.mkdir(parents=True, exist_ok=True)

                self._log(f"Output: {output_dir}")

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

                self._log(f"Download complete! Files saved to:\n  {output_dir}")

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
