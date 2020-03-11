#include <windows.h>
#include "fishcamera.h"
#include <iostream>
#include <math.h>

bool compare_contour_areas(std::vector<cv::Point> contour1, std::vector<cv::Point> contour2) {
	double i = fabs(contourArea(cv::Mat(contour1)));
	double j = fabs(contourArea(cv::Mat(contour2)));
	return (i > j);
}

bool add_fish_roi_to_movie(cv::Mat fish_roi, unsigned int camera_framenum, int errorcode) {

	if (fish_roi_video.isOpened() == true) {

		cv::Mat fish_roi_copy;
		fish_roi.copyTo(fish_roi_copy);

		//cv::putText(fish_roi_copy, std::to_string(camera_framenum) + "," + std::to_string(errorcode), cv::Point(5, 10), cv::FONT_HERSHEY_SIMPLEX, 0.4, 255, 1, 8, false);

		fish_roi_video.write(fish_roi_copy);
		fish_movie_framenum += 1;

		return true;
	}

	return false;
}

unsigned char substract_background(unsigned char image, unsigned char background) {

	// the fish will always be darker than the background

	if (image >= background)
		return 0;
	else
		return background - image;
}


DLLEXPORT bool reset_cam(unsigned int serial_number) {
	
	
	SystemPtr system_gl_reset;
	CameraList camList_reset;
	CameraPtr pCam_reset;

	// Find the camera and connect
	system_gl_reset = System::GetInstance();

	try {


		// Retrieve list of cameras from the system
		camList_reset = system_gl_reset->GetCameras();

		pCam_reset = camList_reset.GetBySerial(to_string(serial_number));
		pCam_reset->Init();

		pCam_reset->DeviceReset();

		pCam_reset->DeInit();

		// Release system
		pCam_reset = NULL;
		
		camList_reset.Clear();
		
		system_gl_reset->ReleaseInstance();

		Sleep(500);
		
		cout << "All good";
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}
	

	return true;
}

