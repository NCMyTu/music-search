import os
import numpy as np
import librosa
from scipy import ndimage
import time
import scipy

def compute_spectrogram(path, start=None, end=None, Fs=11025, N=1024, H=256, bin_max=512, frame_max=None):
    x, Fs = librosa.load(path, sr=Fs)
    x = librosa.to_mono(x)
    if start is not None or end is not None:
        start_time = start * Fs
        end_time = end * Fs
        x = x[start_time:end_time]
    X = librosa.stft(x, n_fft=N, hop_length=H, win_length=N, window='hann')
    if bin_max is None:
        bin_max = X.shape[0]
    if frame_max is None:
        frame_max = X.shape[1]
    Y = np.abs(X[:bin_max, :])
    return Y

def compute_constellation_map(Y, dist_freq=35, dist_time=10, thresh=0.01):
    """Compute constellation map (implementation using image processing)

    Notebook: C7/C7S1_AudioIdentification.ipynb

    Args:
        Y (np.ndarray): Spectrogram (magnitude)
        dist_freq (int): Neighborhood parameter for frequency direction (kappa) (Default value = 7)
        dist_time (int): Neighborhood parameter for time direction (tau) (Default value = 7)
        thresh (float): Threshold parameter for minimal peak magnitude (Default value = 0.01)

    Returns:
        Cmap (np.ndarray): Boolean mask for peak structure (same size as Y)
    """
    result = ndimage.maximum_filter(Y, size=[2*dist_freq+1, 2*dist_time+1], mode="constant")
    Cmap = np.logical_and(Y == result, result > thresh)
    return Cmap

def create_group(Cmap, dist_to_tz=20, tz_w=251, tz_h=171):#
    """
    Parameters:
        Cmap: constellation map
        dist_to_tz: distance from each anchor point to left size of target zone
        tz_w: width of target zone
        tz_h: height of target zone
    Returns:
        a dict of {anchor point: [list of points in target zone]}
    """

    # get all peaks, each peak is a pair (time, frequency)
    points = np.argwhere(Cmap.T == True)
    # sort by time then frequency
    points = points[np.lexsort((points[:, 1], points[:, 0]))]

    groups = []
    
    hh = tz_h // 2
    
    for i in range(len(points)):
        anchor = points[i]
        
        x_lo_bo = anchor[0] + dist_to_tz
        x_hi_bo = anchor[0] + dist_to_tz + tz_w
        y_lo_bo = anchor[1] - hh
        y_hi_bo = anchor[1] + hh

        # print(f"{x_lo_bo}, {x_hi_bo}, {y_lo_bo}, {y_hi_bo}")
        g = []
        for j in range(i+1, len(points)):
            target = points[j]

            if (x_lo_bo <= target[0] <= x_hi_bo) and (y_lo_bo <= target[1] <= y_hi_bo):
                g.append(target)

        g.insert(0, anchor)
        groups.append(g)

    return groups

def create_hashes(Cmap, dist_to_tz=20, tz_w=251, tz_h=171):
    groups = create_group(Cmap, dist_to_tz, tz_w, tz_h)
    hashes = []
    offsets = []
    
    for group in groups:
        # skip if there's only an anchor and no target zone points
        if len(group) == 1:
            continue  
    
        # masked anchor point frequency (9 bits)
        x1 = group[0][1] & ((1 << 9) - 1)
        
        for tz_point in group[1:]:
            # masked target zone frequency (9 bits)
            x2 = tz_point[1] & ((1 << 9) - 1)

            # delta time between anchor and target (14 bits)
            delta_time = tz_point[0] - group[0][0]
            x3 = delta_time & ((1 << 14) - 1)

            # combine into a single 32-bit hash
            combined_hash = (x1 << (9 + 14)) | (x2 << 14) | x3

            hashes.append(int(combined_hash))
            # offset of anchor point relative to start of the song
            offsets.append(group[0][0])

    return hashes, offsets

def fingerprint(path, start=None, end=None, Fs=11025, N=1024, H=256, bin_max=512, frame_max=None):
	Y = compute_spectrogram(path)
	Cmap = compute_constellation_map(Y, dist_freq=15, dist_time=7)
	hashes, offsets = create_hashes(Cmap, dist_to_tz=20, tz_w=111, tz_h=111)
	return hashes, offsets

def fingerprint_with_noise(path, start=None, end=None, Fs=11025, N=1024, H=256, bin_max=512, frame_max=None, 
                            noise_factor=0.1, random_state=None):
    x, Fs = librosa.load(path, sr=Fs)
    x = librosa.to_mono(x)

    if start is not None or end is not None:
        start_time = start * Fs
        end_time = end * Fs
        x = x[start_time:end_time]

    # add noise
    np.random.seed(random_state)
    noise_range = (x.max() - x.min()) * noise_factor
    noise = np.random.uniform(-noise_range, noise_range, x.shape)
    x = x + noise
    x = np.clip(x, -1.0, 1.0)

    X = librosa.stft(x, n_fft=N, hop_length=H, win_length=N, window='hann')
    if bin_max is None:
        bin_max = X.shape[0]
    if frame_max is None:
        frame_max = X.shape[1]
    Y = np.abs(X[:bin_max, :])

    Cmap = compute_constellation_map(Y, dist_freq=15, dist_time=7)
    hashes, offsets = create_hashes(Cmap, dist_to_tz=20, tz_w=111, tz_h=111)
    return hashes, offsets

def offset_to_time(offset, Fs=11025, H=256):
    time = offset * H / Fs
    return time # in seconds