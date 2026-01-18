import logging
import time
from typing import Optional, Dict, Any, Callable

from backend.serial.serial_reader import SerialDataReader
from backend.analysis.data_processor import DataProcessor


class FNIRSAnalyzer:
    
    def __init__(self):
        self.serial_reader = None
        self.data_processor = DataProcessor()
        self.realtime_data = None
        self.is_realtime_mode = False
        
        self.data_update_callbacks = []
        self.status_update_callbacks = []
        self.error_callbacks = []
        
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def add_data_update_callback(self, callback: Callable):
        self.data_update_callbacks.append(callback)
    
    def add_status_update_callback(self, callback: Callable):
        self.status_update_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        self.error_callbacks.append(callback)
    
    def _notify_data_update(self, data: Dict[str, Any]):
        for callback in self.data_update_callbacks:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Ошибка в колбэке обновления данных: {e}")
    
    def _notify_status_update(self, status: str):
        for callback in self.status_update_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Ошибка в колбэке статуса: {e}")
    
    def _notify_error(self, error_message: str):
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Ошибка в колбэке ошибок: {e}")
    
    def start_realtime_analysis(self, port: str = '/dev/ttyUSB0', baudrate: int = 9600):
        try:
            if self.is_realtime_mode:
                self.logger.warning("Режим реального времени уже активен")
                return
            
            self.serial_reader = SerialDataReader(port, baudrate)
            
            self.serial_reader.add_data_callback(self._on_serial_data)
            self.serial_reader.add_error_callback(self._on_serial_error)
            self.serial_reader.add_status_callback(self._on_serial_status)
            
            self.serial_reader.start()
            self.is_realtime_mode = True
            
            self.logger.info(f"Запущен режим реального времени на порту {port}")
            
        except Exception as e:
            error_msg = f"Ошибка при запуске режима реального времени: {str(e)}"
            self._notify_error(error_msg)
            self.logger.error(error_msg)
    
    def stop_realtime_analysis(self):
        if not self.is_realtime_mode:
            return
        
        if self.serial_reader:
            self.serial_reader.stop()
        
        self.is_realtime_mode = False
        self.realtime_data = None
        
        self._notify_status_update("Режим реального времени остановлен")
        self.logger.info("Режим реального времени остановлен")
    
    def _on_serial_data(self, timestamp: float, pin: int, intensity: float):
        pass
    
    def _on_serial_error(self, error_message: str):
        self._notify_error(error_message)
        self.stop_realtime_analysis()
    
    def _on_serial_status(self, status_message: str):
        self._notify_status_update(status_message)
    
    def get_realtime_data(self) -> Optional[Dict[str, Any]]:
        if not self.is_realtime_mode or not self.serial_reader:
            return None
        
        raw_data = self.serial_reader.get_current_data()
        if raw_data is None or len(raw_data['time']) < 5:
            return None
        
        processed_data = self.data_processor.process_realtime_data(raw_data)
        if processed_data is None:
            return None
        
        if len(processed_data['time']) > 10:
            processed_data['stats'] = self._get_realtime_stats(processed_data)
        
        self.realtime_data = processed_data
        return processed_data
    
    def _get_realtime_stats(self, data: Dict[str, Any]) -> Dict[str, str]:
        time_data = data['time']
        intensity_780 = data['intensity_780']
        intensity_850 = data['intensity_850']
        saturation = data['saturation']
        
        n_points = min(50, len(saturation))
        
        return {
            'recording_time': f"{time_data[-1]:.1f} с",
            'data_points': str(len(time_data)),
            'current_intensity_780': f"{intensity_780[-1]:.3f}",
            'current_intensity_850': f"{intensity_850[-1]:.3f}",
            'current_saturation': f"{saturation[-1]:.1f}%",
            'mean_saturation': f"{np.mean(saturation[-n_points:]):.1f}%",
            'min_saturation': f"{np.min(saturation[-n_points:]):.1f}%",
            'max_saturation': f"{np.max(saturation[-n_points:]):.1f}%"
        }
    
    def analyze_file(self, filename: str) -> Optional[Dict[str, Any]]:
        try:
            self._notify_status_update("Чтение данных из файла...")
            
            data = self.data_processor.read_and_interpolate_data(filename)
            
            if data is None or len(data) == 0:
                raise ValueError("Не удалось обработать данные из файла")
            
            self._notify_status_update("Обработка данных...")
            
            results = self.data_processor.process_data(data)
            
            self._notify_status_update("Анализ завершен")
            self.logger.info(f"Успешно проанализирован файл {filename}")
            
            return results
            
        except Exception as e:
            error_msg = f"Ошибка при анализе файла: {str(e)}"
            self._notify_error(error_msg)
            self.logger.error(error_msg)
            return None
    
    def save_realtime_data(self, filename: str = None) -> Optional[str]:
        if not self.realtime_data:
            self._notify_error("Нет данных для сохранения")
            return None
        
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"fnirs_realtime_{timestamp}.csv"
        
        try:
            import pandas as pd
            
            save_data = pd.DataFrame({
                'Time(s)': self.realtime_data['time'],
                'Intensity_780': self.realtime_data['intensity_780'],
                'Intensity_850': self.realtime_data['intensity_850'],
                'Hb': self.realtime_data['Hb'],
                'HbO2': self.realtime_data['HbO2'],
                'Saturation(%)': self.realtime_data['saturation'],
                'Total_Hb': self.realtime_data['total_Hb']
            })
            
            save_data.to_csv(filename, index=False)
            
            self._notify_status_update(f"Данные сохранены в {filename}")
            self.logger.info(f"Данные сохранены в {filename}")
            
            return filename
            
        except Exception as e:
            error_msg = f"Ошибка при сохранении данных: {str(e)}"
            self._notify_error(error_msg)
            self.logger.error(error_msg)
            return None
    
    def get_status(self) -> Dict[str, Any]:
        status = {
            'realtime_mode': self.is_realtime_mode,
            'connected': False,
            'buffer_sizes': {'time': 0, 'pin3': 0, 'pin4': 0}
        }
        
        if self.serial_reader:
            status['connected'] = self.serial_reader.is_connected()
            status['buffer_sizes'] = self.serial_reader.get_buffer_sizes()
        
        return status


import numpy as np