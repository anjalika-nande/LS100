# -*- coding: utf-8 -*-

from multiprocessing import Process
import sys
import os
from ctypes import *
import numpy as np
import pickle
import cv2

python_file_path = os.path.dirname(os.path.abspath(__file__))

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

class Fishcamera(Process):
    def __init__(self, shared, fish_index):
        Process.__init__(self)

        self.shared = shared
        self.fish_index = fish_index
        # update serial numbers
        if self.shared.setup_ID == 0:

            if self.fish_index == 0:
                self.camera_serial = 16307759
            elif self.fish_index == 1:
                self.camera_serial = 19300526
            #elif self.fish_index == 2:
                #self.camera_serial = 19242806
            # elif self.fish_index == 3:
            #     self.camera_serial = 17096220
            #

        # if self.shared.setup_ID == 1:
        #     if self.fish_index == 0:
        #         self.camera_serial = 16307759
        #     elif self.fish_index == 1:
        #         self.camera_serial = 19300526
            #elif self.fish_index == 2:
                #self.camera_serial = 19242806
            # elif self.fish_index == 3:
            #     self.camera_serial = 17475983
            #

        self.camera_opened = False

    def run(self):
        try:
            self.loop()
        except:
            self.shared.error("fishcamera_error.txt", sys.exc_info())

    def loop(self):

        self.lib = cdll.LoadLibrary(r"C:\Users\Max\Desktop\LS100\modules\fishcamera_C\x64\Release\fishcamera.dll")

        self.lib.get_fish_info.restype = Fishreturn

        try:

            [self.shared.alignment_radius[self.fish_index].value, self.shared.alignment_xoffset[self.fish_index].value, self.shared.alignment_yoffset[self.fish_index].value, self.shared.alignment_gain[self.fish_index].value,self.shared.alignment_shutter[self.fish_index].value] = pickle.load(open(os.path.join(self.shared.root_path, "camera_configuration_fish%d.dat"%self.fish_index), 'rb'))
            print(self.shared.root_path, self.shared.alignment_radius[self.fish_index].value)
        except:
            print("Fish %d not started. Either camera not configured or not found."%self.fish_index)
            return



        while self.shared.running.value == 1:

            if self.shared.camera_running[self.fish_index].value == 1 and self.camera_opened == False:

                self.fish_path = self.shared.get_fish_path(self.fish_index)

                #self.lib.reset_cam(self.camera_serial) # needs to be done in a separte programme still

                print("Starting cam", self.fish_index, self.shared.alignment_gain[self.fish_index].value,
                      self.shared.alignment_shutter[self.fish_index].value)

                if self.lib.open_cam(self.camera_serial,
                                    self.shared.alignment_radius[self.fish_index].value,
                                    self.shared.alignment_xoffset[self.fish_index].value,
                                    self.shared.alignment_yoffset[self.fish_index].value,
                                    c_float(self.shared.alignment_gain[self.fish_index].value),
                                    c_float(self.shared.alignment_shutter[self.fish_index].value),
                                    c_char_p(os.path.join(self.fish_path, "fish_roi.avi").encode()), # fish_roi_movie.avi;;; make this an empty string when no movie recording is required (saves a lot of space)
                                    c_char_p(os.path.join(self.fish_path, "mode_movie.avi").encode()),
                                    c_char_p(os.path.join(self.fish_path, "current_mode.png").encode()) ) == False:
                    print("Camera %d could not be opened."%self.fish_index)
                else:

                    self.camera_opened = True

                    self.fish_roi_buffer = create_string_buffer(100*100)

                    # once the recording button was pushed
                    self.full_frame_buffer_list = []
                    self.full_frame_stimulus_information = []
                    self.full_frame_buffer = create_string_buffer(4*self.shared.alignment_radius[self.fish_index].value**2)

            if self.shared.camera_running[self.fish_index].value == 0 and self.camera_opened == True:
                self.lib.close_cam()
                self.camera_opened = False

            if self.camera_opened == True:

                if self.shared.full_frame_recording_started[self.fish_index].value == 0: # not in the fullframe recording mode

                    data = self.lib.get_fish_info(self.fish_roi_buffer, c_bool(self.shared.ignore_fish[self.fish_index].value), c_bool(False), self.full_frame_buffer) # do not copy info to buffer

                # if we want to record (for illustration purposes)
                if self.shared.full_frame_recording_started[self.fish_index].value == 1:
                    data = self.lib.get_fish_info(self.fish_roi_buffer, c_bool(self.shared.ignore_fish[self.fish_index].value), c_bool(True), self.full_frame_buffer)

                    full_frame_buffer_numpy = np.fromstring(self.full_frame_buffer, dtype=np.uint8).reshape((self.shared.alignment_radius[self.fish_index].value*2, self.shared.alignment_radius[self.fish_index].value*2))

                    self.full_frame_buffer_list.append(full_frame_buffer_numpy)
                    self.full_frame_stimulus_information.append([self.shared.current_stimulus_time[self.fish_index].value,
                                                                 self.shared.current_stimulus_index[self.fish_index].value,
                                                                 self.shared.current_trial[self.fish_index].value,
                                                                 data.camera_timestamp,
                                                                 data.fish_position_x,
                                                                 data.fish_position_y,
                                                                 data.fish_orientation,
                                                                 self.shared.current_info0[self.fish_index].value,
                                                                 self.shared.current_info1[self.fish_index].value,
                                                                 self.shared.current_info2[self.fish_index].value])

                    # record 2000 frames... TODO: Make this flexible
                    if len(self.full_frame_buffer_list) > 2500:
                        for i in range(len(self.full_frame_buffer_list)):
                            filename = os.path.join(self.fish_path, "recorded_full_frames", "full_frame_%05d.png"%i)
                            cv2.imwrite(filename, self.full_frame_buffer_list[i])

                        with open(os.path.join(self.fish_path, "recorded_full_frames", "stimulus_fish_info.dat"), 'wb') as f:
                            pickle.dump(self.full_frame_stimulus_information, f)

                        # reset the lists
                        self.full_frame_buffer_list = []
                        self.full_frame_stimulus_information = []

                        self.shared.full_frame_recording_started[self.fish_index].value = 0

                self.shared.current_camera_framenum[self.fish_index].value = data.camera_framenum
                self.shared.current_camera_timestamp[self.fish_index].value = data.camera_timestamp
                self.shared.current_camera_fps[self.fish_index].value = data.camera_fps

                self.shared.current_errorcode[self.fish_index].value = data.errorcode

                self.shared.current_fish_position_x[self.fish_index].value = data.fish_position_x
                self.shared.current_fish_position_y[self.fish_index].value = data.fish_position_y

                self.shared.current_fish_center_distance[self.fish_index].value = np.sqrt(data.fish_position_x**2 + data.fish_position_y**2)

                self.shared.current_fish_orientation[self.fish_index].value = data.fish_orientation
                self.shared.current_fish_accumulated_orientation[self.fish_index].value = data.fish_accumulated_orientation
                self.shared.current_fish_accumulated_orientation_lowpass[self.fish_index].value = data.fish_accumulated_orientation_lowpass
                self.shared.current_fish_accumulated_orientation_variance[self.fish_index].value = data.fish_accumulated_orientation_variance
                self.shared.current_fish_accumulated_path[self.fish_index].value = data.fish_accumulated_path

                self.shared.current_bout_found[self.fish_index].value = data.bout_found
                self.shared.current_bout_timestamp_start[self.fish_index].value = data.bout_timestamp_start
                self.shared.current_bout_timestamp_end[self.fish_index].value = data.bout_timestamp_end

                self.shared.current_fish_area[self.fish_index].value = data.fish_area
                self.shared.current_fish_roi_buffer[self.fish_index][:] = self.fish_roi_buffer

                if data.mode_updated == True:
                    self.shared.mode_calculated[self.fish_index].value = 1
                    self.shared.updated_mode_image[self.fish_index].value = 1

                # add the data to the recorder que
                if self.shared.stimulus_running[self.fish_index].value == 1:
                    # send the current data to the recorder que, also add the current info0 value. if info0 corresponds to some stimulus paramters (for example set when a bout is detectred), info0 will be the setting at the last bout

                    self.shared.dataqueue.put([0, self.fish_index, data.camera_framenum, data.camera_timestamp, data.camera_fps,
                                               data.errorcode, data.fish_movie_framenum, data.fish_position_x, data.fish_position_y,
                                               data.fish_orientation, data.fish_accumulated_orientation, data.fish_accumulated_orientation_lowpass,
                                               data.fish_accumulated_orientation_variance, data.fish_accumulated_path, data.fish_area,
                                               self.shared.current_info0[self.fish_index].value, self.shared.current_info1[self.fish_index].value, self.shared.current_info2[self.fish_index].value])

                    if data.bout_found == True:
                        self.shared.dataqueue.put([4, self.fish_index, data.bout_timestamp_start, data.bout_timestamp_end])

                if data.bout_found == True:
                    self.shared.new_bout[self.fish_index].value = 1 # tell the scene that tere is a new bout, this might update some stimulus parameters
                    self.shared.new_bout_heading_angle_change[self.fish_index].value = data.bout_heading_angle_change
                    self.shared.new_bout_distance_traveled_change[self.fish_index].value = data.bout_distance_traveled_change


        if self.camera_opened == True:
            self.lib.close_cam()
            self.camera_opened = False
