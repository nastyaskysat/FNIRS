import numpy as np
from scipy import signal


def calculate_hb_concentrations(intensity_780, intensity_850):
    if len(intensity_780) == 0 or len(intensity_850) == 0:
        return np.array([]), np.array([]), np.array([]), np.array([])
    
    epsilon_Hb_780 = 0.15    # коэффициент экстинкции дезоксигемоглобина на 780 нм
    epsilon_HbO2_780 = 0.08  # коэффициент экстинкции оксигемоглобина на 780 нм
    epsilon_Hb_850 = 0.06    # коэффициент экстинкции дезоксигемоглобина на 850 нм
    epsilon_HbO2_850 = 0.12  # коэффициент экстинкции оксигемоглобина на 850 нм
    
    intensity_780_arr = np.array(intensity_780)
    intensity_850_arr = np.array(intensity_850)
    
    intensity_780_arr = np.maximum(intensity_780_arr, 0.001)
    intensity_850_arr = np.maximum(intensity_850_arr, 0.001)
    
    OD_780 = -np.log(intensity_780_arr / intensity_780_arr[0])
    OD_850 = -np.log(intensity_850_arr / intensity_850_arr[0])
    
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
    
    with np.errstate(divide='ignore', invalid='ignore'):
        saturation = np.where(total_Hb != 0, (HbO2 / total_Hb) * 100, 0)
    
    saturation = np.nan_to_num(saturation, nan=0, posinf=0, neginf=0)
    
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