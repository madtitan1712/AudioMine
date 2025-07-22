import os
import json
from PyQt6.QtCore import QObject, pyqtSignal


class PlaylistManager(QObject):
    """Manages music playlists"""

    # Signals
    playlistChanged = pyqtSignal(str, list)  # playlist_name, tracks_list
    currentTrackChanged = pyqtSignal(int, str)  # track_index, track_path

    def __init__(self):
        super().__init__()
        self.playlists = {}  # Dictionary of playlist name -> list of tracks
        self.current_playlist = None
        self.current_track_index = -1

    def create_playlist(self, name):
        """Create a new playlist"""
        if name and name not in self.playlists:
            self.playlists[name] = []
            self.playlistChanged.emit(name, [])
            return True
        return False

    def add_to_playlist(self, playlist_name, track_path):
        """Add a track to a playlist"""
        if playlist_name in self.playlists:
            if track_path not in self.playlists[playlist_name]:
                self.playlists[playlist_name].append(track_path)
                self.playlistChanged.emit(playlist_name, self.playlists[playlist_name])
                return True
        return False

    def add_files_to_playlist(self, playlist_name, file_paths):
        """Add multiple files to a playlist"""
        if playlist_name in self.playlists:
            added = False
            for path in file_paths:
                if path not in self.playlists[playlist_name]:
                    self.playlists[playlist_name].append(path)
                    added = True

            if added:
                self.playlistChanged.emit(playlist_name, self.playlists[playlist_name])
            return added
        return False

    def remove_from_playlist(self, playlist_name, track_index):
        """Remove a track from a playlist by index"""
        if playlist_name in self.playlists and 0 <= track_index < len(self.playlists[playlist_name]):
            del self.playlists[playlist_name][track_index]
            self.playlistChanged.emit(playlist_name, self.playlists[playlist_name])
            return True
        return False

    def set_current_playlist(self, playlist_name):
        """Set the current active playlist"""
        if playlist_name in self.playlists:
            self.current_playlist = playlist_name
            self.current_track_index = 0 if self.playlists[playlist_name] else -1
            if self.current_track_index >= 0:
                self.currentTrackChanged.emit(
                    self.current_track_index,
                    self.playlists[playlist_name][self.current_track_index]
                )
            return True
        return False

    def get_current_track(self):
        """Get the current track path"""
        if (self.current_playlist and
                0 <= self.current_track_index < len(self.playlists[self.current_playlist])):
            return self.playlists[self.current_playlist][self.current_track_index]
        return None

    def next_track(self):
        """Move to the next track in playlist"""
        if not self.current_playlist or not self.playlists[self.current_playlist]:
            return None

        self.current_track_index = (self.current_track_index + 1) % len(self.playlists[self.current_playlist])
        track_path = self.playlists[self.current_playlist][self.current_track_index]
        self.currentTrackChanged.emit(self.current_track_index, track_path)
        return track_path

    def previous_track(self):
        """Move to the previous track in playlist"""
        if not self.current_playlist or not self.playlists[self.current_playlist]:
            return None

        self.current_track_index = (self.current_track_index - 1) % len(self.playlists[self.current_playlist])
        track_path = self.playlists[self.current_playlist][self.current_track_index]
        self.currentTrackChanged.emit(self.current_track_index, track_path)
        return track_path

    def save_playlists(self, filepath="playlists.json"):
        """Save playlists to a JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.playlists, f)
            return True
        except Exception as e:
            print(f"Error saving playlists: {e}")
            return False

    def load_playlists(self, filepath="playlists.json"):
        """Load playlists from a JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.playlists = json.load(f)

                # Validate loaded playlists (ensure they're still valid paths)
                for name, tracks in list(self.playlists.items()):
                    valid_tracks = [track for track in tracks if os.path.exists(track)]
                    if valid_tracks:
                        self.playlists[name] = valid_tracks
                        self.playlistChanged.emit(name, valid_tracks)
                    else:
                        # Remove empty playlists
                        del self.playlists[name]

                return True
        except Exception as e:
            print(f"Error loading playlists: {e}")
        return False