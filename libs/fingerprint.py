#!/usr/bin/python
"""
This module provides the core logic for generating audio fingerprints from raw
audio samples. It transforms audio into a spectrogram, finds prominent peaks,
and creates unique hashes based on pairs of these peaks.
"""
import hashlib
from operator import itemgetter

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (
    binary_erosion,
    generate_binary_structure,
    iterate_structure,
)
from termcolor import colored

IDX_FREQ_I = 0
IDX_TIME_J = 1

# Sampling rate, related to the Nyquist conditions, which affects
# the range frequencies we can detect.
DEFAULT_FS = 44100

# Size of the FFT window, affects frequency granularity
DEFAULT_WINDOW_SIZE = 4096

# Ratio by which each sequential window overlaps the last and the
# next window. Higher overlap will allow a higher granularity of offset
# matching, but potentially more fingerprints.
DEFAULT_OVERLAP_RATIO = 0.5

# Degree to which a fingerprint can be paired with its neighbors --
# higher will cause more fingerprints, but potentially better accuracy.
DEFAULT_FAN_VALUE = 15

# Minimum amplitude in spectrogram in order to be considered a peak.
# This can be raised to reduce number of fingerprints, but can negatively
# affect accuracy.
DEFAULT_AMP_MIN = 10

# Number of cells around an amplitude peak in the spectrogram in order
# for Dejavu to consider it a spectral peak. Higher values mean less
# fingerprints and faster matching, but can potentially affect accuracy.
PEAK_NEIGHBORHOOD_SIZE = 20

# Thresholds on how close or far fingerprints can be in time in order
# to be paired as a fingerprint. If your max is too low, higher values of
# DEFAULT_FAN_VALUE may not perform as expected.
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200

# If True, will sort peaks temporally for fingerprinting;
# not sorting will cut down number of fingerprints, but potentially
# affect performance.
PEAK_SORT = True

# Number of bits to throw away from the front of the SHA1 hash in the
# fingerprint calculation. The more you throw away, the less storage, but
# potentially higher collisions and misclassifications when identifying songs.
FINGERPRINT_REDUCTION = 20


def _plot_channel_samples(channel_samples):
    """Helper function to plot audio samples."""
    plt.plot(channel_samples)
    plt.title(f"{len(channel_samples)} samples")
    plt.xlabel("time (s)")
    plt.ylabel("amplitude (A)")
    plt.show()
    plt.gca().invert_yaxis()


def fingerprint(
    channel_samples,
    fs=DEFAULT_FS,
    wsize=DEFAULT_WINDOW_SIZE,
    wratio=DEFAULT_OVERLAP_RATIO,
    fan_value=DEFAULT_FAN_VALUE,
    amp_min=DEFAULT_AMP_MIN,
    plots=False,
):
    """
    Generates audio fingerprints from a channel of audio samples.

    Args:
        channel_samples (np.array): Audio data for a single channel.
        fs (int): Sample rate of the audio.
        wsize (int): FFT window size.
        wratio (float): Overlap ratio for sequential windows.
        fan_value (int): Degree to which a fingerprint can be paired with neighbors.
        amp_min (int): Minimum amplitude for a peak to be considered.
        plots (bool): If True, displays spectrogram and peak plots.

    Returns:
        list: A list of (hash, offset) tuples.
    """
    # show samples plot
    if plots:
        _plot_channel_samples(channel_samples)

    # FFT the channel, log transform output, find local maxima, then return
    # locally sensitive hashes.
    # FFT the signal and extract frequency components
    arr_2d = mlab.specgram(
        channel_samples,
        NFFT=wsize,
        Fs=fs,
        window=mlab.window_hanning,
        noverlap=int(wsize * wratio),
    )[0]

    # show spectrogram plot
    if plots:
        plt.plot(arr_2d)
        plt.title("FFT")
        plt.show()

    # apply log transform since specgram() returns linear array
    # Set NumPy to ignore divide by zero warnings
    np.seterr(divide="ignore", invalid="ignore")
    arr_2d = 10 * np.log10(arr_2d)
    arr_2d[arr_2d == -np.inf] = 0  # replace infs with zeros
    np.seterr(divide="warn", invalid="warn")

    # find local maxima
    local_maxima = get_2d_peaks(arr_2d, plot=plots, amp_min=amp_min)

    msg = "   local_maxima: %d of frequency & time pairs"
    local_maxima_to_list = list(local_maxima)
    print(colored(msg, attrs=["dark"]) % len(local_maxima_to_list))

    return generate_hashes(local_maxima_to_list, fan_value=fan_value)


