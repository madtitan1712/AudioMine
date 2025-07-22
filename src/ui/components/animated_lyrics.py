from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPalette, QFont


class AnimatedLyricsDisplay(QScrollArea):
    """Widget for displaying time-synced animated lyrics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.lyrics_container = QWidget()
        self.setWidget(self.lyrics_container)

        self.layout = QVBoxLayout(self.lyrics_container)
        self.layout.setSpacing(12)  # Space between lines
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Styling
        self.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
            "QScrollBar:vertical { width: 8px; background: rgba(0, 0, 0, 0); }"
            "QScrollBar::handle:vertical { background: rgba(255, 255, 255, 80); border-radius: 4px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )

        self.labels = []  # List of lyric labels
        self.synced_lyrics = []  # List of TimecodedLyric objects
        self.current_line_index = -1  # Index of currently highlighted line
        self.scroll_animation = None

    def set_lyrics(self, synced_lyrics):
        """Set the lyrics to be displayed"""
        # Clear existing lyrics
        self.clear_lyrics()

        if not synced_lyrics:
            # Add a placeholder message
            label = QLabel("No synced lyrics available")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setStyleSheet("color: rgba(255, 255, 255, 120); font-size: 14px;")
            self.layout.addWidget(label)
            self.labels.append(label)
            return

        self.synced_lyrics = synced_lyrics

        # Add each line as a label
        for lyric in synced_lyrics:
            label = QLabel(lyric.text)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setWordWrap(True)

            # Default styling (not highlighted)
            label.setStyleSheet(
                "color: rgba(255, 255, 255, 160); font-size: 14px;"
            )

            self.layout.addWidget(label)
            self.labels.append(label)

    def clear_lyrics(self):
        """Clear all lyrics"""
        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()

        self.labels = []
        self.synced_lyrics = []
        self.current_line_index = -1

    def update_position(self, current_ms):
        """Update highlighted line based on current playback position"""
        if not self.synced_lyrics:
            return

        # Find the current line
        new_index = -1
        for i, lyric in enumerate(self.synced_lyrics):
            if lyric.time_ms <= current_ms:
                new_index = i
            else:
                break

        # If line changed, update highlighting
        if new_index != self.current_line_index:
            self.highlight_line(new_index)

    def highlight_line(self, index):
        """Highlight the specified line"""
        if index < 0 or index >= len(self.labels):
            return

        # Remove highlight from previous line
        if 0 <= self.current_line_index < len(self.labels):
            self.labels[self.current_line_index].setStyleSheet(
                "color: rgba(255, 255, 255, 160); font-size: 14px;"
            )

        # Add highlight to new line
        self.labels[index].setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
        )

        # Store current index
        self.current_line_index = index

        # Scroll to make the current line visible
        self.scroll_to_line(index)

    def scroll_to_line(self, index):
        """Scroll to make the specified line visible with animation"""
        if index < 0 or index >= len(self.labels):
            return

        # Get the position of the target label relative to the scroll area
        label = self.labels[index]
        target_y = label.mapTo(self.lyrics_container, QRect(0, 0, 0, 0).topLeft()).y()

        # Calculate scroll position to center the line
        viewport_height = self.viewport().height()
        label_height = label.height()
        scroll_pos = max(0, target_y - (viewport_height / 2) + (label_height / 2))

        # Create smooth scrolling animation
        if self.scroll_animation:
            self.scroll_animation.stop()

        from PyQt6.QtCore import QAbstractAnimation
        self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_animation.setDuration(300)  # 300ms animation
        self.scroll_animation.setStartValue(self.verticalScrollBar().value())
        self.scroll_animation.setEndValue(int(scroll_pos))
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.scroll_animation.start()