DLLEXPORT bool open_cam(unsigned int serial_number, unsigned int radius, unsigned int xoffset, unsigned int yoffset, float gain, float shutter, const char* filename_fish_roi, const char* filename_mode, const char* filename_modeimage)
{
	picture_width = radius * 2;
	picture_height = radius * 2;
	fish_serial = serial_number;

	global_filename_modeimage = cv::String(filename_modeimage);

	try {
		system_gl = System::GetInstance();
		camList = system_gl->GetCameras();
		cout << "Loading...." << camList.GetSize();
		pCam = camList.GetBySerial(to_string(serial_number));
		
		pCam->Init();
		cout << pCam->DeviceFirmwareVersion();
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}
	

	try {

		INodeMap & nodeMap = pCam->GetNodeMap();
		CEnumerationPtr ptrAcquisitionMode = nodeMap.GetNode("AcquisitionMode");
		CEnumEntryPtr ptrAcquisitionModeContinuous = ptrAcquisitionMode->GetEntryByName("Continuous");
		int64_t acquisitionModeContinuous = ptrAcquisitionModeContinuous->GetValue();
		ptrAcquisitionMode->SetIntValue(acquisitionModeContinuous);

		// setup the buffer properties
		INodeMap & nodeMapTLStream = pCam->GetTLStreamNodeMap();
		CEnumerationPtr StreamNode = nodeMapTLStream.GetNode("StreamBufferHandlingMode");
		StreamNode->SetIntValue(3); // newest, overwrite
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}

	try {
		pCam->ChunkSelector.SetValue(ChunkSelectorEnums::ChunkSelector_Timestamp);
		pCam->ChunkEnable.SetValue(true);
		
		pCam->ChunkSelector.SetValue(ChunkSelectorEnums::ChunkSelector_OffsetX);
		pCam->ChunkEnable.SetValue(true);

		pCam->ChunkSelector.SetValue(ChunkSelectorEnums::ChunkSelector_OffsetY);
		pCam->ChunkEnable.SetValue(true);

		// frame id chunk does not work

		pCam->ChunkModeActive.SetValue(true);
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}

	// set the roi on the camera (don't change anymore)
	// if this is incorrect, crashes, check this!
	try {
		pCam->OffsetX.SetValue(1024 - radius + xoffset, false);
		pCam->OffsetY.SetValue(1024 - radius - yoffset, false);
		pCam->Width.SetValue(picture_width, false);
		pCam->Height.SetValue(picture_height, false);
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}
	
	set_gain(gain);
	set_shutter(shutter);
	
	last_timestamp_s = 0;

	circular_counter = 0;
	fish_accumulated_path = -1;

	/// start off with the full frame (no fish roi yet found)
	roi_x0 = 0;
	roi_x1 = picture_width;
	roi_y0 = 0;
	roi_y1 = picture_height;

	// create a videowriter for the fish roi
	mode = new unsigned char[picture_width * picture_height];
	live_mode = new unsigned char[picture_width * picture_height]; // needs to be freed when closing the camera
	live_mode_counter = new  unsigned char[256 * picture_width * picture_height];
	live_mode_max_counter = new  unsigned char[picture_width * picture_height];

	// mode initializes at zeros (will be changed during run)
	memset(mode, 0, picture_width * picture_height * sizeof(unsigned char));
	mode_mat = cv::Mat::zeros(picture_width, picture_height, CV_8UC1);
	memset(live_mode_counter, 0, 256 * picture_width * picture_height * sizeof(unsigned char));
	memset(live_mode_max_counter, 0, picture_width * picture_height * sizeof(unsigned char));

	live_mode_number = -1; // this counter the number of the mode (for disply in the image)
	live_mode_frame_index = 0;
	last_mode_image_added_time = 0;

	// Dummy function to initalizwe opencv 
	cv::Mat test = cv::Mat::zeros(100, 100, CV_8UC1);
	threshold(test, test, 15, 255, 0);

	// Open the video streams without comporession
	if (strlen(filename_fish_roi) > 0) {
		fish_roi_video.open(cv::String(filename_fish_roi), CV_FOURCC('D', 'I', 'V', 'X'), 60, cv::Size(100, 100), false);
		//fish_roi_video.open(cv::String(filename_fish_roi), 0, 60, cv::Size(100, 100), false);
		fish_movie_framenum = 0;

	}

	if (strlen(filename_mode) > 0) {
		mode_video.open(cv::String(filename_mode), CV_FOURCC('D', 'I', 'V', 'X'), 60, cv::Size(picture_width, picture_height), false);
	}

	// initialize standard variables for the global _last_good_return structure
	_last_good_return.camera_framenum = 0;
	_last_good_return.camera_timestamp = 0;
	_last_good_return.camera_fps = 0;

	_last_good_return.mode_updated = false;
	_last_good_return.errorcode = -1;
	_last_good_return.fish_movie_framenum = fish_movie_framenum;

	_last_good_return.fish_position_x = 0;
	_last_good_return.fish_position_y = 0;

	_last_good_return.fish_orientation = 0;
	_last_good_return.fish_accumulated_orientation = 0;
	_last_good_return.fish_accumulated_orientation_lowpass = 0;
	_last_good_return.fish_accumulated_orientation_variance = 0;

	_last_good_return.fish_accumulated_path = 0;

	_last_good_return.bout_found = false;
	_last_good_return.bout_timestamp_start = 0;
	_last_good_return.bout_timestamp_end = 0;
	_last_good_return.bout_heading_angle_change = 0;
	_last_good_return.bout_distance_traveled_change = 0;

	_last_good_return.fish_area = 0;
	
	
	// and start the image stream
	try {
		pCam->BeginAcquisition();
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}

	timestamp_seconds_start = -1; // reset the timestamp to zero, dont know how to do this on the camera
	
	return true;
}

DLLEXPORT bool close_cam(void)
{	
	delete[] mode;
	delete[] live_mode;
	delete[] live_mode_counter;
	delete[] live_mode_max_counter;
	
	if (fish_roi_video.isOpened() == true) fish_roi_video.release();
	if (mode_video.isOpened() == true) mode_video.release();

	pCam->EndAcquisition();
	pCam->DeInit();

	camList.Clear();

	// Release system
	pCam = NULL;

	system_gl->ReleaseInstance();
	
	return true;
}

DLLEXPORT bool get_image(unsigned char *image_data, size_t size) {
	if (pCam == NULL) return false;
	
	ImagePtr pResultImage = pCam->GetNextImage();
	
	ChunkData chunkData = pResultImage->GetChunkData();

	memcpy(image_data, pResultImage->GetData(), size);

	pResultImage->Release();

	return true;
}

DLLEXPORT bool get_radial_histogram(unsigned char *image, unsigned char *output_radial_mean) {

	double r_n[100];
	double r_sum[100];
	int i, j, k;
	double r;
	
	for (i = 0; i < 100; i++) {
		r_sum[i] = 0;
		r_n[i] = 0;
	}
	
	for (i = 0; i < 500; i++) {
		for (j = 0; j < 500; j++) {
			r = sqrt(pow(i - 250, 2) + pow(j - 250, 2));
			if (r < 250) {
				k = static_cast<int>(100 * r / 250);
				r_sum[k] += image[i * 500 + j];
				r_n[k] += 1;
			}
		}
	}

	for (i = 0; i < 100; i++) {
		output_radial_mean[i] = (unsigned char)(r_sum[i] / r_n[i]);
	}
	
	return true;
}


DLLEXPORT double get_gain() {
	
	if (pCam == NULL) return 0;

	return pCam->Gain.GetValue();

}

