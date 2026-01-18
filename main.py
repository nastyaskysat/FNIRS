import sys
import os
import argparse
from pathlib import Path


project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_qt_environment():
    print("Библиотека libxcb-cursor0 установлена, используем стандартный плагин xcb")

def run_gui():
    setup_qt_environment()
    
    try:
        from frontend.gui.main_window import main
        main()
    except ImportError as e:
        print(f"Ошибка импорта модулей GUI: {e}")
        print("Убедитесь, что установлены все зависимости:")
        print("pip install PySide6 matplotlib pandas numpy scipy pyserial")
        sys.exit(1)

def run_console_analysis(filename):
    try:
        from backend.analysis.data_processor import DataProcessor
        
        if not os.path.exists(filename):
            print(f"Файл {filename} не найден")
            return
        
        processor = DataProcessor()
        print(f"=== АНАЛИЗ FNIRS ДАННЫХ ===")
        print(f"Файл: {filename}")
        
        data = processor.read_and_interpolate_data(filename)
        if data is None:
            print("Не удалось обработать данные")
            return
        
        results = processor.process_data(data)
        
        stats = results.get('stats', {})
        print(f"\n=== РЕЗУЛЬТАТЫ АНАЛИЗА ===")
        print(f"Диапазон времени: {stats.get('time_range', 'N/A')}")
        print(f"Длительность записи: {stats.get('duration', 'N/A')}")
        print(f"Количество точек данных: {stats.get('data_points', 'N/A')}")
        print(f"Интенсивность 780 нм: {stats.get('intensity_780_range', 'N/A')}")
        print(f"Интенсивность 850 нм: {stats.get('intensity_850_range', 'N/A')}")
        print(f"Средняя сатурация: {stats.get('mean_saturation', 'N/A')}")
        print(f"Минимальная сатурация: {stats.get('min_saturation', 'N/A')}")
        print(f"Максимальная сатурация: {stats.get('max_saturation', 'N/A')}")
        print(f"Стандартное отклонение: {stats.get('std_saturation', 'N/A')}")
        
        output_file = f"analysis_results_{Path(filename).stem}.csv"
        processor.save_results(output_file)
        print(f"\nРезультаты сохранены в {output_file}")
        
    except Exception as e:
        print(f"Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='FNIRS Анализатор - Система мониторинга гемоглобина')
    parser.add_argument('--console', '-c', metavar='FILE', 
                       help='Запуск консольного анализа указанного файла')
    parser.add_argument('--gui', '-g', action='store_true',
                       help='Запуск GUI приложения (по умолчанию)')
    
    args = parser.parse_args()
    
    if args.console:
        run_console_analysis(args.console)
    else:
        run_gui()

if __name__ == "__main__":
    main()
