from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QSlider, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
import os

from src.ui.components.circular_button import CircularButton
from src.ui.components.custom_slider import CustomSlider
from src.ui.components.album_art import AlbumArtDisplay


class PlayerControls(QWidget):
    """Widget containing player controls (play/pause, next, prev, etc)"""

    # Signals
    nextRequested = pyqtSignal()
    previousRequested = pyqtSignal()
    fullscreenRequested = pyqtSignal()  # New signal for full-screen mode

    def __init__(self, player, metadata_handler):
        super().__init__()
        self.player = player
        self.metadata_handler = metadata_handler
        self.is_slider_pressed = False
        self.current_track_path = None  # Keep track of current track path
        self.current_metadata = None  # Keep track of current metadata
        self.current_album_art = None  # Keep track of current album art
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)

        # Now playing info
        now_playing_layout = QHBoxLayout()

        # Album art (clickable for full-screen mode)
        self.album_art = AlbumArtDisplay()
        self.album_art.setFixedSize(60, 60)
        self.album_art.setCursor(Qt.CursorShape.PointingHandCursor)  # Change cursor on hover
        now_playing_layout.addWidget(self.album_art)

        # Track info
        track_info_layout = QVBoxLayout()
        self.song_title_label = QLabel("No track playing")
        self.song_title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.artist_album_label = QLabel("")

        track_info_layout.addWidget(self.song_title_label)
        track_info_layout.addWidget(self.artist_album_label)
        track_info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        now_playing_layout.addLayout(track_info_layout)
        now_playing_layout.addStretch()

        # Fullscreen button
        self.fullscreen_button = QPushButton("📺")  # Fullscreen icon
        self.fullscreen_button.setToolTip("Full-screen Mode")
        self.fullscreen_button.setFixedSize(32, 32)
        self.fullscreen_button.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; font-size: 18px; } "
            "QPushButton:hover { color: #1db954; }"
        )
        now_playing_layout.addWidget(self.fullscreen_button)

        # Progress display
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")

        # Add playing info to main layout
        layout.addLayout(now_playing_layout)

        # Progress slider layout
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.current_time_label)

        self.progress_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        progress_layout.addWidget(self.progress_slider, 1)

        progress_layout.addWidget(self.total_time_label)
        layout.addLayout(progress_layout)

        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Previous button
        self.previous_button = CircularButton("⏮", 40)
        controls_layout.addWidget(self.previous_button)

        # Play/Pause button
        self.play_pause_button = CircularButton("▶", 56)
        controls_layout.addWidget(self.play_pause_button)

        # Next button
        self.next_button = CircularButton("⏭", 40)
        controls_layout.addWidget(self.next_button)

        layout.addLayout(controls_layout)

        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        volume_icon = QLabel("🔊")
        volume_layout.addWidget(volume_icon)

        self.volume_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("80%")
        self.volume_label.setFixedWidth(36)
        volume_layout.addWidget(self.volume_label)

        layout.addLayout(volume_layout)

    def setup_connections(self):
        """Connect signals and slots"""
        # Player connections
        self.player.positionChanged.connect(self.update_position)

        # Button connections
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.next_button.clicked.connect(self.nextRequested.emit)
        self.previous_button.clicked.connect(self.previousRequested.emit)
        self.fullscreen_button.clicked.connect(self.fullscreenRequested.emit)

        # Album art click for fullscreen
        self.album_art.mousePressEvent = lambda event: self.fullscreenRequested.emit()

        # Slider connections
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)

        self.volume_slider.valueChanged.connect(self.set_volume)

    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def set_playing_state(self, is_playing):
        """Update UI to reflect playing state"""
        self.play_pause_button.setText("⏸" if is_playing else "▶")

    def update_position(self, current_ms, total_ms):
        """Update position slider and time labels"""
        if not self.is_slider_pressed and total_ms > 0:
            position = int((current_ms / total_ms) * 1000)
            self.progress_slider.setValue(position)
            self.current_time_label.setText(self.format_time(current_ms))
            self.total_time_label.setText(self.format_time(total_ms))

    def slider_pressed(self):
        """Handle slider press event"""
        self.is_slider_pressed = True

    def slider_released(self):
        """Handle slider release event"""
        self.is_slider_pressed = False
        position = self.progress_slider.value() / 1000.0
        self.player.set_position(position)

    def set_volume(self, volume):
        """Set player volume"""
        self.player.set_volume(volume)
        self.volume_label.setText(f"{volume}%")

    def format_time(self, ms):
        """Format milliseconds to mm:ss"""
        if ms <= 0:
            return "0:00"

        seconds = ms // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}:{seconds:02d}"

    def update_track_info(self, metadata):
        """Update track information display"""
        self.current_metadata = metadata

        if metadata:
            self.song_title_label.setText(metadata['title'])
            self.artist_album_label.setText(f"{metadata['artist']} - {metadata['album']}")
        else:
            self.song_title_label.setText("No track playing")
            self.artist_album_label.setText("")

    def update_album_art(self, pixmap):
        """Update album art display"""
        self.current_album_art = pixmap
        self.album_art.set_album_art(pixmap)

    def get_current_track_info(self):
        """Get current track information for fullscreen mode"""
        return {
            'path': self.current_track_path,
            'metadata': self.current_metadata,
            'album_art': self.current_album_art
        }