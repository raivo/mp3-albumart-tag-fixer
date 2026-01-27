"""Main application window."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QApplication, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

from .single_file_view import SingleFileView
from .directory_view import DirectoryView
from .settings_dialog import SettingsDialog
from config import get_config, save_config
from utils.translations import (
    tr, get_language, set_language, add_language_listener,
    TranslationManager
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.config = get_config()

        # Initialize language from config or detect from system
        if self.config.language:
            set_language(self.config.language)
        else:
            detected = TranslationManager.detect_system_language()
            set_language(detected)

        self._setup_ui()
        self._setup_menu()

        # Listen for language changes
        add_language_listener(self._on_language_changed)

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle(tr('app_title'))
        self.setMinimumSize(900, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Header
        header_layout = QHBoxLayout()

        self.title_label = QLabel(tr('app_title'))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Language switcher
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Eesti", "et")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setFixedWidth(90)
        self.lang_combo.setCurrentIndex(0 if get_language() == 'et' else 1)
        self.lang_combo.currentIndexChanged.connect(self._on_language_combo_changed)
        header_layout.addWidget(self.lang_combo)

        self.settings_btn = QPushButton(tr('settings'))
        self.settings_btn.clicked.connect(self._on_settings)
        header_layout.addWidget(self.settings_btn)

        layout.addLayout(header_layout)

        # Mode description
        self.desc_label = QLabel(tr('mode_description'))
        self.desc_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(self.desc_label)

        # Tab widget for different modes
        self.tabs = QTabWidget()

        # Single file mode
        self.single_file_view = SingleFileView()
        self.single_file_view.file_saved.connect(self._on_file_saved)
        self.tabs.addTab(self.single_file_view, tr('single_file'))

        # Directory mode
        self.directory_view = DirectoryView()
        self.directory_view.directory_saved.connect(self._on_directory_saved)
        self.tabs.addTab(self.directory_view, tr('directory'))

        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr('ready'))

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        self.file_menu = menubar.addMenu(tr('menu_file'))

        self.open_file_action = QAction(tr('menu_open_file'), self)
        self.open_file_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_file_action.triggered.connect(self._on_open_file)
        self.file_menu.addAction(self.open_file_action)

        self.open_dir_action = QAction(tr('menu_open_directory'), self)
        self.open_dir_action.setShortcut("Ctrl+Shift+O")
        self.open_dir_action.triggered.connect(self._on_open_directory)
        self.file_menu.addAction(self.open_dir_action)

        self.file_menu.addSeparator()

        self.quit_action = QAction(tr('menu_quit'), self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.quit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.quit_action)

        # Edit menu
        self.edit_menu = menubar.addMenu(tr('menu_edit'))

        self.settings_action = QAction(tr('menu_settings'), self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self._on_settings)
        self.edit_menu.addAction(self.settings_action)

        # Help menu
        self.help_menu = menubar.addMenu(tr('menu_help'))

        self.about_action = QAction(tr('menu_about'), self)
        self.about_action.triggered.connect(self._on_about)
        self.help_menu.addAction(self.about_action)

    def _on_open_file(self):
        """Open file dialog."""
        self.tabs.setCurrentWidget(self.single_file_view)
        self.single_file_view._on_browse()

    def _on_open_directory(self):
        """Open directory dialog."""
        self.tabs.setCurrentWidget(self.directory_view)
        self.directory_view._on_browse()

    def _on_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_language_combo_changed(self, index):
        """Handle language combo box change."""
        lang = self.lang_combo.currentData()
        if lang and lang != get_language():
            set_language(lang)
            # Save to config
            self.config.language = lang
            save_config(self.config)

    def _on_language_changed(self):
        """Handle language change - update all UI text."""
        # Update window title
        self.setWindowTitle(tr('app_title'))
        self.title_label.setText(tr('app_title'))
        self.settings_btn.setText(tr('settings'))
        self.desc_label.setText(tr('mode_description'))

        # Update tabs
        self.tabs.setTabText(0, tr('single_file'))
        self.tabs.setTabText(1, tr('directory'))

        # Update menu
        self.file_menu.setTitle(tr('menu_file'))
        self.open_file_action.setText(tr('menu_open_file'))
        self.open_dir_action.setText(tr('menu_open_directory'))
        self.quit_action.setText(tr('menu_quit'))
        self.edit_menu.setTitle(tr('menu_edit'))
        self.settings_action.setText(tr('menu_settings'))
        self.help_menu.setTitle(tr('menu_help'))
        self.about_action.setText(tr('menu_about'))

        # Update status bar
        self.status_bar.showMessage(tr('ready'))

        # Update language combo without triggering signal
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentIndex(0 if get_language() == 'et' else 1)
        self.lang_combo.blockSignals(False)

        # Update child views
        self.single_file_view.update_translations()
        self.directory_view.update_translations()

    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            tr('about_title'),
            tr('about_text')
        )

    def _on_file_saved(self, track):
        """Handle file saved."""
        self.status_bar.showMessage(f"{tr('saved')}: {track.filename}", 5000)

    def _on_directory_saved(self, album):
        """Handle directory saved."""
        self.status_bar.showMessage(
            tr('saved_files', count=album.track_count),
            5000
        )

    def closeEvent(self, event):
        """Handle window close."""
        # Check for unsaved changes
        single_track = self.single_file_view.get_current_track()
        album = self.directory_view.get_current_album()

        has_changes = False
        if single_track and single_track.has_changes:
            has_changes = True
        if album and any(t.has_changes for t in album.tracks):
            has_changes = True

        if has_changes:
            reply = QMessageBox.question(
                self,
                tr('unsaved_changes'),
                tr('unsaved_changes_msg'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Clean up
        from utils.cache import close_cache
        close_cache()

        event.accept()


def run_app():
    """Run the application."""
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("MP3 Tag Editor")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("MP3TagEditor")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