def _plot_spectrogram_peaks(arr_2d, time_idx, frequency_idx):
    """Helper function to plot spectrogram and peaks."""
    _, ax = plt.subplots()
    ax.imshow(arr_2d)
    ax.scatter(time_idx, frequency_idx)
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency")
    ax.set_title("Spectrogram")
    plt.gca().invert_yaxis()
    plt.show()


def get_2d_peaks(arr_2d, plot=False, amp_min=DEFAULT_AMP_MIN):
    """
    Finds local maxima in a 2D array (the spectrogram).

    Args:
        arr_2d (np.array): The spectrogram.
        plot (bool): If True, displays a scatter plot of the peaks.
        amp_min (int): Minimum amplitude for a peak to be considered.

    Returns:
        list: A list of (frequency_index, time_index) tuples for peaks.
    """
    # http://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.morphology.iterate_structure.html#scipy.ndimage.morphology.iterate_structure
    struct = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, PEAK_NEIGHBORHOOD_SIZE)

    # find local maxima using our fliter shape
    local_max = maximum_filter(arr_2d, footprint=neighborhood) == arr_2d
    background = arr_2d == 0
    eroded_background = binary_erosion(
        background, structure=neighborhood, border_value=1
    )

    # Boolean mask of arr_2d with True at peaks
    detected_peaks = local_max ^ eroded_background

    # extract peaks
    amps = arr_2d[detected_peaks]
    j, i = np.nonzero(detected_peaks)

    # filter peaks
    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = [x for x in peaks if x[2] > amp_min]  # freq, time, amp

    # get indices for frequency and time
    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]

    # scatter of the peaks
    if plot:
        _plot_spectrogram_peaks(arr_2d, time_idx, frequency_idx)

    return zip(frequency_idx, time_idx)


# Hash list structure: sha1_hash[0:20] time_offset
# example: [(e05b341a9b77a51fd26, 32), ... ]
def generate_hashes(peaks, fan_value=DEFAULT_FAN_VALUE):
    """
    Generates hashes from a list of peaks.

    Args:
        peaks (list): A list of (frequency_index, time_index) tuples.
        fan_value (int): Degree to which a fingerprint can be paired with neighbors.

    Yields:
        tuple: (hash, time_offset) tuples.
    """
    if PEAK_SORT:
        peaks.sort(key=itemgetter(1))

    # bruteforce all peaks
    for i in range(len(peaks)):  # pylint: disable=consider-using-enumerate
        for j in range(1, fan_value):
            if (i + j) < len(peaks):
                # take current & next peak frequency value
                freq1 = peaks[i][IDX_FREQ_I]
                freq2 = peaks[i + j][IDX_FREQ_I]

                # take current & next -peak time offset
                t1 = peaks[i][IDX_TIME_J]
                t2 = peaks[i + j][IDX_TIME_J]

                # get diff of time offsets
                t_delta = t2 - t1

                # check if delta is between min & max
                if MIN_HASH_TIME_DELTA <= t_delta <= MAX_HASH_TIME_DELTA:
                    hash_input = f"{freq1}|{freq2}|{t_delta}".encode("utf-8")
                    h = hashlib.sha1(hash_input)

                    yield (h.hexdigest()[:FINGERPRINT_REDUCTION], t1)
