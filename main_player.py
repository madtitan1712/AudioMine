import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPainter, QPen, QBrush, QColor

try:
    import vlc

    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("VLC not available. Install python-vlc: pip install python-vlc")


class CircularButton(QPushButton):
    """Custom circular button with better styling"""

    def __init__(self, text="", size=56):
        super().__init__(text)
        self.setFixedSize(size, size)
        self.size = size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Button background
        if self.isPressed():
            color = QColor("#1ed760")
        elif self.underMouse():
            color = QColor("#1fdf64")
        else:
            color = QColor("#1db954")

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.size, self.size)

        # Button text/icon
        painter.setPen(QPen(QColor("white")))
        font = QFont("Arial", 16 if self.size > 40 else 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class CustomSlider(QSlider):
    """Custom slider with hover effects"""

    def __init__(self, orientation):
        super().__init__(orientation)
        self.setMouseTracking(True)
        self.hovering = False

    def enterEvent(self, event):
        self.hovering = True
        self.update()

    def leaveEvent(self, event):
        self.hovering = False
        self.update()


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player")
        self.setGeometry(200, 100, 480, 720)
        self.setMinimumSize(400, 600)

        # Initialize VLC with safer parameters
        if VLC_AVAILABLE:
            try:
                # More conservative VLC initialization
                self.vlc_instance = vlc.Instance([
                    '--no-xlib',  # Disable X11 (helps on some systems)
                    '--quiet',  # Reduce VLC output
                    '--intf=dummy'  # No interface
                ])
                self.media_player = self.vlc_instance.media_player_new()
                self.vlc_available = True
            except Exception as e:
                print(f"VLC initialization failed: {e}")
                self.vlc_available = False
                self.media_player = None
        else:
            self.vlc_available = False
            self.media_player = None

        self.is_playing = False
        self.current_media_path = None

        # Apply refined dark theme
        self.setStyleSheet(self.get_stylesheet())
        self.init_ui()

    def get_stylesheet(self):
        return """
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #191414,
                    stop:1 #121212
                );
                color: #ffffff;
            }

            QWidget {
                background: transparent;
                color: #ffffff;
            }

            QLabel {
                color: #ffffff;
                background: transparent;
            }

            QLabel#subtitle {
                color: #a7a7a7;
            }

            QLabel#error {
                color: #ff6b6b;
                font-style: italic;
            }

            QPushButton#openButton {
                background: transparent;
                color: #1db954;
                border: 2px solid #1db954;
                border-radius: 20px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 20px;
            }

            QPushButton#openButton:hover {
                background: rgba(29, 185, 84, 0.1);
                border-color: #1ed760;
                color: #1ed760;
            }

            QPushButton#openButton:pressed {
                background: rgba(29, 185, 84, 0.2);
                border-color: #1aa34a;
                color: #1aa34a;
            }

            QPushButton#openButton:disabled {
                background: transparent;
                color: #666666;
                border-color: #666666;
            }

            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #404040;
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

            QSlider::add-page:horizontal {
                background: #404040;
                border-radius: 2px;
            }

            /* Volume slider styling */
            QSlider#volumeSlider::groove:horizontal {
                height: 3px;
            }

            QSlider#volumeSlider::handle:horizontal {
                width: 10px;
                height: 10px;
                margin: -3.5px 0;
                border-radius: 5px;
            }

            QSlider#volumeSlider::handle:horizontal:hover {
                width: 12px;
                height: 12px;
                margin: -4.5px 0;
                border-radius: 6px;
            }
        """

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with more generous spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)

        # Top spacer
        main_layout.addStretch(1)

        # Album art section
        album_section = self.create_album_section()
        main_layout.addWidget(album_section)
        main_layout.addSpacing(30)

        # Song info section
        info_section = self.create_info_section()
        main_layout.addWidget(info_section)
        main_layout.addSpacing(40)

        # Progress section
        progress_section = self.create_progress_section()
        main_layout.addWidget(progress_section)
        main_layout.addSpacing(30)

        # Controls section
        controls_section = self.create_controls_section()
        main_layout.addWidget(controls_section)
        main_layout.addSpacing(25)

        # Volume section
        volume_section = self.create_volume_section()
        main_layout.addWidget(volume_section)

        # Bottom spacer
        main_layout.addStretch(1)

        # Open file button at bottom
        open_layout = QHBoxLayout()
        open_layout.addStretch()
        self.open_button = QPushButton("Choose Music")
        self.open_button.setObjectName("openButton")
        self.open_button.clicked.connect(self.open_file)
        if not self.vlc_available:
            self.open_button.setEnabled(False)
            self.open_button.setText("VLC Not Available")
        open_layout.addWidget(self.open_button)
        open_layout.addStretch()
        main_layout.addLayout(open_layout)
        main_layout.addSpacing(20)

        self.setup_media_player()

    def create_album_section(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Album art with subtle shadow
        self.album_art_label = QLabel()
        self.album_art_label.setFixedSize(280, 280)
        self.album_art_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #404040,
                    stop:1 #2a2a2a
                );
                border-radius: 12px;
                border: 1px solid #333333;
            }
        """)

        # Add shadow effect
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 8)
            shadow.setColor(QColor(0, 0, 0, 60))
            self.album_art_label.setGraphicsEffect(shadow)
        except:
            pass  # Skip shadow if it causes issues

        # Create placeholder with music note
        self.create_placeholder_art()

        layout.addWidget(self.album_art_label)
        return container

    def create_placeholder_art(self):
        pixmap = QPixmap(280, 280)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient background
        gradient = QColor(64, 64, 64)
        painter.fillRect(pixmap.rect(), gradient)

        # Music note icon
        painter.setPen(QPen(QColor(160, 160, 160), 2))
        font = QFont("Arial", 48)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        painter.end()

        self.album_art_label.setPixmap(pixmap)

    def create_info_section(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Song title
        self.song_title_label = QLabel("No song selected")
        self.song_title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.song_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_title_label.setWordWrap(True)

        # Artist and album
        if self.vlc_available:
            subtitle_text = "Choose a track to play"
        else:
            subtitle_text = "VLC media library not available"

        self.artist_album_label = QLabel(subtitle_text)
        self.artist_album_label.setObjectName("subtitle" if self.vlc_available else "error")
        self.artist_album_label.setFont(QFont("Arial", 14))
        self.artist_album_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.song_title_label)
        layout.addWidget(self.artist_album_label)
        return container

    def create_progress_section(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Progress slider
        self.progress_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.progress_slider.setEnabled(self.vlc_available)

        # Time labels
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)

        self.current_time_label = QLabel("0:00")
        self.current_time_label.setFont(QFont("Arial", 12))
        self.current_time_label.setObjectName("subtitle")

        self.total_time_label = QLabel("0:00")
        self.total_time_label.setFont(QFont("Arial", 12))
        self.total_time_label.setObjectName("subtitle")

        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)

        layout.addWidget(self.progress_slider)
        layout.addLayout(time_layout)
        return container

    def create_controls_section(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(25)

        # Previous button
        self.prev_button = CircularButton("⏮", 48)
        self.prev_button.clicked.connect(self.play_previous)
        self.prev_button.setEnabled(self.vlc_available)

        # Play/pause button (larger)
        self.play_pause_button = CircularButton("▶", 64)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(self.vlc_available)

        # Next button
        self.next_button = CircularButton("⏭", 48)
        self.next_button.clicked.connect(self.play_next)
        self.next_button.setEnabled(self.vlc_available)

        layout.addWidget(self.prev_button)
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.next_button)
        return container

    def create_volume_section(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)

        # Volume icon
        volume_icon = QLabel("🔊")
        volume_icon.setFont(QFont("Arial", 16))
        volume_icon.setObjectName("subtitle")

        # Volume slider
        self.volume_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setMaximumWidth(120)
        self.volume_slider.setEnabled(self.vlc_available)

        # Volume percentage
        self.volume_label = QLabel("50%")
        self.volume_label.setFont(QFont("Arial", 12))
        self.volume_label.setObjectName("subtitle")
        self.volume_label.setMinimumWidth(35)

        layout.addWidget(volume_icon)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.volume_label)
        return container

    def setup_media_player(self):
        # Playlist management
        self.playlist = []
        self.current_track_index = -1
        self.is_slider_pressed = False

        if self.vlc_available:
            # Timer for UI updates - with safer interval
            self.timer = QTimer(self)
            self.timer.setInterval(200)  # Slower update interval
            self.timer.timeout.connect(self.update_ui)
            self.timer.start()

            # Set initial volume safely
            try:
                self.media_player.audio_set_volume(50)
            except:
                pass

    # Media player methods with better error handling
    def open_file(self):
        if not self.vlc_available:
            return

        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Music Files", "",
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a);;All Files (*)"
            )
            if file_paths:
                self.playlist = file_paths
                self.current_track_index = 0
                self.load_and_play_current_track()
        except Exception as e:
            print(f"Error opening file: {e}")
            self.song_title_label.setText("Error loading file")
            self.artist_album_label.setText("Please try another file")

    def load_and_play_current_track(self):
        if not self.vlc_available or not self.playlist or self.current_track_index < 0:
            return

        try:
            file_path = self.playlist[self.current_track_index]
            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.media_player.play()
            self.is_playing = True
            self.play_pause_button.setText("⏸")

            # Update UI with track info
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]

            # Safely try to get metadata
            try:
                media.parse()
                # Give it a moment to parse
                QApplication.processEvents()

                title = media.get_meta(vlc.Meta.Title) or name_without_ext
                artist = media.get_meta(vlc.Meta.Artist) or "Unknown Artist"
                album = media.get_meta(vlc.Meta.Album) or "Unknown Album"
            except:
                title = name_without_ext
                artist = "Unknown Artist"
                album = "Unknown Album"

            self.song_title_label.setText(title)
            self.artist_album_label.setText(f"{artist} • {album}")

        except Exception as e:
            print(f"Error loading track: {e}")
            self.song_title_label.setText("Playback Error")
            self.artist_album_label.setText("Could not play this file")

    def toggle_play_pause(self):
        if not self.vlc_available:
            return

        try:
            if self.media_player.get_media() is None:
                self.open_file()
                return

            if self.is_playing:
                self.media_player.pause()
                self.is_playing = False
                self.play_pause_button.setText("▶")
            else:
                self.media_player.play()
                self.is_playing = True
                self.play_pause_button.setText("⏸")
        except Exception as e:
            print(f"Error toggling playback: {e}")

    def play_next(self):
        if not self.vlc_available or not self.playlist:
            return
        try:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.load_and_play_current_track()
        except Exception as e:
            print(f"Error playing next: {e}")

    def play_previous(self):
        if not self.vlc_available or not self.playlist:
            return
        try:
            self.current_track_index = (self.current_track_index - 1) % len(self.playlist)
            self.load_and_play_current_track()
        except Exception as e:
            print(f"Error playing previous: {e}")

    def set_volume(self, volume):
        if not self.vlc_available:
            return
        try:
            self.media_player.audio_set_volume(volume)
            self.volume_label.setText(f"{volume}%")
        except Exception as e:
            print(f"Error setting volume: {e}")

    def set_position(self, position):
        if not self.vlc_available:
            return
        try:
            if self.media_player.is_seekable():
                self.media_player.set_position(position / 1000.0)
        except Exception as e:
            print(f"Error setting position: {e}")

    def slider_pressed(self):
        self.is_slider_pressed = True

    def slider_released(self):
        self.is_slider_pressed = False
        self.set_position(self.progress_slider.value())

    def update_ui(self):
        if not self.vlc_available or not self.is_slider_pressed:
            try:
                media_length = self.media_player.get_length()
                current_time = self.media_player.get_time()

                if media_length > 0 and current_time >= 0:
                    position = int((current_time / media_length) * 1000)
                    self.progress_slider.setValue(position)
                    self.current_time_label.setText(self.format_time(current_time))
                    self.total_time_label.setText(self.format_time(media_length))
                else:
                    self.progress_slider.setValue(0)
                    self.current_time_label.setText("0:00")
                    self.total_time_label.setText("0:00")

                # Auto-play next track when current ends
                if self.media_player.get_state() == vlc.State.Ended:
                    self.play_next()

            except Exception as e:
                # Silently handle VLC state errors
                pass

    def format_time(self, ms):
        if ms <= 0:
            return "0:00"
        try:
            seconds = ms // 1000
            minutes = seconds // 60
            seconds %= 60
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"

    def closeEvent(self, event):
        try:
            if self.vlc_available and self.media_player and self.media_player.is_playing():
                self.media_player.stop()
                self.media_player.release()  # Properly release VLC resources
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