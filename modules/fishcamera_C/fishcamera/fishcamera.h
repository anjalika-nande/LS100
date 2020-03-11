#pragma once
#define DLLEXPORT extern "C" __declspec(dllexport)

#include "Spinnaker.h"
#include "SpinGenApi/SpinnakerGenApi.h"
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include "windows.h"

using namespace Spinnaker;
using namespace Spinnaker::GenApi;
using namespace Spinnaker::GenICam;
using namespace std;
using namespace cv;

struct FishReturn
{
	unsigned int camera_framenum;
	double camera_timestamp;

	double camera_fps;

	bool mode_updated;
	int errorcode;

	int fish_movie_framenum;

	double fish_position_x;
	double fish_position_y;

	double fish_orientation;
	double fish_accumulated_orientation;
	double fish_accumulated_orientation_lowpass;
	double fish_accumulated_orientation_variance;

	double fish_accumulated_path;

	bool bout_found;
	double bout_timestamp_start;
	double bout_timestamp_end;
	double bout_heading_angle_change;
	double bout_distance_traveled_change;

	double fish_area;
};

// Camera stuff
SystemPtr system_gl;
CameraList camList;
CameraPtr pCam;
ImagePtr pResultImage;

VideoWriter fish_roi_video;
VideoWriter mode_video;

cv::String global_filename_modeimage;

double last_timestamp_s;
double timestamp_seconds_start;

int circular_counter;
int fish_movie_framenum;

double fish_accumulated_orientation_lowpass;

double circular_history_time[100];
double circular_history_fish_accumulated_orientation[100];
double circular_history_fish_accumulated_path[100];

double last_bout_timestamp_end;

double fish_accumulated_path = -1, fish_accumulated_orientation;

int fish_serial;

int picture_height;
int picture_width;

int roi_x0;
int roi_x1;
int roi_y0;
int roi_y1;

bool inside_bout;
bool any_error_during_bout;
bool variance_was_low;

int bout_start_i;
int bout_end_i;

int live_mode_number;
int live_mode_frame_index;
double last_mode_image_added_time;

// needs to be freed when closing the camera
unsigned char* mode;
unsigned char* live_mode; 
unsigned char *live_mode_counter;
unsigned char *live_mode_max_counter;
cv::Mat mode_mat;

cv::Mat frame100 = cv::Mat(100, 100, CV_8U);
cv::Mat frame100a = cv::Mat(100, 100, CV_8U);
cv::Mat frame100b = cv::Mat(100, 100, CV_8U);
cv::Mat frame100c = cv::Mat(100, 100, CV_8U);
cv::Mat frame100d = cv::Mat(100, 100, CV_8U);
cv::Mat thresholded100 = cv::Mat(100, 100, CV_8U);
cv::Mat blurred100 = cv::Mat(100, 100, CV_8U);

cv::Mat frame100_bigger = cv::Mat(200, 200, CV_8U);
cv::Mat thresholded100_bigger = cv::Mat(200, 200, CV_8U);
cv::Mat blurred100_bigger = cv::Mat(200, 200, CV_8U);

cv::Point min_loc, max_loc;

struct FishReturn _last_good_return;

/// non-export internal functions

bool compare_contour_areas(std::vector<cv::Point> contour1, std::vector<cv::Point> contour2);
bool add_fish_roi_to_movie(cv::Mat fish_roi, unsigned int camera_framenum, int errorcode);

// functions visible from the outside of the dll
DLLEXPORT bool reset_cam(unsigned int serial_number);
DLLEXPORT bool open_cam(unsigned int serial_number, unsigned int radius, unsigned int xoffset, unsigned int yoffset, float gain, float shutter, const char* filename_fish_roi, const char* filename_mode, const char* filename_modeimage);
DLLEXPORT bool close_cam(void);
DLLEXPORT bool get_image(unsigned char *image_data, size_t size);
DLLEXPORT bool get_radial_histogram(unsigned char *image, unsigned char *output_radial_mean);

DLLEXPORT double get_gain();
DLLEXPORT bool set_gain(double value);

DLLEXPORT double get_brightness();
DLLEXPORT bool set_brightness(double value);

DLLEXPORT double get_shutter();
DLLEXPORT bool set_shutter(double value);

DLLEXPORT struct FishReturn const get_fish_info(unsigned char *fish_roi, bool ignore_fish, bool copy_full_frame, unsigned char *full_frame_buffer);

