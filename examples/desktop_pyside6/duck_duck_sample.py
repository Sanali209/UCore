import sys
import os
import re
import json
from pathlib import Path
import requests
import functools
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLineEdit, QPushButton, QLabel, QFileDialog,
    QScrollArea, QGridLayout, QSpinBox, QMessageBox, QComboBox
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QMetaObject
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        raise ImportError("Please install 'duckduckgo-search' or 'ddgs' package: pip install duckduckgo-search")

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.ui.pyside6_adapter import PySide6Adapter
from framework.config import Config
from framework.logging import Logging
from framework.cpu_tasks import ConcurrentFuturesAdapter


class DuckDuckGoImageSearch(QMainWindow):
    def __init__(self, config: Config, concurrent_adapter: ConcurrentFuturesAdapter, app:App):
        super().__init__()
        self.app = app
        self.config = config
        self.concurrent_adapter = concurrent_adapter

        # Define config file path
        self.config_file = "duck_duck_config.yml"

        # Load existing config or create with defaults
        if os.path.exists(self.config_file):
            self.config.load_from_file(self.config_file)
        else:
            # Set default values
            self.config.set("CONCURRENT_WORKERS", 4)
            self.config.set("CONCURRENT_TIMEOUT", 30.0)
            self.config.set("DEFAULT_MAX_RESULTS", 200)

        self.setWindowTitle("Поиск изображений DuckDuckGo")
        self.setGeometry(100, 100, 800, 600)

        self.current_images_info = [] # Stores (url, filename)
        self.download_path = ""

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите поисковый запрос...")
        search_layout.addWidget(self.search_input)

        self.max_results_input = QSpinBox()
        self.max_results_input.setMinimum(1)
        self.max_results_input.setMaximum(1000)
        self.max_results_input.setValue(self.config.get("DEFAULT_MAX_RESULTS", 200))
        search_layout.addWidget(QLabel("Макс. результатов:"))
        search_layout.addWidget(self.max_results_input)

        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # Dynamic Configuration Controls
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Динамическая конфигурация:"))

        # Worker count control
        worker_layout = QVBoxLayout()
        worker_layout.addWidget(QLabel("Рабочие потоки:"))
        self.worker_spinbox = QSpinBox()
        self.worker_spinbox.setMinimum(1)
        self.worker_spinbox.setMaximum(20)
        self.worker_spinbox.setValue(self.config.get("CONCURRENT_WORKERS", 4))
        worker_layout.addWidget(self.worker_spinbox)
        config_layout.addLayout(worker_layout)

        # Timeout control
        timeout_layout = QVBoxLayout()
        timeout_layout.addWidget(QLabel("Таймаут (сек):"))
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setMinimum(10)
        self.timeout_spinbox.setMaximum(300)
        self.timeout_spinbox.setValue(int(self.config.get("CONCURRENT_TIMEOUT", 30.0)))
        timeout_layout.addWidget(self.timeout_spinbox)
        config_layout.addLayout(timeout_layout)

        # Update config button
        self.update_config_button = QPushButton("Обновить конфигурацию")
        self.update_config_button.clicked.connect(self.on_update_config)
        config_layout.addWidget(self.update_config_button)

        # Save config button
        self.save_config_button = QPushButton("Сохранить настройки")
        self.save_config_button.clicked.connect(self.on_save_config)
        config_layout.addWidget(self.save_config_button)

        main_layout.addLayout(config_layout)

        # Log level control
        log_layout = QHBoxLayout()
        log_layout.addWidget(QLabel("Уровень логирования:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(self.app.container.get(Logging).get_available_levels())
        current_level = self.config.get("LOG_LEVEL", "INFO")
        current_index = self.log_level_combo.findText(current_level)
        if current_index >= 0:
            self.log_level_combo.setCurrentIndex(current_index)
        self.log_level_combo.currentTextChanged.connect(self.on_log_level_changed)
        log_layout.addWidget(self.log_level_combo)
        main_layout.addLayout(log_layout)

        # Download directory
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("Директория для скачивания: не выбрана")
        dir_layout.addWidget(self.dir_label)
        self.select_dir_button = QPushButton("Выбрать основную директорию")
        self.select_dir_button.clicked.connect(self.select_download_directory)
        dir_layout.addWidget(self.select_dir_button)
        main_layout.addLayout(dir_layout)
        self.base_download_directory = ""

        # Image display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.image_grid_layout = QGridLayout(self.scroll_content_widget)
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area)

        # Status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.search_input.returnPressed.connect(self.perform_search)

        # Create central widget for QMainWindow
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def select_download_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите основную директорию для сохранения")
        if directory:
            self.base_download_directory = directory
            self.dir_label.setText(f"Основная директория: {directory}")

    def _sanitize_filename(self, name):
        # Удаляем недопустимые символы и заменяем пробелы на подчеркивания
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        name = re.sub(r'\s+', '_', name)
        return name[:100] # Ограничиваем длину

    def perform_search(self):
        query = self.search_input.text()
        max_results = self.max_results_input.value()

        if not query:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите поисковый запрос.")
            return

        if not self.base_download_directory:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите основную директорию для скачивания.")
            return

        search_specific_dirname = self._sanitize_filename(query)
        self.download_path = os.path.join(self.base_download_directory, search_specific_dirname)

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.clear_image_grid()
        self.status_label.setText(f"Поиск изображений для '{query}'...")
        QApplication.processEvents()

        # Submit search task to concurrent executor
        self.concurrent_adapter.submit_with_callback(
            self._search_images_task,
            success_callback=self.on_search_completed,
            error_callback=self.on_search_error,
            query=query,
            max_results=max_results
        )

    def _search_images_task(self, query, max_results):
        """Task function that runs in worker thread"""
        results = []
        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.images(
                    keywords=query,
                    region='wt-wt',
                    safesearch='off',
                    timeout=10,
                    max_results=max_results
                ))
                results = search_results
        except Exception as e:
            raise RuntimeError(f"Ошибка при поиске: {e}")

        return results

    def on_search_completed(self, results):
        """Called in main thread when search is successful"""
        if not results:
            self.status_label.setText("Изображения не найдены.")
            return

        self.status_label.setText(f"Найдено {len(results)} изображений. Загрузка...")
        self.images_loaded_count = 0
        self.total_images_to_load = len(results)
        self.image_grid_layout.setSpacing(5)

        # Submit download tasks for each image
        for i, result in enumerate(results):
            image_url = result.get('image')
            if image_url:
                query = self.search_input.text()
                query_part_for_filename = self._sanitize_filename(query)
                base_filename_for_item = f"{query_part_for_filename}_{i}"

                # Submit download task
                self.concurrent_adapter.submit_with_callback(
                    self._download_image_task,
                    success_callback=functools.partial(self.on_image_downloaded, image_url),
                    error_callback=functools.partial(self.handle_download_error, result),
                    result=result,
                    download_path=self.download_path,
                    base_filename=base_filename_for_item
                )

    def on_search_error(self, error):
        """Called in main thread when search fails"""
        self.status_label.setText(f"Ошибка поиска: {error}")
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при поиске: {error}")

    def _download_image_task(self, result, download_path, base_filename):
        """Download image function that runs in worker thread"""
        url = result.get('image')
        if not url:
            raise ValueError(f"Отсутствует URL изображения в данных: {result.get('title', 'Без названия')}")

        image_filename_ext = os.path.splitext(url.split("?")[0])[-1]
        if not image_filename_ext or len(image_filename_ext) > 5 or len(image_filename_ext) < 2:
            image_filename_ext = ".jpg"

        image_full_filename = base_filename + image_filename_ext
        metadata_filename = base_filename + ".json"

        # Download image
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        image = QImage()
        success_load = image.loadFromData(response.content)
        if not success_load:
            raise ValueError(f"Не удалось загрузить изображение с URL: {url}")

        pixmap = QPixmap.fromImage(image)

        # Save the full image
        full_image_path = os.path.join(download_path, image_full_filename)
        os.makedirs(os.path.dirname(full_image_path), exist_ok=True)

        saved_successfully = image.save(full_image_path)
        if not saved_successfully:
            png_image_full_filename = base_filename + ".png"
            full_image_path = os.path.join(download_path, png_image_full_filename)
            if not pixmap.save(full_image_path):
                raise RuntimeError(f"Не удалось сохранить изображение: {png_image_full_filename}")
            image_full_filename = png_image_full_filename

        # Save metadata
        metadata_file_path = os.path.join(download_path, metadata_filename)
        with open(metadata_file_path, 'w', encoding='utf-8') as mf:
            json.dump(result, mf, ensure_ascii=False, indent=4)

        # Create thumbnail for UI
        thumbnail_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return {
            'thumbnail': thumbnail_pixmap,
            'url': url,
            'filename': base_filename
        }

    def on_image_downloaded(self, url, result):
        """Called in main thread when image is downloaded successfully"""
        if result:
            thumbnail = result['thumbnail']
            if thumbnail and not thumbnail.isNull():
                image_label = QLabel()
                image_label.setPixmap(thumbnail)
                image_label.setFixedSize(150, 150)
                image_label.setAlignment(Qt.AlignCenter)

                self.images_loaded_count += 1
                row = self.images_loaded_count // 5
                col = self.images_loaded_count % 5
                self.image_grid_layout.addWidget(image_label, row, col)

                self.status_label.setText(f"Загружено {self.images_loaded_count}/{self.total_images_to_load} изображений...")

    def handle_download_error(self, result, error):
        """Called in main thread when image download fails"""
        print(f"Ошибка загрузки: {error}")
        self.status_label.setText(f"Ошибка загрузки: {error}")

    def on_update_config(self):
        """Handle update configuration button click"""
        workers = self.worker_spinbox.value()
        timeout = self.timeout_spinbox.value()
        max_results = self.max_results_input.value()

        try:
            # Update configuration
            self.config.set("CONCURRENT_WORKERS", workers)
            self.config.set("CONCURRENT_TIMEOUT", float(timeout))
            self.config.set("DEFAULT_MAX_RESULTS", max_results)

            # Update concurrent adapter
            self.concurrent_adapter.update_config(workers=workers, timeout=float(timeout))

            self.status_label.setText(f"Конфигурация обновлена: {workers} потоков, {timeout}с таймаут")
            QMessageBox.information(self, "Обновление", f"Конфигурация обновлена успешно!\n\nПотоки: {workers}\nТаймаут: {timeout}с")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить конфигурацию: {e}")

    def on_save_config(self):
        """Handle save configuration button click"""
        workers = self.worker_spinbox.value()
        timeout = self.timeout_spinbox.value()
        max_results = self.max_results_input.value()
        log_level = self.log_level_combo.currentText()

        try:
            # Update all configuration values
            self.config.set("CONCURRENT_WORKERS", workers)
            self.config.set("CONCURRENT_TIMEOUT", float(timeout))
            self.config.set("DEFAULT_MAX_RESULTS", max_results)
            self.config.set("LOG_LEVEL", log_level)

            # Save to file
            self.config.save_to_file(self.config_file)

            self.status_label.setText("Настройки сохранены в файл")
            QMessageBox.information(self, "Сохранение", f"Настройки успешно сохранены!\n\nФайл: {self.config_file}\nПотоки: {workers}\nТаймаут: {timeout}с\nЛоги: {log_level}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {e}")

    def on_log_level_changed(self, level):
        """Handle log level combo box change"""
        try:
            # Update configuration
            self.config.set("LOG_LEVEL", level)

            # Update the app's logging immediately
            self.app.update_log_level(level)

            self.status_label.setText(f"Уровень логирования изменен на: {level}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить уровень логирования: {e}")

    def update_config_and_save(self, workers=None, timeout=None, default_max_results=None):
        """
        Update configuration values at runtime and save to file.
        Can also update the concurrent adapter settings.
        """
        try:
            if workers is not None:
                self.config.set("CONCURRENT_WORKERS", workers)
            if timeout is not None:
                self.config.set("CONCURRENT_TIMEOUT", timeout)
            if default_max_results is not None:
                self.config.set("DEFAULT_MAX_RESULTS", default_max_results)

            # Save configuration to file
            self.config.save_to_file(self.config_file)

            # Update the adapter settings
            if workers is not None or timeout is not None:
                self.concurrent_adapter.update_config(workers=workers, timeout=timeout)

            self.status_label.setText("Настройки сохранены успешно")
            QMessageBox.information(self, "Сохранение", "Настройки успешно сохранены!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {e}")

    def clear_image_grid(self):
        self.images_loaded_count = 0
        self.current_images_info = []
        for i in reversed(range(self.image_grid_layout.count())):
            widget_to_remove = self.image_grid_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()


def create_duck_duck_app():
    """
    Application factory for the DuckDuckGo image search app.
    """
    # 1. Initialize the main App object
    app = App(name="DuckDuckGoImageSearch")

    # 2. Register the PySide6Adapter for UI
    pyside6_adapter = PySide6Adapter(app)
    app.register_component(lambda: pyside6_adapter)

    # 3. Register the ConcurrentFuturesAdapter for threading
    concurrent_adapter = ConcurrentFuturesAdapter(app)
    app.register_component(lambda: concurrent_adapter)
    # Register the instance for dependency injection
    app.container.register(ConcurrentFuturesAdapter, concurrent_adapter)

    # 4. Create and show the main window (dependency injection will handle parameters)
    main_window = pyside6_adapter.create_widget(DuckDuckGoImageSearch)
    pyside6_adapter.add_window(main_window)
    main_window.show()

    return app


if __name__ == "__main__":
    # Create the application instance
    ucore_app = create_duck_duck_app()

    # Run the application
    ucore_app.run()
