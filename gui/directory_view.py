"""View for processing a directory of MP3 files."""

from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QSplitter,
    QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject

from models.track import Track
from models.album import Album
from core.analyzer import TrackAnalyzer
from artwork.fetcher import ArtworkFetcher
from .widgets.file_list import FileListWidget
from .widgets.tag_editor import TagEditorWidget
from .widgets.artwork_preview import ArtworkPreviewWidget
from .conflict_dialog import ConflictDialog, BatchConflictDialog
from .artwork_picker import ArtworkPickerDialog
from .preview_dialog import PreviewDialog
from config import get_config


class AnalysisWorker(QObject):
    """Worker for background directory analysis."""

    progress = Signal(int, str)  # (percentage, current_file)
    finished = Signal(Album)
    error = Signal(str)

    def __init__(self, analyzer: TrackAnalyzer, directory: Path):
        super().__init__()
        self.analyzer = analyzer
        self.directory = directory

    def run(self):
        """Perform the analysis."""
        try:
            album = self.analyzer.analyze_directory(self.directory)

            # Emit progress for each track (for UI feedback)
            total = len(album.tracks)
            for i, track in enumerate(album.tracks):
                progress = int((i + 1) / total * 100) if total > 0 else 100
                self.progress.emit(progress, track.filename)

            self.finished.emit(album)

        except Exception as e:
            self.error.emit(str(e))


