import sys
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft


# Sample rate by default 16000
# Target: 20ms per processed sample, that's every 320 samples to 1
SAMPLE_RATE = 16000


def log_spectrogram(wav):
    freqs, times, spec = stft(wav,
                              fs=SAMPLE_RATE,  # sample rate
                              nperseg=320,  # length of each segment
                              noverlap=160,  # number of points to overlap
                                             # between segments
                              nfft=512,  # Length of the FFT used
                              padded=False,
                              boundary=None)
    # Log spectrogram
    amp = np.log(np.abs(spec) + 1e-10)

    return freqs, times, amp


def load(file, linesToLoad=sys.maxsize):
    file = os.path.expanduser(file)
    # Read wavfile using scipy wavfile.read
    _, wav = wavfile.read(file)
    # Normalize
    content = [wav.astype(np.float32) / np.iinfo(np.int16).max]
    return content


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    DIR = '../test'
    fns = ['/sample.wav']
    fig = plt.figure(figsize=(14, 8))
    for i, fn in enumerate(fns):
        wav = load(DIR + fn)[0]
        freqs, times, amp = log_spectrogram(wav)

        ax = fig.add_subplot(3, 1, i + 1)
        ax.imshow(amp, aspect='auto', origin='lower',
                  extent=[times.min(), times.max(), freqs.min(), freqs.max()])
        ax.set_title('Spectrogram of ' + fn)
        ax.set_ylabel('Freqs in Hz')
        ax.set_xlabel('Seconds')

    fig.tight_layout()
