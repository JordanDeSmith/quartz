from loopSound import LoopSound
import simpleaudio as sa

"""
From Simple Audio:
The following sample rates are allowed (though not necessarily guaranteed to be supported on your platform/hardware): 
8, 11.025, 16, 22.05, 32, 44.1, 48, 88.2, 96, and 192 kHz.
"""
SUPPORTED_SAMPLE_RATES = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88.200, 96000, 192000]

class SoundPlayer:
    """
    A class to handle playing sound effects given their names
    Also handles stopping playing sounds with functionality to handle looping audio.
    """
    def __init__(self):
        self.loopingSounds = []


    def playSound(self, fileName, looping=False):
        """
        Given a sound file, and bool for whether or not the sound should be looping, 
        searches for the sound under the 'sound' directory, and plays it accordingly.
        """
        waveObj = sa.WaveObject.from_wave_file(fileName)
        if waveObj.sample_rate not in SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"File {fileName} has unsuported sample rate")
        if looping:
            self.loopingSounds.append(LoopSound(fileName))
        else:
            waveObj.play()

    def stopRepeating(self, fileName):
        """Stops given currently repeating sound after it has finished playing its current loop"""
        for sound in self.loopingSounds:
            if fileName == sound.soundFile:
                sound.stop()

    def stopAll(self):
        """Immediately stops all playing sounds, including looping."""
        sa.stop_all()
        for sound in self.loopingSounds:
            sound.stopImmediately()
    

    def stopAllRepeating(self):
        """Stops all currently repeating sounds after they have finished playing their current loop"""
        for sound in self.loopingSounds:
            sound.stop()
