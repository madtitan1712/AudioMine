import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QScrollArea, QListWidget, QListWidgetItem, QSplitter, QMenu, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread, QObject
from PyQt6.QtGui import (
    QPixmap, QFont, QPainter, QPen, QBrush, QColor, QLinearGradient,
    QAction, QIcon, QImage, QGuiApplication, QCursor
)
import io

try:
    import vlc

    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("VLC not available. Install python-vlc: pip install python-vlc")

# Try to import metadata parsing libraries
try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.mp4 import MP4

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Mutagen not available. Install for better metadata: pip install mutagen")


class MetadataExtractor(QObject):
    """Thread-safe metadata extraction for audio files"""
    metadata_ready = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.abort = False

    def extract_metadata(self, file_path):
        """Extract metadata from audio files using Mutagen"""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'year': None,
            'genre': None,
            'duration': 0,
            'cover_art': None
        }

        try:
            # Extract basic metadata
            if not MUTAGEN_AVAILABLE:
                # Basic fallback if mutagen not available
                filename = os.path.basename(file_path)
                metadata['title'] = os.path.splitext(filename)[0]
                return metadata

            # Load the file with mutagen
            audio = MutagenFile(file_path)
            if audio is None:
                return metadata

            # Try to extract common tags - handle different audio formats
            if isinstance(audio, MP3):
                metadata = self._extract_mp3_tags(audio, file_path)
            elif isinstance(audio, FLAC):
                metadata = self._extract_flac_tags(audio)
            elif isinstance(audio, OggVorbis):
                metadata = self._extract_ogg_tags(audio)
            elif isinstance(audio, MP4):
                metadata = self._extract_mp4_tags(audio)
            else:
                # Generic tag extraction
                if hasattr(audio, 'tags') and audio.tags:
                    for key in ['title', 'artist', 'album', 'date', 'genre']:
                        if key in audio:
                            metadata[key] = str(audio[key][0])

            # Get duration if available
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                metadata['duration'] = int(audio.info.length * 1000)  # Convert to ms

        except Exception as e:
            print(f"Metadata extraction error: {e}")
            # Fallback to filename
            filename = os.path.basename(file_path)
            metadata['title'] = os.path.splitext(filename)[0]

        return metadata

    def _extract_mp3_tags(self, audio, file_path):
        """Extract tags from MP3 files"""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'year': None,
            'genre': None,
            'duration': 0,
            'cover_art': None
        }

        try:
            # Try loading ID3 tags
            id3 = ID3(file_path)

            # Extract basic tags
            if 'TIT2' in id3:  # Title
                metadata['title'] = str(id3['TIT2'])
            if 'TPE1' in id3:  # Artist
                metadata['artist'] = str(id3['TPE1'])
            if 'TALB' in id3:  # Album
                metadata['album'] = str(id3['TALB'])
            if 'TDRC' in id3:  # Year
                metadata['year'] = str(id3['TDRC'])
            if 'TCON' in id3:  # Genre
                metadata['genre'] = str(id3['TCON'])

            # Extract album art
            if 'APIC:' in id3 or 'APIC' in id3:
                apic_key = 'APIC:' if 'APIC:' in id3 else 'APIC'
                artwork = id3[apic_key].data
                metadata['cover_art'] = artwork
        except:
            pass

        # Get duration
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            metadata['duration'] = int(audio.info.length * 1000)  # Convert to ms

        return metadata

    def _extract_flac_tags(self, audio):
        """Extract tags from FLAC files"""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'year': None,
            'genre': None,
            'duration': 0,
            'cover_art': None
        }

        # Extract basic tags
        if 'title' in audio:
            metadata['title'] = str(audio['title'][0])
        if 'artist' in audio:
            metadata['artist'] = str(audio['artist'][0])
        if 'album' in audio:
            metadata['album'] = str(audio['album'][0])
        if 'date' in audio:
            metadata['year'] = str(audio['date'][0])
        if 'genre' in audio:
            metadata['genre'] = str(audio['genre'][0])

        # Extract album art from pictures
        if audio.pictures:
            metadata['cover_art'] = audio.pictures[0].data

        # Get duration
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            metadata['duration'] = int(audio.info.length * 1000)  # Convert to ms

        return metadata

    def _extract_ogg_tags(self, audio):
        """Extract tags from OGG files"""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'year': None,
            'genre': None,
            'duration': 0,
            'cover_art': None
        }

        # Extract basic tags
        if 'title' in audio:
            metadata['title'] = str(audio['title'][0])
        if 'artist' in audio:
            metadata['artist'] = str(audio['artist'][0])
        if 'album' in audio:
            metadata['album'] = str(audio['album'][0])
        if 'date' in audio:
            metadata['year'] = str(audio['date'][0])
        if 'genre' in audio:
            metadata['genre'] = str(audio['genre'][0])

        # Get duration
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            metadata['duration'] = int(audio.info.length * 1000)  # Convert to ms

        return metadata

    def _extract_mp4_tags(self, audio):
        """Extract tags from MP4/M4A files"""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'year': None,
            'genre': None,
            'duration': 0,
            'cover_art': None
        }

        # Map of MP4 tags to metadata fields
        mp4_map = {
            '\xa9nam': 'title',
            '\xa9ART': 'artist',
            '\xa9alb': 'album',
            '\xa9day': 'year',
            '\xa9gen': 'genre'
        }

        # Extract tags
        for mp4_tag, meta_field in mp4_map.items():
            if mp4_tag in audio:
                metadata[meta_field] = str(audio[mp4_tag][0])

        # Extract cover art
        if 'covr' in audio:
            metadata['cover_art'] = audio['covr'][0]

        # Get duration
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            metadata['duration'] = int(audio.info.length * 1000)  # Convert to ms

        return metadata

    def process_file(self, file_path):
        """Process a file in a separate thread"""
        metadata = self.extract_metadata(file_path)
        self.metadata_ready.emit(metadata)


