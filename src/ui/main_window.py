import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QMessageBox, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction
from src.ui.fullscreen_player import FullscreenPlayer
from src.ui.player_controls import PlayerControls
from src.ui.playlist_view import PlaylistView
from src.ui.library_view import LibraryView
from src.ui.visualizer import AudioVisualizer

from src.core.player import Player
from src.core.playlist_manager import PlaylistManager
from src.core.library_manager import LibraryManager
from src.core.metadata_handler import MetadataHandler

from src.utils.audio_effects import AudioEffects
from src.utils.constants import APP_NAME, DEFAULT_STYLES


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Core components
        self.player = Player()
        self.playlist_manager = PlaylistManager()
        self.library_manager = LibraryManager()
        self.metadata_handler = MetadataHandler()
        self.audio_effects = AudioEffects(self.player)

        # Setup UI
        self.setWindowTitle(APP_NAME)
        self.setGeometry(200, 100, 1000, 700)
        self.setMinimumSize(800, 600)

        # Apply styling
        self.setStyleSheet(DEFAULT_STYLES)

        # Initialize UI components
        self._init_ui()
        self._setup_connections()
        self._load_settings()

        # Show status message
        if not self.player.vlc_available:
            self.statusBar().showMessage("VLC not available. Please install python-vlc")
            QMessageBox.warning(
                self, "VLC Missing",
                "VLC player is not available. Some features may not work.\n\n"
                "Please install python-vlc: pip install python-vlc"
            )

    def _init_ui(self):
        """Initialize UI components"""
        # Central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Upper area: Visualization + album art
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)

        # Audio visualizer
        self.visualizer = AudioVisualizer()
        upper_layout.addWidget(self.visualizer)

        splitter.addWidget(upper_widget)

        # Center area: Tabs for library and playlists
        tabs = QTabWidget()
        self.library_view = LibraryView(self.library_manager, self.metadata_handler)
        self.playlist_view = PlaylistView(self.playlist_manager, self.metadata_handler)

        tabs.addTab(self.library_view, "Library")
        tabs.addTab(self.playlist_view, "Playlists")

        splitter.addWidget(tabs)

        # Bottom area: Player controls
        self.player_controls = PlayerControls(self.player, self.metadata_handler)

        # Add widgets to main layout
        main_layout.addWidget(splitter, 1)
        main_layout.addWidget(self.player_controls)

        self.setCentralWidget(central_widget)
        self.fullscreen_player = None

        # Setup menu bar
        self._setup_menu_bar()
        try:
            style_path = os.path.join("resources", "styles", "dark_theme.qss")
            if os.path.exists(style_path):
                with open(style_path, 'r') as f:
                    self.setStyleSheet(f.read())
            else:
                # Fall back to built-in styles
                self.setStyleSheet(DEFAULT_STYLES)
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            self.setStyleSheet(DEFAULT_STYLES)

    def _setup_menu_bar(self):
        """Setup application menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("&Open File...", self)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        open_folder_action = QAction("Open Fol&der...", self)
        open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        scan_library_action = QAction("&Scan Music Library...", self)
        scan_library_action.triggered.connect(self._scan_library)
        file_menu.addAction(scan_library_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Playback menu
        playback_menu = self.menuBar().addMenu("&Playback")

        play_action = QAction("&Play/Pause", self)
        play_action.triggered.connect(self._toggle_playback)
        playback_menu.addAction(play_action)

        next_action = QAction("&Next", self)
        next_action.triggered.connect(self._play_next)
        playback_menu.addAction(next_action)

        prev_action = QAction("Pre&vious", self)
        prev_action.triggered.connect(self._play_previous)
        playback_menu.addAction(prev_action)

        playback_menu.addSeparator()

        effects_action = QAction("&Equalizer...", self)
        effects_action.triggered.connect(self._show_equalizer)
        playback_menu.addAction(effects_action)

        # Playlist menu
        playlist_menu = self.menuBar().addMenu("P&laylist")

        new_playlist_action = QAction("&New Playlist...", self)
        new_playlist_action.triggered.connect(self.playlist_view.create_new_playlist)
        playlist_menu.addAction(new_playlist_action)

        # Help menu
        help_menu = self.menuBar().addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_connections(self):
        """Connect signals between components"""
        # Player signals
        self.player.stateChanged.connect(self._on_player_state_changed)

        # Playlist manager signals
        self.playlist_manager.currentTrackChanged.connect(self._on_current_track_changed)

        # Library view signals
        self.library_view.trackSelected.connect(self._play_track)
        self.library_view.addToPlaylist.connect(self.playlist_view.add_to_current_playlist)

        # Playlist view signals
        self.playlist_view.playTrack.connect(self._play_track)

        # Player controls signals
        self.player_controls.nextRequested.connect(self._play_next)
        self.player_controls.previousRequested.connect(self._play_previous)
        self.player_controls.fullscreenRequested.connect(self.show_fullscreen_player)

    def show_fullscreen_player(self):
        """Show the fullscreen player with proper error handling"""
        try:
            # Get current track info
            if not hasattr(self.player_controls, 'get_current_track_info'):
                # Fallback if method not available
                track_info = {
                    'path': getattr(self.player_controls, 'current_track_path', None),
                    'metadata': getattr(self.player_controls, 'current_metadata', None),
                    'album_art': getattr(self.player_controls, 'current_album_art', None)
                }
            else:
                track_info = self.player_controls.get_current_track_info()

            # Create fullscreen player if not exists or was closed
            if not self.fullscreen_player or not self.fullscreen_player.isVisible():
                from src.ui.fullscreen_player import FullscreenPlayer
                self.fullscreen_player = FullscreenPlayer(self.player, self.metadata_handler)
                self.fullscreen_player.closeRequested.connect(self.on_fullscreen_closed)

            # Update with current track if available
            if track_info.get('path') and track_info.get('metadata'):
                self.fullscreen_player.update_track(
                    track_info['path'],
                    track_info['metadata'],
                    track_info.get('album_art')
                )

            # Show fullscreen after everything is set up
            self.fullscreen_player.showFullScreen()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            print(f"Error showing fullscreen player: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open fullscreen mode: {str(e)}"
            )

    def on_fullscreen_closed(self):
        """Handle fullscreen player close"""
        try:
            # Update main UI if needed
            pass
        except Exception as e:
            print(f"Error in on_fullscreen_closed: {e}")
    def _on_player_state_changed(self, state):
        """Handle player state changes"""
        if state == 'playing':
            self.player_controls.set_playing_state(True)
        else:
            self.player_controls.set_playing_state(False)

        # Update window title with current track
        if state in ('playing', 'paused'):
            current_track = self.playlist_manager.get_current_track()
            if current_track:
                metadata = self.metadata_handler.extract_metadata(current_track)
                self.setWindowTitle(f"{metadata['title']} - {metadata['artist']} | {APP_NAME}")
        else:
            self.setWindowTitle(APP_NAME)

    def _on_current_track_changed(self, track_index, track_path):
        """Handle current track change in playlist"""
        if track_path and os.path.exists(track_path):
            self._play_track(track_path)

    def _play_track(self, file_path):
        """Play a specific audio track"""
        if not file_path or not os.path.exists(file_path):
            return

        # Load and play the file
        if self.player.load_media(file_path):
            self.player.play()

            # Update UI with track info
            metadata = self.metadata_handler.extract_metadata(file_path)
            self.player_controls.update_track_info(metadata)

            # Load album art
            album_art = self.metadata_handler.extract_album_art(file_path)
            self.player_controls.update_album_art(album_art)
        self.player_controls.current_track_path = file_path

    def _toggle_playback(self):
        """Toggle play/pause state"""
        if self.player.is_playing():
            self.player.pause()
        else:
            current_track = self.playlist_manager.get_current_track()
            if current_track:
                self.player.play()
            else:
                self._open_file()

    def _play_next(self):
        """Play next track in playlist"""
        next_track = self.playlist_manager.next_track()
        if next_track:
            self._play_track(next_track)

    def _play_previous(self):
        """Play previous track in playlist"""
        prev_track = self.playlist_manager.previous_track()
        if prev_track:
            self._play_track(prev_track)

    def _open_file(self):
        """Open audio file dialog"""
        file_filter = "Audio Files (*.mp3 *.flac *.wav *.ogg *.m4a);;All Files (*)"
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Audio Files", "", file_filter
        )

        if file_paths:
            # If no playlist exists, create one
            if not self.playlist_manager.playlists:
                self.playlist_manager.create_playlist("Default")
                self.playlist_manager.set_current_playlist("Default")

            # Add to current playlist and play first file
            if self.playlist_manager.current_playlist:
                self.playlist_manager.add_files_to_playlist(
                    self.playlist_manager.current_playlist, file_paths
                )

                if not self.player.is_playing():
                    self._play_track(file_paths[0])

            # Update library with these files
            for file in file_paths:
                if file not in self.library_manager.library:
                    self.library_manager.library.append(file)
            self.library_manager.libraryUpdated.emit()

    def _open_folder(self):
        """Open folder dialog to add all audio files"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Open Music Folder", ""
        )

        if folder_path:
            self.library_manager.scan_directory(folder_path)

    def _scan_library(self):
        """Open dialog to scan for music library"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Music Library Folder", ""
        )

        if folder_path:
            self.library_manager.scan_directory(folder_path)

    def _show_equalizer(self):
        """Show equalizer dialog"""
        self.audio_effects.show_equalizer_dialog(self)

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            "<p>A modern, modular music player application.</p>"
            "<p>Version 1.0</p>"
            "<p>Copyright © 2025</p>"
        )

    def _load_settings(self):
        """Load application settings"""
        settings = QSettings("AudioMine", "AudioMine")

        # Window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Load playlists
        self.playlist_manager.load_playlists()

        # Load library
        self.library_manager.load_library()

    def _save_settings(self):
        """Save application settings"""
        settings = QSettings("AudioMine", "AudioMine")

        # Window geometry
        settings.setValue("geometry", self.saveGeometry())

        # Save playlists
        self.playlist_manager.save_playlists()

        # Save library
        self.library_manager.save_library()

    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up player
        self.player.cleanup()

        # Save settings
        self._save_settings()

        event.accept()
