import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioMine")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
                    QMainWindow {
                        background-color: #121212; /* Very dark grey, typical Spotify background */
                        color: #b3b3b3; /* Light grey for default text */
                        font-family: 'Inter', sans-serif; /* A modern, clean font */
                    }
                    /* We'll add more specific styles for other widgets later */
                """)
        if __name__=="__main__":
            app = QApplication(sys.argv)
            player=MusicPlayer()
            player.show()
            sys.exit(app.exec())
