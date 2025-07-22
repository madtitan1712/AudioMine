import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, pyqtSlot, QPropertyAnimation, QEasingCurve


class AudioVisualizer(QWidget):
    """Audio visualizer that reacts to music"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)

        # Visualization data
        self.bar_count = 64
        self._bar_heights = np.zeros(self.bar_count)
        self._target_heights = np.zeros(self.bar_count)

        # Colors
        self.gradient_start = QColor("#1db954")  # Spotify green
        self.gradient_end = QColor("#1ed760")

        # Animation
        self._animations = []

        # Setup update timer
        self.timer = QTimer(self)
        self.timer.setInterval(50)  # 50ms refresh rate (20fps)
        self.timer.timeout.connect(self._generate_random_data)  # Replace with real audio data
        self.timer.start()

    def _generate_random_data(self):
        """Generate random visualization data for testing"""
        # This is a placeholder - in a real app you'd use audio spectrum data

        # Gentle random movement for bars
        rnd = np.random.random(self.bar_count) * 0.3

        # Create a "beat" effect every 20 frames
        if np.random.random() < 0.05:
            beat_pos = np.random.randint(0, self.bar_count)
            beat_width = np.random.randint(5, 15)
            beat_intensity = np.random.random() * 0.7 + 0.3

            # Apply a bell curve for the beat
            for i in range(self.bar_count):
                dist = min(abs(i - beat_pos), abs(i - beat_pos + self.bar_count),
                           abs(i - beat_pos - self.bar_count))
                if dist < beat_width:
                    factor = beat_intensity * (1 - dist / beat_width)
                    rnd[i] += factor

        # Update target heights with smoothing
        self._target_heights = 0.3 * rnd + 0.7 * self._target_heights

        # Animate current heights toward targets
        self._bar_heights = 0.3 * self._target_heights + 0.7 * self._bar_heights

        # Ensure legal range
        self._bar_heights = np.clip(self._bar_heights, 0.01, 1.0)

        self.update()

    def set_audio_data(self, fft_data):
        """Set visualization data from audio FFT"""
        # This would be connected to actual audio processing
        # For now, using random data in _generate_random_data
        pass

    def paintEvent(self, event):
        """Draw the visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Fill background
        painter.fillRect(0, 0, width, height, QColor(30, 30, 30))

        # Calculate bar dimensions
        bar_width = width / self.bar_count * 0.8
        bar_spacing = width / self.bar_count * 0.2

        # Draw bars
        painter.setPen(Qt.PenStyle.NoPen)

        for i, value in enumerate(self._bar_heights):
            # Calculate bar height and position
            bar_height = value * height * 0.8
            x = i * (bar_width + bar_spacing) + bar_spacing / 2
            y = height - bar_height

            # Create gradient
            gradient = QLinearGradient(x, y, x, height)
            gradient.setColorAt(0, self.gradient_start)
            gradient.setColorAt(1, self.gradient_end)

            # Draw bar
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 2, 2)

    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        self.update()