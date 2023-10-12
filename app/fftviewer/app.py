'''
FFT & Spectogram viewer
@author bh.hwang@iae.re.kr
'''

import sys, os
from PyQt6 import QtGui
import cv2
import pathlib
import json
from PyQt6.QtGui import QImage, QPixmap, QCloseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QMessageBox
from PyQt6.uic import loadUi
from PyQt6.QtCore import QObject, Qt, QTimer, QThread, pyqtSignal
import timeit
from datetime import datetime
import argparse

# pre-defined options
WORKING_PATH = pathlib.Path(__file__).parent
APP_UI = WORKING_PATH / "gui.ui"

# Viewer Main window GUI
class viewerWindow(QMainWindow):
    def __init__(self, config:str):
        super().__init__()
        loadUi(APP_UI, self)


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
    window.start_monitor()
    sys.exit(app.exec())