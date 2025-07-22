import os
import requests
import json
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QPixmap, QPalette, QColor, QLinearGradient, QBrush, QPainter, QFont


class ColorExtractor:
    """Extract dominant colors from album art for gradient background"""

    @staticmethod
    def extract_colors(pixmap, num_colors=2):
        """Extract dominant colors from a QPixmap"""
        if not pixmap or pixmap.isNull():
            # Return default colors if no pixmap
            return [QColor("#191414"), QColor("#121212")]

        # Convert QPixmap to QImage for pixel access
        image = pixmap.toImage()
        width = image.width()
        height = image.height()

        # Sample pixels from the image (for performance, don't check every pixel)
        sample_rate = max(1, min(width, height) // 50)  # Adjust based on image size
        colors = []

        for y in range(0, height, sample_rate):
            for x in range(0, width, sample_rate):
                pixel = image.pixel(x, y)
                colors.append(QColor(pixel))

        # Group similar colors and find dominant ones
        color_groups = {}
        for color in colors:
            # Simplify color to reduce number of unique colors
            r = (color.red() // 16) * 16
            g = (color.green() // 16) * 16
            b = (color.blue() // 16) * 16

            key = f"{r},{g},{b}"
            if key in color_groups:
                color_groups[key]['count'] += 1
            else:
                color_groups[key] = {
                    'color': QColor(r, g, b),
                    'count': 1
                }

        # Sort color groups by count
        sorted_colors = sorted(
            color_groups.values(),
            key=lambda x: x['count'],
            reverse=True
        )

        # Get the most dominant colors
        dominant_colors = [group['color'] for group in sorted_colors[:num_colors]]

        # If we don't have enough colors, duplicate the last one
        while len(dominant_colors) < num_colors:
            dominant_colors.append(dominant_colors[-1] if dominant_colors else QColor("#121212"))

        # Ensure colors are not too similar (adjust lightness if needed)
        if len(dominant_colors) >= 2:
            color1 = dominant_colors[0]
            color2 = dominant_colors[1]

            # If colors are too similar, adjust second color
            if (abs(color1.red() - color2.red()) +
                abs(color1.green() - color2.green()) +
                abs(color1.blue() - color2.blue())) < 100:

                # Make second color darker or lighter
                h, s, l, a = color2.getHsl()
                if l > 128:
                    l = max(0, l - 100)
                else:
                    l = min(255, l + 100)
                color2.setHsl(h, s, l, a)
                dominant_colors[1] = color2

        return dominant_colors


class LyricsProvider:
    """Provider for song lyrics from Musixmatch or local files"""

    def __init__(self):
        self.api_key = "2d782bc7a52a41ba2fc1ef05b9cf40d7"  # Musixmatch API key
        self.base_url = "https://api.musixmatch.com/ws/1.1/"
        self.lyrics_cache = {}  # Cache lyrics by artist+title
        self.lyrics_dir = os.path.join("resources", "lyrics")

        # Create lyrics directory if it doesn't exist
        os.makedirs(self.lyrics_dir, exist_ok=True)

    def get_lyrics(self, artist, title, album=None):
        """Get lyrics for a song from cache, file or API"""
        # Clean up inputs
        artist = self._clean_string(artist)
        title = self._clean_string(title)

        # Generate cache key
        cache_key = f"{artist.lower()}_{title.lower()}"

        # Check cache first
        if cache_key in self.lyrics_cache:
            return self.lyrics_cache[cache_key]

        # Try to find lyrics in local files
        lyrics = self._get_lyrics_from_file(artist, title)
        if lyrics:
            self.lyrics_cache[cache_key] = lyrics
            return lyrics

        # Try Musixmatch API
        try:
            lyrics = self._get_lyrics_from_api(artist, title)
            if lyrics:
                self.lyrics_cache[cache_key] = lyrics
                self._save_lyrics_to_file(artist, title, lyrics)
                return lyrics
        except Exception as e:
            print(f"Error fetching lyrics from API: {e}")

        # No lyrics found
        no_lyrics = "No lyrics found for this song."
        self.lyrics_cache[cache_key] = no_lyrics
        return no_lyrics

    def _clean_string(self, text):
        """Clean up artist or title for better matching"""
        if not text:
            return "Unknown"

        # Remove featuring artists
        text = re.sub(r'\(feat\..*?\)', '', text)
        text = re.sub(r'ft\..*?$', '', text)

        # Remove version info
        text = re.sub(r'\(.*?version.*?\)', '', text, flags=re.IGNORECASE)

        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _get_lyrics_from_file(self, artist, title):
        """Retrieve lyrics from a local file"""
        filename = f"{artist.lower()}_{title.lower()}.txt".replace(" ", "_")
        filepath = os.path.join(self.lyrics_dir, filename)

        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading lyrics file: {e}")

        return None

    def _save_lyrics_to_file(self, artist, title, lyrics):
        """Save lyrics to a local file"""
        if not lyrics or lyrics == "No lyrics found for this song.":
            return

        filename = f"{artist.lower()}_{title.lower()}.txt".replace(" ", "_")
        filepath = os.path.join(self.lyrics_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(lyrics)
        except Exception as e:
            print(f"Error saving lyrics: {e}")

    def _get_lyrics_from_api(self, artist, title):
        """Fetch lyrics from Musixmatch API"""
        # First, search for the track
        search_params = {
            'q_artist': artist,
            'q_track': title,
            'page_size': 1,
            'page': 1,
            'apikey': self.api_key
        }

        search_url = f"{self.base_url}matcher.lyrics.get"
        response = requests.get(search_url, params=search_params)

        if response.status_code == 200:
            data = response.json()

            # Check if we got a match
            if (data['message']['header']['status_code'] == 200 and
                    'lyrics' in data['message']['body']):

                lyrics_body = data['message']['body']['lyrics']['lyrics_body']

                # Musixmatch free API adds a disclaimer at the end, remove it
                if "..." in lyrics_body:
                    lyrics_body = lyrics_body.split("...")[0]

                # Remove commercial usage disclaimer
                disclaimer = "This Lyrics is NOT for Commercial use"
                if disclaimer in lyrics_body:
                    lyrics_body = lyrics_body.replace(disclaimer, "").strip()

                return lyrics_body

        # Try another endpoint if the first one failed
        search_params = {
            'q_artist': artist,
            'q_track': title,
            'page_size': 1,
            'page': 1,
            's_track_rating': 'desc',
            'apikey': self.api_key
        }

        search_url = f"{self.base_url}track.search"
        response = requests.get(search_url, params=search_params)

        if response.status_code == 200:
            data = response.json()

            # Check if we found tracks
            if (data['message']['header']['status_code'] == 200 and
                    'track_list' in data['message']['body'] and
                    len(data['message']['body']['track_list']) > 0):

                track_id = data['message']['body']['track_list'][0]['track']['track_id']

                # Get lyrics for the found track
                lyrics_params = {
                    'track_id': track_id,
                    'apikey': self.api_key
                }

                lyrics_url = f"{self.base_url}track.lyrics.get"
                lyrics_response = requests.get(lyrics_url, params=lyrics_params)

                if lyrics_response.status_code == 200:
                    lyrics_data = lyrics_response.json()

                    if (lyrics_data['message']['header']['status_code'] == 200 and
                            'lyrics' in lyrics_data['message']['body']):

                        lyrics_body = lyrics_data['message']['body']['lyrics']['lyrics_body']

                        # Clean up lyrics
                        if "..." in lyrics_body:
                            lyrics_body = lyrics_body.split("...")[0]

                        # Remove commercial usage disclaimer
                        disclaimer = "This Lyrics is NOT for Commercial use"
                        if disclaimer in lyrics_body:
                            lyrics_body = lyrics_body.replace(disclaimer, "").strip()

                        return lyrics_body

        return None


class FullscreenPlayer(QWidget):
    """Full-screen player with album art, controls and lyrics"""

    closeRequested = pyqtSignal()  # Signal to exit full-screen mode

    def __init__(self, player, metadata_handler):
        super().__init__()
        self.player = player
        self.metadata_handler = metadata_handler
        self.color_extractor = ColorExtractor()
        self.lyrics_provider = LyricsProvider()
        self.current_track_path = None
        self.current_metadata = None
        self.current_album_art = None
        self.background_colors = [QColor("#191414"), QColor("#121212")]

        self.init_ui()
        self.setup_connections()

        # Set window properties
        self.setWindowTitle("AudioMine - Now Playing")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Left side: Album art
        self.album_art_frame = QFrame()
        self.album_art_frame.setMinimumSize(400, 400)
        self.album_art_frame.setMaximumSize(800, 800)
        self.album_art_frame.setStyleSheet(
            "background-color: rgba(40, 40, 40, 100); "
            "border-radius: 10px;"
        )

        album_art_layout = QVBoxLayout(self.album_art_frame)

        self.album_art_label = QLabel()
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setStyleSheet("background: transparent;")
        album_art_layout.addWidget(self.album_art_label)

        layout.addWidget(self.album_art_frame, 1)

        # Center: Track info and controls
        center_widget = QWidget()
        center_widget.setMinimumWidth(400)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Track info
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: white;"
        )
        center_layout.addWidget(self.title_label)

        self.artist_label = QLabel()
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist_label.setStyleSheet(
            "font-size: 18px; color: #1db954;"
        )
        center_layout.addWidget(self.artist_label)

        self.album_label = QLabel()
        self.album_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_label.setStyleSheet(
            "font-size: 14px; color: rgba(255, 255, 255, 160);"
        )
        center_layout.addWidget(self.album_label)

        # Spacer
        spacer1 = QWidget()
        spacer1.setSizePolicy(
            QWidget.SizePolicy.Policy.Expanding,
            QWidget.SizePolicy.Policy.Expanding
        )
        center_layout.addWidget(spacer1)

        # Progress display
        progress_layout = QHBoxLayout()

        self.current_time = QLabel("0:00")
        self.current_time.setStyleSheet("color: white; font-size: 12px;")
        progress_layout.addWidget(self.current_time)

        self.progress_bar = QWidget()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setStyleSheet(
            "background-color: #1db954; border-radius: 2px;"
        )
        progress_layout.addWidget(self.progress_bar, 1)

        self.total_time = QLabel("0:00")
        self.total_time.setStyleSheet("color: white; font-size: 12px;")
        progress_layout.addWidget(self.total_time)

        center_layout.addLayout(progress_layout)

        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.setSpacing(30)

        self.previous_button = QPushButton("⏮")
        self.previous_button.setFixedSize(70, 70)
        self.previous_button.setStyleSheet(
            "QPushButton { font-size: 24px; background-color: rgba(29, 185, 84, 120); "
            "border-radius: 35px; color: white; } "
            "QPushButton:hover { background-color: rgba(29, 185, 84, 180); }"
        )
        controls_layout.addWidget(self.previous_button)

        self.play_pause_button = QPushButton("⏸")
        self.play_pause_button.setFixedSize(90, 90)
        self.play_pause_button.setStyleSheet(
            "QPushButton { font-size: 32px; background-color: #1db954; "
            "border-radius: 45px; color: white; } "
            "QPushButton:hover { background-color: #1ed760; }"
        )
        controls_layout.addWidget(self.play_pause_button)

        self.next_button = QPushButton("⏭")
        self.next_button.setFixedSize(70, 70)
        self.next_button.setStyleSheet(
            "QPushButton { font-size: 24px; background-color: rgba(29, 185, 84, 120); "
            "border-radius: 35px; color: white; } "
            "QPushButton:hover { background-color: rgba(29, 185, 84, 180); }"
        )
        controls_layout.addWidget(self.next_button)

        center_layout.addLayout(controls_layout)

        # Spacer
        spacer2 = QWidget()
        spacer2.setSizePolicy(
            QWidget.SizePolicy.Policy.Expanding,
            QWidget.SizePolicy.Policy.Expanding
        )
        center_layout.addWidget(spacer2)

        # Close button at bottom
        self.close_button = QPushButton("Exit Full Screen")
        self.close_button.setStyleSheet(
            "QPushButton { background-color: rgba(255, 255, 255, 80); "
            "border-radius: 16px; color: white; padding: 8px 16px; } "
            "QPushButton:hover { background-color: rgba(255, 255, 255, 120); }"
        )
        center_layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(center_widget, 1)

        # Right side: Lyrics
        lyrics_container = QWidget()
        lyrics_container.setMinimumWidth(300)
        lyrics_container.setMaximumWidth(500)
        lyrics_layout = QVBoxLayout(lyrics_container)

        lyrics_header = QLabel("Lyrics")
        lyrics_header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        lyrics_layout.addWidget(lyrics_header)

        # Lyrics scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            "QScrollArea { background-color: rgba(40, 40, 40, 100); border-radius: 10px; }"
            "QScrollBar:vertical { width: 8px; background: rgba(0, 0, 0, 0); }"
            "QScrollBar::handle:vertical { background: rgba(255, 255, 255, 80); border-radius: 4px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )

        lyrics_content = QWidget()
        lyrics_layout_inner = QVBoxLayout(lyrics_content)

        self.lyrics_label = QLabel()
        self.lyrics_label.setWordWrap(True)
        self.lyrics_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.lyrics_label.setStyleSheet("color: white; font-size: 14px; line-height: 150%;")
        lyrics_layout_inner.addWidget(self.lyrics_label)
        lyrics_layout_inner.addStretch()

        scroll_area.setWidget(lyrics_content)
        lyrics_layout.addWidget(scroll_area)

        layout.addWidget(lyrics_container, 1)

        # Set default text
        self.title_label.setText("Not Playing")
        self.artist_label.setText("")
        self.album_label.setText("")
        self.lyrics_label.setText("No lyrics available")

    def setup_connections(self):
        """Connect signals and slots"""
        self.close_button.clicked.connect(self.close_fullscreen)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.previous_button.clicked.connect(self.previous_track)
        self.next_button.clicked.connect(self.next_track)

        # Player connections
        self.player.positionChanged.connect(self.update_position)
        self.player.stateChanged.connect(self.update_play_state)

        # Timer for smooth progress updates
        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(50)  # 20fps
        self.progress_timer.timeout.connect(self.update_progress_bar)
        self.progress_timer.start()

    def update_track(self, file_path, metadata=None, pixmap=None):
        """Update the display with new track information"""
        self.current_track_path = file_path

        if not metadata:
            metadata = self.metadata_handler.extract_metadata(file_path)

        self.current_metadata = metadata

        # Update track info
        self.title_label.setText(metadata['title'])
        self.artist_label.setText(metadata['artist'])
        self.album_label.setText(f"{metadata['album']} • {metadata.get('year', '')}")

        # Set album art
        if not pixmap:
            pixmap = self.metadata_handler.extract_album_art(file_path)

        if pixmap and not pixmap.isNull():
            self.current_album_art = pixmap

            # Scale pixmap to fit the label
            scaled_pixmap = pixmap.scaled(
                400, 400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.album_art_label.setPixmap(scaled_pixmap)

            # Extract colors for gradient background
            self.background_colors = self.color_extractor.extract_colors(pixmap)
            self.update_background()
        else:
            self.current_album_art = None
            self.album_art_label.clear()
            self.album_art_label.setText("No Album Art")
            self.background_colors = [QColor("#191414"), QColor("#121212")]
            self.update_background()

        # Update times
        length = metadata.get('length', 0)
        self.total_time.setText(self.format_time(int(length * 1000)))

        # Get and set lyrics
        self.update_lyrics(metadata['artist'], metadata['title'], metadata.get('album', ''))

    def update_lyrics(self, artist, title, album=None):
        """Update the lyrics display"""
        # Show loading message
        self.lyrics_label.setText("Loading lyrics...")

        # Function to set lyrics after retrieval
        def set_lyrics():
            lyrics = self.lyrics_provider.get_lyrics(artist, title, album)

            # Format lyrics for display
            if lyrics:
                # Replace line breaks with HTML breaks for proper rendering
                formatted_lyrics = lyrics.replace('\n', '<br>')
                self.lyrics_label.setText(f"<div style='line-height: 150%;'>{formatted_lyrics}</div>")
            else:
                self.lyrics_label.setText("No lyrics found for this song.")

        # Use QTimer to prevent UI blocking
        QTimer.singleShot(100, set_lyrics)

    def update_position(self, current_ms, total_ms):
        """Update time display"""
        if total_ms > 0:
            self.current_time.setText(self.format_time(current_ms))
            self.total_time.setText(self.format_time(total_ms))

    def update_progress_bar(self):
        """Update progress bar width based on playback position"""
        if not self.player.is_playing():
            return

        try:
            current = self.player.media_player.get_time()
            total = self.player.media_player.get_length()

            if total > 0:
                progress = current / total
                width = int(self.progress_bar.parent().width() * progress)
                self.progress_bar.setFixedWidth(width)
        except:
            # Handle any VLC errors silently
            pass

    def update_play_state(self, state):
        """Update play/pause button based on player state"""
        if state == 'playing':
            self.play_pause_button.setText("⏸")
        else:
            self.play_pause_button.setText("▶")

    def update_background(self):
        """Update background gradient based on album colors"""
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Paint custom background gradient"""
        painter = QPainter(self)

        # Create gradient from extracted colors
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.background_colors[0])
        gradient.setColorAt(1, self.background_colors[1])

        # Apply semi-transparent overlay for better readability
        painter.fillRect(0, 0, self.width(), self.height(), gradient)

        # Add overlay gradient for text readability
        overlay = QLinearGradient(0, 0, 0, self.height())
        overlay.setColorAt(0, QColor(0, 0, 0, 80))
        overlay.setColorAt(1, QColor(0, 0, 0, 160))
        painter.fillRect(0, 0, self.width(), self.height(), overlay)

    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def previous_track(self):
        """Signal to play previous track"""
        self.player.previousRequested.emit()

    def next_track(self):
        """Signal to play next track"""
        self.player.nextRequested.emit()

    def close_fullscreen(self):
        """Exit full-screen mode"""
        self.closeRequested.emit()
        self.close()

    def format_time(self, ms):
        """Format milliseconds to mm:ss"""
        if ms <= 0:
            return "0:00"

        seconds = ms // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}:{seconds:02d}"

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close_fullscreen()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key.Key_Left:
            self.previous_track()
        elif event.key() == Qt.Key.Key_Right:
            self.next_track()
        else:
            super().keyPressEvent(event)