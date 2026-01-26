"""File list widget for displaying MP3 files."""

from pathlib import Path
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor

from models.track import Track


class FileListWidget(QWidget):
    """Widget for displaying a list of MP3 files."""

    file_selected = Signal(Track)  # Emitted when a file is selected
    file_double_clicked = Signal(Track)  # Emitted on double-click

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: list[Track] = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Failid")
        self.title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.title_label)

        self.count_label = QLabel("0 faili")
        self.count_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # File list
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._on_double_clicked)
        layout.addWidget(self.list_widget)

    def set_tracks(self, tracks: list[Track]):
        """Set the list of tracks to display."""
        self._tracks = tracks
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the list display."""
        self.list_widget.clear()

        for track in self._tracks:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, track)

            # Display text
            display_text = track.filename
            if track.resolved_info:
                info = track.resolved_info
                if info.artist and info.title:
                    display_text = f"{info.artist} - {info.title}"

            item.setText(display_text)

            # Set icon/color based on status
            if track.error_message:
                item.setForeground(QColor(255, 0, 0))  # Red for errors
            elif track.has_changes:
                item.setForeground(QColor(0, 128, 0))  # Green for pending changes
            elif track.is_processed:
                item.setForeground(QColor(0, 0, 255))  # Blue for processed

            # Tooltip
            tooltip = f"Fail: {track.filename}\n"
            if track.tag_info:
                tooltip += f"Tag: {track.tag_info.artist} - {track.tag_info.title}\n"
            if track.error_message:
                tooltip += f"Viga: {track.error_message}"
            item.setToolTip(tooltip)

            self.list_widget.addItem(item)

        self.count_label.setText(f"{len(self._tracks)} faili")

    def _on_selection_changed(self):
        """Handle selection change."""
        items = self.list_widget.selectedItems()
        if items:
            track = items[0].data(Qt.ItemDataRole.UserRole)
            self.file_selected.emit(track)

    def _on_double_clicked(self, item: QListWidgetItem):
        """Handle double-click."""
        track = item.data(Qt.ItemDataRole.UserRole)
        self.file_double_clicked.emit(track)

    def get_selected_track(self) -> Optional[Track]:
        """Get the currently selected track."""
        items = self.list_widget.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def select_track(self, track: Track):
        """Select a specific track in the list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == track:
                self.list_widget.setCurrentItem(item)
                break

    def update_track(self, track: Track):
        """Update the display for a specific track."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole).file_path == track.file_path:
                item.setData(Qt.ItemDataRole.UserRole, track)

                # Update display
                display_text = track.filename
                if track.resolved_info:
                    info = track.resolved_info
                    if info.artist and info.title:
                        display_text = f"{info.artist} - {info.title}"
                item.setText(display_text)

                # Update color
                if track.error_message:
                    item.setForeground(QColor(255, 0, 0))
                elif track.has_changes:
                    item.setForeground(QColor(0, 128, 0))
                elif track.is_processed:
                    item.setForeground(QColor(0, 0, 255))
                else:
                    item.setForeground(QColor(0, 0, 0))
                break

    def get_all_tracks(self) -> list[Track]:
        """Get all tracks in the list."""
        return self._tracks.copy()
