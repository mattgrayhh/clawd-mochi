"""
Simple sound effects using pygame.mixer.
Generates tones programmatically (no external WAV files needed).
"""

import os
import struct
import math
import wave
import tempfile

_mixer_available = False
try:
    import pygame.mixer
    _mixer_available = True
except ImportError:
    pass


SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


def _generate_tone(frequency, duration_ms, volume=0.3, sample_rate=22050):
    """Generate a simple sine wave tone as raw PCM data."""
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(n_samples):
        # Apply envelope (fade in/out) to avoid clicks
        t = i / n_samples
        envelope = min(t * 20, 1.0) * min((1.0 - t) * 20, 1.0)
        val = volume * envelope * math.sin(2 * math.pi * frequency * i / sample_rate)
        samples.append(int(val * 32767))
    return struct.pack(f"<{len(samples)}h", *samples)


def _save_wav(filepath, pcm_data, sample_rate=22050):
    """Save PCM data as a WAV file."""
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)


class Audio:
    """Manages sound effects for Clawd Mochi."""

    def __init__(self, enabled=True, volume=0.5):
        self.enabled = enabled and _mixer_available
        self.volume = volume
        self._sounds = {}

        if self.enabled:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                pygame.mixer.set_num_channels(4)
                self._generate_sounds()
            except Exception:
                self.enabled = False

    def _generate_sounds(self):
        """Generate and cache sound effects."""
        os.makedirs(SOUNDS_DIR, exist_ok=True)

        effects = {
            # name: (frequency_hz, duration_ms, volume)
            "switch": (880, 80, 0.25),       # Quick high beep for view switch
            "blink": (440, 50, 0.15),         # Soft beep for blink
            "startup": (660, 200, 0.3),       # Startup chime
            "click": (1200, 30, 0.2),         # Button click
            "terminal": (520, 60, 0.15),      # Terminal keystroke
            "canvas": (330, 100, 0.2),        # Canvas mode enter
        }

        for name, (freq, dur, vol) in effects.items():
            filepath = os.path.join(SOUNDS_DIR, f"{name}.wav")
            if not os.path.exists(filepath):
                pcm = _generate_tone(freq, dur, vol)
                _save_wav(filepath, pcm)
            try:
                sound = pygame.mixer.Sound(filepath)
                sound.set_volume(self.volume)
                self._sounds[name] = sound
            except Exception:
                pass

        # Startup is a two-tone chirp
        startup_path = os.path.join(SOUNDS_DIR, "startup.wav")
        tone1 = _generate_tone(523, 120, 0.3)  # C5
        tone2 = _generate_tone(784, 180, 0.3)  # G5
        # Small gap between tones
        gap = b'\x00\x00' * 1100  # ~50ms silence
        _save_wav(startup_path, tone1 + gap + tone2)
        try:
            sound = pygame.mixer.Sound(startup_path)
            sound.set_volume(self.volume)
            self._sounds["startup"] = sound
        except Exception:
            pass

    def play(self, name):
        """Play a named sound effect."""
        if not self.enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def set_volume(self, volume):
        """Set volume for all sounds (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self._sounds.values():
            sound.set_volume(self.volume)

    def cleanup(self):
        """Clean up pygame mixer."""
        if self.enabled:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
