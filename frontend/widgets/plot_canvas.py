import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class PlotCanvas(FigureCanvas):
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        plt.style.use('seaborn-v0_8-whitegrid')
        
        self.axes = self.fig.subplots(2, 2)
        self.fig.tight_layout(pad=3.0)
        
        self._init_empty_plots()
    
    def _init_empty_plots(self):
        ax1 = self.axes[0, 0]
        ax1.set_title('Интенсивность ИК излучения')
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Интенсивность')
        ax1.grid(True, alpha=0.3)
        
        ax2 = self.axes[0, 1]
        ax2.set_title('Концентрации гемоглобина')
        ax2.set_xlabel('Время (с)')
        ax2.set_ylabel('Концентрация (усл. ед.)')
        ax2.grid(True, alpha=0.3)

        ax3 = self.axes[1, 0]
        ax3.set_title('Сатурация крови')
        ax3.set_xlabel('Время (с)')
        ax3.set_ylabel('Сатурация (%)')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([0, 100])

        ax4 = self.axes[1, 1]
        ax4.set_title('Общий гемоглобин')
        ax4.set_xlabel('Время (с)')
        ax4.set_ylabel('Концентрация (усл. ед.)')
        ax4.grid(True, alpha=0.3)
        
        self.draw()
    
    def plot_results(self, results):
        time = results['time']
        intensity_780 = results['intensity_780']
        intensity_850 = results['intensity_850']
        Hb = results['Hb']
        HbO2 = results['HbO2']
        saturation = results['saturation']
        
        for ax in self.axes.flat:
            ax.clear()
        
        ax1 = self.axes[0, 0]
        ax1.plot(time, intensity_780, 'r-', label='780 нм (Pin 3)', alpha=0.8, linewidth=0.8)
        ax1.plot(time, intensity_850, 'b-', label='850 нм (Pin 4)', alpha=0.8, linewidth=0.8)
        ax1.set_title('Интенсивность ИК излучения')
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Интенсивность')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Уменьшаем масштаб и ограничиваем количество отображаемых точек
        if len(time) > 500:
            step = max(1, len(time) // 200)  # Показываем примерно 200 точек
            time_display = time[::step]
            intensity_780_display = intensity_780[::step]
            intensity_850_display = intensity_850[::step]
            ax1.clear()
            ax1.plot(time_display, intensity_780_display, 'r-', label='780 нм (Pin 3)', alpha=0.8, linewidth=0.8)
            ax1.plot(time_display, intensity_850_display, 'b-', label='850 нм (Pin 4)', alpha=0.8, linewidth=0.8)
            ax1.set_title('Интенсивность ИК излучения')
            ax1.set_xlabel('Время (с)')
            ax1.set_ylabel('Интенсивность')
            ax1.legend(fontsize=8)
            ax1.grid(True, alpha=0.3)
            # Автоматическое масштабирование по Y
            ax1.relim()
            ax1.autoscale_view()
        
        ax2 = self.axes[0, 1]
        ax2.plot(time, Hb, 'b-', label='Деоксигенированный Hb', alpha=0.8, linewidth=1.5)
        ax2.plot(time, HbO2, 'r-', label='Оксигенированный Hb', alpha=0.8, linewidth=1.5)
        total_Hb = HbO2 + Hb
        ax2.plot(time, total_Hb, 'purple', label='Общий Hb', alpha=0.8, linewidth=1.5)
        ax2.set_title('Концентрации гемоглобина')
        ax2.set_xlabel('Время (с)')
        ax2.set_ylabel('Концентрация (усл. ед.)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        ax3 = self.axes[1, 0]
        ax3.plot(time, saturation, 'g-', linewidth=2.0)
        ax3.set_title('Сатурация крови')
        ax3.set_xlabel('Время (с)')
        ax3.set_ylabel('Сатурация (%)')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([0, 100])
        
        ax4 = self.axes[1, 1]
        ax4.plot(time, total_Hb, 'purple', linewidth=2.0)
        ax4.set_title('Общий гемоглобин')
        ax4.set_xlabel('Время (с)')
        ax4.set_ylabel('Концентрация (усл. ед.)')
        ax4.grid(True, alpha=0.3)
        
        self.fig.tight_layout(pad=3.0)
        self.draw()
    
    def update_realtime_plot(self, data):
        if data is None or len(data['time']) < 5:
            return
            
        time = data['time']
        intensity_780 = data['intensity_780']
        intensity_850 = data['intensity_850']
        Hb = data['Hb']
        HbO2 = data['HbO2']
        saturation = data['saturation']
        total_Hb = HbO2 + Hb
        
        for ax in self.axes.flat:
            ax.clear()
        
        ax1 = self.axes[0, 0]
        ax1.plot(time, intensity_780, 'r-', label='780 нм (Pin 3)', alpha=0.8, linewidth=0.8)
        ax1.plot(time, intensity_850, 'b-', label='850 нм (Pin 4)', alpha=0.8, linewidth=0.8)
        ax1.set_title('Интенсивность ИК излучения')
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Интенсивность')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Для реального времени показываем только последние 50 точек
        if len(time) > 50:
            start_idx = len(time) - 50
            time_display = time[start_idx:]
            intensity_780_display = intensity_780[start_idx:]
            intensity_850_display = intensity_850[start_idx:]
            ax1.clear()
            ax1.plot(time_display, intensity_780_display, 'r-', label='780 нм (Pin 3)', alpha=0.8, linewidth=0.8)
            ax1.plot(time_display, intensity_850_display, 'b-', label='850 нм (Pin 4)', alpha=0.8, linewidth=0.8)
            ax1.set_title('Интенсивность ИК излучения')
            ax1.set_xlabel('Время (с)')
            ax1.set_ylabel('Интенсивность')
            ax1.legend(fontsize=8)
            ax1.grid(True, alpha=0.3)
            # Автоматическое масштабирование по Y
            ax1.relim()
            ax1.autoscale_view()
        
        ax2 = self.axes[0, 1]
        ax2.plot(time, Hb, 'b-', label='Деоксигенированный Hb', alpha=0.8, linewidth=1.5)
        ax2.plot(time, HbO2, 'r-', label='Оксигенированный Hb', alpha=0.8, linewidth=1.5)
        ax2.plot(time, total_Hb, 'purple', label='Общий Hb', alpha=0.8, linewidth=1.5)
        ax2.set_title('Концентрации гемоглобина')
        ax2.set_xlabel('Время (с)')
        ax2.set_ylabel('Концентрация (усл. ед.)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        ax3 = self.axes[1, 0]
        ax3.plot(time, saturation, 'g-', linewidth=2.0)
        ax3.set_title('Сатурация крови')
        ax3.set_xlabel('Время (с)')
        ax3.set_ylabel('Сатурация (%)')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([0, 100])
        
        ax4 = self.axes[1, 1]
        ax4.plot(time, total_Hb, 'purple', linewidth=2.0)
        ax4.set_title('Общий гемоглобин (реальное время)')
        ax4.set_xlabel('Время (с)')
        ax4.set_ylabel('Концентрация (усл. ед.)')
        ax4.grid(True, alpha=0.3)
        
        self.fig.tight_layout(pad=3.0)
        self.draw()
    
    def clear_plots(self):
        for ax in self.axes.flat:
            ax.clear()
            ax.grid(True, alpha=0.3)
        
        self._init_empty_plots()


class PlotWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.plot_canvas = PlotCanvas(self)
        self.layout.addWidget(self.plot_canvas)
        
        self.setMinimumSize(800, 600)
    
    def plot_results(self, results):
        self.plot_canvas.plot_results(results)
    
    def update_realtime_plot(self, data):
        self.plot_canvas.update_realtime_plot(data)
    
    def clear_plots(self):
        self.plot_canvas.clear_plots()
    
    def save_plot(self, filename):
        try:
            self.plot_canvas.fig.savefig(filename, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Ошибка при сохранении графика: {e}")
            return False
