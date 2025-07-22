from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QSize, QRect


class AlbumArtDisplay(QLabel):
    """Custom widget for displaying album art with fallback"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(100, 100)
        self.pixmap = None
        self.default_art = True

    def set_album_art(self, pixmap):
        """Set album art pixmap"""
        if pixmap and not pixmap.isNull():
            self.pixmap = pixmap
            self.default_art = False
            self.update()
            return True
        else:
            self.pixmap = None
            self.default_art = True
            self.update()
            return False

    def paintEvent(self, event):
        """Custom paint event to draw album art or fallback"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw border
        painter.setPen(QPen(QColor("#3e3e3e"), 1))
        painter.setBrush(QBrush(QColor("#282828")))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        if self.pixmap and not self.default_art:
            # Draw scaled pixmap
            scaled_pixmap = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Center the pixmap
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Draw default placeholder
            painter.setPen(Qt.PenStyle.NoPen)

            # Draw gradient background
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor("#333333"))
            gradient.setColorAt(1, QColor("#222222"))
            painter.setBrush(QBrush(gradient))
            painter.drawRect(0, 0, self.width(), self.height())

            # Draw music note icon
            painter.setPen(QPen(QColor("#1db954"), 2))

            # Draw a simple music note
            center_x = self.width() // 2
            center_y = self.height() // 2
            note_width = min(self.width(), self.height()) // 3

            # Note head
            painter.setBrush(QBrush(QColor("#1db954")))
            painter.drawEllipse(
                center_x - note_width // 4,
                center_y + note_width // 2,
                note_width // 2,
                note_width // 3
            )

            # Note stem
            painter.drawLine(
                center_x + note_width // 4,
                center_y - note_width // 2,
                center_x + note_width // 4,
                center_y + note_width // 2
            )

            # Flag
            painter.drawLine(
                center_x + note_width // 4,
                center_y - note_width // 2,
                center_x + note_width // 2,
                center_y - note_width // 3
            )

    def sizeHint(self):
        """Default size hint"""
        return QSize(150, 150)