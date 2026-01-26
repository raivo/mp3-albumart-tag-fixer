"""Main application window."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

from .single_file_view import SingleFileView
from .directory_view import DirectoryView
from .settings_dialog import SettingsDialog
from config import get_config


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("MP3 Tag Editor")
        self.setMinimumSize(900, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("MP3 Tag Editor")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        settings_btn = QPushButton("Seaded")
        settings_btn.clicked.connect(self._on_settings)
        header_layout.addWidget(settings_btn)

        layout.addLayout(header_layout)

        # Mode description
        desc_label = QLabel(
            "Vali režiim: töötlemine üksiku faili või terve kataloogi kaupa."
        )
        desc_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # Tab widget for different modes
        self.tabs = QTabWidget()

        # Single file mode
        self.single_file_view = SingleFileView()
        self.single_file_view.file_saved.connect(self._on_file_saved)
        self.tabs.addTab(self.single_file_view, "Üksik fail")

        # Directory mode
        self.directory_view = DirectoryView()
        self.directory_view.directory_saved.connect(self._on_directory_saved)
        self.tabs.addTab(self.directory_view, "Kataloog")

        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Valmis")

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("Fail")

        open_file_action = QAction("Ava fail...", self)
        open_file_action.setShortcut(QKeySequence.StandardKey.Open)
        open_file_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_file_action)

        open_dir_action = QAction("Ava kataloog...", self)
        open_dir_action.setShortcut("Ctrl+Shift+O")
        open_dir_action.triggered.connect(self._on_open_directory)
        file_menu.addAction(open_dir_action)

        file_menu.addSeparator()

        quit_action = QAction("Välju", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Redigeeri")

        settings_action = QAction("Seaded...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._on_settings)
        edit_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("Abi")

        about_action = QAction("Teave...", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

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

    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Teave",
            "<h2>MP3 Tag Editor</h2>"
            "<p>Versioon 1.0</p>"
            "<p>Rakendus MP3 failide metaandmete haldamiseks.</p>"
            "<p>Funktsioonid:</p>"
            "<ul>"
            "<li>Failinime ja kataloogi analüüs</li>"
            "<li>Audio fingerprinting (AcoustID)</li>"
            "<li>Kaanepiltide otsing mitmetest allikatest</li>"
            "<li>Üksiku faili või terve kataloogi töötlemine</li>"
            "</ul>"
        )

    def _on_file_saved(self, track):
        """Handle file saved."""
        self.status_bar.showMessage(f"Salvestatud: {track.filename}", 5000)

    def _on_directory_saved(self, album):
        """Handle directory saved."""
        self.status_bar.showMessage(
            f"Salvestatud {album.track_count} faili kataloogist {album.directory.name}",
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
                "Salvestamata muudatused",
                "Sul on salvestamata muudatusi. Kas oled kindel, et soovid väljuda?",
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