DLLEXPORT bool set_gain(double value) {

	if (pCam == NULL) return false;

	pCam->GainAuto.SetValue(Spinnaker::GainAutoEnums::GainAuto_Off);
	try {
		pCam->Gain.SetValue(value);
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}
	
	return true; 
}

DLLEXPORT double get_brightness() { return 0; }
DLLEXPORT bool set_brightness(double value) { return true; }

DLLEXPORT double get_shutter() { 

	if (pCam == NULL) return 0; 
	
	return pCam->ExposureTime.GetValue() / 1000.;  // make us in ms 
} 

DLLEXPORT bool set_shutter(double value) {

	if (pCam == NULL) return false;

	pCam->ExposureAuto.SetValue(Spinnaker::ExposureAutoEnums::ExposureAuto_Off);
	pCam->ExposureMode.SetValue(Spinnaker::ExposureModeEnums::ExposureMode_Timed);
	
	try {
		pCam->ExposureTime.SetValue(value*1000); // in make ms in us
	} catch (Spinnaker::Exception &e) {
		cout << "Error: " << e.what() << endl;
		return false;
	}
	
	return true;
}

DLLEXPORT struct FishReturn const get_fish_info(unsigned char *fish_roi, bool ignore_fish, bool copy_full_frame, unsigned char *full_frame_buffer)
{
	int i, j;
	
	unsigned char* pixrow;
	int fish_position_x, fish_position_y;
	double timestamp_seconds, delta_timestamp;
	double alpha_lowpass;
	
	double min_value, max_value;
	double fish_position_x_scaled, fish_position_y_scaled, fish_orientation;
	double fish_delta_position_x, fish_delta_position_y;
	double fish_delta_orientation;
	double fish_delta_path;

	double fish_area;
	double picture_norm_factor;

	double bout_finder_t_now;
	double bout_finder_t_past;

	double bout_finder_mean_sum;
	double bout_finder_mean;
	double bout_finder_variance;
	int bout_finder_i0;
	int bout_finder_past_i;
	double timestamp_seconds_now;

	// if we get an error, we assume the following: fish is still at the same position where it was before, same orientation, etc.
	struct FishReturn _return = _last_good_return;
	_return.bout_found = false;
	_return.mode_updated = false;
	
	cv::Mat frame = cv::Mat(roi_x1 - roi_x0, roi_y1 - roi_y0, CV_8U);
	cv::Mat thresholded = cv::Mat(roi_x1 - roi_x0, roi_y1 - roi_y0, CV_8U);
	cv::Mat blurred = cv::Mat(roi_x1 - roi_x0, roi_y1 - roi_y0, CV_8U);
	
	// standard of fish roi buffer is empty
	for (i = 0; i < 100 * 100; i++) fish_roi[i] = 0;

	ImagePtr pResultImage;

	try {

		pResultImage = pCam->GetNextImage();
	
	} catch (Spinnaker::Exception &e) {

		cout << "Error: " << e.what() << endl;
		
		roi_x0 = 0;
		roi_x1 = picture_width;
		roi_y0 = 0;
		roi_y1 = picture_height;
		any_error_during_bout = true;

		_return.errorcode = 7; // Camera error

		return _return;
	}
	
	// if full_frame_buffer is availble, copy the entire frame there
	memcpy(full_frame_buffer, pResultImage->GetData(), picture_height*picture_width);
	
	ChunkData chunkData = pResultImage->GetChunkData();
	
	// dont know how to reset the camera time stamp... so first frame is zero 
	timestamp_seconds_now = chunkData.GetTimestamp() / (1000 * 1000 * 1000.); //old flycapture: timestamp.cycleSeconds + ((timestamp.cycleCount + (timestamp.cycleOffset / 3072.0)) / 8000.0);
	if (timestamp_seconds_start == -1) timestamp_seconds_start = timestamp_seconds_now;
	timestamp_seconds = timestamp_seconds_now - timestamp_seconds_start;
	
	// The timestamp runs with rather high preceision from 0 to 128 (exluding 128), so we need to correct for this
	delta_timestamp = timestamp_seconds - last_timestamp_s;
	last_timestamp_s = timestamp_seconds;

	_return.camera_timestamp = timestamp_seconds;
	_return.camera_framenum = (unsigned int) pResultImage->GetFrameID();// chunkData.GetCounterValue(); does not work!
	_return.camera_fps = 1.0 / delta_timestamp;
	
	_return.fish_movie_framenum = fish_movie_framenum;

	pResultImage->Release();
	
	/////////////////////////////////////
	// Live mode calculation
	unsigned char c;
	int i0, i1, j0, j1, binx, biny;
	
	if (live_mode_frame_index > 1200) {

		// for 16 frames stay in this loop
		// this is to reset the background image counters, but split this into 16 parts, to distribute computation among between different frames
		// this is 1/16 of the entire buffer length
		binx = 256 * picture_width * picture_height / 16;
		biny = picture_width * picture_height / 16; // both width and height should be dividable by 32

		memset(live_mode_counter + (live_mode_frame_index - 1200)*binx, 0, binx * sizeof(unsigned char));
		memset(live_mode_max_counter + (live_mode_frame_index - 1200)*biny, 0, biny * sizeof(unsigned char));

		live_mode_frame_index += 1;

		if (live_mode_frame_index == 1216) {
			live_mode_frame_index = 0;
		}

	} else if (_return.camera_timestamp - last_mode_image_added_time >= 0.05) {
		// every 50 ms update a 1/16 of the whole mode... we use a 1/16 to better distribute computation time in between frames
				
		// determine which region of the mode we are in (use the index as a counter between 0 to 15)
		binx = (live_mode_frame_index % 16) / 4;
		biny = (live_mode_frame_index % 4);

		i0 = biny * picture_height / 4;
		i1 = i0 + picture_height / 4;

		j0 = binx * picture_width / 4;
		j1 = j0 + picture_width / 4;
		
		for (i = i0; i < i1; i++) {
			for (j = j0; j < j1; j++) {
				c = full_frame_buffer[i * picture_width + j];

				// in the 3d matrix add one to the pixel brightness count
				live_mode_counter[c *  picture_width * picture_height + i * picture_width + j] += 1;
				// values in that counter can only run up to 255!, 
				// so pay attention that this does not happen.. with live_mode_frame_index < 1200, where each region is analyzed every 1/16, this means, now the max val is less than 100

				if (live_mode_max_counter[i * picture_width + j] < live_mode_counter[c * picture_width * picture_height + i * picture_width + j]) {
					live_mode_max_counter[i * picture_width + j] = live_mode_counter[c * picture_width * picture_height + i * picture_width + j];
					live_mode[i * picture_width + j] = c;
				}
			}
		}

		live_mode_frame_index += 1;
		last_mode_image_added_time = _return.camera_timestamp;

		if (live_mode_frame_index == 1200) { /// should happen after circa 70 seconds!

			live_mode_number += 1;
			
			// Copy this to the mode structure which is used for background substraction
			memcpy(mode, live_mode, picture_width * picture_height * sizeof(unsigned char));
			
			// Transform it to an opencv image
			for (i = 0; i < picture_height; i++) {
				pixrow = mode_mat.ptr<uchar>(i);

				for (j = 0; j < picture_width; j++)
					pixrow[j] = mode[i * picture_width + j];
			}
			
			// Add the timestamp to the mode image
			cv::putText(mode_mat, "#" + std::to_string(live_mode_number) + ", " + std::to_string(_return.camera_timestamp) + "s", cv::Point(20, 30), cv::FONT_HERSHEY_SIMPLEX, 1, 255, 1, 8, false);

			// Add the mode image to the mode video
			if (mode_video.isOpened() == true) mode_video.write(mode_mat);

			// Also write this image as a jpeg file, so it can be displayed in the gui
			if (global_filename_modeimage.length() > 0) {
				cv::imwrite(global_filename_modeimage, mode_mat);
			}

			_return.mode_updated = true; // so that the gui knows it has to load the current mode jpeg file
		}
	}

	if (live_mode_number == -1) {

		roi_x0 = 0;
		roi_x1 = picture_width;
		roi_y0 = 0;
		roi_y1 = picture_height;
		any_error_during_bout = true;
		
		_return.errorcode = 8; // still calculating the mode

		return _return;
	}

	if (ignore_fish == true) { // for example when one wants to illustrate how many fish swim without implementing feedback
		
		return _return;
	}

	///////////////////////////////////////////////////
	/// Find the FISH!

	// just copy the region into the opencv frame, the ptr method is supposed to be more efficient than the at method
	// and at the same time substract the mode
	for (i = roi_y0; i < roi_y1; i++) {
		pixrow = frame.ptr<uchar>(i - roi_y0);

		for (j = roi_x0; j < roi_x1; j++)
			pixrow[j - roi_x0] = substract_background(full_frame_buffer[i * picture_width + j], mode[i * picture_width + j]);
	}

	cv::threshold(frame, thresholded, 15, 255, 0);
	cv::GaussianBlur(thresholded, blurred, Size(25, 25), 0);
	
	// find the darkest pixel (should be approximatelty the middle of the fish)
	cv::minMaxLoc(blurred, &min_value, &max_value, &min_loc, &max_loc);
	
	if (max_value < 20) { // fish too dim (or not found)

		roi_x0 = 0;
		roi_x1 = picture_width;
		roi_y0 = 0;
		roi_y1 = picture_height;
		any_error_during_bout = true;

		_return.errorcode = 1; // Blob not bright enough

		// add an empty frame to the fish movie
		add_fish_roi_to_movie(cv::Mat::zeros(100, 100, CV_8UC1), _return.camera_framenum, _return.errorcode);


		return _return;
	}
	
	picture_norm_factor = 255 / max_value; // Use the max_value to normalize the next step
	
	fish_position_x = max_loc.x + roi_x0;
	fish_position_y = max_loc.y + roi_y0;

	// if the fish is too close to the walls, its probably not a fish
	if (fish_position_x < 50 || fish_position_y < 50 || fish_position_x >= picture_width - 50 || fish_position_y >= picture_height - 50) {

		// also reset the roi
		roi_x0 = 0;
		roi_x1 = picture_width;
		roi_y0 = 0;
		roi_y1 = picture_height;
		any_error_during_bout = true;

		_return.errorcode = 2; // Fish blob too close to the wall
		
		// add an empty frame to the fish movie
		add_fish_roi_to_movie(cv::Mat::zeros(100, 100, CV_8UC1), _return.camera_framenum, _return.errorcode);

		return _return;
	}
	
	// just use an area of +- 50 around the fish of the original image for determining its head position and orientation
	for (i = 0; i < 100; i++) {
		pixrow = frame100.ptr<uchar>(i);

		for (j = 0; j < 100; j++) {
			pixrow[j] = static_cast<unsigned char>(picture_norm_factor * substract_background(full_frame_buffer[(fish_position_y + i - 50) * picture_width + fish_position_x + j - 50], mode[(fish_position_y + i - 50) * picture_width + fish_position_x + j - 50]));
		}
	}
	
	// find the fish orientation and refine its position, for this blow the picture up, and smooth it a bit, then threshold
	cv::resize(frame100, frame100_bigger, cv::Size(200, 200));
	cv::GaussianBlur(frame100_bigger, frame100_bigger, Size(5, 5), 0); // week smoothing
	
	cv::minMaxLoc(frame100_bigger, &min_value, &max_value, &min_loc, &max_loc);

	double thresh;
	bool found = false;

	vector<vector<Point> >fish_hull(1);

	// apply a variable threshold, start from 0.8*maxvalue and go slowly down
	for (thresh = 0.7; thresh > 0.2; thresh -= 0.05) {
		
		vector<vector<Point> > fish_contours;
		vector<Point> fish_contour_points;

		cv::threshold(frame100_bigger, thresholded100_bigger, thresh*max_value, 255, 0); // the threshold here defines how much of the fish will be used... low thresholds can lead to much to include the detailed tail shape, which leads to tracking artifacts

		// calculate the fraction of how many pixels are white now
		fish_area = (double)cv::sum(thresholded100_bigger)[0] / (200 * 200 * 255);

		if (fish_area > 0.2) {
			continue; // something went wrong, there are too many white dots
		}

		cv::Mat thresholded100_dummy = thresholded100_bigger.clone();

		// find all contours in the tresholded blown up image
		cv::findContours(thresholded100_dummy, fish_contours, CV_RETR_LIST, CV_CHAIN_APPROX_SIMPLE); // This crashes for images with a lot of noise!!! To be solved

		if (fish_contours.size() == 0 || fish_contours.size() > 7) {
			continue; // no or too many contours found, probaly some big dust particles, which we don't want!
		}

		// combine all contours which are large enough into one array of points
		// sort the contours, and add the three largest ones together
		std::sort(fish_contours.begin(), fish_contours.end(), compare_contour_areas);
		for (i = 0; i < 3 && i < fish_contours.size(); i++) {
			
			if (contourArea(fish_contours[i]) > 10) { // we dont want to pick up noise
				fish_contour_points.insert(fish_contour_points.end(), fish_contours[i].begin(), fish_contours[i].end());
			}
		}

		if (fish_contour_points.size() == 0) {
			continue; // no big enough contours found
		}

		// Calculate a convex hull around these points
		convexHull(cv::Mat(fish_contour_points), fish_hull[0]);

		fish_area = contourArea(fish_hull[0]);

		if (fish_area > 2500 || fish_area < 400) { // was 2000 for larval zebrafish, but changed it 2500 to track big Drosophila larvae (12/11/2017)
			continue; // the found hull is too big, or too small, so its probably not a fish

		}

		found = true;
		break; /// all is good
	}
	
	// set the fish area to the return vector
	_return.fish_area = fish_area;

	if (found == false) { 
		// also reset the roi
		roi_x0 = 0;
		roi_x1 = picture_width;
		roi_y0 = 0;
		roi_y1 = picture_height;
		any_error_during_bout = true;

		_return.errorcode = 3; /// threshold searh did not find properly sized contours

		// add the current frame100 to the fish movie, this might not be the fish
		add_fish_roi_to_movie(frame100, _return.camera_framenum, _return.errorcode);

		return _return;
	}
	
	// calculate the orientation of the convex hull with image moments
	Moments m;
	m = moments(fish_hull[0], false);
	
	// first order moments (represent the center off mass)
	double x_ = m.m10 / m.m00;
	double y_ = m.m01 / m.m00;
	
	// second order moments (represent the covariances for x, y, xy)
	double mu20 = m.mu20 / m.m00;
	double mu02 = m.mu02 / m.m00;
	double mu11 = m.mu11 / m.m00;
	
	// the eigenvectors of the covariance matrix represent to direction of largest and smalles variances, out of this one can calculate the angle of the fish (equation from wikipedia)
	double angle = 0.5*atan2(2 * mu11, mu20 - mu02);
	
	// This angle does not allow to determine whether the fish is oriented right, or left, so we rotate the fish by that angle and calculate the point of its largest width, which should be the eyes
	
	// OpenCV allows the creaton of a rotation matrix around the center of mass with the angle of the largest variance
	Mat rotMat = getRotationMatrix2D(Point2f(static_cast<float>(x_), static_cast<float>(y_)), angle * 180 / 3.141592653589793, 1);
	Mat rotMat_inv;
	
	// And the inverted rotation matrix
	invertAffineTransform(rotMat, rotMat_inv);
	
	// Draw the hull into an empty image
	Mat dummy_image_original = cv::Mat::zeros(200, 200, CV_32F);
	drawContours(dummy_image_original, fish_hull, 0, 1, CV_FILLED, 8); // the image will be only 1s and 0s

	// Rotate that image around its center of mass and with the angle found before
	Mat dummy_image_rotated = cv::Mat::zeros(200, 200, CV_32F);
	cv::warpAffine(dummy_image_original, dummy_image_rotated, rotMat, cv::Size(200, 200));

	// Sum all the columns of the rotated image, so we can determine the maximal wisdth of the fish
	Mat dummy_image_reduced = cv::Mat::zeros(1, 200, CV_32F); // 1 row 200 columns
	cv::reduce(dummy_image_rotated, dummy_image_reduced, 0, CV_REDUCE_SUM);

	// Determine where the maximal value is in that image (corresponds to the widtgh of the fish)
	cv::minMaxLoc(dummy_image_reduced, &min_value, &max_value, &min_loc, &max_loc);
	
	// The location of the maximum along the x-axis is the point of the head
	Point2f point_head(static_cast<float>(max_loc.x), static_cast<float>(y_)); // as the image was reduced, the y position is the center of mass of the non-reduced image, as we rotated around that point, that is the center of mass of the original image
	
	// for precision purposes, make a very long virtual tail
	Point2f point_dummy_tail;
	if (max_loc.x < x_)	point_dummy_tail = Point2f(+1000, static_cast<float>(y_));
	else point_dummy_tail = Point2f(-1000, static_cast<float>(y_));
	
	// Apply the inverse rotation matrix to that vector by hand (see warpAffine documetion how opencv arranges its rotation matrix, 3rd column if for the translation)
	Point2f point_head_rotatedback(static_cast<float>(point_head.x*rotMat_inv.at<double>(0, 0) + point_head.y*rotMat_inv.at<double>(0, 1) + rotMat_inv.at<double>(0, 2)), 
								   static_cast<float>(point_head.x*rotMat_inv.at<double>(1, 0) + point_head.y*rotMat_inv.at<double>(1, 1) + rotMat_inv.at<double>(1, 2)));

	Point2f point_dummy_tail_rotatedback(static_cast<float>(point_dummy_tail.x*rotMat_inv.at<double>(0, 0) + point_dummy_tail.y*rotMat_inv.at<double>(0, 1) + rotMat_inv.at<double>(0, 2)),
										 static_cast<float>(point_dummy_tail.x*rotMat_inv.at<double>(1, 0) + point_dummy_tail.y*rotMat_inv.at<double>(1, 1) + rotMat_inv.at<double>(1, 2)));

	// calculate the final angle fround the infinitale tail position and head position
	fish_orientation = atan2(-(point_head_rotatedback.y - point_dummy_tail_rotatedback.y), point_head_rotatedback.x - point_dummy_tail_rotatedback.x);


	////////////////////////////////////
	//// All information are now availble

	// Update the fish position
	fish_position_x = static_cast<int>(fish_position_x - 50 + point_head_rotatedback.x / 2); // devide by two because of the scaling from roi 100 to roi 200
	fish_position_y = static_cast<int>(fish_position_y - 50 + point_head_rotatedback.y / 2);
	
	if (fish_position_x < 50 || fish_position_y < 50 || fish_position_x >= picture_width - 50 || fish_position_y >= picture_height - 50) {

		// also reset the roi
		roi_x0 = 0;
		roi_x1 = picture_width;
		roi_y0 = 0;
		roi_y1 = picture_height;
		any_error_during_bout = true;
		
		_return.errorcode = 2; // Fish is too close to the wall
		
		add_fish_roi_to_movie(frame100, _return.camera_framenum, _return.errorcode);

		return _return;
	}
	
	// Update the roi position for the next round (search in a 200x200 window around the last fish head position)
	roi_x0 = fish_position_x - 100;
	roi_x1 = fish_position_x + 100;
	roi_y0 = fish_position_y - 100;
	roi_y1 = fish_position_y + 100;

	// the roi might now be too close to the walls, make it still 200x200
	if (roi_x0 < 0) {
		roi_x0 = 0;
		roi_x1 = 200;
	}

	if (roi_x1 >= picture_width) {
		roi_x1 = picture_width - 1;
		roi_x0 = picture_width - 1 - 200;
	}

	if (roi_y0 < 0) {
		roi_y0 = 0;
		roi_y1 = 200;
	}

	if (roi_y1 >= picture_height) {
		roi_y1 = picture_height - 1;
		roi_y0 = picture_height - 1 - 200;
	}

	// Update the fish roi to its final position
	for (i = 0; i < 100; i++) {

		pixrow = frame100.ptr<uchar>(i);

		for (j = 0; j < 100; j++) {
			
			fish_roi[i * 100 + j] = static_cast<unsigned char>(picture_norm_factor * substract_background(full_frame_buffer[(fish_position_y + i - 50) * picture_width + fish_position_x + j - 50], mode[(fish_position_y + i - 50) * picture_width + fish_position_x + j - 50]));
			
			pixrow[j] = fish_roi[i * 100 + j];

		}
	}

	// For debugging
	/*
	Scalar color = Scalar(0, 255, 255);
	Scalar color2 = Scalar(255, 0, 255);
	Scalar color3 = Scalar(0, 0, 255);

	cv::Mat test = cv::Mat::zeros(200, 200, CV_8UC3);
	drawContours(test, fish_hull, 0, color, CV_FILLED, 8);
	cv::circle(test, point_head_rotatedback, 3, color3, -1);
	
	cv::imshow("Convex hull", test);*/

	//cv::waitKey(1);
	
	// Scale the value between -1 and 1
	fish_position_x_scaled = 2 * ((double)fish_position_x) / picture_width - 1;
	fish_position_y_scaled = - (2 * ((double)fish_position_y) / picture_height - 1);
	fish_orientation = fish_orientation * 180 / 3.141592653589793; /// Make it degree


	/////////////////////////
	/// Live bout finder

	if (fish_accumulated_path == -1) { // the very first function call
		fish_accumulated_path = 0;
		fish_accumulated_orientation = fish_orientation;
				
		circular_counter = 0;

		circular_history_time[0] = timestamp_seconds;
		circular_history_fish_accumulated_orientation[0] = fish_accumulated_orientation;
		
		fish_accumulated_orientation_lowpass = fish_accumulated_orientation;
		inside_bout = false;
		variance_was_low = false;
		last_bout_timestamp_end = -1;

	} else {

		// determine the delta time between this return and the last one that was good
		delta_timestamp = _return.camera_timestamp - _last_good_return.camera_timestamp;

		// what is is the delta orientation
		fish_delta_orientation = fmod(fish_orientation - _last_good_return.fish_orientation + 180 + 360, 360) - 180;
		
		// is there some error (flipping)?
		// assuming the framerate is about 100 hz, maximal heading angle change during espaces can be up to 10000deg/s (Tim), but set the threshold for us here at 5000deg/s
		if (fabs(fish_delta_orientation / delta_timestamp) > 5000) {
			// also reset the roi
			roi_x0 = 0;
			roi_x1 = picture_width;
			roi_y0 = 0;
			roi_y1 = picture_height;
			any_error_during_bout = true;

			_return.errorcode = 4; // Fish is flipping

			add_fish_roi_to_movie(frame100, _return.camera_framenum, _return.errorcode);

			return _return;
		}
		
		fish_delta_position_x = fish_position_x_scaled - _last_good_return.fish_position_x;
		fish_delta_position_y = fish_position_y_scaled - _last_good_return.fish_position_y;

		fish_delta_path = sqrt(fish_delta_position_x*fish_delta_position_x + fish_delta_position_y*fish_delta_position_y);

		// is the fish jumping (because for example, some dust particle?
		// we assume that the maximal upper bound for a path change/s is one dish per second
		if (fish_delta_path / delta_timestamp > 2) {
			// also reset the roi
			roi_x0 = 0;
			roi_x1 = picture_width;
			roi_y0 = 0;
			roi_y1 = picture_height;
			any_error_during_bout = true;

			_return.errorcode = 5; // Fish is jumping

			add_fish_roi_to_movie(frame100, _return.camera_framenum, _return.errorcode);

			return _return;
		}

		fish_accumulated_path += fish_delta_path;
		fish_accumulated_orientation += fish_delta_orientation;

		// use the accumulated fish orientation for bout detection via analyzing the variance with a 100ms time bin
		circular_history_fish_accumulated_orientation[circular_counter] = fish_accumulated_orientation;
		circular_history_fish_accumulated_path[circular_counter] = fish_accumulated_path;

		circular_history_time[circular_counter] = timestamp_seconds;
		
		// apply a weak lowpass filter to the accumulated orientation
		alpha_lowpass = delta_timestamp / (0.05 + delta_timestamp);
		fish_accumulated_orientation_lowpass = alpha_lowpass*fish_accumulated_orientation + (1 - alpha_lowpass)*fish_accumulated_orientation_lowpass;
		
		// find how many indixes we have to go to the past for 50ms
		// find the indexes which mark the last 50ms (as time might be variable, search for the right index based on the timestamps
		bout_finder_t_now = circular_history_time[circular_counter];
		bout_finder_past_i = 0;
		
		/// TODO
		/// need to have the array filled before that loop, otherwise might run forever, check for that!

		while (true) {
			bout_finder_past_i++;
			
			bout_finder_t_past = circular_history_time[(circular_counter - bout_finder_past_i + 100) % 100];
			
			if (bout_finder_t_now - bout_finder_t_past >= 0.05) {
				break;
			}
		}

		// Calculate the mean
		bout_finder_mean_sum = 0;

		for (i = 0; i < bout_finder_past_i; i++) {

			bout_finder_i0 = (circular_counter - i + 100) % 100;
			bout_finder_mean_sum += circular_history_fish_accumulated_orientation[bout_finder_i0];
		}

		bout_finder_mean = bout_finder_mean_sum / bout_finder_past_i;

		// Calculate the variance
		bout_finder_variance = 0;
		for (i = 0; i < bout_finder_past_i; i++) {
			bout_finder_i0 = (circular_counter - i + 100) % 100;
			bout_finder_variance += pow(circular_history_fish_accumulated_orientation[bout_finder_i0] - bout_finder_mean, 2);
		}

		bout_finder_variance /= bout_finder_past_i;

		// Variance needs to be higher than a threshold, for the first time
		if (bout_finder_variance > 2 && inside_bout == false && variance_was_low == true) {
			inside_bout = true;
			variance_was_low = false; // whatever happens, the algorithm needs to find a variance smaller than 1 in order to find a new bout
			any_error_during_bout = false; /// keep track of poential errors, if any, this bout is not reliable and we'll ignore it

			bout_start_i = (circular_counter - bout_finder_past_i + 100) % 100;
		}

		if (bout_finder_variance < 1 && inside_bout == true) {
			inside_bout = false;
			
			// we ignore the whole thing, if any error happened
			if (any_error_during_bout == false) {

				bout_end_i = circular_counter;

				// was this really a bout? the starttime of the new bout should be at least 50ms away from the old bout (or first bout ever)
				if (circular_history_time[bout_start_i] - last_bout_timestamp_end > 0.05 || last_bout_timestamp_end == -1) {

					_return.bout_found = true;
					_return.bout_timestamp_start = circular_history_time[bout_start_i];
					_return.bout_timestamp_end = circular_history_time[bout_end_i];

					_return.bout_heading_angle_change = circular_history_fish_accumulated_orientation[bout_end_i] - circular_history_fish_accumulated_orientation[bout_start_i];
					_return.bout_distance_traveled_change = circular_history_fish_accumulated_path[bout_end_i] - circular_history_fish_accumulated_path[bout_start_i];

					last_bout_timestamp_end = circular_history_time[bout_end_i];
				}
			}
		}

		if (bout_finder_variance < 1) {
			variance_was_low = true;
		}
	}

	circular_counter++;
	if (circular_counter == 100) circular_counter = 0;

	_return.errorcode = 0; // Fish found, all good

	_return.fish_position_x = fish_position_x_scaled;
	_return.fish_position_y = fish_position_y_scaled;
	
	_return.fish_orientation = fish_orientation;
	_return.fish_accumulated_orientation = fish_accumulated_orientation;
	_return.fish_accumulated_orientation_lowpass = fish_accumulated_orientation_lowpass;
	_return.fish_accumulated_orientation_variance = bout_finder_variance;

	_return.fish_accumulated_path = fish_accumulated_path;
	
	_last_good_return = _return; // memorize this return structure, in case next round something goes wrong

	add_fish_roi_to_movie(frame100, _return.camera_framenum, _return.errorcode);

	return _return;
}