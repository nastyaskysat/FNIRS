SERIAL_CONFIG = {
    'default_port': '/dev/ttyUSB0',
    'default_baudrate': 9600,
    'timeout': 1,
    'buffer_size': 1000
}

ANALYSIS_CONFIG = {
    'cutoff_frequency': 0.5, 
    'sampling_rate': 10,      
    'epsilon_hb_780': 0.15,  
    'epsilon_hbo2_780': 0.08, 
    'epsilon_hb_850': 0.06,  
    'epsilon_hbo2_850': 0.12  
}

UI_CONFIG = {
    'window_width': 1600,
    'window_height': 900,
    'plot_update_interval': 500,  
    'autosave_enabled': True
}

FILE_CONFIG = {
    'supported_formats': ['.log', '.txt', '.csv'],
    'default_save_dir': 'data',
    'autosave_prefix': 'fnirs_realtime_'
}

LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'fnirs_analyzer.log'
}
