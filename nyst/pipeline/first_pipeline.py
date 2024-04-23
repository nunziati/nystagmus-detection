import cv2
import numpy as np

from nyst.roi import FirstRegionSelector, FirstEyeRoiDetector
from nyst.utils import FirstLatch
from nyst.pupil import ThresholdingPupilDetector
from nyst.analysis import FirstSpeedExtractor
from nyst.visualization import FirstFrameAnnotator

class FirstPipeline:
    def __init__(self):
        self.region_selector = FirstRegionSelector()
        self.eye_roi_detector = FirstEyeRoiDetector("yolov8")
        self.left_eye_roi_latch = FirstLatch()
        self.right_eye_roi_latch = FirstLatch()
        self.pupil_detector = ThresholdingPupilDetector()
        self.frame_annotator = FirstFrameAnnotator()
        self.speed_extractor = FirstSpeedExtractor()

    def apply(self, frame, update_roi=False):
        # Uptdating eyes ROI
        if update_roi:
            # Calculate the ROI of left and right eyes
            rois = self.eye_roi_detector.apply(frame) 
            # Unpack the ROIs and assign them individually to two separate variables
            left_eye_roi = rois.get_left_roi()
            right_eye_roi = rois.get_right_roi()

            # Save the ROIs to the latch variables in order to have two distinct pipeline blocks
            self.left_eye_roi_latch.set(left_eye_roi)
            self.right_eye_roi_latch.set(right_eye_roi)

        # Get distinct ROIs value and save them to two specific variables
        left_eye_roi = self.left_eye_roi_latch.get()
        right_eye_roi = self.right_eye_roi_latch.get()

        # Apply ROI to the selected frame and assign the result to specific variables
        left_eye_frame = self.region_selector.apply(frame, left_eye_roi)
        right_eye_frame = self.region_selector.apply(frame, right_eye_roi)

        # 
        left_pupil_relative_position = self.pupil_detector.apply(left_eye_frame)
        right_pupil_relative_position = self.pupil_detector.apply(right_eye_frame)

        left_pupil_absolute_position = self.region_selector.relative_to_absolute(left_pupil_relative_position, left_eye_roi)
        right_pupil_absolute_position = self.region_selector.relative_to_absolute(right_pupil_relative_position, right_eye_roi)

        return left_pupil_absolute_position, right_pupil_absolute_position

    def run(self, video_path):
        left_eye_absolute_positions = []
        right_eye_absolute_positions = []

        cap = cv2.VideoCapture(video_path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        resolution = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        resolution = (resolution[1], resolution[0])

        annotated_video_writer = cv2.VideoWriter("annotated_video.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, resolution)

        ret, frame = cap.read()
        if ret is False:
            raise RuntimeError("Error reading video")

        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        left_pupil_absolute_position, right_pupil_absolute_position = self.apply(frame, update_roi=True)

        left_eye_absolute_positions.append(left_pupil_absolute_position)
        right_eye_absolute_positions.append(right_pupil_absolute_position)
        
        annotated_frame = self.frame_annotator.apply(frame, left_pupil_absolute_position, right_pupil_absolute_position)

        cv2.imshow("frame", annotated_frame)
        cv2.waitKey(30)
        annotated_video_writer.write(annotated_frame)

        while True:
            ret, frame = cap.read()
            if ret is False:
                break

            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            left_pupil_absolute_position, right_pupil_absolute_position = self.apply(frame)

            left_eye_absolute_positions.append(left_pupil_absolute_position)
            right_eye_absolute_positions.append(right_pupil_absolute_position)

            annotated_frame = self.frame_annotator.apply(frame, left_pupil_absolute_position, right_pupil_absolute_position)

            cv2.imshow("frame", annotated_frame)
            cv2.waitKey(30)

            annotated_video_writer.write(annotated_frame)
        
        cv2.destroyAllWindows()
        cap.release()
        annotated_video_writer.release()

        left_eye_absolute_positions = np.array(left_eye_absolute_positions, dtype=np.float32)
        right_eye_absolute_positions = np.array(right_eye_absolute_positions, dtype=np.float32)

        left_eye_speed_dict = self.speed_extractor.apply(left_eye_absolute_positions, fps)
        right_eye_speed_dict = self.speed_extractor.apply(right_eye_absolute_positions, fps)


        speed_dict = {
            resolution: {"left": left_eye_speed_dict[resolution], "right": right_eye_speed_dict[resolution]}
            for resolution in left_eye_speed_dict
            }

        output_dict = {
            "position": {
                "left": left_eye_absolute_positions,
                "right": right_eye_absolute_positions
            },
            "speed": speed_dict
        }

        return output_dict