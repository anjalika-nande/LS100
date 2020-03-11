# -*- coding: utf-8 -*-
import sys
import numpy as np
import os
from multiprocessing import Process, Value
import pickle
import cv2
from ctypes import *
import pyqtgraph as pg
import socket

from PyQt5 import QtGui, QtWidgets, QtCore, Qt, uic
import sys
sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook

class Fishreturn(Structure):
    _fields_ = [("camera_framenum", c_uint),
                ("camera_timestamp", c_double),
                ("camera_fps", c_double),

                ("mode_updated", c_bool),

                ("errorcode", c_int),

                ("fish_movie_framenum", c_uint),

                ("fish_position_x", c_double),
                ("fish_position_y", c_double),

                ("fish_orientation", c_double),
                ("fish_accumulated_orientation", c_double),
                ("fish_accumulated_orientation_lowpass", c_double),
                ("fish_accumulated_orientation_variance", c_double),

                ("fish_accumulated_path", c_double),

                ("bout_found", c_bool),
                ("bout_timestamp_start", c_double),
                ("bout_timestamp_end", c_double),
                ("bout_heading_angle_change", c_double),
                ("bout_distance_traveled_change", c_double),

                ("fish_area", c_double),
                ]


class keyPressEvent(QtCore.QObject):
    def __init__(self, parent):
        super(keyPressEvent, self).__init__(parent)
        self.parent = parent


    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.KeyPress:
            #print event.key()
            if event.key() == 16777236:
                self.parent.xoffset += 2

            if event.key() == 16777234:
                self.parent.xoffset -= 2

            if event.key() == 16777235:
                self.parent.yoffset += 2

            if event.key() == 16777237:
                self.parent.yoffset -= 2


            if event.key() == ord('T'):
                self.parent.radius += 16

            if event.key() == ord('R'):
                self.parent.radius -= 16 # the width has to be devidable to 32

            if event.key() == ord('G'):
                self.parent.gain -= 0.05

            if event.key() == ord('H'):
                self.parent.gain += 0.05

            if event.key() == ord('S'):
                self.parent.shutter -= 0.05

            if event.key() == ord('D'):
                self.parent.shutter += 0.05

            if event.key() == 16777216:  # ESC
                self.parent.close()

        return False # not complete

