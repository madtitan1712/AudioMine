import os
import json
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QRunnable, QThreadPool, QMetaObject, Qt, Q_ARG


class ScannerWorker(QRunnable):
    """Worker thread for scanning the music library"""

    class Signals(QObject):
        progress = pyqtSignal(int, int)  # files_found, total_scanned
        finished = pyqtSignal(list)  # list of found files

    def __init__(self, directory, supported_extensions):
        super().__init__()
        self.directory = directory
        self.supported_extensions = supported_extensions
        self.signals = self.Signals()
        self.abort = False

    def run(self):
        files_found = []
        files_scanned = 0

        try:
            for root, dirs, files in os.walk(self.directory):
                if self.abort:
                    break

                for file in files:
                    files_scanned += 1

                    if self.abort:
                        break

                    if any(file.lower().endswith(ext) for ext in self.supported_extensions):
                        full_path = os.path.join(root, file)
                        files_found.append(full_path)
                        self.signals.progress.emit(len(files_found), files_scanned)

            self.signals.finished.emit(files_found)
        except Exception as e:
            print(f"Error in scanner thread: {e}")
            self.signals.finished.emit([])


class LibraryManager(QObject):
    """Manages the music library (scanning, indexing, etc.)"""

    # Signals
    scanStarted = pyqtSignal()
    scanProgress = pyqtSignal(int, int)  # files_found, total_scanned
    scanFinished = pyqtSignal(int)  # total_files_found
    libraryUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.library = []
        self.supported_extensions = ['.mp3', '.flac', '.wav', '.ogg', '.m4a']
        self.current_scanner = None
        self.thread_pool = QThreadPool()

    def scan_directory(self, directory_path):
        """Start scanning a directory for music files"""
        if not os.path.exists(directory_path):
            return False

        self.scanStarted.emit()

        # Create scanner worker
        scanner = ScannerWorker(directory_path, self.supported_extensions)
        scanner.signals.progress.connect(self._on_scan_progress)
        scanner.signals.finished.connect(self._on_scan_finished)

        # Store reference to cancel if needed
        self.current_scanner = scanner

        # Start scanning
        self.thread_pool.start(scanner)
        return True

    def cancel_scan(self):
        """Cancel an ongoing scan"""
        if self.current_scanner:
            self.current_scanner.abort = True

    def _on_scan_progress(self, files_found, total_scanned):
        """Handle progress updates from scanner"""
        self.scanProgress.emit(files_found, total_scanned)

    def _on_scan_finished(self, files):
        """Handle scan completion"""
        # Add only new files to library
        new_files = [f for f in files if f not in self.library]
        if new_files:
            self.library.extend(new_files)
            self.libraryUpdated.emit()

        self.scanFinished.emit(len(new_files))
        self.current_scanner = None

    def get_library(self):
        """Get the current library file list"""
        return self.library

    def clear_library(self):
        """Clear the entire library"""
        self.library = []
        self.libraryUpdated.emit()

    def remove_missing_files(self):
        """Remove files that no longer exist"""
        original_count = len(self.library)
        self.library = [f for f in self.library if os.path.exists(f)]
        if len(self.library) != original_count:
            self.libraryUpdated.emit()
        return original_count - len(self.library)

    def save_library(self, filepath="music_library.json"):
        """Save the music library to a JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.library, f)
            return True
        except Exception as e:
            print(f"Error saving library: {e}")
            return False

    def load_library(self, filepath="music_library.json"):
        """Load the music library from a JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.library = json.load(f)
                self.remove_missing_files()  # Clean up any missing files
                self.libraryUpdated.emit()
                return len(self.library)
        except Exception as e:
            print(f"Error loading library: {e}")
        return 0