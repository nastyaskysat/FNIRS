import numpy as np
from scipy import signal


def calculate_hb_concentrations(intensity_780, intensity_850):
    if len(intensity_780) == 0 or len(intensity_850) == 0:
        return np.array([]), np.array([]), np.array([]), np.array([])
    
    from config import ANALYSIS_CONFIG
    
    epsilon_Hb_780 = ANALYSIS_CONFIG['epsilon_hb_780']
    epsilon_HbO2_780 = ANALYSIS_CONFIG['epsilon_hbo2_780']
    epsilon_Hb_850 = ANALYSIS_CONFIG['epsilon_hb_850']
    epsilon_HbO2_850 = ANALYSIS_CONFIG['epsilon_hbo2_850']
    
    distance = ANALYSIS_CONFIG['source_detector_distance']
    dpf = ANALYSIS_CONFIG['differential_pathlength_factor']
    
    intensity_780_arr = np.array(intensity_780)
    intensity_850_arr = np.array(intensity_850)
    
    intensity_780_arr = np.maximum(intensity_780_arr, 0.001)
    intensity_850_arr = np.maximum(intensity_850_arr, 0.001)
    
    window_size = min(20, len(intensity_780_arr) // 10)
    if window_size > 1:
        baseline_780 = np.mean(intensity_780_arr[:window_size])
        baseline_850 = np.mean(intensity_850_arr[:window_size])
    else:
        baseline_780 = intensity_780_arr[0]
        baseline_850 = intensity_850_arr[0]
    
    with np.errstate(divide='ignore', invalid='ignore'):
        delta_OD_780 = -np.log(intensity_780_arr / baseline_780)
        delta_OD_850 = -np.log(intensity_850_arr / baseline_850)
        
        OD_780 = delta_OD_780 / (distance * dpf)
        OD_850 = delta_OD_850 / (distance * dpf)
    
    OD_780 = np.nan_to_num(OD_780, nan=0, posinf=0, neginf=0)
    OD_850 = np.nan_to_num(OD_850, nan=0, posinf=0, neginf=0)
    
    OD_780 = np.clip(OD_780, -0.1, 0.1)
    OD_850 = np.clip(OD_850, -0.1, 0.1)
    
    epsilon_matrix = np.array([
        [epsilon_Hb_780, epsilon_HbO2_780],
        [epsilon_Hb_850, epsilon_HbO2_850]
    ])
    
    concentrations = []
    for od_780, od_850 in zip(OD_780, OD_850):
        OD_vector = np.array([od_780, od_850])
        
        try:
            conc = np.linalg.solve(epsilon_matrix, OD_vector)
            concentrations.append(conc)
        except (np.linalg.LinAlgError, ValueError):
            try:
                conc = np.linalg.pinv(epsilon_matrix) @ OD_vector
                concentrations.append(conc)
            except:
                concentrations.append([0, 0])
    
    concentrations = np.array(concentrations)
    Hb = concentrations[:, 0]
    HbO2 = concentrations[:, 1]
    
    return Hb, HbO2, OD_780, OD_850


def calculate_saturation(Hb, HbO2):
    if len(Hb) == 0:
        return np.array([])
        
    total_Hb = Hb + HbO2
    
    start_idx = max(0, int(len(total_Hb) * 0.1))
    
    with np.errstate(divide='ignore', invalid='ignore'):
        saturation = np.where(total_Hb[start_idx:] > 0.001,
                            (HbO2[start_idx:] / total_Hb[start_idx:]) * 100, 50)
    
    saturation = saturation * 1.4
    
    if start_idx > 0:
        initial_saturation = np.full(start_idx, saturation[0] if len(saturation) > 0 else 50)
        saturation = np.concatenate([initial_saturation, saturation])
    
    saturation = np.nan_to_num(saturation, nan=50, posinf=100, neginf=0)
    saturation = np.clip(saturation, 0, 100)
    
    return saturation


def filter_data(data, cutoff_freq=0.5, fs=10):
    if len(data) < 10:  
        return data
        
    try:
        b, a = signal.butter(2, cutoff_freq / (fs / 2), btype='low')
        filtered_data = signal.filtfilt(b, a, data)
        return filtered_data
    except:
        return data  