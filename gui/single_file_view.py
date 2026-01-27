"""View for processing a single MP3 file."""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QSplitter,
    QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal

from models.track import Track
from core.analyzer import TrackAnalyzer
from artwork.fetcher import ArtworkFetcher
from .widgets.tag_editor import TagEditorWidget
from .widgets.artwork_preview import ArtworkPreviewWidget
from .conflict_dialog import ConflictDialog
from .artwork_picker import ArtworkPickerDialog
from .preview_dialog import PreviewDialog
from config import get_config
from utils.translations import tr


class SingleFileView(QWidget):
    """View for editing a single MP3 file."""

    file_saved = Signal(Track)  # Emitted when file is saved

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.analyzer = TrackAnalyzer()
        self.artwork_fetcher = ArtworkFetcher()
        self._current_track: Optional[Track] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the view UI."""
        layout = QVBoxLayout(self)

        # File selection
        file_layout = QHBoxLayout()

        self.file_label = QLabel(tr('no_file_selected'))
        self.file_label.setStyleSheet("font-weight: bold;")
        file_layout.addWidget(self.file_label, stretch=1)

        self.browse_btn = QPushButton(tr('select_file'))
        self.browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.browse_btn)

        layout.addLayout(file_layout)

        # Progress bar (for analysis)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Main content (splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - tag editor
        self.tag_editor = TagEditorWidget()
        self.tag_editor.tags_changed.connect(self._on_tags_changed)
        splitter.addWidget(self.tag_editor)

        # Right side - artwork
        self.artwork_preview = ArtworkPreviewWidget()
        self.artwork_preview.artwork_selected.connect(self._on_artwork_selected)
        self.artwork_preview.search_requested.connect(self._on_artwork_search)
        splitter.addWidget(self.artwork_preview)

        splitter.setSizes([400, 300])
        layout.addWidget(splitter, stretch=1)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.analyze_btn = QPushButton(tr('analyze_again'))
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setEnabled(False)
        button_layout.addWidget(self.analyze_btn)

        button_layout.addStretch()

        self.save_btn = QPushButton(tr('save'))
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _on_browse(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr('select_mp3_file'),
            "",
            f"{tr('mp3_files')};;{tr('all_files')}"
        )

        if file_path:
            self.load_file(Path(file_path))

    def load_file(self, file_path: Path):
        """Load and analyze an MP3 file."""
        if not file_path.exists():
            QMessageBox.warning(self, tr('error'), f"{tr('file_not_found')}: {file_path}")
            return

        self.file_label.setText(file_path.name)
        self.status_label.setText(tr('analyzing_file'))
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate

        try:
            # Analyze the file
            self._current_track = self.analyzer.analyze_file(file_path)

            # Check for conflicts
            if self.analyzer.matcher.needs_user_input(self._current_track):
                self._show_conflict_dialog()
            else:
                # Auto-resolve
                if self._current_track.resolved_info is None:
                    self._current_track.resolved_info = self.analyzer.matcher.auto_resolve(
                        self._current_track
                    )

            # Update UI
            self.tag_editor.set_track(self._current_track)
            self.artwork_preview.set_artwork(self._current_track.current_artwork)

            self.analyze_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.status_label.setText(tr('file_loaded'))

        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"{tr('analysis_failed')}: {e}")
            self.status_label.setText(f"{tr('error')}: {e}")

        finally:
            self.progress_bar.hide()

    def _show_conflict_dialog(self):
        """Show conflict resolution dialog."""
        conflicts = self.analyzer.matcher.find_conflicts(self._current_track)

        if conflicts:
            dialog = ConflictDialog(self._current_track, conflicts, self)
            if dialog.exec():
                # Apply resolutions
                resolutions = dialog.get_resolutions()
                for field, value in resolutions.items():
                    self.analyzer.resolve_conflict(self._current_track, field, value)

    def _on_analyze(self):
        """Re-analyze the current file."""
        if self._current_track:
            self.load_file(self._current_track.file_path)

    def _on_tags_changed(self, track: Track):
        """Handle tag changes."""
        self._current_track = track
        self.save_btn.setEnabled(True)
        self.status_label.setText(tr('changes_unsaved'))

    def _on_artwork_selected(self, artwork_data: bytes):
        """Handle artwork selection."""
        if self._current_track:
            if artwork_data:
                self._current_track.new_artwork = artwork_data
            else:
                self._current_track.new_artwork = b''  # Mark for removal
            self._current_track.has_changes = True
            self.save_btn.setEnabled(True)
            self.status_label.setText(tr('changes_unsaved'))

    def _on_artwork_search(self, url_or_artist: str, source_or_album: str):
        """Handle artwork search request."""
        if not self._current_track:
            return

        # Get artist, album and title from resolved info
        info = self._current_track.resolved_info or self._current_track.tag_info
        artist = info.artist if info else ""
        album = info.album if info else ""
        title = info.title if info else ""

        # If URL provided, download directly
        if url_or_artist.startswith('http'):
            self.status_label.setText(tr('loading_image'))
            try:
                # Find provider by source name
                from artwork.providers.base import ArtworkResult
                result = ArtworkResult(image_url=url_or_artist, source=source_or_album)
                image_data = self.artwork_fetcher.download(result)
                if image_data:
                    self.artwork_preview.set_artwork(image_data)
                    self._on_artwork_selected(image_data)
                self.status_label.setText("")
            except Exception as e:
                self.status_label.setText(f"{tr('error')}: {e}")
            return

        # Open artwork picker dialog
        dialog = ArtworkPickerDialog(artist, album, title, self)
        if dialog.exec():
            artwork = dialog.get_selected_artwork()
            if artwork:
                self.artwork_preview.set_artwork(artwork)
                self._on_artwork_selected(artwork)

    def _on_save(self):
        """Save changes to the file."""
        if not self._current_track:
            return

        # Show preview if configured
        if self.config.show_preview:
            dialog = PreviewDialog([self._current_track], self)
            if not dialog.exec():
                return

        self.status_label.setText(tr('saving'))
        self.save_btn.setEnabled(False)

        try:
            success = self.analyzer.apply_changes(self._current_track)

            if success:
                self.status_label.setText(tr('saved'))
                self._current_track.has_changes = False
                self.file_saved.emit(self._current_track)

                # Reload to verify
                self._current_track.current_artwork = self._current_track.new_artwork
                self._current_track.new_artwork = None
                self.artwork_preview.set_artwork(self._current_track.current_artwork)

            else:
                self.status_label.setText(tr('save_failed'))
                self.save_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"{tr('save_failed')}: {e}")
            self.status_label.setText(f"{tr('error')}: {e}")
            self.save_btn.setEnabled(True)

    def get_current_track(self) -> Optional[Track]:
        """Get the current track."""
        return self._current_track

    def update_translations(self):
        """Update all translatable text."""
        if not self._current_track:
            self.file_label.setText(tr('no_file_selected'))
        self.browse_btn.setText(tr('select_file'))
        self.analyze_btn.setText(tr('analyze_again'))
        self.save_btn.setText(tr('save'))
        self.tag_editor.update_translations()
        self.artwork_preview.update_translations()
