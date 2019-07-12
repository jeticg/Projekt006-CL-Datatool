import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from scipy.signal import stft


DIR = '/Users/jetic/Daten/speech-data/timit/train/DR1/FCJF0'
fns = ['/SA1.WAV']
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


def read_wav_file(x):
    # Read wavfile using scipy wavfile.read
    _, wav = wavfile.read(x)
    # Normalize
    wav = wav.astype(np.float32) / np.iinfo(np.int16).max
    return wav


fig = plt.figure(figsize=(14, 8))
for i, fn in enumerate(fns):
    wav = read_wav_file(DIR + fn)
    freqs, times, amp = log_spectrogram(wav)

    ax = fig.add_subplot(3, 1, i + 1)
    ax.imshow(amp, aspect='auto', origin='lower',
              extent=[times.min(), times.max(), freqs.min(), freqs.max()])
    ax.set_title('Spectrogram of ' + fn)
    ax.set_ylabel('Freqs in Hz')
    ax.set_xlabel('Seconds')

fig.tight_layout()
