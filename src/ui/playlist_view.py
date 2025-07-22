from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QComboBox, QInputDialog, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction


class PlaylistView(QWidget):
    """Widget for displaying and managing playlists"""

    # Signals
    playTrack = pyqtSignal(str)  # Emits file path when track is played

    def __init__(self, playlist_manager, metadata_handler):
        super().__init__()
        self.playlist_manager = playlist_manager
        self.metadata_handler = metadata_handler
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)

        # Playlist selector
        playlist_selector_layout = QHBoxLayout()

        self.playlist_selector = QComboBox()
        self.playlist_selector.setMinimumWidth(200)

        create_playlist_button = QPushButton("New Playlist")

        playlist_selector_layout.addWidget(QLabel("Playlist:"))
        playlist_selector_layout.addWidget(self.playlist_selector, 1)
        playlist_selector_layout.addWidget(create_playlist_button)

        layout.addLayout(playlist_selector_layout)

        # Playlist tracks
        self.tracks_list = QListWidget()
        self.tracks_list.setAlternatingRowColors(True)
        self.tracks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        layout.addWidget(self.tracks_list, 1)

        # Control buttons
        button_layout = QHBoxLayout()

        self.play_button = QPushButton("Play")
        self.add_files_button = QPushButton("Add Files")
        self.remove_button = QPushButton("Remove Selected")

        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.add_files_button)
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

        # Connect buttons
        create_playlist_button.clicked.connect(self.create_new_playlist)
        self.play_button.clicked.connect(self.play_selected)
        self.add_files_button.clicked.connect(self.add_files)
        self.remove_button.clicked.connect(self.remove_selected)
        self.tracks_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tracks_list.customContextMenuRequested.connect(self.show_context_menu)

        # Initial state
        self.update_playlist_selector()

    def setup_connections(self):
        """Connect signals from the playlist manager"""
        self.playlist_manager.playlistChanged.connect(self.on_playlist_changed)
        self.playlist_manager.currentTrackChanged.connect(self.on_current_track_changed)
        self.playlist_selector.currentTextChanged.connect(self.on_playlist_selected)

    def update_playlist_selector(self):
        """Update the playlist selector combobox"""
        current = self.playlist_selector.currentText()

        self.playlist_selector.clear()

        # Add all playlists
        for name in self.playlist_manager.playlists.keys():
            self.playlist_selector.addItem(name)

        # Restore previous selection if it still exists
        index = self.playlist_selector.findText(current)
        if index >= 0:
            self.playlist_selector.setCurrentIndex(index)
        elif self.playlist_selector.count() > 0:
            self.playlist_selector.setCurrentIndex(0)
            self.on_playlist_selected(self.playlist_selector.currentText())

    def on_playlist_changed(self, playlist_name, tracks):
        """Handle playlist content changes"""
        current_playlist = self.playlist_selector.currentText()

        # Update playlist selector if needed
        if playlist_name not in self.playlist_manager.playlists:
            self.update_playlist_selector()

        # Update tracks list if this is the current playlist
        if playlist_name == current_playlist:
            self.update_tracks_list(tracks)

    def update_tracks_list(self, tracks):
        """Update the tracks list with new tracks"""
        self.tracks_list.clear()

        for track_path in tracks:
            metadata = self.metadata_handler.extract_metadata(track_path)
            display_text = f"{metadata['title']} - {metadata['artist']}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, track_path)  # Store file path
            self.tracks_list.addItem(item)

    def on_playlist_selected(self, playlist_name):
        """Handle playlist selection change"""
        if not playlist_name:
            return

        if playlist_name in self.playlist_manager.playlists:
            # Update tracks list
            tracks = self.playlist_manager.playlists[playlist_name]
            self.update_tracks_list(tracks)

            # Set as current playlist
            self.playlist_manager.set_current_playlist(playlist_name)

    def on_current_track_changed(self, track_index, track_path):
        """Handle current track change"""
        # Highlight the current track in the list
        for i in range(self.tracks_list.count()):
            item = self.tracks_list.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)

            if path == track_path:
                # Highlight this item
                self.tracks_list.setCurrentItem(item)
                break

    def create_new_playlist(self):
        """Create a new playlist"""
        name, ok = QInputDialog.getText(
            self, "New Playlist", "Enter playlist name:"
        )

        if ok and name:
            if name in self.playlist_manager.playlists:
                QMessageBox.warning(
                    self, "Duplicate Name",
                    f"A playlist named '{name}' already exists."
                )
            else:
                self.playlist_manager.create_playlist(name)
                self.update_playlist_selector()

                # Select the new playlist
                index = self.playlist_selector.findText(name)
                if index >= 0:
                    self.playlist_selector.setCurrentIndex(index)

    def add_files(self):
        """Add files to the current playlist"""
        from PyQt6.QtWidgets import QFileDialog

        # Check if we have a current playlist
        current_playlist = self.playlist_selector.currentText()
        if not current_playlist:
            QMessageBox.warning(
                self, "No Playlist",
                "Please create or select a playlist first."
            )
            return

        # Open file dialog
        file_filter = "Audio Files (*.mp3 *.flac *.wav *.ogg *.m4a);;All Files (*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Audio Files", "", file_filter
        )

        if file_paths:
            self.playlist_manager.add_files_to_playlist(current_playlist, file_paths)

    def add_to_current_playlist(self, file_paths):
        """Add files to current playlist (called from outside)"""
        current_playlist = self.playlist_selector.currentText()

        if not current_playlist:
            # If no playlist exists, create one
            self.playlist_manager.create_playlist("Default")
            self.update_playlist_selector()
            current_playlist = "Default"

        if current_playlist:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            self.playlist_manager.add_files_to_playlist(current_playlist, file_paths)

    def play_selected(self):
        """Play the selected track"""
        selected_items = self.tracks_list.selectedItems()

        if not selected_items:
            return

        track_path = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Find the index of this track
        current_playlist = self.playlist_selector.currentText()
        if current_playlist in self.playlist_manager.playlists:
            try:
                track_index = self.playlist_manager.playlists[current_playlist].index(track_path)

                # Update the current track in playlist manager
                self.playlist_manager.current_track_index = track_index

                # Emit signal to play this track
                self.playTrack.emit(track_path)
            except ValueError:
                pass

    def remove_selected(self):
        """Remove selected tracks from playlist"""
        selected_items = self.tracks_list.selectedItems()

        if not selected_items:
            return

        current_playlist = self.playlist_selector.currentText()

        # Remove in reverse order to avoid index shifting
        indexes = [self.tracks_list.row(item) for item in selected_items]
        indexes.sort(reverse=True)

        for index in indexes:
            self.playlist_manager.remove_from_playlist(current_playlist, index)

    def on_item_double_clicked(self, item):
        """Handle double click on track item"""
        track_path = item.data(Qt.ItemDataRole.UserRole)
        self.playTrack.emit(track_path)

    def show_context_menu(self, position):
        """Show context menu for playlist items"""
        menu = QMenu(self)

        play_action = QAction("Play", self)
        remove_action = QAction("Remove", self)

        menu.addAction(play_action)
        menu.addAction(remove_action)

        # Connect actions
        play_action.triggered.connect(self.play_selected)
        remove_action.triggered.connect(self.remove_selected)

        menu.exec(self.tracks_list.mapToGlobal(position))