"""Constants used throughout the application"""

# Application info
APP_NAME = "AudioMine"
APP_VERSION = "1.0.0"

# Default styling
DEFAULT_STYLES = """
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
    }

    QPushButton {
        background-color: #1db954;
        border-radius: 16px;
        color: white;
        padding: 8px 16px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #1ed760;
    }

    QPushButton:pressed {
        background-color: #1aa34a;
    }

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
        margin: -4px 0;
        border-radius: 8px;
    }

    QSlider::handle:horizontal:hover {
        background: #1ed760;
        border: 1px solid #1ed760;
    }

    QListWidget, QTreeWidget, QTableWidget {
        background-color: #282828;
        alternate-background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #3e3e3e;
        border-radius: 4px;
    }

    QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
        background-color: #1db954;
        color: white;
    }

    QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {
        background-color: #333333;
    }

    QTabWidget::pane {
        border: 1px solid #3e3e3e;
        border-radius: 4px;
    }

    QTabBar::tab {
        background-color: #282828;
        color: #b3b3b3;
        border: 1px solid #3e3e3e;
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }

    QTabBar::tab:selected {
        background-color: #333333;
        color: #ffffff;
        border-bottom-color: #1db954;
    }

    QTabBar::tab:hover:!selected {
        background-color: #333333;
    }
"""

# File paths
DEFAULT_LIBRARY_PATH = "music_library.json"
DEFAULT_PLAYLISTS_PATH = "playlists.json"
DEFAULT_SETTINGS_PATH = "settings.json"

# Default equalizer presets
EQUALIZER_PRESETS = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Rock": [4, 3, -2, -4, -2, 2, 5, 6, 6, 6],
    "Pop": [-1, 2, 3, 4, 2, -1, -1, -2, -2, -3],
    "Jazz": [4, 3, 1, 1, -2, -2, 0, 1, 3, 4],
    "Classical": [5, 4, 3, 2, -1, -1, 0, 1, 3, 4],
    "Electronic": [4, 3, 0, -3, -3, 0, 4, 5, 5, 5],
    "Hip-Hop": [5, 4, 2, 1, -1, -2, 0, 2, 3, 4],
    "Bass Boost": [6, 5, 4, 3, 2, 0, 0, 0, 0, 0],
    "Treble Boost": [0, 0, 0, 0, 0, 2, 4, 5, 6, 7]
}