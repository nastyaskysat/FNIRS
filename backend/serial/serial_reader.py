import serial
import time
from collections import deque
import threading
import logging
import numpy as np


class SerialDataReader:
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, buffer_size=1000):
        self.port = port
        self.baudrate = baudrate
        self.buffer_size = buffer_size
        self.running = False
        self.serial_connection = None
        self.read_thread = None
        
        self.time_buffer = deque(maxlen=buffer_size)
        self.pin3_buffer = deque(maxlen=buffer_size)  # 780 нм
        self.pin4_buffer = deque(maxlen=buffer_size)  # 850 нм
        self.start_time = None
        
        self.data_callbacks = []
        self.error_callbacks = []
        self.status_callbacks = []
        
        self.logger = logging.getLogger(__name__)
    
    def add_data_callback(self, callback):
        self.data_callbacks.append(callback)
    
    def add_error_callback(self, callback):
        self.error_callbacks.append(callback)
    
    def add_status_callback(self, callback):
        self.status_callbacks.append(callback)
    
    def _notify_data_callbacks(self, timestamp, pin, intensity):
        for callback in self.data_callbacks:
            try:
                callback(timestamp, pin, intensity)
            except Exception as e:
                self.logger.error(f"Ошибка в колбэке данных: {e}")
    
    def _notify_error_callbacks(self, error_message):
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                self.logger.error(f"Ошибка в колбэке ошибок: {e}")
    
    def _notify_status_callbacks(self, status_message):
        for callback in self.status_callbacks:
            try:
                callback(status_message)
            except Exception as e:
                self.logger.error(f"Ошибка в колбэке статуса: {e}")
    
    def start(self):
        if self.running:
            self.logger.warning("Чтение данных уже запущено")
            return
        
        try:
            self.serial_connection = serial.Serial(
                self.port, 
                self.baudrate, 
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.running = True
            self.start_time = time.time()
            
            self.read_thread = threading.Thread(target=self._read_loop)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            self._notify_status_callbacks(f"Подключен к {self.port}")
            self.logger.info(f"Запущено чтение данных с порта {self.port}")
            
        except serial.SerialException as e:
            error_msg = f"Не удалось подключиться к {self.port}: {str(e)}"
            self._notify_error_callbacks(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"Неожиданная ошибка при подключении: {str(e)}"
            self._notify_error_callbacks(error_msg)
            self.logger.error(error_msg)
    
    def stop(self):
        if not self.running:
            return
        
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=2.0)
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        
        self._notify_status_callbacks("Отключен")
        self.logger.info("Чтение данных остановлено")
    
    def _read_loop(self):
        while self.running:
            try:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._parse_data_line(line)
                else:
                    time.sleep(0.01)  
                    
            except serial.SerialException as e:
                error_msg = f"Ошибка чтения данных: {str(e)}"
                self._notify_error_callbacks(error_msg)
                self.logger.error(error_msg)
                break
            except Exception as e:
                error_msg = f"Неожиданная ошибка в цикле чтения: {str(e)}"
                self._notify_error_callbacks(error_msg)
                self.logger.error(error_msg)
                break
    
    def _parse_data_line(self, line):
        try:
            parts = line.split('\t')
            if len(parts) >= 3:
                current_time = time.time() - self.start_time
                pin = int(parts[1])
                intensity = float(parts[2])
                
                if pin == 3:  # 780 нм
                    self.time_buffer.append(current_time)
                    self.pin3_buffer.append(intensity)
                elif pin == 4:  # 850 нм
                    self.pin4_buffer.append(intensity)
                
                self._notify_data_callbacks(current_time, pin, intensity)
                
        except (ValueError, IndexError) as e:
            self.logger.debug(f"Некорректная строка данных: {line}")
    
    def get_current_data(self):
        if len(self.time_buffer) == 0:
            return None
            
        time_array = np.array(self.time_buffer)
        pin3_array = np.array(self.pin3_buffer)
        pin4_array = np.array(self.pin4_buffer)
        
        min_len = min(len(time_array), len(pin3_array), len(pin4_array))
        if min_len == 0:
            return None
            
        return {
            'time': time_array[-min_len:],
            'intensity_780': pin3_array[-min_len:],
            'intensity_850': pin4_array[-min_len:]
        }
    
    def is_connected(self):
        return self.running and self.serial_connection and self.serial_connection.is_open
    
    def get_buffer_sizes(self):
        return {
            'time': len(self.time_buffer),
            'pin3': len(self.pin3_buffer),
            'pin4': len(self.pin4_buffer)
        }


def parse_time(time_str):
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds_with_ms = float(parts[1])
            return minutes * 60 + seconds_with_ms
        else:
            return float(time_str)
    except:
        return 0.0