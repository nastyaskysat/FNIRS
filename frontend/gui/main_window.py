import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QPushButton, QFileDialog, QLabel, QTextEdit,
                               QProgressBar, QSplitter, QGroupBox, QComboBox, QSpinBox,
                               QCheckBox, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon

# Добавляем путь к модулям проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.core.fnirs_analyzer import FNIRSAnalyzer
from frontend.widgets.plot_canvas import PlotWidget


class AnalysisWorker(QThread):

    finished = Signal(object) 
    error = Signal(str)      
    progress = Signal(str)  
    
    def __init__(self, analyzer, filename):
        super().__init__()
        self.analyzer = analyzer
        self.filename = filename
    
    def run(self):
        try:
            self.progress.emit("Чтение данных из файла...")
            results = self.analyzer.analyze_file(self.filename)
            
            if results is None:
                self.error.emit("Не удалось проанализировать данные")
                return
            
            self.progress.emit("Анализ завершен")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Ошибка при анализе: {str(e)}")


class FNIRSMainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.analyzer = FNIRSAnalyzer()
        self.current_file = None
        self.analysis_worker = None
        self.realtime_timer = None
        self.is_realtime_mode = False
        

        self.init_ui()
        
        self.analyzer.data_updated.connect(self.on_analyzer_data_update)
        self.analyzer.status_updated.connect(self.on_analyzer_status_update)
        self.analyzer.error_occurred.connect(self.on_analyzer_error)
    
    def init_ui(self):
        self.setWindowTitle('FNIRS Анализатор - Система мониторинга гемоглобина')
        self.setGeometry(100, 100, 1600, 900)
        
 
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        content_panel = self.create_content_panel()
        splitter.addWidget(content_panel)
        
        splitter.setSizes([350, 1250])
        
        self.realtime_timer = QTimer()
        self.realtime_timer.timeout.connect(self.update_realtime_display)
    
    def create_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        title = QLabel("FNIRS Анализатор")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(title)
        
        file_group = QGroupBox("Загрузка данных")
        file_layout = QVBoxLayout(file_group)
        
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("padding: 5px; background-color: #f8f8f8; border: 1px solid #ddd;")
        file_layout.addWidget(self.file_label)
        
        self.load_button = QPushButton("Выбрать файл данных")
        self.load_button.clicked.connect(self.load_file)
        self.load_button.setStyleSheet("QPushButton { padding: 8px; }")
        file_layout.addWidget(self.load_button)
        
        layout.addWidget(file_group)
        
        realtime_group = QGroupBox("Сбор данных в реальном времени")
        realtime_layout = QVBoxLayout(realtime_group)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Порт:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems(['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', 'COM1', 'COM2', 'COM3'])
        self.port_combo.setEditable(True)
        port_layout.addWidget(self.port_combo)
        realtime_layout.addLayout(port_layout)
        
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Скорость:"))
        self.baud_spinbox = QSpinBox()
        self.baud_spinbox.setRange(1200, 115200)
        self.baud_spinbox.setValue(9600)
        self.baud_spinbox.setSingleStep(1200)
        baud_layout.addWidget(self.baud_spinbox)
        realtime_layout.addLayout(baud_layout)
        
        self.start_realtime_button = QPushButton("Начать сбор данных")
        self.start_realtime_button.clicked.connect(self.start_realtime_collection)
        self.start_realtime_button.setStyleSheet("QPushButton { padding: 8px; background-color: #4CAF50; color: white; }")
        realtime_layout.addWidget(self.start_realtime_button)
        
        self.stop_realtime_button = QPushButton("Остановить сбор")
        self.stop_realtime_button.clicked.connect(self.stop_realtime_collection)
        self.stop_realtime_button.setEnabled(False)
        self.stop_realtime_button.setStyleSheet("QPushButton { padding: 8px; background-color: #f44336; color: white; }")
        realtime_layout.addWidget(self.stop_realtime_button)
        
        self.autosave_checkbox = QCheckBox("Автосохранение данных при остановке")
        self.autosave_checkbox.setChecked(True)
        realtime_layout.addWidget(self.autosave_checkbox)
        
        layout.addWidget(realtime_group)
        
        analysis_group = QGroupBox("Анализ данных")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analyze_button = QPushButton("Запустить анализ файла")
        self.analyze_button.clicked.connect(self.start_file_analysis)
        self.analyze_button.setEnabled(False)
        self.analyze_button.setStyleSheet("QPushButton { padding: 8px; background-color: #2196F3; color: white; }")
        analysis_layout.addWidget(self.analyze_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        analysis_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f4fd; border: 1px solid #b3d9ff;")
        analysis_layout.addWidget(self.status_label)
        
        layout.addWidget(analysis_group)
        
        plot_group = QGroupBox("Управление графиками")
        plot_layout = QVBoxLayout(plot_group)
        
        self.clear_plots_button = QPushButton("Очистить графики")
        self.clear_plots_button.clicked.connect(self.clear_plots)
        plot_layout.addWidget(self.clear_plots_button)
        
        self.save_plot_button = QPushButton("Сохранить график")
        self.save_plot_button.clicked.connect(self.save_plot)
        plot_layout.addWidget(self.save_plot_button)
        
        layout.addWidget(plot_group)
        
        layout.addStretch()
        
        return panel
    
    def create_content_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.tab_widget = QTabWidget()
        
        self.plot_widget = PlotWidget()
        self.tab_widget.addTab(self.plot_widget, "Графики")
        
        self.results_widget = self.create_results_widget()
        self.tab_widget.addTab(self.results_widget, "Результаты")
        
        self.logs_widget = self.create_logs_widget()
        self.tab_widget.addTab(self.logs_widget, "Логи")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_results_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.results_text)
        
        return widget
    
    def create_logs_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.logs_text)
        
        return widget
    
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл данных FNIRS",
            "",
            "Log files (*.log *.txt);;CSV files (*.csv);;All files (*.*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"Выбран: {os.path.basename(file_path)}")
            self.analyze_button.setEnabled(True)
            self.status_label.setText("Файл загружен, готов к анализу")
    
    def start_file_analysis(self):
        if not self.current_file:
            QMessageBox.warning(self, "Ошибка", "Файл не выбран")
            return
        

        self.analyze_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  
        
        self.analysis_worker = AnalysisWorker(self.analyzer, self.current_file)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.progress.connect(self.on_analysis_progress)
        self.analysis_worker.start()
    
    def on_analysis_progress(self, message):
        self.status_label.setText(message)
    
    def on_analysis_finished(self, results):
        self.analyze_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.plot_widget.plot_results(results)
        
        stats = results.get('stats', {})
        stats_text = self.format_stats_text(stats)
        self.results_text.setText(stats_text)
        
        self.status_label.setText("Анализ завершен успешно")
        self.add_log("Анализ файла завершен успешно")
    
    def on_analysis_error(self, error_message):
        self.analyze_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText(f"Ошибка: {error_message}")
        self.results_text.setText(f"Произошла ошибка при анализе:\n{error_message}")
        self.add_log(f"Ошибка анализа: {error_message}")
    
    def format_stats_text(self, stats):
        """Форматирование текста статистики"""
        return f"""=== РЕЗУЛЬТАТЫ АНАЛИЗА ===

Общая информация:
Диапазон времени: {stats.get('time_range', 'N/A')}
Длительность записи: {stats.get('duration', 'N/A')}
Количество точек данных: {stats.get('data_points', 'N/A')}

Интенсивности:
780 нм: {stats.get('intensity_780_range', 'N/A')}
850 нм: {stats.get('intensity_850_range', 'N/A')}

Сатурация крови:
Средняя: {stats.get('mean_saturation', 'N/A')}
Минимальная: {stats.get('min_saturation', 'N/A')}
Максимальная: {stats.get('max_saturation', 'N/A')}
Стандартное отклонение: {stats.get('std_saturation', 'N/A')}"""
    
    def start_realtime_collection(self):
        port = self.port_combo.currentText()
        baudrate = self.baud_spinbox.value()
        
        self.analyzer.start_realtime_analysis(port, baudrate)
        
        self.realtime_timer.start(500)  
        
        self.start_realtime_button.setEnabled(False)
        self.stop_realtime_button.setEnabled(True)
        self.analyze_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.is_realtime_mode = True
        
        self.add_log(f"Запущен режим реального времени на порту {port}")
    
    def stop_realtime_collection(self):
        self.analyzer.stop_realtime_analysis()
        
        self.realtime_timer.stop()
        
        if self.autosave_checkbox.isChecked():
            self.analyzer.save_realtime_data()
        
        self.start_realtime_button.setEnabled(True)
        self.stop_realtime_button.setEnabled(False)
        self.analyze_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.is_realtime_mode = False
        
        self.add_log("Режим реального времени остановлен")
    
    def update_realtime_display(self):
        data = self.analyzer.get_realtime_data()
        if data:
            self.plot_widget.update_realtime_plot(data)
            
            stats = data.get('stats', {})
            if stats:
                stats_text = self.format_realtime_stats(stats)
                self.results_text.setText(stats_text)
    
    def format_realtime_stats(self, stats):
        """Форматирование статистики реального времени"""
        return f"""=== ДАННЫЕ В РЕАЛЬНОМ ВРЕМЕНИ ===

Текущие значения:
Время записи: {stats.get('recording_time', 'N/A')}
Точек данных: {stats.get('data_points', 'N/A')}
Интенсивность 780 нм: {stats.get('current_intensity_780', 'N/A')}
Интенсивность 850 нм: {stats.get('current_intensity_850', 'N/A')}
Текущая сатурация: {stats.get('current_saturation', 'N/A')}

Статистика (последние точки):
Средняя сатурация: {stats.get('mean_saturation', 'N/A')}
Мин. сатурация: {stats.get('min_saturation', 'N/A')}
Макс. сатурация: {stats.get('max_saturation', 'N/A')}"""
    
    def clear_plots(self):

        self.plot_widget.clear_plots()
        self.results_text.clear()
        self.add_log("Графики очищены")
    
    def save_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить график",
            "fnirs_plot.png",
            "PNG files (*.png);;PDF files (*.pdf);;All files (*.*)"
        )
        
        if file_path:
            if self.plot_widget.save_plot(file_path):
                self.add_log(f"График сохранен в {file_path}")
                QMessageBox.information(self, "Успех", "График успешно сохранен")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить график")
    
    def on_analyzer_data_update(self, data):
        print(f"Получены данные для обновления графиков: {data}")
        
   
    def on_analyzer_status_update(self, status):
        self.status_label.setText(status)
    
    def on_analyzer_error(self, error_message):
        self.status_label.setText(f"Ошибка: {error_message}")
        self.add_log(f"Ошибка: {error_message}")
        QMessageBox.warning(self, "Ошибка", error_message)
    
    def add_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.logs_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        if self.is_realtime_mode:
            self.stop_realtime_collection()
        
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.terminate()
            self.analysis_worker.wait()
        
        event.accept()


from PySide6.QtCore import QDateTime


def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    window = FNIRSMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()