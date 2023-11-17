'''
FFT & Spectogram viewer + with serial comm.
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
from scipy import signal as scisignal
from PIL import ImageQt, Image
import serial
from sys import platform
import threading
import signal
import time

# pre-defined options
WORKING_PATH = pathlib.Path(__file__).parent
APP_UI = WORKING_PATH / "gui.ui"

# Viewer Main window GUI
class viewerWindow(QMainWindow):
    def __init__(self, config:str):
        super().__init__()
        loadUi("./gui.ui", self)
        
        # communication device
        self.serial = None
        
        # menu
        self.actionOpen.triggered.connect(self.on_select_file_open)
        
        # event
        self.btn_calculate.clicked.connect(self.on_click_calculate)
        self.btn_connect.clicked.connect(self.on_click_connect)
        self.btn_disconnect.clicked.connect(self.on_click_disconnect)
        self.table_output.doubleClicked.connect(self.on_dbclick_select)
        
        # signals
        signal.signal(signal.SIGINT, self.serial_thread_handler)
        signal.signal(signal.SIGTERM, self.serial_thread_handler)
        
        # gui component
        output_table = pyqtSignal(str)
        self.output_table_columns = ["Output", "Last updated"]
        
        self.output_model = QStandardItemModel()
        self.output_model.setColumnCount(len(self.output_table_columns))
        self.output_model.setHorizontalHeaderLabels(self.output_table_columns)
        self.table_output.setModel(self.output_model)
        
        # component initialize
        self.btn_disconnect.setEnabled(False)
        
        # variables
        self.csv_filepath = pathlib.Path()
        self.result_path = pathlib.Path()
        self.csv_filename = ""
        self.csv_data = pd.DataFrame()
        self.sampling_freq = 0.0
        self.use_channels = 1
        self.available_channels = 1
        self.csv_rows = 1                       # opened csv file number of rows
        self.serial_read_thread = None          # pyserial object
        self.serial_read_thread_exit = False    # serial read thread termination flag
        
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
                self.edit_time_range_end.setText(str(self.csv_data.shape[0]*self.sampling_time))
                self.edit_time_range_start.setText(str(0.0))
                self.statusBar().showMessage(f"Opened Data Dimension : {self.csv_data.shape}")
                self.label_filepath.setText(str(self.csv_filepath))
                self.label_rows.setText(str(self.csv_data.shape[0]))
                self.label_cols.setText(str(self.csv_data.shape[1]))
                
                # update prev result images
                self.result_path = self.csv_filepath.parent / self.csv_filename
                self.result_path.mkdir(parents=True, exist_ok=True)
                self.result_update(self.result_path)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"{e}")

    # serial thread exit handler        
    def serial_thread_handler(self, signum, frame):
        self.serial_read_thread_exit = True
        
    # connect to communication device (serial)
    def on_click_connect(self):
        try:
            if self.serial!=None:
                QMessageBox.warning(self, "Connection Warning", "Serial communication device is currently in use")
                raise Exception("Serial communication device is currently in use.")
            
            # _port = self.edit_serial_port.text()
            # _baudrate = int(self.edit_serial_baudrate.text())
            # self.serial = serial.Serial(port=_port, baudrate=_baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0, xonxoff=False)
            # if not self.serial.is_open:
            #     self.serial.open()
            #     self.statusBar().showMessage(f"{_port} opened successfully")
            
            self.btn_disconnect.setEnabled(True)
            self.btn_connect.setEnabled(False)
            
            # read thread starting..
            self.serial_read_thread = threading.Thread(target=self.read_thread, args=self)
            self.serial_read_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{e}")
    
    # disconnect to communication device (serial)
    def on_click_disconnect(self):
        try:
            signal.siginterrupt(signal.SIGUSR1, False) # read thread exit signal
            
            if self.serial!=None:
                self.serial.close()
                del self.serial
                self.serial = None
                
                self.btn_disconnect.setEnabled(False)
                self.btn_connect.setEnabled(True)
                
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{e}")
            
    # serial comm. data parsing
    def serial_parse(self, packet):
        pass
    
    # threads in read from  serial
    def read_thread(self):
        try:        
            while not self.serial_read_thread_exit:
                print("reading....")
                
                # buffer = self.serial.read()
                # self.serial_parse(buffer)# !!! must changing
                
                time.sleep(0.1)
        except Exception as e:
            
            pass
    
    # calculate fft & spectogram
    def on_click_calculate(self):
        # clear output table
        self.output_model.setRowCount(0)
               
        # read user parameters
        self.sampling_freq = float(self.edit_sampling_freq.text())
        self.use_channels = int(self.edit_use_channels.text())
        self.sampling_time = 1/self.sampling_freq
        self.use_time_range_start = float(self.edit_time_range_start.text())
        self.use_time_range_end = float(self.edit_time_range_end.text())
        
        if len(self.csv_filename)<1:
            QMessageBox.critical(self, "Error", f"No file specified to open")
            return
        
        # check parameters
        if self.use_channels > self.available_channels:
            QMessageBox.critical(self, "Error", f"Use Channel parameter exceeds the number of columns {self.available_channels}")
            return
        
        # re-open csv file
        _row_start = int(self.csv_rows*self.use_time_range_start/(self.csv_rows*self.sampling_time))
        if self.use_time_range_end-self.use_time_range_start<0:
            QMessageBox.warning(self, "Warning", f"Invalid Time Range")
            return
        _rows = int(self.csv_rows*(self.use_time_range_end-self.use_time_range_start)/(self.csv_rows*self.sampling_time))
        self.csv_data = pd.read_csv(self.csv_filepath, usecols=range(self.use_channels), skiprows=range(1, _row_start), nrows=_rows)
        
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
                    t = np.arange(0.0, float(_data.shape[0]*self.sampling_time), self.sampling_time)
                    plt.subplot(3, 1, 1)
                    plt.plot(t, _data, '-')
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
                    f, tt, Sxx = scisignal.spectrogram(_data, fs=self.sampling_freq, scaling='density')
                    plt.pcolormesh(tt, f, Sxx, shading='gouraud', cmap='jet')
                    plt.title('Spectogram', fontsize=13)
                    plt.xlabel('Time(s)', fontsize=10, labelpad=5)
                    plt.ylabel('Frequency(Hz)', fontsize=10, labelpad=5)
                    
                    plt.tight_layout()
                    plt.savefig(self.result_path / f'{col_head}.png', dpi=100)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"{e}")
                
            # update output table
            self.result_update(self.result_path)
            
            QMessageBox.information(self, "Processing", "Done")
    
    # result image file list update in path
    def result_update(self, path):
        self.output_model.setRowCount(0)
        output_files = [f for f in self.result_path.iterdir() if f.is_file()]
        for file in output_files:
            m_time = os.path.getmtime(file.absolute())
            dt_m = datetime.fromtimestamp(m_time)
            self.output_model.appendRow([QStandardItem(str(file.name)), QStandardItem(str(dt_m))])
        self.table_output.resizeColumnsToContents()
    
    # close event callback function by user
    def closeEvent(self, a0: QCloseEvent) -> None:
        # do action for user
        return super().closeEvent(a0)
    
    # select result in image list & show 
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