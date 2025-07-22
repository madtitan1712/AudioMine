from PyQt6.QtWidgets import QSlider
from PyQt6.QtCore import Qt, QEvent


class CustomSlider(QSlider):
    """Custom slider with hover effects"""

    def __init__(self, orientation):
        super().__init__(orientation)
        self.setMouseTracking(True)
        self.hovering = False
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #3e3e3e;
                margin: 2px 0;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: #1db954;
                border: 1px solid #1db954;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #1ed760;
                border: 1px solid #1ed760;
                width: 18px;
                margin: -6px 0;
            }
        """)

    def enterEvent(self, event):
        self.hovering = True
        self.update()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovering = False
        self.update()
        return super().leaveEvent(event)