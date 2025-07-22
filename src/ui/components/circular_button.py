from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtCore import Qt

class CircularButton(QPushButton):
    """Custom circular button with better styling"""

    def __init__(self, text="", size=56):
        super().__init__(text)
        self.setFixedSize(size, size)
        self.size = size
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Button background
        if self.isDown():
            color = QColor("#1aa34a")
        elif self.underMouse():
            color = QColor("#1ed760")
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