class CircularButton(QPushButton):
    """Enhanced circular button with hover effects"""

    def __init__(self, text="", size=56):
        super().__init__(text)
        self.setFixedSize(size, size)
        self.size = size
        self.hover = False
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.hover = True
        self.update()
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event):
        self.hover = False
        self.update()
        QApplication.restoreOverrideCursor()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define colors based on state
        if self.isDown():
            color = QColor("#1aa34a")  # Pressed color
        elif self.hover:
            color = QColor("#1ed760")  # Hover color
        else:
            color = QColor("#1db954")  # Normal color

        # Create gradient for more depth
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, color.lighter(110))
        gradient.setColorAt(1, color)

        # Draw button background
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, self.size - 4, self.size - 4)

        # Add subtle border
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawEllipse(2, 2, self.size - 4, self.size - 4)

        # Draw text/icon
        painter.setPen(QPen(QColor("white")))
        font = QFont("Arial", 16 if self.size > 40 else 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class CustomSlider(QSlider):
    """Enhanced slider with hover effects"""

    def __init__(self, orientation):
        super().__init__(orientation)
        self.setMouseTracking(True)
        self.hover = False
        self.hover_position = 0

    def enterEvent(self, event):
        self.hover = True
        self.update()
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event):
        self.hover = False
        self.update()
        QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event):
        self.hover_position = event.position().x()
        self.update()
        super().mouseMoveEvent(event)


class PlaylistItem(QListWidgetItem):
    """Custom playlist item with metadata"""

    def __init__(self, file_path, title="Unknown Title", artist="Unknown Artist", duration=0):
        super().__init__()
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.duration = duration

        # Set display text
        duration_str = self.format_duration(duration)
        self.setText(f"{title} - {artist} ({duration_str})")

    def format_duration(self, ms):
        """Format milliseconds to MM:SS"""
        if ms <= 0:
            return "0:00"

        seconds = ms // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}:{seconds:02d}"


