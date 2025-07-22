import os
import vlc
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class Player(QObject):
    """Core audio player handling VLC media playback"""

    # Signals
    positionChanged = pyqtSignal(int, int)  # current_ms, total_ms
    stateChanged = pyqtSignal(str)  # 'playing', 'paused', 'stopped', 'error'
    mediaChanged = pyqtSignal(str)  # file_path

    def __init__(self):
        super().__init__()
        self.vlc_available = False
        self.media_player = None
        self.vlc_instance = None
        self.current_media = None
        self._initialize_vlc()

        # Setup timer for position updates
        self.timer = QTimer()
        self.timer.setInterval(100)  # 100ms refresh
        self.timer.timeout.connect(self._update_position)
        self.timer.start()

    def _initialize_vlc(self):
        """Initialize VLC instance with error handling"""
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

    def load_media(self, file_path):
        """Load a media file into the player"""
        if not self.vlc_available or not file_path:
            return False

        try:
            # Create media and set it to the player
            media = self.vlc_instance.media_new(file_path)
            self.media_player.set_media(media)
            self.current_media = file_path
            self.mediaChanged.emit(file_path)
            return True
        except Exception as e:
            print(f"Error loading media: {e}")
            return False

    def play(self):
        """Play the currently loaded media"""
        if not self.vlc_available:
            return False

        try:
            result = self.media_player.play()
            if result == 0:  # Success
                self.stateChanged.emit('playing')
                return True
            return False
        except Exception as e:
            print(f"Error playing media: {e}")
            return False

    def pause(self):
        """Pause playback"""
        if not self.vlc_available:
            return False

        try:
            self.media_player.pause()
            self.stateChanged.emit('paused')
            return True
        except Exception as e:
            print(f"Error pausing media: {e}")
            return False

    def stop(self):
        """Stop playback"""
        if not self.vlc_available:
            return False

        try:
            self.media_player.stop()
            self.stateChanged.emit('stopped')
            return True
        except Exception as e:
            print(f"Error stopping media: {e}")
            return False

    def is_playing(self):
        """Check if media is currently playing"""
        if not self.vlc_available:
            return False
        return self.media_player.is_playing()

    def get_state(self):
        """Get the current state of the player"""
        if not self.vlc_available:
            return 'unavailable'

        try:
            state = self.media_player.get_state()
            if state == vlc.State.Playing:
                return 'playing'
            elif state == vlc.State.Paused:
                return 'paused'
            elif state == vlc.State.Ended:
                return 'ended'
            elif state == vlc.State.Error:
                return 'error'
            else:
                return 'stopped'
        except:
            return 'error'

    def set_position(self, position):
        """Set position as float between 0.0 and 1.0"""
        if not self.vlc_available:
            return False

        try:
            if self.media_player.is_seekable():
                self.media_player.set_position(position)
                return True
            return False
        except Exception as e:
            print(f"Error setting position: {e}")
            return False

    def set_volume(self, volume):
        """Set volume (0-100)"""
        if not self.vlc_available:
            return False

        try:
            self.media_player.audio_set_volume(volume)
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False

    def _update_position(self):
        """Update the current playback position"""
        if not self.vlc_available:
            return

        try:
            if self.media_player.is_playing():
                length = self.media_player.get_length()
                current = self.media_player.get_time()
                if length > 0 and current >= 0:
                    self.positionChanged.emit(current, length)
        except:
            # Silently handle VLC errors
            pass

    def get_equalizer(self):
        """Get VLC equalizer for audio effects"""
        if self.vlc_available:
            try:
                # Different VLC versions have different equalizer creation methods
                if hasattr(vlc, 'AudioEqualizer') and hasattr(vlc.AudioEqualizer, 'new'):
                    return vlc.AudioEqualizer.new()
                elif hasattr(vlc, 'libvlc_audio_equalizer_new'):
                    return vlc.libvlc_audio_equalizer_new()
                elif hasattr(self.vlc_instance, 'audio_equalizer_new'):
                    return self.vlc_instance.audio_equalizer_new()
                else:
                    print("Warning: VLC equalizer not available in this version")
                    return None
            except Exception as e:
                print(f"Error creating equalizer: {e}")
                return None
        return None

    def set_equalizer(self, equalizer):
        """Apply an equalizer to the player"""
        if self.vlc_available:
            try:
                self.media_player.set_equalizer(equalizer)
                return True
            except Exception as e:
                print(f"Error setting equalizer: {e}")
        return False

    def cleanup(self):
        """Clean up VLC resources"""
        if self.vlc_available:
            try:
                if self.media_player:
                    if self.media_player.is_playing():
                        self.media_player.stop()
                    self.media_player.release()
            except Exception as e:
                print(f"Error during cleanup: {e}")