import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import csv

class ThresholdingPupilDetector:
    '''
    Class that detects the pupil or iris in a given ROI frame using thresholding.

    Attributes:
    - threshold: The threshold value used for binary thresholding of the image.
    '''
    def __init__(self, threshold):
        self.save_threshold_interval_counts = {"left_pupil+iris":0,"left_pupil":0,"left_pupil_list":[],"left_iris_list":[],"right_pupil+iris":0,"right_pupil":0,"right_pupil_list":[],"right_iris_list":[]}
        self.threshold = threshold
        
    
    
    def apply(self, frame, mask, count, label, eyes_pos):
        '''
        Detects the pupil or iris in the given frame using thresholding and contour analysis.

        Arguments:
        - frame: The input image frame in which the pupil/iris is to be detected.

        Returns:
        - A numpy array containing the coordinates of the center of the detected pupil/iris, 
          or (None, None) if no contours are found.
        '''
        #cv2.imshow('Image', frame)


        # Calculate the mean of the iris and pupil regions
        pupil_pixels = mask == label["pupil"]
        iris_pixels = mask == label["iris"]

        # Merge the masks
        merged_mask = (pupil_pixels | iris_pixels).astype(np.uint8)

        #cv2.imshow(f'Image {eyes_pos}', merged_mask*255)

        # Find the contours of the pupil/iris mask
        contours, _ = cv2.findContours(merged_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Display the original image with contours
        frame_with_contours = frame.copy()
        cv2.drawContours(frame_with_contours, contours, -1, (0, 255, 0), 2)
        #cv2.imshow('Contours', frame_with_contours)


        # Control the number of contours found
        if len(contours) == 0:
            return (None, None)
        
        # Sort the contours in descending order of their area
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True) # Sort in descending order of the list of contours by their area
        cv2.drawContours(frame, [contours[0]], -1, (0, 255, 0), 2)
        #cv2.imshow('Largest Contour', frame)

        # Find the contour with the biggest area
        largest_contour = contours[0]

        # Check that the contour has enough points to fit an ellipse (at least 5)
        if len(largest_contour) >= 5:
            # Fit an ellipse to the largest contour
            ellipse = cv2.fitEllipse(largest_contour)
            
            # Validate ellipse dimensions
            (center, axes, angle) = ellipse
            (major_axis, minor_axis) = axes
            
            if major_axis > 0 and minor_axis > 0:
                # Draw the ellipse on the original frame
                cv2.ellipse(frame_with_contours, ellipse, (255, 0, 0), 2)
                
                # The center of the ellipse is the center of the pupil/iris
                center = np.array([int(center[0]), int(center[1])], dtype=np.int32)
            else:
                center = (None, None)  # Invalid ellipse dimensions

        else:
            center = (None, None) # Invalid ellipse dimensions

        cv2.waitKey(1)

        return center  # Return the center of the pupil/iris                   
    
    def apply_3(self, frame, count):
        '''
        Detects the pupil or iris in the given frame using thresholding and contour analysis.

        Arguments:
        - frame: The input image frame in which the pupil/iris is to be detected.

        Returns:
        - A numpy array containing the coordinates of the center of the detected pupil/iris, 
          or (None, None) if no contours are found.
        '''
        #cv2.imshow('Image', frame)

        # Transform the frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #cv2.imshow('Image gray', gray_frame)
        
        # Take a copy of the frame
        gray_frame_copy = gray_frame.copy()

        # Increase frame contrast
        alpha = 2.2  # Contrast factor
        beta = 0.     # Lightness factor
        high_contrast_gray = cv2.convertScaleAbs(gray_frame_copy, alpha=alpha, beta=beta)
        #cv2.imshow('High Contrast Gray', high_contrast_gray)

          
        # Calculate the median between distinct gray levels excluding white to set a correct threshold
        non_white_pixels = high_contrast_gray[high_contrast_gray < 255] # All pixel with gray levels different from white
        unique_gray_levels = np.unique(non_white_pixels) # Gray levels excluding white
        median_value = np.median(unique_gray_levels) if len(unique_gray_levels) > 0 else 50 # Median

        # Median percentage variation
        perc_var = 0.10

        # Add a small value to the median value to correctly estimate a threshold
        threshold_value = median_value - (perc_var*median_value)

        # Apply a Gaussian blur to the grayscale frame
        blurred_roi = cv2.GaussianBlur(high_contrast_gray, (7, 7), 0) # 7x7: dimension of the kernel, 0: "0" indicates that the standard deviation will be automatically calculated based on the size of the kernel

        # Return the pupil/iris mask
        _, threshold = cv2.threshold(blurred_roi, threshold_value, 255, cv2.THRESH_BINARY_INV)
        #cv2.imshow('Threshold Image', threshold)

        # Find the contours of the pupil/iris mask
        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Display the original image with contours
        frame_with_contours = frame.copy()
        cv2.drawContours(frame_with_contours, contours, -1, (0, 255, 0), 2)
        #cv2.imshow('Contours', frame_with_contours)


        # Control the number of contours found
        if len(contours) == 0:
            return (None, None)
        
        # Sort the contours in descending order of their area
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True) # Sort in descending order of the list of contours by their area
        cv2.drawContours(frame, [contours[0]], -1, (0, 255, 0), 2)
        #cv2.imshow('Largest Contour', frame)

        # Find the contour with the biggest area
        largest_contour = contours[0]

        # Check that the contour has enough points to fit an ellipse (at least 5)
        if len(largest_contour) >= 5:
            # Fit an ellipse to the largest contour
            ellipse = cv2.fitEllipse(largest_contour)
            
            # Validate ellipse dimensions
            (center, axes, angle) = ellipse
            (major_axis, minor_axis) = axes
            
            if major_axis > 0 and minor_axis > 0:
                # Draw the ellipse on the original frame
                cv2.ellipse(frame_with_contours, ellipse, (255, 0, 0), 2)
                
                # The center of the ellipse is the center of the pupil/iris
                center = np.array([int(center[0]), int(center[1])], dtype=np.int32)
            else:
                center = (None, None)  # Invalid ellipse dimensions

        else:
            center = (None, None) # Invalid ellipse dimensions

        cv2.waitKey(1)

        return center  # Return the center of the pupil/iris
    
    def apply_2(self, frame, count):
        '''
        Detects the pupil or iris in the given frame using thresholding and contour analysis.

        Arguments:
        - frame: The input image frame in which the pupil/iris is to be detected.
        - count: The counter indicating the number of frame.

        Returns:
        - A numpy array containing the coordinates of the center of the detected pupil/iris, 
          or (None, None) if no contours are found.
        '''
        #cv2.imshow('Image', frame)

        # Transform the frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #cv2.imshow('Image gray', gray_frame)
        
        # Take a copy of the frame
        gray_frame_copy = gray_frame.copy()

        # Increase frame contrast
        alpha = 2.2  # Contrast factor
        beta = 0.     # Lightness factor
        high_contrast_gray = cv2.convertScaleAbs(gray_frame_copy, alpha=alpha, beta=beta)
        #cv2.imshow('High Contrast Gray', high_contrast_gray)
              
        # Creating the mask to exclude white pixels
        non_white_pixels = high_contrast_gray[high_contrast_gray < 255]

        # Calculate the histogram of non-white pixels
        histogram, _ = np.histogram(non_white_pixels, bins=256, range=(0, 255))

        # Calculate the percentile of nonwhite pixels
        cumulative_histogram = np.cumsum(histogram)
        total_non_white_pixels = cumulative_histogram[-1]

        # Calculate the predominant and average intensity based on the histogram
        max_intensity_idx = np.argmax(histogram) 
        dominant_intensity = max_intensity_idx
        mean_intensity = np.mean(non_white_pixels)

        # Reset the counter of the threshold bands
        if count == 0:
            self.save_threshold_interval_counts = {"dominant>=125_mean>=100":0,"dominant>=125_mean>=75":0,"dominant>=125_mean>=50":0,"dominant>=125_mean>=0":0,"dominant>=125_mean>=100":0,"dominant>=100_mean>=100":0,"dominant>=100_mean>=75":0,
                                               "dominant>=100_mean>=50":0,"dominant>=100_mean>=0":0,"dominant>=75_mean>=100":0, "dominant>=75_mean>=75":0,"dominant>=75_mean>=50":0,
                                               "dominant>=75_mean>=0":0,"dominant>=50_mean>=100":0,"dominant>=50_mean>=75":0,"dominant>=50_mean>=50":0,
                                               "dominant>=50_mean>=0":0,"dominant>=0_mean>=100":0,"dominant>=0_mean>=75":0,"dominant>=0_mean>=50":0,
                                               "dominant>=0_mean>=0}":0}


        # Calculation of val based on dominant and average intensity
        if dominant_intensity >= 150 and mean_intensity >= 125:
            unique_gray_levels = np.unique(non_white_pixels)  # Unique gray levels, excluding whites.
            median_value = np.median(unique_gray_levels) if len(unique_gray_levels) > 0 else 50  # Median
            print(f"\nMedian: {median_value}")
            print('dominant_intensity: ',dominant_intensity)
            print('mean_intensity: ', mean_intensity)
            val = 0.08
            self.save_threshold_interval_counts["dominant>=125_mean>=100"] += 1
        else:
            unique_gray_levels = np.unique(non_white_pixels)  # Unique gray levels, excluding whites.
            median_value = np.median(unique_gray_levels) if len(unique_gray_levels) > 0 else 50  # Median
            print(f"\nMedian: {median_value}")
            print('dominant_intensity: ',dominant_intensity)
            print('mean_intensity: ', mean_intensity)
            if dominant_intensity >= 125 and mean_intensity >= 100:
                perc_var = 0.7
                self.save_threshold_interval_counts["dominant>=125_mean>=100"] += 1
            elif dominant_intensity >= 125 and mean_intensity >= 75:
                perc_var = 0.65
                self.save_threshold_interval_counts["dominant>=125_mean>=75"] += 1
            elif dominant_intensity >= 125 and mean_intensity >= 50:
                perc_var = 0.45
                self.save_threshold_interval_counts["dominant>=125_mean>=50"] += 1
            elif dominant_intensity >= 125 and mean_intensity >= 0:
                perc_var = 0.35
                self.save_threshold_interval_counts["dominant>=125_mean>=0"] += 1
            elif dominant_intensity >= 100 and mean_intensity >= 100:
                perc_var = 0.7
                self.save_threshold_interval_counts["dominant>=100_mean>=100"] += 1
            elif dominant_intensity >= 100 and mean_intensity >= 75:
                perc_var = 0.5
                self.save_threshold_interval_counts["dominant>=100_mean>=75"] += 1
            elif dominant_intensity >= 100 and mean_intensity >= 50:
                perc_var = 0.4
                self.save_threshold_interval_counts["dominant>=100_mean>=50"] += 1
            elif dominant_intensity >= 100 and mean_intensity >= 0:
                perc_var = 0.1
                self.save_threshold_interval_counts["dominant>=100_mean>=0"] += 1
            elif dominant_intensity >= 75 and mean_intensity >= 100:
                perc_var = 0.2
                self.save_threshold_interval_counts["dominant>=75_mean>=100"] += 1
            elif dominant_intensity >= 75 and mean_intensity >= 75:
                perc_var = -0.05
                self.save_threshold_interval_counts["dominant>=75_mean>=75"] += 1
            elif dominant_intensity >= 75 and mean_intensity >= 50:
                perc_var = -0.1
                self.save_threshold_interval_counts["dominant>=75_mean>=50"] += 1
            elif dominant_intensity >= 75 and mean_intensity >= 0:
                perc_var = -0.2
                self.save_threshold_interval_counts["dominant>=75_mean>=0"] += 1
            elif dominant_intensity >= 50 and mean_intensity >= 100:
                perc_var = -0.45
                self.save_threshold_interval_counts["dominant>=50_mean>=100"] += 1
            elif dominant_intensity >= 50 and mean_intensity >= 75:
                perc_var = -0.55
                self.save_threshold_interval_counts["dominant>=50_mean>=75"] += 1
            elif dominant_intensity >= 50 and mean_intensity >= 50:
                perc_var = -0.65
                self.save_threshold_interval_counts["dominant>=50_mean>=50"] += 1
            elif dominant_intensity >= 50 and mean_intensity >= 0:
                perc_var = -0.85
                self.save_threshold_interval_counts["dominant>=50_mean>=0"] += 1
            elif dominant_intensity >= 0 and mean_intensity >= 100:
                perc_var = -0.45
                self.save_threshold_interval_counts["dominant>=0_mean>=100"] += 1
            elif dominant_intensity >= 0 and mean_intensity >= 75:
                perc_var = -0.65
                self.save_threshold_interval_counts["dominant>=0_mean>=75"] += 1
            elif dominant_intensity >= 0 and mean_intensity >= 50:
                perc_var = -0.85
                self.save_threshold_interval_counts["dominant>=0_mean>=50"] += 1
            elif dominant_intensity >= 0 and mean_intensity >= 0:
                perc_var = -0.95
                self.save_threshold_interval_counts["dominant>=0_mean>=0"] += 1
            
            # Dynamic calculation of val
            val = (dominant_intensity - perc_var * median_value) / 255.0  # Normalizzazione
        
        # Check of the correctness of the value
        if not (0 <= val <= 1):
            raise ValueError(f"Valore fuori range: {val}")
        print('VAL: ',val)
        
        # Total number of pixels in the selected range
        percentile_val = val * total_non_white_pixels

        # Find the index in the cumulative histogram that is less than or equal to the desired percentile
        threshold_value = np.argmax(cumulative_histogram >= percentile_val)

        '''# Plot dell'istogramma 
        plt.figure() 
        plt.title("Istogramma dei Pixel Non Bianchi") 
        plt.xlabel("Intensità di Grigio") 
        plt.ylabel("Frequenza") 
        plt.plot(histogram) 
        # Aggiungi una linea verticale per indicare il punto in cui si raggiunge il val% dei pixel 
        plt.axvline(threshold_value, color='r', linestyle='dashed', linewidth=2, label=f'{val*100}% ({threshold_value})') 
        plt.legend() 
        # Salva il plot come immagine 
        plot_path = os.path.join("D:/nyst_labelled_videos/Plot", f"frame_{count:04d}.png") 
        plt.savefig(plot_path) 
        plt.close()'''

        # Apply Gaussian blurring
        blurred_roi = cv2.GaussianBlur(high_contrast_gray, (7, 7), 0)

        # Apply the threshold found
        _, threshold = cv2.threshold(blurred_roi, threshold_value, 255, cv2.THRESH_BINARY_INV)

        '''# Aumentare il contrasto
        #equalized_gray_frame = cv2.equalizeHist(gray_frame_copy)

        # Calcolare la media dei pixel diversi dal bianco
        non_white_pixels = high_contrast_gray[high_contrast_gray < 255]
        #mean_value = np.mean(non_white_pixels) if len(non_white_pixels) > 0 else 50'''
        
        '''# Calculate the median between distinct gray levels excluding white to set a correct threshold
        non_white_pixels = high_contrast_gray[high_contrast_gray < 255] # All pixel with gray levels different from white
        unique_gray_levels = np.unique(non_white_pixels) # Gray levels excluding white
        median_value = np.median(unique_gray_levels) if len(unique_gray_levels) > 0 else 50 # Median

        # Median percentage variation
        perc_var = 0.45

        # Add a small value to the median value to correctly estimate a threshold
        threshold_value = int(median_value - (perc_var*median_value))
        
        # Apply a Gaussian blur to the grayscale frame
        blurred_roi = cv2.GaussianBlur(high_contrast_gray, (7, 7), 0) # 7x7: dimension of the kernel, 0: "0" indicates that the standard deviation will be automatically calculated based on the size of the kernel

        # Return the pupil/iris mask
        _, threshold = cv2.threshold(blurred_roi, threshold_value, 255, cv2.THRESH_BINARY_INV)'''

        '''# Visualizzazione della soglia
        cv2.imshow('Threshold Image', threshold)
        cv2.waitKey(1)'''

        # Find the contours of the pupil/iris mask
        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Display the original image with contours
        frame_with_contours = frame.copy()
        cv2.drawContours(frame_with_contours, contours, -1, (0, 255, 0), 2)
        #cv2.imshow('Contours', frame_with_contours)


        # Control the number of contours found
        if len(contours) == 0:
            return (None, None)
        
        # Sort the contours in descending order of their area
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True) # Sort in descending order of the list of contours by their area
        cv2.drawContours(frame, [contours[0]], -1, (0, 255, 0), 2)
        #cv2.imshow('Largest Contour', frame)

        # Find the contour with the biggest area
        largest_contour = contours[0]

        # Check that the contour has enough points to fit an ellipse (at least 5)
        if len(largest_contour) >= 5:
            # Fit an ellipse to the largest contour
            ellipse = cv2.fitEllipse(largest_contour)
            
            # Validate ellipse dimensions
            (center, axes, angle) = ellipse
            (major_axis, minor_axis) = axes
            
            if major_axis > 0 and minor_axis > 0:
                # Draw the ellipse on the original frame
                cv2.ellipse(frame_with_contours, ellipse, (255, 0, 0), 2)
                
                # The center of the ellipse is the center of the pupil/iris
                center = np.array([int(center[0]), int(center[1])], dtype=np.int32)
            else:
                center = (None, None)  # Invalid ellipse dimensions

        else:
            center = (None, None) # Invalid ellipse dimensions
        
        return center  # Return the center of the pupil/iris
    
    def apply_4(self, frame, mask, count, label, eyes_pos):
            '''
            Detects the pupil or iris in the given frame using thresholding and contour analysis.

            Arguments:
            - frame: The input image frame in which the pupil/iris is to be detected.

            Returns:
            - A numpy array containing the coordinates of the center of the detected pupil/iris, 
            or (None, None) if no contours are found.
            '''
            #cv2.imshow('Image', frame)

            # Transform the frame to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            

            #cv2.imshow('Image gray', gray_frame)
            
            # Take a copy of the frame
            gray_frame_copy = gray_frame.copy()

            
            # Calculate the mean of the iris and pupil regions
            pupil_pixels = gray_frame[mask == label["pupil"]]
            iris_pixels = gray_frame[mask == label["iris"]]
            pupil_mean_intensity = np.mean(pupil_pixels)
            iris_mean_intensity = np.mean(iris_pixels)
            
            # Reset the counter of the threshold bands
            if count == 0:
                self.save_threshold_interval_counts = {"left_pupil+iris":0,"left_pupil":0,"left_pupil_list":[],"left_iris_list":[],"right_pupil+iris":0,"right_pupil":0,"right_pupil_list":[],"right_iris_list":[]}

            # Calculate the correct threshold based on the means differences  between this two regions 
            min_pupil_distinction_threshold_extr = 35 #35 
            iris_intensity_ratio_extr = 0.7
            

            # Track the mean valyue of the left/right pupil/iris intensity 
            if eyes_pos == "l":
                self.save_threshold_interval_counts["left_pupil_list"].append(pupil_mean_intensity)
                self.save_threshold_interval_counts["left_iris_list"].append(iris_mean_intensity)
            else:
                self.save_threshold_interval_counts["right_pupil_list"].append(pupil_mean_intensity)
                self.save_threshold_interval_counts["right_iris_list"].append(iris_mean_intensity)
    
            if (iris_mean_intensity - pupil_mean_intensity) > max(min_pupil_distinction_threshold_extr, iris_intensity_ratio_extr * iris_mean_intensity):
                # Use only pupil
                threshold_value = np.percentile(np.concatenate((pupil_pixels, iris_pixels)), 95)
                print(f"PUPIL     {threshold_value} ")
                # For the info file 
                if eyes_pos == "l":
                    self.save_threshold_interval_counts["left_pupil"] += 1
                else:
                    self.save_threshold_interval_counts["right_pupil"] += 1
            else:
                # Use both pupil and iris
                threshold_value = np.percentile(np.concatenate((pupil_pixels, iris_pixels)), 95)
                print(f"PUPIL + IRIS     {threshold_value} ")
                # For the info file 
                if eyes_pos == "l":
                    self.save_threshold_interval_counts["left_pupil+iris"] += 1
                else:
                    self.save_threshold_interval_counts["right_pupil+iris"] += 1

            
            # Apply a Gaussian blur to the grayscale frame
            blurred_roi = cv2.GaussianBlur(gray_frame_copy, (7, 7), 0) # 7x7: dimension of the kernel, 0: "0" indicates that the standard deviation will be automatically calculated based on the size of the kernel

            # Return the pupil/iris mask
            _, threshold = cv2.threshold(blurred_roi, threshold_value, 255, cv2.THRESH_BINARY_INV)
            #cv2.imshow('Threshold Image', threshold)

            # Find the contours of the pupil/iris mask
            contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Display the original image with contours
            frame_with_contours = frame.copy()
            cv2.drawContours(frame_with_contours, contours, -1, (0, 255, 0), 2)
            #cv2.imshow('Contours', frame_with_contours)


            # Control the number of contours found
            if len(contours) == 0:
                return (None, None)
            
            # Sort the contours in descending order of their area
            contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True) # Sort in descending order of the list of contours by their area
            cv2.drawContours(frame, [contours[0]], -1, (0, 255, 0), 2)
            #cv2.imshow('Largest Contour', frame)

            # Find the contour with the biggest area
            largest_contour = contours[0]

            # Check that the contour has enough points to fit an ellipse (at least 5)
            if len(largest_contour) >= 5:
                # Fit an ellipse to the largest contour
                ellipse = cv2.fitEllipse(largest_contour)
                
                # Validate ellipse dimensions
                (center, axes, angle) = ellipse
                (major_axis, minor_axis) = axes
                
                if major_axis > 0 and minor_axis > 0:
                    # Draw the ellipse on the original frame
                    cv2.ellipse(frame_with_contours, ellipse, (255, 0, 0), 2)
                    
                    # The center of the ellipse is the center of the pupil/iris
                    center = np.array([int(center[0]), int(center[1])], dtype=np.int32)
                else:
                    center = (None, None)  # Invalid ellipse dimensions

            else:
                center = (None, None) # Invalid ellipse dimensions

            cv2.waitKey(1)

            return center  # Return the center of the pupil/iris 

    # Salva i risultati del PupilDetector in un file CSV
    def save_threshold_counts(self, output_file, video_name):
        '''
        Save the counts of each threshold to a CSV file.

        Arguments:
        - output_file: The file path where to save the threshold counts.
        - video_name: The name of the video being processed (for labeling the results).
        '''
        # Verifica se il file esiste per decidere se scrivere l'intestazione
        write_header = False
        try:
            with open(output_file, "r") as f:
                pass
        except FileNotFoundError:
            write_header = True

        # Scrittura in modalità append
        with open(output_file, "a", newline="") as f:
            writer = csv.writer(f)
            
            # Scrivi l'intestazione solo se il file è nuovo
            if write_header:
                writer.writerow(["Video", "Threshold", "Count"])
            
            # Scrivi i dati per ogni threshold
            for threshold, count in self.save_threshold_interval_counts.items():
                writer.writerow([video_name, threshold, count])

        print(f"Saved threshold counts to {output_file}.")

    
    def relative_to_absolute(self, relative_position:np.array, roi):
        '''
        Converts the relative coordinates of a position within a region of interest (ROI) 
        to absolute coordinates in the original image.

        Arguments:
        - relative_position: An array (x, y) coordinates of the positions.
        - roi: (x, y) coordinates of the top-left corner of the ROI 
            in the original image.

        Returns:
        - A tuple containing the absolute (x, y) coordinates of the position in the original image.
        If either coordinate in relative_position is None, returns (None, None).
        '''
        # If the relative position coordinates are None, return None for both coordinates
        if relative_position[0] is None or relative_position[1] is None:
            return None,None
        # Convert relative position to absolute position based on the ROI
        return int(roi[0] + relative_position[0]), int(roi[1] + relative_position[1])