import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from .hb_calculations import calculate_hb_concentrations, calculate_saturation, filter_data


class DataProcessor:
    
    def __init__(self):
        self.data = None
        self.results = None
    
    def read_and_interpolate_data(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            clean_lines = []
            for line in lines:
                clean_line = line.strip()
                if clean_line and not all(c == '\x00' for c in clean_line):
                    if not clean_line.startswith('---') and not 'Time(s:ms)' in clean_line:
                        clean_lines.append(clean_line)
            
            data = []
            for line in clean_lines:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        time_str = parts[0]
                        pin = int(parts[1])
                        intensity = float(parts[2])
                        data.append([time_str, pin, intensity])
                    except (ValueError, IndexError):
                        continue
            
            if len(data) == 0:
                raise ValueError("Нет корректных данных после очистки")
            
            df = pd.DataFrame(data, columns=['TimeStr', 'Pin', 'Intensity'])
            
            from backend.serial.serial_reader import parse_time
            df['Time(s)'] = df['TimeStr'].apply(parse_time)
            
            df['Pin'] = pd.to_numeric(df['Pin'], errors='coerce')
            df['Intensity'] = pd.to_numeric(df['Intensity'], errors='coerce')
            
            df = df.dropna()
            
            if len(df) == 0:
                raise ValueError("Нет данных после очистки")
            
            data_780 = df[df['Pin'] == 3][['Time(s)', 'Intensity']].copy()
            data_850 = df[df['Pin'] == 4][['Time(s)', 'Intensity']].copy()
            
            if len(data_780) == 0 or len(data_850) == 0:
                raise ValueError("Не найдены данные для одного или обоих каналов")
            
            min_time = max(data_780['Time(s)'].min(), data_850['Time(s)'].min())
            max_time = min(data_780['Time(s)'].max(), data_850['Time(s)'].max())
            
            if min_time >= max_time:
                return self._alternative_read_method(df)
            
            avg_interval_780 = data_780['Time(s)'].diff().mean()
            avg_interval_850 = data_850['Time(s)'].diff().mean()
            avg_interval = (avg_interval_780 + avg_interval_850) / 2
            
            if pd.isna(avg_interval) or avg_interval <= 0:
                avg_interval = 0.3  
            
            time_grid = np.arange(min_time, max_time, avg_interval)
            
            if len(data_780) > 1 and len(data_850) > 1:
                data_780 = data_780.sort_values('Time(s)')
                data_850 = data_850.sort_values('Time(s)')
                
                f_780 = interp1d(data_780['Time(s)'].values, data_780['Intensity'].values, 
                                 kind='linear', bounds_error=False, fill_value='extrapolate')
                f_850 = interp1d(data_850['Time(s)'].values, data_850['Intensity'].values, 
                                 kind='linear', bounds_error=False, fill_value='extrapolate')
                
                intensity_780_interp = f_780(time_grid)
                intensity_850_interp = f_850(time_grid)
            else:
                raise ValueError("Недостаточно данных для интерполяции")
            
            combined_data = pd.DataFrame({
                'Time(s)': time_grid,
                'Intensity_780': intensity_780_interp,
                'Intensity_850': intensity_850_interp
            })
            
            combined_data = combined_data.dropna()
            
            self.data = combined_data
            return combined_data
            
        except Exception as e:
            raise ValueError(f"Ошибка при чтении файла: {e}")
    
    def _alternative_read_method(self, df):
        data_780 = df[df['Pin'] == 3][['Time(s)', 'Intensity']].copy()
        data_850 = df[df['Pin'] == 4][['Time(s)', 'Intensity']].copy()
        
        data_780 = data_780.sort_values('Time(s)')
        data_850 = data_850.sort_values('Time(s)')
        
        combined_data = []
        
        for _, row_780 in data_780.iterrows():
            time_780 = row_780['Time(s)']
            intensity_780 = row_780['Intensity']
            
            if len(data_850) > 0:
                time_diff = np.abs(data_850['Time(s)'] - time_780)
                closest_idx = time_diff.idxmin()
                
                if time_diff[closest_idx] < 1.0:  
                    intensity_850 = data_850.loc[closest_idx, 'Intensity']
                    combined_data.append({
                        'Time(s)': time_780,
                        'Intensity_780': intensity_780,
                        'Intensity_850': intensity_850
                    })
        
        if len(combined_data) == 0:
            raise ValueError("Не удалось сопоставить данные по времени")
            
        combined_df = pd.DataFrame(combined_data)
        self.data = combined_df
        return combined_df
    
    def process_data(self, data=None):
        if data is None:
            if self.data is None:
                raise ValueError("Нет данных для обработки")
            data = self.data
        
        time = data['Time(s)'].values
        intensity_780 = data['Intensity_780'].values
        intensity_850 = data['Intensity_850'].values
        
        Hb, HbO2, OD_780, OD_850 = calculate_hb_concentrations(intensity_780, intensity_850)
        
        if len(Hb) == 0:
            raise ValueError("Не удалось рассчитать концентрации гемоглобина")
        
        saturation = calculate_saturation(Hb, HbO2)
        
        Hb_filtered = filter_data(Hb)
        HbO2_filtered = filter_data(HbO2)
        saturation_filtered = np.clip(filter_data(saturation), 0, 100)
        
        self.results = {
            'time': time,
            'intensity_780': intensity_780,
            'intensity_850': intensity_850,
            'Hb': Hb_filtered,
            'HbO2': HbO2_filtered,
            'saturation': saturation_filtered,
            'total_Hb': HbO2_filtered + Hb_filtered,
            'stats': self._calculate_statistics(time, intensity_780, intensity_850, saturation_filtered)
        }
        
        return self.results
    
    def _calculate_statistics(self, time, intensity_780, intensity_850, saturation):
        if len(time) == 0:
            return {}
        
        start_idx = max(0, int(len(saturation) * 0.1))
        
        return {
            'time_range': f"{time[0]:.2f} - {time[-1]:.2f} с",
            'duration': f"{time[-1] - time[0]:.2f} с",
            'intensity_780_range': f"{np.min(intensity_780):.3f} - {np.max(intensity_780):.3f}",
            'intensity_850_range': f"{np.min(intensity_850):.3f} - {np.max(intensity_850):.3f}",
            'mean_saturation': f"{np.mean(saturation[start_idx:]):.2f}%",
            'min_saturation': f"{np.min(saturation[start_idx:]):.2f}%",
            'max_saturation': f"{np.max(saturation[start_idx:]):.2f}%",
            'std_saturation': f"{np.std(saturation[start_idx:]):.2f}%",
            'data_points': len(time)
        }
    
    def process_realtime_data(self, realtime_data):
        if realtime_data is None or len(realtime_data['time']) < 5:
            return None
        
        time = realtime_data['time']
        intensity_780 = realtime_data['intensity_780']
        intensity_850 = realtime_data['intensity_850']
        
        try:
            Hb, HbO2, _, _ = calculate_hb_concentrations(intensity_780, intensity_850)
            saturation = calculate_saturation(Hb, HbO2)
            
            if len(Hb) > 5:
                Hb = filter_data(Hb)
                HbO2 = filter_data(HbO2)
                saturation = np.clip(filter_data(saturation), 0, 100)
            
            return {
                'time': time,
                'intensity_780': intensity_780,
                'intensity_850': intensity_850,
                'Hb': Hb,
                'HbO2': HbO2,
                'saturation': saturation,
                'total_Hb': HbO2 + Hb
            }
            
        except Exception as e:
            return None
    
    def save_results(self, filename):
        if self.results is None:
            raise ValueError("Нет результатов для сохранения")
        
        results_df = pd.DataFrame({
            'Time(s)': self.results['time'],
            'Intensity_780': self.results['intensity_780'],
            'Intensity_850': self.results['intensity_850'],
            'Hb': self.results['Hb'],
            'HbO2': self.results['HbO2'],
            'Saturation(%)': self.results['saturation'],
            'Total_Hb': self.results['total_Hb']
        })
        
        results_df.to_csv(filename, index=False)
        return filename