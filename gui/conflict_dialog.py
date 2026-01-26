"""Dialog for resolving metadata conflicts."""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QLineEdit,
    QGroupBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt

from models.track import Track, InfoSource
from core.matcher import Conflict


class ConflictDialog(QDialog):
    """Dialog for resolving conflicts between metadata sources."""

    def __init__(self, track: Track, conflicts: list[Conflict], parent=None):
        super().__init__(parent)
        self.track = track
        self.conflicts = conflicts
        self.resolutions = {}  # field -> resolved value

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Lahenda konfliktid")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Failis '{self.track.filename}' leiti vastuolulisi andmeid.")
        header.setWordWrap(True)
        header.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        info = QLabel("Palun vali iga välja jaoks õige väärtus või sisesta oma:")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; margin-bottom: 15px;")
        layout.addWidget(info)

        # Scroll area for conflicts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        self.field_groups = {}

        for conflict in self.conflicts:
            group = self._create_conflict_group(conflict)
            content_layout.addWidget(group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Tühista")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.apply_btn = QPushButton("Rakenda")
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

    def _create_conflict_group(self, conflict: Conflict) -> QGroupBox:
        """Create a group box for a single conflict."""
        field_names = {
            'artist': 'Esitaja',
            'album': 'Album',
            'title': 'Pealkiri',
            'year': 'Aasta'
        }

        group = QGroupBox(field_names.get(conflict.field, conflict.field))
        layout = QVBoxLayout(group)

        button_group = QButtonGroup(group)
        buttons = []

        # Create radio button for each source value
        for source, value in conflict.values.items():
            source_name = self._get_source_name(source)
            radio = QRadioButton(f"{source_name}: {value}")
            radio.setProperty('value', value)
            button_group.addButton(radio)
            buttons.append(radio)
            layout.addWidget(radio)

        # Option for custom value
        custom_layout = QHBoxLayout()
        custom_radio = QRadioButton("Muu:")
        custom_radio.setProperty('value', None)
        button_group.addButton(custom_radio)
        custom_layout.addWidget(custom_radio)

        custom_edit = QLineEdit()
        custom_edit.setEnabled(False)
        custom_layout.addWidget(custom_edit)
        layout.addLayout(custom_layout)

        # Enable custom edit when custom radio is selected
        def on_toggle(checked):
            custom_edit.setEnabled(checked)
            if checked:
                custom_edit.setFocus()

        custom_radio.toggled.connect(on_toggle)

        # Select first option by default
        if buttons:
            buttons[0].setChecked(True)

        # Store references
        self.field_groups[conflict.field] = {
            'button_group': button_group,
            'custom_radio': custom_radio,
            'custom_edit': custom_edit
        }

        return group

    def _get_source_name(self, source: InfoSource) -> str:
        """Get human-readable source name."""
        names = {
            InfoSource.TAG: "Tag",
            InfoSource.FILENAME: "Failinimi",
            InfoSource.DIRECTORY: "Kataloog",
            InfoSource.ACOUSTID: "AcoustID",
            InfoSource.MUSICBRAINZ: "MusicBrainz",
            InfoSource.USER: "Kasutaja"
        }
        return names.get(source, str(source))

    def _on_apply(self):
        """Handle apply button click."""
        for field, widgets in self.field_groups.items():
            button_group = widgets['button_group']
            custom_radio = widgets['custom_radio']
            custom_edit = widgets['custom_edit']

            checked_button = button_group.checkedButton()
            if checked_button:
                if checked_button == custom_radio:
                    # Use custom value
                    value = custom_edit.text()
                else:
                    # Use selected value
                    value = checked_button.property('value')

                self.resolutions[field] = value

        self.accept()

    def get_resolutions(self) -> dict:
        """Get the resolved values."""
        return self.resolutions


class BatchConflictDialog(QDialog):
    """Dialog for resolving conflicts for multiple tracks at once."""

    def __init__(self, tracks_with_conflicts: list[tuple[Track, list[Conflict]]], parent=None):
        super().__init__(parent)
        self.tracks_with_conflicts = tracks_with_conflicts
        self.all_resolutions = {}  # track_path -> {field -> value}
        self.current_index = 0

        self._setup_ui()
        self._show_current()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Lahenda konfliktid")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Progress info
        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.progress_label)

        # Container for current conflict dialog content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        layout.addWidget(self.content_widget)

        # Navigation buttons
        nav_layout = QHBoxLayout()

        self.skip_btn = QPushButton("Jäta vahele")
        self.skip_btn.clicked.connect(self._on_skip)
        nav_layout.addWidget(self.skip_btn)

        nav_layout.addStretch()

        self.prev_btn = QPushButton("Eelmine")
        self.prev_btn.clicked.connect(self._on_prev)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Järgmine")
        self.next_btn.clicked.connect(self._on_next)
        nav_layout.addWidget(self.next_btn)

        self.finish_btn = QPushButton("Lõpeta")
        self.finish_btn.clicked.connect(self.accept)
        self.finish_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        nav_layout.addWidget(self.finish_btn)

        layout.addLayout(nav_layout)

    def _show_current(self):
        """Show the current track's conflicts."""
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total = len(self.tracks_with_conflicts)
        self.progress_label.setText(f"Fail {self.current_index + 1}/{total}")

        # Update button states
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < total - 1)

        if self.current_index < total:
            track, conflicts = self.tracks_with_conflicts[self.current_index]

            # Create embedded conflict resolution UI
            track_label = QLabel(f"Fail: {track.filename}")
            track_label.setWordWrap(True)
            self.content_layout.addWidget(track_label)

            # Add conflict groups (simplified version)
            for conflict in conflicts:
                group = self._create_conflict_group(track, conflict)
                self.content_layout.addWidget(group)

            self.content_layout.addStretch()

    def _create_conflict_group(self, track: Track, conflict: Conflict) -> QGroupBox:
        """Create conflict resolution group."""
        # Similar to ConflictDialog but stores in batch resolutions
        field_names = {
            'artist': 'Esitaja',
            'album': 'Album',
            'title': 'Pealkiri',
            'year': 'Aasta'
        }

        group = QGroupBox(field_names.get(conflict.field, conflict.field))
        layout = QVBoxLayout(group)

        button_group = QButtonGroup(group)

        for source, value in conflict.values.items():
            radio = QRadioButton(f"{source.value}: {value}")
            radio.setProperty('track_path', str(track.file_path))
            radio.setProperty('field', conflict.field)
            radio.setProperty('value', value)
            radio.toggled.connect(self._on_selection_changed)
            button_group.addButton(radio)
            layout.addWidget(radio)

        # Select first by default
        if button_group.buttons():
            button_group.buttons()[0].setChecked(True)

        return group

    def _on_selection_changed(self, checked: bool):
        """Handle selection change."""
        if checked:
            sender = self.sender()
            track_path = sender.property('track_path')
            field = sender.property('field')
            value = sender.property('value')

            if track_path not in self.all_resolutions:
                self.all_resolutions[track_path] = {}
            self.all_resolutions[track_path][field] = value

    def _on_skip(self):
        """Skip current track."""
        self._on_next()

    def _on_prev(self):
        """Go to previous track."""
        if self.current_index > 0:
            self.current_index -= 1
            self._show_current()

    def _on_next(self):
        """Go to next track."""
        if self.current_index < len(self.tracks_with_conflicts) - 1:
            self.current_index += 1
            self._show_current()

    def get_all_resolutions(self) -> dict:
        """Get all resolutions."""
        return self.all_resolutions
