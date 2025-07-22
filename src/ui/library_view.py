from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QProgressBar,
    QFileDialog, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QIcon, QColor


class LibraryView(QWidget):
    """Widget for displaying and managing the music library"""

    # Signals
    trackSelected = pyqtSignal(str)  # Emits file path when track is played
    addToPlaylist = pyqtSignal(str)  # Emits file path when track is added to playlist

    def __init__(self, library_manager, metadata_handler):
        super().__init__()
        self.library_manager = library_manager
        self.metadata_handler = metadata_handler
        self.init_ui()
        self.setup_connections()

        # Initially populate library
        self.populate_library()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search library...")

        scan_button = QPushButton("Scan Folder")

        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(scan_button)

        layout.addLayout(search_layout)

        # Progress bar for scanning (initially hidden)
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        layout.addWidget(self.scan_progress)

        # Library table
        self.library_table = QTableWidget(0, 5)  # Rows, Columns
        self.library_table.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Genre", "Duration"])
        self.library_table.setAlternatingRowColors(True)
        self.library_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.library_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Set column widths
        header = self.library_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Artist
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Album
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Genre
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Duration

        layout.addWidget(self.library_table, 1)

        # Control buttons
        button_layout = QHBoxLayout()

        self.play_button = QPushButton("Play Selected")
        self.add_to_playlist_button = QPushButton("Add to Playlist")
        clear_button = QPushButton("Clear Search")

        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.add_to_playlist_button)
        button_layout.addWidget(clear_button)

        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("0 tracks in library")
        layout.addWidget(self.status_label)

        # Connect buttons
        scan_button.clicked.connect(self.scan_music_folder)
        clear_button.clicked.connect(self.clear_search)
        self.search_input.textChanged.connect(self.filter_library)
        self.play_button.clicked.connect(self.play_selected)
        self.add_to_playlist_button.clicked.connect(self.add_selected_to_playlist)
        self.library_table.doubleClicked.connect(self.on_table_double_clicked)
        self.library_table.customContextMenuRequested.connect(self.show_context_menu)

    def setup_connections(self):
        """Connect signals from the library manager"""
        self.library_manager.scanStarted.connect(self.on_scan_started)
        self.library_manager.scanProgress.connect(self.on_scan_progress)
        self.library_manager.scanFinished.connect(self.on_scan_finished)
        self.library_manager.libraryUpdated.connect(self.populate_library)

    def populate_library(self):
        """Populate the library table with tracks"""
        # Clear table
        self.library_table.setRowCount(0)

        # Get library tracks
        tracks = self.library_manager.get_library()

        # Filter if search is active
        search_text = self.search_input.text().lower()
        if search_text:
            filtered_tracks = []
            for track in tracks:
                metadata = self.metadata_handler.extract_metadata(track)
                if (search_text in metadata['title'].lower() or
                        search_text in metadata['artist'].lower() or
                        search_text in metadata['album'].lower()):
                    filtered_tracks.append(track)
            tracks = filtered_tracks

        # Populate table
        self.library_table.setSortingEnabled(False)  # Disable sorting while updating

        for track in tracks:
            metadata = self.metadata_handler.extract_metadata(track)

            # Create new row
            row = self.library_table.rowCount()
            self.library_table.insertRow(row)

            # Add track data
            self.library_table.setItem(row, 0, QTableWidgetItem(metadata['title']))
            self.library_table.setItem(row, 1, QTableWidgetItem(metadata['artist']))
            self.library_table.setItem(row, 2, QTableWidgetItem(metadata['album']))
            self.library_table.setItem(row, 3, QTableWidgetItem(metadata.get('genre', 'Unknown')))

            # Format duration
            duration = "Unknown"
            if 'length' in metadata:
                minutes = int(metadata['length']) // 60
                seconds = int(metadata['length']) % 60
                duration = f"{minutes}:{seconds:02d}"

            self.library_table.setItem(row, 4, QTableWidgetItem(duration))

            # Store file path as item data
            for col in range(5):
                self.library_table.item(row, col).setData(Qt.ItemDataRole.UserRole, track)

        self.library_table.setSortingEnabled(True)  # Re-enable sorting

        # Update status
        self.status_label.setText(f"{len(tracks)} tracks in library")

    def filter_library(self):
        """Filter library based on search text"""
        self.populate_library()

    def clear_search(self):
        """Clear search field and show all library"""
        self.search_input.clear()
        self.populate_library()

    def scan_music_folder(self):
        """Open folder dialog and scan for music"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Music Folder", ""
        )

        if folder_path:
            self.library_manager.scan_directory(folder_path)

    @pyqtSlot()
    def on_scan_started(self):
        """Handle scan start"""
        self.scan_progress.setValue(0)
        self.scan_progress.setVisible(True)
        self.status_label.setText("Scanning...")

    @pyqtSlot(int, int)
    def on_scan_progress(self, files_found, total_scanned):
        """Handle scan progress updates"""
        self.scan_progress.setValue(files_found)
        self.scan_progress.setMaximum(max(files_found, 1))  # Avoid division by zero
        self.status_label.setText(f"Scanning... Found {files_found} tracks")

    @pyqtSlot(int)
    def on_scan_finished(self, new_files):
        """Handle scan completion"""
        self.scan_progress.setVisible(False)
        self.status_label.setText(f"Scan complete. Added {new_files} new tracks")

        # Hide status after a delay
        QTimer.singleShot(3000, lambda: self.status_label.setText(
            f"{len(self.library_manager.get_library())} tracks in library")
                          )

    def play_selected(self):
        """Play selected track"""
        selected_rows = self.library_table.selectedItems()

        if not selected_rows:
            return

        # Get file path from first selected item
        file_path = selected_rows[0].data(Qt.ItemDataRole.UserRole)
        self.trackSelected.emit(file_path)

    def add_selected_to_playlist(self):
        """Add selected tracks to playlist"""
        selected_rows = set()
        for item in self.library_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        # Get file paths for all selected rows
        file_paths = []
        for row in selected_rows:
            file_path = self.library_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            file_paths.append(file_path)

        # Emit signal for each file
        for file_path in file_paths:
            self.addToPlaylist.emit(file_path)

    def on_table_double_clicked(self, index):
        """Handle double click on table item"""
        file_path = self.library_table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.trackSelected.emit(file_path)

    def show_context_menu(self, position):
        """Show context menu for library items"""
        menu = QMenu(self)

        play_action = QAction("Play", self)
        add_action = QAction("Add to Playlist", self)

        menu.addAction(play_action)
        menu.addAction(add_action)

        # Connect actions
        play_action.triggered.connect(self.play_selected)
        add_action.triggered.connect(self.add_selected_to_playlist)

        menu.exec(self.library_table.mapToGlobal(position))