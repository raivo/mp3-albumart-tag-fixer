"""Dialog for previewing changes before applying."""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from models.track import Track
from core.analyzer import TrackAnalyzer


class PreviewDialog(QDialog):
    """Dialog for previewing changes before applying them."""

    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.tracks = [t for t in tracks if t.has_changes]
        self.selected_tracks = set(range(len(self.tracks)))  # All selected by default
        self.analyzer = TrackAnalyzer()

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Muudatuste eelvaade")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Vaata üle {len(self.tracks)} faili muudatused enne salvestamist:")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Vali", "Fail", "Väli", "Praegune väärtus", "Uus väärtus"
        ])

        # Adjust column widths
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)

        layout.addWidget(self.table)

        # Selection buttons
        selection_layout = QHBoxLayout()

        select_all_btn = QPushButton("Vali kõik")
        select_all_btn.clicked.connect(self._select_all)
        selection_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Tühista valik")
        deselect_all_btn.clicked.connect(self._deselect_all)
        selection_layout.addWidget(deselect_all_btn)

        selection_layout.addStretch()

        self.count_label = QLabel(f"Valitud: {len(self.selected_tracks)}/{len(self.tracks)}")
        selection_layout.addWidget(self.count_label)

        layout.addLayout(selection_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Tühista")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        apply_btn = QPushButton("Salvesta valitud")
        apply_btn.clicked.connect(self.accept)
        apply_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

    def _populate_table(self):
        """Populate the table with changes."""
        rows = []

        for track_idx, track in enumerate(self.tracks):
            changes = self.analyzer.preview_changes(track)

            for field, values in changes.items():
                rows.append({
                    'track_idx': track_idx,
                    'filename': track.filename,
                    'field': field,
                    'old': values['old'],
                    'new': values['new']
                })

        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(row_data['track_idx'] in self.selected_tracks)
            checkbox.setProperty('track_idx', row_data['track_idx'])
            checkbox.stateChanged.connect(self._on_checkbox_changed)

            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)

            self.table.setCellWidget(row_idx, 0, checkbox_widget)

            # Filename
            self.table.setItem(row_idx, 1, QTableWidgetItem(row_data['filename']))

            # Field name
            field_names = {
                'artist': 'Esitaja',
                'album': 'Album',
                'title': 'Pealkiri',
                'year': 'Aasta',
                'track_number': 'Loo nr',
                'genre': 'Žanr',
                'artwork': 'Kaanepilt'
            }
            field_item = QTableWidgetItem(field_names.get(row_data['field'], row_data['field']))
            self.table.setItem(row_idx, 2, field_item)

            # Old value
            old_val = str(row_data['old']) if row_data['old'] else "(tühi)"
            old_item = QTableWidgetItem(old_val)
            old_item.setForeground(QColor(128, 128, 128))
            self.table.setItem(row_idx, 3, old_item)

            # New value
            new_val = str(row_data['new']) if row_data['new'] else "(tühi)"
            new_item = QTableWidgetItem(new_val)
            new_item.setForeground(QColor(0, 128, 0))
            self.table.setItem(row_idx, 4, new_item)

    def _on_checkbox_changed(self, state):
        """Handle checkbox state change."""
        checkbox = self.sender()
        track_idx = checkbox.property('track_idx')

        if state == Qt.CheckState.Checked.value:
            self.selected_tracks.add(track_idx)
        else:
            self.selected_tracks.discard(track_idx)

        self.count_label.setText(f"Valitud: {len(self.selected_tracks)}/{len(self.tracks)}")

    def _select_all(self):
        """Select all tracks."""
        self.selected_tracks = set(range(len(self.tracks)))
        self._update_checkboxes()
        self.count_label.setText(f"Valitud: {len(self.selected_tracks)}/{len(self.tracks)}")

    def _deselect_all(self):
        """Deselect all tracks."""
        self.selected_tracks = set()
        self._update_checkboxes()
        self.count_label.setText(f"Valitud: 0/{len(self.tracks)}")

    def _update_checkboxes(self):
        """Update all checkboxes to match selected_tracks."""
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    track_idx = checkbox.property('track_idx')
                    checkbox.blockSignals(True)
                    checkbox.setChecked(track_idx in self.selected_tracks)
                    checkbox.blockSignals(False)

    def get_selected_tracks(self) -> list[Track]:
        """Get the list of selected tracks."""
        return [self.tracks[i] for i in sorted(self.selected_tracks)]
