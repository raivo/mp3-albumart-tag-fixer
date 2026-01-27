"""Tag editor widget for editing track metadata."""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QLabel, QPushButton, QComboBox,
    QGroupBox
)
from PySide6.QtCore import Signal

from models.track import Track, TrackInfo, InfoSource
from utils.translations import tr


class TagEditorWidget(QWidget):
    """Widget for editing MP3 tag metadata."""

    tags_changed = Signal(Track)  # Emitted when tags are modified

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_track: Optional[Track] = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel(tr('metadata'))
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # Form for metadata
        self.form_group = QGroupBox(tr('tag_info'))
        self.form_layout = QFormLayout(self.form_group)

        # Artist
        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText(tr('artist_placeholder'))
        self.artist_edit.textChanged.connect(self._on_field_changed)
        self.artist_label = QLabel(tr('artist') + ":")
        self.form_layout.addRow(self.artist_label, self.artist_edit)

        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr('title_placeholder'))
        self.title_edit.textChanged.connect(self._on_field_changed)
        self.title_field_label = QLabel(tr('title') + ":")
        self.form_layout.addRow(self.title_field_label, self.title_edit)

        # Album
        self.album_edit = QLineEdit()
        self.album_edit.setPlaceholderText(tr('album_placeholder'))
        self.album_edit.textChanged.connect(self._on_field_changed)
        self.album_label = QLabel(tr('album') + ":")
        self.form_layout.addRow(self.album_label, self.album_edit)

        # Year
        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 2030)
        self.year_spin.setSpecialValueText(tr('year_not_set'))
        self.year_spin.valueChanged.connect(self._on_field_changed)
        self.year_label = QLabel(tr('year') + ":")
        self.form_layout.addRow(self.year_label, self.year_spin)

        # Track number
        track_layout = QHBoxLayout()
        self.track_spin = QSpinBox()
        self.track_spin.setRange(0, 999)
        self.track_spin.setSpecialValueText("-")
        self.track_spin.valueChanged.connect(self._on_field_changed)
        track_layout.addWidget(self.track_spin)

        track_layout.addWidget(QLabel("/"))

        self.total_tracks_spin = QSpinBox()
        self.total_tracks_spin.setRange(0, 999)
        self.total_tracks_spin.setSpecialValueText("-")
        self.total_tracks_spin.valueChanged.connect(self._on_field_changed)
        track_layout.addWidget(self.total_tracks_spin)
        track_layout.addStretch()

        self.track_label = QLabel(tr('track') + ":")
        self.form_layout.addRow(self.track_label, track_layout)

        # Genre
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        self.genre_combo.addItems([
            "", "Rock", "Pop", "Electronic", "Classical", "Jazz",
            "Hip-Hop", "R&B", "Country", "Folk", "Metal", "Punk",
            "Blues", "Reggae", "Soul", "Funk", "Disco", "House",
            "Techno", "Trance", "Ambient", "Alternative", "Indie"
        ])
        self.genre_combo.currentTextChanged.connect(self._on_field_changed)
        self.genre_label = QLabel(tr('genre') + ":")
        self.form_layout.addRow(self.genre_label, self.genre_combo)

        layout.addWidget(self.form_group)

        # Source info
        self.source_group = QGroupBox(tr('data_sources'))
        source_layout = QVBoxLayout(self.source_group)
        self.source_labels = {}

        for source in ['tag', 'filename', 'directory', 'acoustid']:
            label = QLabel(f"{source}: -")
            label.setWordWrap(True)
            label.setStyleSheet("color: gray; font-size: 11px;")
            self.source_labels[source] = label
            source_layout.addWidget(label)

        layout.addWidget(self.source_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.reset_btn = QPushButton(tr('reset'))
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)

        self.apply_btn = QPushButton(tr('apply'))
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

        layout.addStretch()

        # Initially disabled
        self.setEnabled(False)

    def set_track(self, track: Optional[Track]):
        """Set the track to edit."""
        self._current_track = track

        if track is None:
            self.setEnabled(False)
            self._clear_fields()
            return

        self.setEnabled(True)
        self._update_fields()
        self._update_source_info()

    def _update_fields(self):
        """Update fields from current track."""
        if not self._current_track:
            return

        # Use resolved info if available, otherwise tag info
        info = self._current_track.resolved_info or self._current_track.tag_info

        # Block signals while updating
        self._block_signals(True)

        if info:
            self.artist_edit.setText(info.artist or "")
            self.title_edit.setText(info.title or "")
            self.album_edit.setText(info.album or "")
            self.year_spin.setValue(info.year or 0)
            self.track_spin.setValue(info.track_number or 0)
            self.total_tracks_spin.setValue(info.total_tracks or 0)
            self.genre_combo.setCurrentText(info.genre or "")
        else:
            self._clear_fields()

        self._block_signals(False)

    def _clear_fields(self):
        """Clear all fields."""
        self._block_signals(True)
        self.artist_edit.clear()
        self.title_edit.clear()
        self.album_edit.clear()
        self.year_spin.setValue(0)
        self.track_spin.setValue(0)
        self.total_tracks_spin.setValue(0)
        self.genre_combo.setCurrentText("")
        self._block_signals(False)

    def _block_signals(self, block: bool):
        """Block or unblock signals from all fields."""
        self.artist_edit.blockSignals(block)
        self.title_edit.blockSignals(block)
        self.album_edit.blockSignals(block)
        self.year_spin.blockSignals(block)
        self.track_spin.blockSignals(block)
        self.total_tracks_spin.blockSignals(block)
        self.genre_combo.blockSignals(block)

    def _update_source_info(self):
        """Update source information labels."""
        if not self._current_track:
            for label in self.source_labels.values():
                label.setText("-")
            return

        track = self._current_track

        # Tag info
        if track.tag_info and track.tag_info.artist:
            self.source_labels['tag'].setText(
                f"{tr('source_tag')}: {track.tag_info.artist} - {track.tag_info.title or '?'}"
            )
        else:
            self.source_labels['tag'].setText(f"{tr('source_tag')}: {tr('missing')}")

        # Filename info
        if track.filename_info and track.filename_info.artist:
            self.source_labels['filename'].setText(
                f"{tr('source_filename')}: {track.filename_info.artist} - {track.filename_info.title or '?'}"
            )
        else:
            self.source_labels['filename'].setText(f"{tr('source_filename')}: {track.filename}")

        # Directory info
        if track.directory_info and (track.directory_info.artist or track.directory_info.album):
            self.source_labels['directory'].setText(
                f"{tr('source_directory')}: {track.directory_info.artist or '?'} - {track.directory_info.album or '?'}"
            )
        else:
            self.source_labels['directory'].setText(f"{tr('source_directory')}: {track.directory.name}")

        # AcoustID info
        if track.acoustid_info and track.acoustid_info.artist:
            confidence = f"({track.acoustid_info.confidence:.0%})"
            self.source_labels['acoustid'].setText(
                f"{tr('source_acoustid')}: {track.acoustid_info.artist} - {track.acoustid_info.title or '?'} {confidence}"
            )
        else:
            self.source_labels['acoustid'].setText(f"{tr('source_acoustid')}: {tr('not_detected')}")

    def _on_field_changed(self):
        """Handle field value change."""
        if not self._current_track:
            return

        # Create or update resolved info
        if self._current_track.resolved_info is None:
            self._current_track.resolved_info = TrackInfo(source=InfoSource.USER)

        info = self._current_track.resolved_info
        info.artist = self.artist_edit.text() or None
        info.title = self.title_edit.text() or None
        info.album = self.album_edit.text() or None
        info.year = self.year_spin.value() if self.year_spin.value() > 0 else None
        info.track_number = self.track_spin.value() if self.track_spin.value() > 0 else None
        info.total_tracks = self.total_tracks_spin.value() if self.total_tracks_spin.value() > 0 else None
        info.genre = self.genre_combo.currentText() or None

        self._current_track.has_changes = True

    def _on_reset(self):
        """Reset to original tag values."""
        if self._current_track and self._current_track.tag_info:
            self._current_track.resolved_info = TrackInfo(source=InfoSource.USER)

            # Copy from original tag info
            for field in ['artist', 'title', 'album', 'year', 'track_number', 'total_tracks', 'genre']:
                setattr(self._current_track.resolved_info, field,
                       getattr(self._current_track.tag_info, field))

            self._current_track.has_changes = False
            self._update_fields()
            self.tags_changed.emit(self._current_track)

    def _on_apply(self):
        """Emit signal that tags should be applied."""
        if self._current_track:
            self.tags_changed.emit(self._current_track)

    def get_current_info(self) -> Optional[TrackInfo]:
        """Get the current edited info."""
        if self._current_track:
            return self._current_track.resolved_info
        return None

    def update_translations(self):
        """Update all translatable text."""
        self.title_label.setText(tr('metadata'))
        self.form_group.setTitle(tr('tag_info'))
        self.artist_label.setText(tr('artist') + ":")
        self.artist_edit.setPlaceholderText(tr('artist_placeholder'))
        self.title_field_label.setText(tr('title') + ":")
        self.title_edit.setPlaceholderText(tr('title_placeholder'))
        self.album_label.setText(tr('album') + ":")
        self.album_edit.setPlaceholderText(tr('album_placeholder'))
        self.year_label.setText(tr('year') + ":")
        self.year_spin.setSpecialValueText(tr('year_not_set'))
        self.track_label.setText(tr('track') + ":")
        self.genre_label.setText(tr('genre') + ":")
        self.source_group.setTitle(tr('data_sources'))
        self.reset_btn.setText(tr('reset'))
        self.apply_btn.setText(tr('apply'))
        self._update_source_info()