class CameraAlignment_Dialog(QtWidgets.QDialog):
    def __init__(self, fish_index, running, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.fish_index = fish_index
        self.running = running

        path = os.path.dirname(__file__)
        uic.loadUi(os.path.join(path, "camera_alignment.ui"), self)

        computer_name = socket.gethostname()

        if computer_name == "NW152-beh-2":
            self.setup_ID = 0

        #if computer_name == "NW152-beh-2":
            #self.setup_ID = 1


        if self.setup_ID == 0:
            self.root_path = r"C:\LS100\LS100_free_swimming_4fish_data"
            self.lib = cdll.LoadLibrary(r"C:\Users\Max\Desktop\LS100\modules\fishcamera_C\x64\Release\fishcamera.dll")

        #if self.setup_ID == 1:
            #self.root_path = r"D:\Yasuko_free_swimming_4fish_data"
            #self.lib = cdll.LoadLibrary(r"C:\Users\Yasuko Isoe\PyCharm_projects\fishsetup\modules\fishcamera_C\x64\Release\fishcamera.dll")

        self.installEventFilter(keyPressEvent(self))
        self.layout_histogram.installEventFilter(keyPressEvent(self))
        self.label_view_camera.installEventFilter(keyPressEvent(self))

        self.lib.get_fish_info.restype = Fishreturn
        self.lib.get_gain.restype = c_double
        self.lib.get_shutter.restype = c_double

        [self.radius, self.xoffset, self.yoffset, self.gain, self.shutter] = 1024, 0, 0, 0.5, 0.5


        if self.setup_ID == 0:
            if self.fish_index == 0:
                self.camera_serial = 16307759
            elif self.fish_index == 1:
                self.camera_serial = 19300526
            # elif self.fish_index == 2:
            #     self.camera_serial = 19242806

        # if self.setup_ID == 1:
        #
        #     if self.fish_index == 0:
        #         self.camera_serial = 16307759
        #     elif self.fish_index == 1:
        #         self.camera_serial = 19300526
            # elif self.fish_index == 2:
            #     self.camera_serial = 19242806

        try:
            [self.radius, self.xoffset, self.yoffset, self.gain, self.shutter] = pickle.load(open(os.path.join(self.root_path, "camera_configuration_fish%d.dat"%self.fish_index), 'rb'))
        except:
            print("???")
            pass

        self.lib.open_cam(self.camera_serial, 1024, 0, 0, c_float(self.gain), c_float(self.shutter), c_char_p("".encode()), c_char_p("".encode()), c_char_p("".encode()))

        pg.setConfigOption('background', pg.mkColor(0.95))
        pg.setConfigOption('foreground', 'k')

        self.my_plot = pg.PlotWidget()
        self.layout_histogram.addWidget(self.my_plot)

        self.my_plot.setLabel('left', 'Mean Brightness')
        self.my_plot.setLabel('bottom', 'Normalized radius')
        self.my_plot.setXRange(0, 1)
        self.my_plot.setYRange(0, 255)

        curvePen = pg.mkPen(color=(255, 15, 10), width=4.5)

        self.curve = pg.PlotCurveItem(pen = curvePen)

        self.my_plot.addItem(self.curve)

        self.fish_roi_buffer = create_string_buffer(2048*2048)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.Refresh)
        self.timer.start(40.)

    def closeEvent(self, event):
        print("Closing...")

        self.lib.close_cam()
        print("Saving configuration file")
        pickle.dump([self.radius, self.xoffset, self.yoffset, self.gain, self.shutter], open(os.path.join(self.root_path, "camera_configuration_fish%d.dat"%self.fish_index), 'wb'))

        # also tell the panda3d to close
        self.running.value = 0

        self.close()

    def Refresh(self):

        self.radius = int(self.radius/16)*16
        self.xoffset = int(self.xoffset/2)*2
        self.yoffset = int(self.yoffset/2)*2

        self.lib.set_gain(c_double(self.gain))
        self.lib.set_shutter(c_double(self.shutter))

        rs = np.linspace(0, 500, 100)/500.
        import datetime
        t = datetime.datetime.now()
        self.lib.get_image(self.fish_roi_buffer, 2048*2048)

        roi_ar = np.fromstring(self.fish_roi_buffer, dtype=np.uint8).reshape((2048, 2048))
        #roi_ar = (np.random.random((2048, 2048))*255).astype(np.uint8)
        pic = cv2.resize(roi_ar, (500, 500)).flatten()

        radial_histogram = create_string_buffer(100)
        self.lib.get_radial_histogram(pic.tobytes(), radial_histogram)

        radial_histogram = np.fromstring(radial_histogram, dtype=np.uint8)
        self.curve.setData(rs, radial_histogram)

        roi_ar = cv2.cvtColor(roi_ar, cv2.COLOR_GRAY2RGBA)

        cv2.circle(roi_ar, (1024+self.xoffset, 1024-self.yoffset), radius = self.radius, color = (0, 255, 255, 255), thickness=3)

        cv2.line(roi_ar, (1024-int(0.5*self.radius)+self.xoffset, 1024-self.yoffset), (1024+int(0.5*self.radius)+self.xoffset, 1024-self.yoffset), color = (0, 255, 255, 255), thickness=3)
        cv2.line(roi_ar, (1024+self.xoffset, 1024-int(0.5*self.radius)-self.yoffset), (1024+self.xoffset, 1024+int(0.5*self.radius)-self.yoffset), color = (0, 255, 255, 255), thickness=3)

        roi_ar = cv2.resize(roi_ar, (900, 900)) #1800, 1800
        QI = QtGui.QImage(roi_ar, 900, 900, QtGui.QImage.Format_ARGB32) # 1800, 1800

        self.label_view_camera.setPixmap(QtGui.QPixmap.fromImage(QI))

        text = "Radius: %d; xoffset: %d; yoffset: %d; Gain set : %.2f; Shutter set: %.2f\n"%(self.radius, self.xoffset, self.yoffset, self.gain, self.shutter)
        text += "Gain actual: %.2f; Shutter actual: %.2f" % (float(self.lib.get_gain()), float(self.lib.get_shutter()))
        self.label_info.setText(text)

        self.timer.start(40.)


class GUI_Process(Process):
    def __init__(self, fish_index):
        Process.__init__(self)
        self.fish_index = fish_index

        self.running = Value("i", 1)

    def run(self):
        app = QtWidgets.QApplication(sys.argv)

        main = CameraAlignment_Dialog(self.fish_index, self.running)

        main.show()
        app.exec_()

