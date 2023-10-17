'''
FFT & Spectogram viewer
@author bh.hwang@iae.re.kr
'''

import sys, os
from PyQt6 import QtGui
import pathlib
from PyQt6.QtGui import QImage, QPixmap, QCloseEvent, QStandardItemModel, QStandardItem
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
from PIL import ImageQt, Image

# pre-defined options
WORKING_PATH = pathlib.Path(__file__).parent
APP_UI = WORKING_PATH / "gui.ui"

# Viewer Main window GUI
class viewerWindow(QMainWindow):
    def __init__(self, config:str):
        super().__init__()
        loadUi("./gui.ui", self)
        
        # menu
        self.actionOpen.triggered.connect(self.on_select_file_open)
        
        # event
        self.btn_calculate.clicked.connect(self.on_click_calculate)
        self.table_output.doubleClicked.connect(self.on_dbclick_select)
        
        # gui component
        output_table = pyqtSignal(str)
        self.output_table_columns = ["Output"]
        
        self.output_model = QStandardItemModel()
        self.output_model.setColumnCount(len(self.output_table_columns))
        self.output_model.setHorizontalHeaderLabels(self.output_table_columns)
        self.table_output.setModel(self.output_model)
        
        # variables
        self.csv_filepath = pathlib.Path()
        self.result_path = pathlib.Path()
        self.csv_filename = ""
        self.csv_data = pd.DataFrame()
        self.sampling_freq = 0.0
        self.use_channels = 1
        self.available_channels = 1
        self.use_time_range = 1.0 # sec
        self.csv_rows = 1
        
    # event callback functions
    def on_select_file_open(self):
        selected = QFileDialog.getOpenFileName(self, 'Open Data file', './')
        
        if selected[0]: # 0=abs path
            self.csv_filepath = pathlib.Path(selected[0]).absolute()
            # print(f"Open {self.csv_filepath}")
            self.csv_filename = self.csv_filepath.stem
            
            try :
                self.csv_data = pd.read_csv(self.csv_filepath)
                self.sampling_time = 1.0/float(self.edit_sampling_freq.text())
                self.available_channels = int(self.csv_data.shape[1])
                self.edit_use_channels.setText(str(self.available_channels))
                self.csv_rows = self.csv_data.shape[0]
                self.edit_time_range.setText(str(self.csv_data.shape[0]*self.sampling_time))
                self.statusBar().showMessage(f"Opened Data Dimension : {self.csv_data.shape}")
                self.label_filepath.setText(str(self.csv_filepath))
                self.label_rows.setText(str(self.csv_data.shape[0]))
                self.label_cols.setText(str(self.csv_data.shape[1]))
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"{e}")

    
    # calculate fft & spectogram
    def on_click_calculate(self):
        # clear output table
        self.output_model.setRowCount(0)
               
        # read user parameters
        self.sampling_freq = float(self.edit_sampling_freq.text())
        self.use_channels = int(self.edit_use_channels.text())
        self.sampling_time = 1/self.sampling_freq
        self.use_time_range = float(self.edit_time_range.text())
        
        if len(self.csv_filename)<1:
            QMessageBox.critical(self, "Error", f"No file specified to open")
            return
        
        # check parameters
        if self.use_channels > self.available_channels:
            QMessageBox.critical(self, "Error", f"Use Channel parameter exceeds the number of columns {self.available_channels}")
            return
        
        # re-open csv file
        _rows = int(self.csv_rows*self.use_time_range/(self.csv_rows*self.sampling_time))
        self.csv_data = pd.read_csv(self.csv_filepath, usecols=range(self.use_channels), nrows=_rows)
        
        # create directory
        self.result_path = self.csv_filepath.parent / self.csv_filename
        self.result_path.mkdir(parents=True, exist_ok=True)
        
        # signal normalize
        if not self.csv_data.empty:
            _s_data = self.csv_data
            _s_mean = _s_data.mean()
            _s_data = _s_data-_s_mean
            _head_list = self.csv_data.columns.values.tolist()
            
            try:
                for idx, col_head in enumerate(_head_list):
                    _data = np.transpose(_s_data[col_head])
                    
                    fx = np.fft.fft(_data, n=None, axis=-1, norm=None)
                    amplitude = abs(fx)*2/len(fx)
                    frequency = np.fft.fftfreq(len(fx), self.sampling_time)
                    peak_frequency = frequency[amplitude.argmax()]
                    
                    # draw 
                    plt.ioff()
                    plt.clf()
                    
                    _dpi = 100
                    plt.figure(figsize=(800/_dpi,900/_dpi), dpi=_dpi)
                    plt.rc('xtick', labelsize=7)
                    plt.rc('ytick', labelsize=7)
                    
                    # draw raw data
                    plt.subplot(3, 1, 1)
                    plt.plot(_data, '-')
                    plt.title(f'Raw Data({col_head})', fontsize=13)
                    plt.xlabel(f'Time({self.sampling_time}sec)', fontsize=10, labelpad=5)
                    plt.ylabel('Magnitude', fontsize=10, labelpad=5)
                    
                    # draw fft
                    plt.subplot(3, 1, 2)
                    plt.plot(frequency, amplitude, '-')
                    plt.title('FFT', fontsize=13)
                    plt.xlabel('Frequency(Hz)', fontsize=10, labelpad=5)
                    plt.ylabel('Amplitude', fontsize=10, labelpad=5)
                    
                    plt.annotate(f"Peak : {peak_frequency:.2f}Hz", xy=(peak_frequency, amplitude[amplitude.argmax()]), fontsize=7)

                    # draw spectogram
                    plt.subplot(3, 1, 3)
                    f, tt, Sxx = signal.spectrogram(_data, fs=self.sampling_freq, scaling='density')
                    plt.pcolormesh(tt, f, Sxx, shading='gouraud', cmap='jet')
                    plt.title('Spectogram', fontsize=13)
                    plt.xlabel('Time(s)', fontsize=10, labelpad=5)
                    plt.ylabel('Frequency(Hz)', fontsize=10, labelpad=5)
                    
                    plt.tight_layout()
                    plt.savefig(self.result_path / f'{col_head}.png', dpi=100)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"{e}")
                
            # update output table
            output_files = [f for f in self.result_path.iterdir() if f.is_file()]
            for file in output_files:
                self.output_model.appendRow([QStandardItem(str(file.name))])
            self.table_output.resizeColumnsToContents()
            
            QMessageBox.information(self, "Processing", "Done")
                
    
    # close event callback function by user
    def closeEvent(self, a0: QCloseEvent) -> None:
        # do action for user
        return super().closeEvent(a0)
    
    def on_dbclick_select(self):
        row = self.table_output.currentIndex().row()
        col = self.table_output.currentIndex().column()
        
        image_path = self.result_path / self.output_model.index(row, col).data()
        image = ImageQt.ImageQt(Image.open(image_path))
        pixmap = QtGui.QPixmap.fromImage(image)
        
        self.wnd_view.setPixmap(pixmap.scaled(self.wnd_view.size(), Qt.AspectRatioMode.KeepAspectRatio))

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