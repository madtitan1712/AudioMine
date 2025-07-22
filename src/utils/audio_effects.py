from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QLabel, QSlider, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt


class AudioEffects:
    """Handles audio effects and equalizer for the player"""

    def __init__(self, player):
        self.player = player
        self.equalizer = None
        self.current_preset = "Flat"

        # Define equalizer presets
        self.presets = {
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

        self._initialize_equalizer()

    def _initialize_equalizer(self):
        """Initialize VLC equalizer if available"""
        if not self.player.vlc_available:
            return

        try:
            self.equalizer = self.player.get_equalizer()
            if self.equalizer:
                self.apply_preset("Flat")  # Default preset
            else:
                print("VLC equalizer functionality not available")
        except Exception as e:
            print(f"Error initializing equalizer: {e}")
            self.equalizer = None

    def apply_preset(self, preset_name):
        """Apply an equalizer preset"""
        if not self.equalizer or preset_name not in self.presets:
            return False

        try:
            for i, gain in enumerate(self.presets[preset_name]):
                self.equalizer.set_amp_at_index(gain, i)

            self.player.set_equalizer(self.equalizer)
            self.current_preset = preset_name
            return True
        except Exception as e:
            print(f"Error applying equalizer preset: {e}")
            return False

    def set_custom_gains(self, gains):
        """Set custom equalizer gains"""
        if not self.equalizer or len(gains) != 10:
            return False

        try:
            for i, gain in enumerate(gains):
                # Try different methods of setting equalizer values
                if hasattr(self.equalizer, 'set_amp_at_index'):
                    self.equalizer.set_amp_at_index(gain, i)
                elif hasattr(self.equalizer, 'set_band_amp'):
                    self.equalizer.set_band_amp(i, gain)
                else:
                    print(f"Cannot set equalizer band {i}")

            self.player.set_equalizer(self.equalizer)
            return True
        except Exception as e:
            print(f"Error setting custom equalizer: {e}")
            return False
    def show_equalizer_dialog(self, parent=None):
        """Show equalizer settings dialog"""
        if not self.player.vlc_available:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                parent,
                "Equalizer Unavailable",
                "The audio equalizer is not available. Please install python-vlc."
            )
            return
        dialog = QDialog(parent)
        dialog.setWindowTitle("Audio Equalizer")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))

        preset_combo = QComboBox()
        for preset in self.presets.keys():
            preset_combo.addItem(preset)

        # Set current preset
        preset_combo.setCurrentText(self.current_preset)

        preset_layout.addWidget(preset_combo, 1)
        layout.addLayout(preset_layout)

        # Sliders group
        sliders_group = QGroupBox("Frequency Bands")
        sliders_layout = QHBoxLayout(sliders_group)

        # Frequency bands (approximate Hz values)
        bands = ["32", "64", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]

        # Create sliders for each band
        sliders = []
        for i, band in enumerate(bands):
            band_layout = QVBoxLayout()

            # Gain value label
            gain_label = QLabel("0 dB")
            gain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Slider
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-20, 20)  # -20dB to +20dB
            slider.setTickPosition(QSlider.TickPosition.TicksRight)
            slider.setTickInterval(5)
            slider.setMinimumHeight(150)

            # Set current value
            current_gain = 0
            if self.equalizer and self.current_preset in self.presets:
                current_gain = self.presets[self.current_preset][i]
            slider.setValue(current_gain)
            gain_label.setText(f"{current_gain} dB")

            # Connect value changed
            slider.valueChanged.connect(lambda v, label=gain_label: label.setText(f"{v} dB"))

            # Frequency band label
            band_label = QLabel(band)
            band_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Add to layout
            band_layout.addWidget(gain_label)
            band_layout.addWidget(slider, 1)
            band_layout.addWidget(band_label)

            sliders_layout.addLayout(band_layout)
            sliders.append(slider)

        layout.addWidget(sliders_group)

        # Buttons
        button_layout = QHBoxLayout()

        apply_button = QPushButton("Apply")
        reset_button = QPushButton("Reset")
        close_button = QPushButton("Close")

        button_layout.addWidget(apply_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # Connect signals
        def on_preset_selected(preset_name):
            if preset_name in self.presets:
                # Update sliders to match preset
                for i, gain in enumerate(self.presets[preset_name]):
                    sliders[i].setValue(gain)

        def apply_settings():
            # Get values from sliders
            gains = [slider.value() for slider in sliders]

            # Apply custom gains
            self.set_custom_gains(gains)

            # Check if this matches any preset
            for preset_name, preset_gains in self.presets.items():
                if gains == preset_gains:
                    self.current_preset = preset_name
                    preset_combo.setCurrentText(preset_name)
                    return

            # If no match, it's a custom preset
            self.current_preset = "Custom"

        def reset_settings():
            # Reset to flat response
            on_preset_selected("Flat")
            preset_combo.setCurrentText("Flat")

        preset_combo.currentTextChanged.connect(on_preset_selected)
        apply_button.clicked.connect(apply_settings)
        reset_button.clicked.connect(reset_settings)
        close_button.clicked.connect(dialog.accept)

        # Show dialog
        dialog.exec()