class AlbumArtFrame(QFrame):
    """Custom frame to display album artwork with shadow effect"""

    def __init__(self, size=280):
        super().__init__()
        self.setFixedSize(size, size)
        self.setObjectName("albumArt")
        self.setStyleSheet("""
            #albumArt {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #353535,
                    stop:1 #252525
                );
                border-radius: 10px;
                border: 1px solid #444444;
            }
        """)

        # Apply drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        # Create layout for album art
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Album art display
        self.art_label = QLabel()
        self.art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.art_label)

        # Set default placeholder image
        self.set_placeholder_art()

    def set_placeholder_art(self):
        """Create a placeholder for when no album art is available"""
        size = self.width() - 2  # Account for border
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw gradient background
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor(70, 70, 70, 255))
        gradient.setColorAt(1, QColor(40, 40, 40, 255))
        painter.fillRect(0, 0, size, size, gradient)

        # Draw music note icon
        painter.setPen(QPen(QColor(180, 180, 180, 200), 2))
        font = QFont("Arial", 50)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        painter.end()

        self.set_artwork(pixmap)

    def set_artwork(self, pixmap_or_data):
        """Set the album artwork image from pixmap or raw image data"""
        try:
            if isinstance(pixmap_or_data, QPixmap):
                pixmap = pixmap_or_data
            else:
                # Convert raw image data to pixmap
                image = QImage()
                image.loadFromData(pixmap_or_data)
                pixmap = QPixmap.fromImage(image)

            # Scale pixmap to fit the frame while maintaining aspect ratio
            size = self.width() - 4  # Account for padding
            scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)

            self.art_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error setting artwork: {e}")
            self.set_placeholder_art()


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(900, 600)

        # Setup application font
        default_font = QFont("Segoe UI", 9)
        QApplication.setFont(default_font)

        # Apply stylesheet
        self.setStyleSheet(self.get_stylesheet())

        # Setup metadata extractor
        self.metadata_extractor = MetadataExtractor()
        self.metadata_extractor.metadata_ready.connect(self.update_with_metadata)

        # VLC initialization with better error handling
        self.vlc_available = VLC_AVAILABLE
        if self.vlc_available:
            try:
                self.vlc_instance = vlc.Instance()
                self.media_player = self.vlc_instance.media_player_new()
            except Exception as e:
                print(f"VLC init failed: {e}")
                self.vlc_available = False
                self.media_player = None
        else:
            self.media_player = None

        # Player state
        self.playlist = []
        self.current_track_index = -1
        self.is_playing = False
        self.is_slider_pressed = False

        # Create the UI
        self.init_ui()
        self.setup_shortcuts()

        # Set application icon
        # You can add your own app icon here

        # Set status
        self.statusBar().showMessage("Ready. " + ("VLC available." if self.vlc_available else "VLC not available."))

    def get_stylesheet(self):
        """Return the application's stylesheet"""
        return """
            QMainWindow {
                background: #121212;
                color: #ffffff;
            }
            QWidget {
                background-color: transparent;
                color: #ffffff;
            }
            QSplitter {
                background: #121212;
            }
            QSplitter::handle {
                background: #333333;
            }
            QScrollArea, QListWidget {
                background-color: #1e1e1e;
                border-radius: 8px;
                border: 1px solid #333333;
                padding: 5px;
            }
            QListWidget::item {
                color: #e0e0e0;
                padding: 6px;
                margin: 2px 0px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #333333;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: #2a2a2a;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QLabel#title {
                font-weight: bold;
                font-size: 20px;
                color: #ffffff;
            }
            QLabel#subtitle {
                color: #b3b3b3;
                font-size: 14px;
            }
            QLabel#time {
                color: #b3b3b3;
                font-size: 12px;
            }
            QLabel#info {
                color: #b3b3b3;
                font-size: 12px;
                font-style: italic;
            }
            QPushButton {
                background-color: #1db954;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
            QPushButton:pressed {
                background-color: #1aa34a;
            }
            QPushButton#navButton {
                background-color: #333333;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: normal;
                text-align: left;
            }
            QPushButton#navButton:hover {
                background-color: #444444;
                color: white;
            }
            QPushButton#openButton {
                background: transparent;
                color: #1db954;
                border: 2px solid #1db954;
                border-radius: 20px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#openButton:hover {
                background: rgba(29, 185, 84, 0.1);
                color: #1ed760;
                border-color: #1ed760;
            }
            QPushButton#openButton:pressed {
                background: rgba(29, 185, 84, 0.2);
                color: #1aa34a;
                border-color: #1aa34a;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #535353;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: none;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #1db954;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #1db954;
                border-radius: 2px;
            }

            /* Volume slider specific styles */
            QSlider#volumeSlider::groove:horizontal {
                height: 3px;
            }
            QSlider#volumeSlider::handle:horizontal {
                width: 10px;
                height: 10px;
                margin: -3.5px 0;
            }

            QMenuBar {
                background-color: #212121;
                color: white;
                padding: 2px;
                border-bottom: 1px solid #333333;
            }
            QMenuBar::item {
                background: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background: #333333;
            }
            QMenuBar::item:pressed {
                background: #444444;
            }
            QMenu {
                background-color: #212121;
                color: white;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #333333;
            }

            QToolBar {
                background: #212121;
                border: none;
                padding: 4px;
            }
            QToolBar::separator {
                background: #444444;
                width: 1px;
                height: 20px;
                margin: 0 8px;
            }
            QStatusBar {
                background: #212121;
                color: #b3b3b3;
                border-top: 1px solid #333333;
            }
            QScrollBar:vertical {
                border: none;
                background: #2a2a2a;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #606060;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #707070;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    def init_ui(self):
        """Initialize the user interface"""
        # Set up the menu bar
        self.create_menu_bar()

        # Set up the toolbar
        self.create_tool_bar()

        # Create status bar
        self.statusBar()

        # Create main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create splitter for main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Left panel - Library & Playlist
        left_panel = self.create_left_panel()

        # Right panel - Player controls
        right_panel = self.create_right_panel()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([300, 700])

        main_layout.addWidget(splitter)

        # Setup player and timer
        self.setup_media_player()

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        # Open file action
        open_action = QAction('&Open File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)

        # Open folder action
        open_folder_action = QAction('Open &Folder...', self)
        open_folder_action.setShortcut('Ctrl+D')
        open_folder_action.triggered.connect(self.open_folder)

        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Playback menu
        playback_menu = menubar.addMenu('&Playback')

        # Play/Pause action
        play_action = QAction('&Play/Pause', self)
        play_action.setShortcut('Space')
        play_action.triggered.connect(self.toggle_play_pause)

        # Next track action
        next_action = QAction('&Next Track', self)
        next_action.setShortcut('Ctrl+Right')
        next_action.triggered.connect(self.play_next)

        # Previous track action
        prev_action = QAction('P&revious Track', self)
        prev_action.setShortcut('Ctrl+Left')
        prev_action.triggered.connect(self.play_previous)

        playback_menu.addAction(play_action)
        playback_menu.addSeparator()
        playback_menu.addAction(next_action)
        playback_menu.addAction(prev_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        # About action
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_tool_bar(self):
        """Create the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # Open file action
        open_action = QAction('Open File', self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        # Add separator
        toolbar.addSeparator()

        # Play/Pause action
        self.play_action = QAction('Play', self)
        self.play_action.triggered.connect(self.toggle_play_pause)
        toolbar.addAction(self.play_action)

        # Next track action
        next_action = QAction('Next', self)
        next_action.triggered.connect(self.play_next)
        toolbar.addAction(next_action)

        # Previous track action
        prev_action = QAction('Previous', self)
        prev_action.triggered.connect(self.play_previous)
        toolbar.addAction(prev_action)

    def create_left_panel(self):
        """Create left panel with library and playlist"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Library section title
        library_title = QLabel("Playlist")
        library_title.setObjectName("title")

        # Create playlist widget
        self.playlist_widget = QListWidget()
        self.playlist_widget.setAlternatingRowColors(True)
        self.playlist_widget.itemDoubleClicked.connect(self.playlist_item_clicked)

        # Library controls
        library_controls = QHBoxLayout()

        # Add button
        self.add_button = QPushButton("Add Files")
        self.add_button.clicked.connect(self.open_file)

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_playlist)

        library_controls.addWidget(self.add_button)
        library_controls.addWidget(self.clear_button)

        left_layout.addWidget(library_title)
        left_layout.addWidget(self.playlist_widget)
        left_layout.addLayout(library_controls)

        return left_widget

    def create_right_panel(self):
        """Create right panel with player controls"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 10, 20, 10)
        right_layout.setSpacing(20)

        # Add top spacing
        right_layout.addStretch(1)

        # Album art display
        self.album_art = AlbumArtFrame(280)
        right_layout.addWidget(self.album_art, 0, Qt.AlignmentFlag.AlignCenter)

        # Track info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.song_title_label = QLabel("No song selected")
        self.song_title_label.setObjectName("title")
        self.song_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_title_label.setWordWrap(True)

        self.artist_album_label = QLabel("Choose a track to play" if self.vlc_available else "VLC not available")
        self.artist_album_label.setObjectName("subtitle")
        self.artist_album_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(self.song_title_label)
        info_layout.addWidget(self.artist_album_label)

        right_layout.addLayout(info_layout)

        # Progress slider and time
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)

        self.progress_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.progress_slider.setEnabled(self.vlc_available)

        # Time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setObjectName("time")
        self.total_time_label = QLabel("0:00")
        self.total_time_label.setObjectName("time")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)

        progress_layout.addWidget(self.progress_slider)
        progress_layout.addLayout(time_layout)

        right_layout.addLayout(progress_layout)

        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_button = CircularButton("⏮", 48)
        self.prev_button.clicked.connect(self.play_previous)
        self.prev_button.setEnabled(self.vlc_available)

        self.play_pause_button = CircularButton("▶", 64)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(self.vlc_available)

        self.next_button = CircularButton("⏭", 48)
        self.next_button.clicked.connect(self.play_next)
        self.next_button.setEnabled(self.vlc_available)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_button)

        right_layout.addLayout(controls_layout)

        # Volume controls
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(30, 0, 30, 0)

        volume_icon = QLabel("🔊")
        volume_icon.setFont(QFont("Arial", 16))
        volume_icon.setObjectName("subtitle")

        self.volume_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setEnabled(self.vlc_available)

        self.volume_label = QLabel("50%")
        self.volume_label.setObjectName("time")
        self.volume_label.setMinimumWidth(40)

        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)

        right_layout.addLayout(volume_layout)

        # Track info display
        self.track_info_label = QLabel("")
        self.track_info_label.setObjectName("info")
        self.track_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info_label.setWordWrap(True)
        right_layout.addWidget(self.track_info_label)

        # Add bottom spacing
        right_layout.addStretch(1)

        return right_widget

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Space bar - Play/Pause
        # Already handled in menu shortcuts

    def setup_media_player(self):
        """Setup the media player and timers"""
        if self.vlc_available:
            try:
                # Timer for UI updates
                self.timer = QTimer(self)
                self.timer.setInterval(200)
                self.timer.timeout.connect(self.update_ui)
                self.timer.start()

                # Set initial volume
                self.media_player.audio_set_volume(50)
            except Exception as e:
                print(f"Error setting up media player: {e}")
                self.vlc_available = False

    def open_file(self):
        """Open file dialog to select music files"""
        if not self.vlc_available:
            self.statusBar().showMessage("VLC not available. Cannot open files.")
            return

        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Music Files", "",
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a);;All Files (*)"
            )

            if file_paths:
                # Add files to playlist
                for file_path in file_paths:
                    self.add_to_playlist(file_path)

                # If this is the first track, start playing
                if self.current_track_index == -1:
                    self.current_track_index = 0
                    self.load_and_play_current_track()

                self.statusBar().showMessage(f"Added {len(file_paths)} files to playlist")
        except Exception as e:
            print(f"Error opening files: {e}")
            self.statusBar().showMessage(f"Error opening files: {str(e)}")

    def open_folder(self):
        """Open folder dialog to select music folder"""
        if not self.vlc_available:
            self.statusBar().showMessage("VLC not available. Cannot open files.")
            return

        try:
            folder_path = QFileDialog.getExistingDirectory(
                self, "Select Folder Containing Music Files"
            )

            if folder_path:
                # Get all audio files in the folder
                audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
                file_count = 0

                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in audio_extensions):
                            file_path = os.path.join(root, file)
                            self.add_to_playlist(file_path)
                            file_count += 1

                # If this is the first track, start playing
                if self.current_track_index == -1 and file_count > 0:
                    self.current_track_index = 0
                    self.load_and_play_current_track()

                self.statusBar().showMessage(f"Added {file_count} files from folder")
        except Exception as e:
            print(f"Error opening folder: {e}")
            self.statusBar().showMessage(f"Error opening folder: {str(e)}")

    def add_to_playlist(self, file_path):
        """Add a file to the playlist"""
        try:
            # Extract filename for initial display
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]

            # Create playlist item with basic info
            item = PlaylistItem(file_path, name_without_ext, "Loading...", 0)
            self.playlist_widget.addItem(item)
            self.playlist.append(file_path)

            # Start metadata extraction in a separate thread
            threading.Thread(
                target=self.extract_file_metadata,
                args=(file_path, len(self.playlist) - 1),
                daemon=True
            ).start()

        except Exception as e:
            print(f"Error adding to playlist: {e}")

    def extract_file_metadata(self, file_path, index):
        """Extract metadata for a file in a separate thread"""
        try:
            metadata = self.metadata_extractor.extract_metadata(file_path)
            metadata['file_path'] = file_path
            metadata['index'] = index
            self.metadata_extractor.metadata_ready.emit(metadata)
        except Exception as e:
            print(f"Error extracting metadata: {e}")

    def update_with_metadata(self, metadata):
        """Update UI with extracted metadata"""
        try:
            # Extract data from metadata
            file_path = metadata.get('file_path')
            index = metadata.get('index')
            title = metadata.get('title') or os.path.basename(file_path)
            artist = metadata.get('artist') or "Unknown Artist"
            album = metadata.get('album') or "Unknown Album"
            duration = metadata.get('duration') or 0
            cover_art = metadata.get('cover_art')

            # Update playlist item if index is valid
            if 0 <= index < self.playlist_widget.count():
                item = self.playlist_widget.item(index)
                if isinstance(item, PlaylistItem):
                    item.title = title
                    item.artist = artist
                    item.duration = duration
                    duration_str = self.format_time(duration)
                    item.setText(f"{title} - {artist} ({duration_str})")

            # If this is the current track, update UI
            if self.playlist and self.current_track_index >= 0 and index == self.current_track_index:
                self.song_title_label.setText(title)
                self.artist_album_label.setText(f"{artist} • {album}")

                # Update additional info
                genre = metadata.get('genre') or "Unknown Genre"
                year = metadata.get('year') or ""
                info_text = f"{genre}"
                if year:
                    info_text += f" • {year}"
                self.track_info_label.setText(info_text)

                # Update album art if available
                if cover_art:
                    self.album_art.set_artwork(cover_art)
                else:
                    self.album_art.set_placeholder_art()

        except Exception as e:
            print(f"Error updating metadata: {e}")

    def clear_playlist(self):
        """Clear the playlist"""
        self.playlist_widget.clear()
        self.playlist = []
        self.current_track_index = -1

        # Stop playback if active
        if self.vlc_available and self.is_playing:
            self.media_player.stop()
            self.is_playing = False
            self.play_pause_button.setText("▶")

        # Reset UI
        self.song_title_label.setText("No song selected")
        self.artist_album_label.setText("Choose a track to play" if self.vlc_available else "VLC not available")
        self.track_info_label.setText("")
        self.album_art.set_placeholder_art()
        self.current_time_label.setText("0:00")
        self.total_time_label.setText("0:00")
        self.progress_slider.setValue(0)

        self.statusBar().showMessage("Playlist cleared")

    def playlist_item_clicked(self, item):
        """Handle playlist item double-click"""
        if not isinstance(item, PlaylistItem):
            return

        # Find the index of the clicked item
        for i in range(self.playlist_widget.count()):
            if self.playlist_widget.item(i) == item:
                self.current_track_index = i
                self.load_and_play_current_track()
                break

    def load_and_play_current_track(self):
        """Load and play the current track from the playlist"""
        if not self.vlc_available or not self.playlist or self.current_track_index < 0:
            return

        try:
            # Highlight the current item in playlist
            self.playlist_widget.setCurrentRow(self.current_track_index)

            # Get the file path
            file_path = self.playlist[self.current_track_index]

            # Create a new media and play
            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            self.play_pause_button.setText("⏸")

            # Update UI with track info from playlist item
            item = self.playlist_widget.item(self.current_track_index)
            if isinstance(item, PlaylistItem):
                self.song_title_label.setText(item.title)
                self.artist_album_label.setText(f"{item.artist}")

            # Load metadata for this file (will update UI when ready)
            threading.Thread(
                target=self.extract_file_metadata,
                args=(file_path, self.current_track_index),
                daemon=True
            ).start()

            self.statusBar().showMessage(f"Playing: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"Error loading track: {e}")
            self.statusBar().showMessage(f"Error playing track: {str(e)}")

    def toggle_play_pause(self):
        """Toggle between play and pause states"""
        if not self.vlc_available:
            return

        try:
            if not self.media_player.get_media():
                self.open_file()
                return

            if self.is_playing:
                self.media_player.pause()
                self.is_playing = False
                self.play_pause_button.setText("▶")
                self.statusBar().showMessage("Paused")
            else:
                self.media_player.play()
                self.is_playing = True
                self.play_pause_button.setText("⏸")
                self.statusBar().showMessage("Playing")
        except Exception as e:
            print(f"Error toggling play/pause: {e}")

    def play_next(self):
        """Play the next track in the playlist"""
        if not self.vlc_available or not self.playlist:
            return

        try:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.load_and_play_current_track()
        except Exception as e:
            print(f"Error playing next track: {e}")

    def play_previous(self):
        """Play the previous track in the playlist"""
        if not self.vlc_available or not self.playlist:
            return

        try:
            self.current_track_index = (self.current_track_index - 1) % len(self.playlist)
            self.load_and_play_current_track()
        except Exception as e:
            print(f"Error playing previous track: {e}")

    def slider_pressed(self):
        """Handle when the progress slider is pressed"""
        self.is_slider_pressed = True

    def slider_released(self):
        """Handle when the progress slider is released"""
        self.is_slider_pressed = False
        self.set_position(self.progress_slider.value())

    def set_position(self, position):
        """Set the playback position based on slider value"""
        if not self.vlc_available:
            return

        try:
            if self.media_player.is_seekable():
                self.media_player.set_position(position / 1000.0)
        except Exception as e:
            print(f"Error setting position: {e}")

    def set_volume(self, volume):
        """Set the playback volume"""
        if not self.vlc_available:
            return

        try:
            self.media_player.audio_set_volume(volume)
            self.volume_label.setText(f"{volume}%")
        except Exception as e:
            print(f"Error setting volume: {e}")

    def format_time(self, ms):
        """Format milliseconds into MM:SS format"""
        if ms <= 0:
            return "0:00"

        try:
            seconds = ms // 1000
            minutes = seconds // 60
            seconds %= 60
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"

    def update_ui(self):
        """Update UI elements based on player state"""
        if not self.vlc_available:
            return

        try:
            if not self.is_slider_pressed:
                # Update progress slider and time labels
                try:
                    media_length = self.media_player.get_length()
                    current_time = self.media_player.get_time()

                    if media_length > 0:
                        position = int((current_time / media_length) * 1000)
                        self.progress_slider.setValue(position)
                        self.current_time_label.setText(self.format_time(current_time))
                        self.total_time_label.setText(self.format_time(media_length))
                except:
                    pass

            # Check for end of track
            if self.media_player.get_state() == vlc.State.Ended:
                self.play_next()
        except Exception as e:
            # Silent handling of UI update errors
            pass

    def show_about(self):
        """Show the about dialog"""
        # You could implement a proper about dialog here
        self.statusBar().showMessage("Music Player - A PyQt6 and VLC based music player")

    def closeEvent(self, event):
        """Handle application close event"""
        if self.vlc_available:
            try:
                if self.media_player:
                    self.media_player.stop()
                    self.media_player.release()
                if hasattr(self, 'timer'):
                    self.timer.stop()
            except:
                pass
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    try:
        player = MusicPlayer()
        player.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)