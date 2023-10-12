'''
FFT & Spectogram viewer
@author bh.hwang@iae.re.kr
'''

import sys, os
from PyQt6 import QtGui
import cv2
import pathlib
from PyQt6.QtGui import QImage, QPixmap, QCloseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QMessageBox, QFileDialog
from PyQt6.uic import loadUi
from PyQt6.QtCore import QObject, Qt, QTimer, QThread, pyqtSignal
import timeit
from datetime import datetime
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# pre-defined options
WORKING_PATH = pathlib.Path(__file__).parent
APP_UI = WORKING_PATH / "gui.ui"

# Viewer Main window GUI
class viewerWindow(QMainWindow):
    def __init__(self, config:str):
        super().__init__()
        loadUi(APP_UI, self)
        
        # menu
        self.actionOpen.triggered.connect(self.on_select_file_open)
        
        # button event
        self.btn_save_image.clicked.connect(self.on_click_save_image)
        self.btn_calculate.clicked.connect(self.on_click_calculate)
        
        # variables
        self.csv_filepath = ""
        self.csv_data = pd.DataFrame()
        self.sampling_freq = 0.0
        self.use_channels = 1
        
    # event callback functions
    def on_select_file_open(self):
        selected = QFileDialog.getOpenFileName(self, 'Open Data file', './')
        
        if selected[0]: # 0=abs path
            self.csv_filepath = selected[0]
            
            try :
                self.csv_data = pd.read_csv(self.csv_filepath, usecols=range(4))
            except Exception as e:
                lambda:QMessageBox.critical(self, "Error", f"{e}")
                
            self.label_filepath.setText(self.csv_filepath)
                    
    
    def on_select_file_exit(self):
        pass
    
    # 
    def on_click_save_image(self):
        pass
    
    # calculate fft & spectogram
    def on_click_calculate(self):
        self.sampling_freq = float(self.edit_sampling_freq.text())
        self.use_channels = int(self.edit_use_channels.text())
        self.sampling_time = 1/self.sampling_freq
        
        # signal normalize
        if not self.csv_data.empty:
            _s_mean = self.csv_data.mean()
            _s_data = self.csv_data-_s_mean
            
            fx = np.fft.fft(_s_data, n=None, norm=None)/len(_s_data)
            for ch in np.transpose(fx):
                amplitude = abs(ch)*2/len(ch)
                frequency = np.fft.fftfreq(len(ch), self.sampling_time)
                peak_frequency = frequency[amplitude.argmax()]
                
                plt.clf()
                plt.subplot(3, 1, 1)                # nrows=2, ncols=1, index=1
                plt.plot(ch, '-')
                plt.title('Vibration Raw Data')
                plt.xlabel('Time({}sec)'.format(self.sampling_time))
                plt.ylabel('Magnitude')
                
                plt.subplot(3, 1, 2)                # nrows=2, ncols=1, index=1
                plt.plot(frequency, amplitude, '-')
                plt.title('FFT')
                plt.xlabel('Frequency(Hz)')
                plt.ylabel('Amplitude')

                plt.subplot(3, 1, 3)                # nrows=2, ncols=1, index=2
                f, tt, Sxx = signal.spectrogram(ch, fs=self.sampling_freq)
                plt.pcolormesh(tt, f, Sxx, shading='gouraud')
                plt.title('Spectogram')
                plt.xlabel('Time(s)')
                plt.ylabel('Frequency(Hz)')
                
                plt.tight_layout()
                plt.show()
                
                
                
            # amplitude = np.absolute(fx)*2/len(fx)
            # frequency = np.fft.fftfreq(len(fx), self.sampling_time)
            # print(frequency)
            # print(np.argmax(amplitude))
            # peak_frequency = frequency[amplitude.argmax()]
            
            
            # amplitude = abs(fx)*2/len(fx)
            # print(amplitude.shape)
            # frequency = np.fft.fftfreq(len(fx), self.sampling_time)
            # peak_frequency = frequency[amplitude.argmax()]
            # print(peak_frequency)
            
            # for ch in self.use_channels:
            #     fx = np.fft.fft(_s_data, n=None, axis=-1, norm=None)/len(_s_data)
            #     print(fx)
                # amplitude = abs(fx)*2/len(fx)
                # frequency = np.fft.fftfreq(len(fx), _sampling_time)
                # peak_frequency = frequency[amplitude.argmax()]
                # print("Peak Frequenct : {}".format(peak_frequency))
                
        
    
    # close event callback function by user
    def closeEvent(self, a0: QCloseEvent) -> None:
        # do action for user
        return super().closeEvent(a0)

'''
 Entry point
'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', nargs='?', required=False, help="Custom Configuration File")
    args = parser.parse_args()

    conf_file = "conf.cfg"
    if args.config is not None:
        conf_file = args.config

    app = QApplication(sys.argv)
    window = viewerWindow(config=conf_file)
    window.show()
    sys.exit(app.exec())