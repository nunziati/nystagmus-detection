import os
import torch
from torch.utils.data import Dataset
import numpy as np
import pandas as pd

class CustomDataset(Dataset):
    """
    Expected npy format:
    {
        'signals': np.array['left_position X', 'left_position Y', 
                    'right_position X', 'right_position Y', 'left_speed X', 'left_speed Y', 
                    'right_speed X', 'right_speed Y']
        'resolutions': 'val_resolution'
        'patients': np.array: patient folder number, 
        'samples': np.array: patient video, clip and number of valid resolutions for this clip # (n_samples, n_clip, valid_resolution)
        'labels': np.array, # (len(samples)*len(val_resolution), 1)
    }
    """

    def __init__(self, csv_input_file, csv_label_file, preprocess=None, transform=None):
        # Load the CSV file
        self.input_data = pd.read_csv(csv_input_file)
        self.label_data = pd.read_csv(csv_label_file)

        # Perform the join on the 'video' column
        self.merged_data = pd.merge(self.input_data, self.label_data, on='video', how='left')
        print(self.merged_data.head(6))

        # Applica la funzione di preprocessing se fornita
        if preprocess:
            self.data = preprocess(self.merged_data)
        else:
            self.data = self.merged_data

        # Exctraction data
        self.data = self.exctraction_values(self.data)

        # Extract the different components of the dataset
        self.signals = self.data['signals']
        self.resolutions = self.data['resolutions']
        self.patients = self.data['patients']
        self.samples = self.data['samples']
        self.labels = self.data['labels']

        # Store the transformation function (if any)
        self.transform = transform

    # Return the number of samples in the dataset
    def __len__(self):
        return len(self.samples)

    # Return the signal and label
    def __getitem__(self, idx):
        # Convert tensor index to list if necessary
        if torch.is_tensor(idx):
            idx = idx.tolist()

        # Retrieve the sample and its corresponding label
        signal = self.signals[idx]
        label = self.labels[idx]

        # Apply the transformation to the sample if provided
        if self.transform:
            sample = self.transform(sample)

        return signal, label

    def exctraction_values(self, merged_data):
            """
            Preprocessing di default dei dati uniti. Qui viene implementata la logica di base
            per estrarre i segnali, le risoluzioni, i pazienti, i campioni e le etichette.
            """
            # Estrai i segnali
            signals = merged_data[['left_position X', 'left_position Y', 
                                    'right_position X', 'right_position Y',
                                    'left_speed X', 'left_speed Y', 
                                    'right_speed X', 'right_speed Y']].to_numpy()

            # Estrai le risoluzioni
            resolutions = merged_data['resolution'].to_numpy().reshape(-1, 1)

            # Estrai le informazioni sui pazienti (questo può dipendere dai tuoi dati)
            patients = merged_data['video'].apply(lambda x: x.split('\\')[-1].split('_')[0]) .to_numpy().reshape(-1, 1)


            # Estrarre campioni e informazioni sui video
            samples = merged_data.apply(
                lambda x: [
                    x['video'].split('\\')[-1].split('_')[0],
                    x['video'].split('_')[1],  # '001', '002', '001'
                    x['video'].split('_')[2].split('.')[0],  # '001', '001', '002'
                    x['resolution']  # 1 se la risoluzione è valida
                ], 
                axis=1
            ).to_numpy()

            # Estrai le etichette
            labels = merged_data['label'].to_numpy().reshape(-1, 1)

            return {
                'signals': signals,
                'resolutions': resolutions,
                'patients': patients,
                'samples': samples,
                'labels': labels
            }
 

def split_data(dictionary_input, perc_test):
    # Extract unique patients
    patients = dictionary_input['patients'].flatten()
    unique_patients = np.unique(patients)

    # Shuffle the patients to ensure randomness
    np.random.shuffle(unique_patients)
    
    # Initialize test and training sets
    test_patients = []
    current_test_size = 0
    total_size = len(patients)
    
    # Distribute patients into test set until the percentage is approximately met
    for patient in unique_patients:
        if current_test_size / total_size < perc_test:
            test_patients.append(patient)
            # Update the current test size
            patient_mask = patients == patient
            current_test_size += np.sum(patient_mask)
        else:
            break

    # The remaining patients are for training
    train_patients = [patient for patient in unique_patients if patient not in test_patients]
    
    # Function to filter data based on patients
    def filter_data_by_patients(data, selected_patients):
        # Create a boolean mask indicating which patients are in the specific set
        mask = np.isin(data['patients'], selected_patients)
        # Data filtered by patients
        filtered_data = {key: value[mask.flatten()] for key, value in data.items()}
        return filtered_data
    
    # Filter the data into train and test sets based on the selected patients
    test_data = filter_data_by_patients(dictionary_input, test_patients)
    train_data = filter_data_by_patients(dictionary_input, train_patients)
    
    # Shuffle the clips within each set to randomize order
    def shuffle_data(data):
        # Shuffle the order of the clips
        indices = np.random.permutation(data['samples'].shape[0])
        # Shuffle data
        shuffled_data = {key: value[indices] for key, value in data.items()}
        return shuffled_data
    
    # Shuffled data
    train_data = shuffle_data(train_data)
    test_data = shuffle_data(test_data)
    
    return train_data, test_data

if __name__ == '__main__':
    # Replace with the actual paths to your CSV files
    csv_input_file = 'D:/nyst_labelled_videos/video_features.csv'
    csv_label_file = 'D:/nyst_labelled_videos/labels.csv'

    # Create an instance of the CustomDataset to trigger the print
    dataset = CustomDataset(csv_input_file, csv_label_file)
    train_data, test_data = split_data(dataset.data, perc_test=0.1)

    print('Train data:', train_data['patients'])
    print('Test data:', test_data['patients'])