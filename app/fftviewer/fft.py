import numpy as np
import matplotlib.pyplot as plt
import argparse
import csv
import scipy.fftpack
import math
import scipy.signal


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', nargs='?', required=True, help="csv file to load")
    args = parser.parse_args()
    
    _source_data = np.loadtxt(args.csv, delimiter=',')
    
    _sampling_freq = 1000 # hz
    _sampleing_time = 1/_sampling_freq
    
    # signal normalization
    _source_mean = _source_data.mean()
    _source_data = _source_data-_source_mean
    
    fx = np.fft.fft(_source_data, n=None, axis=-1, norm=None)/len(_source_data)
    amplitude = abs(fx)*2/len(fx)
    frequency = np.fft.fftfreq(len(fx), _sampleing_time)
    peak_frequency = frequency[amplitude.argmax()]
    print("Peak Frequenct : {}".format(peak_frequency))

    
    plt.clf()
    plt.subplot(2, 1, 1)                # nrows=2, ncols=1, index=1
    plt.plot(_source_data, '-')
    plt.title('Vibration Raw Data')
    plt.xlabel('Time({}sec)'.format(_sampleing_time))
    plt.ylabel('Magnitude')

    plt.subplot(2, 1, 2)                # nrows=2, ncols=1, index=2
    plt.plot(frequency, amplitude, '-')
    plt.title('FFT')
    plt.xlabel('Frequency(Hz)')
    plt.ylabel('Amplitude')

    plt.tight_layout()
    plt.show()