class DirectoryView(QWidget):
    """View for editing MP3 files in a directory."""

    directory_saved = Signal(Album)  # Emitted when directory is saved

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.analyzer = TrackAnalyzer()
        self.artwork_fetcher = ArtworkFetcher()
        self._current_album: Optional[Album] = None
        self._analysis_thread: Optional[QThread] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the view UI."""
        layout = QVBoxLayout(self)

        # Directory selection
        dir_layout = QHBoxLayout()

        self.dir_label = QLabel("Kataloogi pole valitud")
        self.dir_label.setStyleSheet("font-weight: bold;")
        dir_layout.addWidget(self.dir_label, stretch=1)

        self.browse_btn = QPushButton("Vali kataloog...")
        self.browse_btn.clicked.connect(self._on_browse)
        dir_layout.addWidget(self.browse_btn)

        layout.addLayout(dir_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Album info
        self.album_info = QGroupBox("Albumi info")
        album_layout = QHBoxLayout(self.album_info)

        self.artist_label = QLabel("Esitaja: -")
        album_layout.addWidget(self.artist_label)

        self.album_label = QLabel("Album: -")
        album_layout.addWidget(self.album_label)

        self.year_label = QLabel("Aasta: -")
        album_layout.addWidget(self.year_label)

        self.count_label = QLabel("Lugusid: -")
        album_layout.addWidget(self.count_label)

        album_layout.addStretch()
        layout.addWidget(self.album_info)

        # Main content (splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - file list
        self.file_list = FileListWidget()
        self.file_list.file_selected.connect(self._on_file_selected)
        splitter.addWidget(self.file_list)

        # Middle - tag editor
        self.tag_editor = TagEditorWidget()
        self.tag_editor.tags_changed.connect(self._on_tags_changed)
        splitter.addWidget(self.tag_editor)

        # Right side - artwork
        self.artwork_preview = ArtworkPreviewWidget()
        self.artwork_preview.artwork_selected.connect(self._on_artwork_selected)
        self.artwork_preview.search_requested.connect(self._on_artwork_search)
        splitter.addWidget(self.artwork_preview)

        splitter.setSizes([250, 350, 250])
        layout.addWidget(splitter, stretch=1)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.resolve_btn = QPushButton("Lahenda konfliktid")
        self.resolve_btn.clicked.connect(self._on_resolve_conflicts)
        self.resolve_btn.setEnabled(False)
        button_layout.addWidget(self.resolve_btn)

        self.apply_album_btn = QPushButton("Rakenda kõigile")
        self.apply_album_btn.clicked.connect(self._on_apply_to_all)
        self.apply_album_btn.setEnabled(False)
        self.apply_album_btn.setToolTip("Rakenda praegused metaandmed kõigile lugudele")
        button_layout.addWidget(self.apply_album_btn)

        button_layout.addStretch()

        self.save_btn = QPushButton("Salvesta kõik")
        self.save_btn.clicked.connect(self._on_save_all)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _on_browse(self):
        """Handle browse button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Vali kataloog MP3 failidega",
            ""
        )

        if directory:
            self.load_directory(Path(directory))

    def load_directory(self, directory: Path):
        """Load and analyze a directory of MP3 files."""
        if not directory.exists():
            QMessageBox.warning(self, "Viga", f"Kataloogi ei leitud: {directory}")
            return

        self.dir_label.setText(directory.name)
        self.status_label.setText("Analüüsin faile...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        # Clear current state
        self._current_album = None
        self.file_list.set_tracks([])
        self.tag_editor.set_track(None)
        self.artwork_preview.clear()

        try:
            # Analyze directory
            self._current_album = self.analyzer.analyze_directory(directory)

            if not self._current_album.tracks:
                QMessageBox.information(
                    self, "Info",
                    "Kataloogis ei leitud MP3 faile."
                )
                self.progress_bar.hide()
                return

            # Update UI
            self._update_album_info()
            self.file_list.set_tracks(self._current_album.tracks)

            # Select first track
            if self._current_album.tracks:
                first_track = self._current_album.tracks[0]
                self.file_list.select_track(first_track)
                self._on_file_selected(first_track)

            # Check for tracks with conflicts
            tracks_with_conflicts = [
                t for t in self._current_album.tracks
                if self.analyzer.matcher.needs_user_input(t)
            ]

            if tracks_with_conflicts:
                self.resolve_btn.setEnabled(True)
                self.status_label.setText(
                    f"Leiti {len(tracks_with_conflicts)} faili konfliktidega"
                )
            else:
                self.status_label.setText(f"Laetud {len(self._current_album.tracks)} faili")

            self.apply_album_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Viga", f"Kataloogi analüüsimine ebaõnnestus: {e}")
            self.status_label.setText(f"Viga: {e}")

        finally:
            self.progress_bar.hide()

    def _update_album_info(self):
        """Update album info display."""
        if not self._current_album:
            return

        album = self._current_album
        self.artist_label.setText(f"Esitaja: {album.artist or '-'}")
        self.album_label.setText(f"Album: {album.album_name or '-'}")
        self.year_label.setText(f"Aasta: {album.year or '-'}")
        self.count_label.setText(f"Lugusid: {album.track_count}")

    def _on_file_selected(self, track: Track):
        """Handle file selection."""
        self.tag_editor.set_track(track)
        self.artwork_preview.set_artwork(
            track.new_artwork or track.current_artwork
        )

    def _on_tags_changed(self, track: Track):
        """Handle tag changes."""
        self.file_list.update_track(track)
        self._update_save_button()
        self.status_label.setText("Muudatused salvestamata")

    def _on_artwork_selected(self, artwork_data: bytes):
        """Handle artwork selection."""
        track = self.file_list.get_selected_track()
        if track:
            if artwork_data:
                track.new_artwork = artwork_data
            else:
                track.new_artwork = b''
            track.has_changes = True
            self.file_list.update_track(track)
            self._update_save_button()

    def _on_artwork_search(self, url_or_artist: str, source_or_album: str):
        """Handle artwork search request."""
        if not self._current_album:
            return

        artist = self._current_album.artist or ""
        album = self._current_album.album_name or ""

        # Get title from selected track if available
        title = ""
        selected_track = self.file_list.get_selected_track()
        if selected_track:
            info = selected_track.resolved_info or selected_track.tag_info
            if info and info.title:
                title = info.title

        # If URL provided, download directly
        if url_or_artist.startswith('http'):
            self.status_label.setText("Laen pilti...")
            try:
                from artwork.providers.base import ArtworkResult
                result = ArtworkResult(image_url=url_or_artist, source=source_or_album)
                image_data = self.artwork_fetcher.download(result)
                if image_data:
                    self.artwork_preview.set_artwork(image_data)
                    self._on_artwork_selected(image_data)
                self.status_label.setText("")
            except Exception as e:
                self.status_label.setText(f"Viga: {e}")
            return

        # Open artwork picker dialog
        dialog = ArtworkPickerDialog(artist, album, title, self)
        if dialog.exec():
            artwork = dialog.get_selected_artwork()
            if artwork:
                # Ask if should apply to all tracks
                reply = QMessageBox.question(
                    self,
                    "Rakenda kõigile?",
                    "Kas soovid selle pildi rakendada kõigile lugudele albumis?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self._current_album.set_artwork_for_all(artwork)
                    self.file_list._refresh_list()
                else:
                    self.artwork_preview.set_artwork(artwork)
                    self._on_artwork_selected(artwork)

                self._update_save_button()

    def _on_resolve_conflicts(self):
        """Open conflict resolution dialog."""
        if not self._current_album:
            return

        # Find tracks with conflicts
        tracks_with_conflicts = []
        for track in self._current_album.tracks:
            conflicts = self.analyzer.matcher.find_conflicts(track)
            if conflicts:
                tracks_with_conflicts.append((track, conflicts))

        if not tracks_with_conflicts:
            QMessageBox.information(
                self, "Info",
                "Konflikte ei leitud."
            )
            return

        # Show batch conflict dialog
        dialog = BatchConflictDialog(tracks_with_conflicts, self)
        if dialog.exec():
            resolutions = dialog.get_all_resolutions()

            # Apply resolutions
            for track_path, fields in resolutions.items():
                for track in self._current_album.tracks:
                    if str(track.file_path) == track_path:
                        for field, value in fields.items():
                            self.analyzer.resolve_conflict(track, field, value)
                        break

            # Refresh display
            self.file_list._refresh_list()
            self._update_save_button()
            self.resolve_btn.setEnabled(False)

    def _on_apply_to_all(self):
        """Apply current track's metadata to all tracks."""
        current_track = self.file_list.get_selected_track()
        if not current_track or not current_track.resolved_info:
            QMessageBox.warning(
                self, "Hoiatus",
                "Palun vali kõigepealt lugu ja täida metaandmed."
            )
            return

        reply = QMessageBox.question(
            self,
            "Kinnitus",
            "Kas oled kindel, et soovid praeguse loo albumi, "
            "esitaja ja aasta info rakendada kõigile lugudele?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            info = current_track.resolved_info
            self._current_album.apply_to_all_tracks(info)
            self.file_list._refresh_list()
            self._update_save_button()
            self.status_label.setText("Info rakendatud kõigile lugudele")

    def _update_save_button(self):
        """Update save button state."""
        if self._current_album:
            has_changes = any(t.has_changes for t in self._current_album.tracks)
            self.save_btn.setEnabled(has_changes)

    def _on_save_all(self):
        """Save all changes."""
        if not self._current_album:
            return

        tracks_with_changes = self._current_album.get_tracks_with_changes()
        if not tracks_with_changes:
            QMessageBox.information(
                self, "Info",
                "Muudatusi pole salvestada."
            )
            return

        # Show preview if configured
        if self.config.show_preview:
            dialog = PreviewDialog(tracks_with_changes, self)
            if not dialog.exec():
                return
            tracks_with_changes = dialog.get_selected_tracks()

        if not tracks_with_changes:
            return

        # Save changes
        self.status_label.setText("Salvestan...")
        self.progress_bar.show()
        self.progress_bar.setRange(0, len(tracks_with_changes))

        success_count = 0
        error_count = 0

        for i, track in enumerate(tracks_with_changes):
            self.progress_bar.setValue(i + 1)

            try:
                if self.analyzer.apply_changes(track):
                    success_count += 1
                    track.current_artwork = track.new_artwork
                    track.new_artwork = None
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                track.error_message = str(e)

        self.progress_bar.hide()
        self.file_list._refresh_list()
        self._update_save_button()

        if error_count > 0:
            QMessageBox.warning(
                self,
                "Hoiatus",
                f"Salvestatud {success_count} faili.\n"
                f"Vigu: {error_count}"
            )
        else:
            QMessageBox.information(
                self,
                "Valmis",
                f"Salvestatud {success_count} faili."
            )

        self.status_label.setText(f"Salvestatud {success_count} faili")
        self.directory_saved.emit(self._current_album)

    def get_current_album(self) -> Optional[Album]:
        """Get the current album."""
        return self._current_album
