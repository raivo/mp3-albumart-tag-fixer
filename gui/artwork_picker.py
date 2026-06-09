"""Dialog for searching and selecting album artwork."""

from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QWidget,
    QGridLayout, QFrame, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer, QRunnable, QThreadPool
from PySide6.QtGui import QPixmap, QImage

from artwork.fetcher import ArtworkFetcher
from artwork.providers.base import ArtworkResult


class SearchWorker(QObject):
    """Worker for background artwork search."""

    finished = Signal(list)  # List of (ArtworkResult, thumbnail_bytes)
    progress = Signal(int)
    error = Signal(str)

    def __init__(self, fetcher: ArtworkFetcher, artist: str, album: str):
        super().__init__()
        self.fetcher = fetcher
        self.artist = artist
        self.album = album
        self._cancelled = False

    def cancel(self):
        """Cancel the search."""
        self._cancelled = True

    def run(self):
        """Perform the search."""
        try:
            if self._cancelled:
                return

            results = self.fetcher.search(self.artist, self.album)

            if self._cancelled:
                return

            # Download thumbnails
            results_with_thumbs = []
            for i, result in enumerate(results[:12]):  # Limit to 12 results
                if self._cancelled:
                    return

                thumb = self.fetcher.get_thumbnail(result)
                results_with_thumbs.append((result, thumb))

                if not self._cancelled:
                    self.progress.emit(int((i + 1) / min(len(results), 12) * 100))

            if not self._cancelled:
                self.finished.emit(results_with_thumbs)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))


class ThumbnailLoader(QRunnable):
    """Loads a single thumbnail in the thread pool."""

    class Signals(QObject):
        loaded = Signal(int, bytes)  # (loader_id, data)
        failed = Signal(int)         # (loader_id,)

    def __init__(self, loader_id: int, fetcher: ArtworkFetcher, result: ArtworkResult):
        super().__init__()
        self.loader_id = loader_id
        self.fetcher = fetcher
        self.result = result
        self.signals = ThumbnailLoader.Signals()
        # setAutoDelete(False) so Python keeps ownership and signals stay alive
        self.setAutoDelete(False)

    def run(self):
        try:
            data = self.fetcher.get_thumbnail(self.result)
            if data:
                self.signals.loaded.emit(self.loader_id, data)
            else:
                self.signals.failed.emit(self.loader_id)
        except Exception:
            self.signals.failed.emit(self.loader_id)


class ArtworkPickerDialog(QDialog):
    """Dialog for searching and selecting album artwork."""

    def __init__(self, artist: str = "", album: str = "", title: str = "", parent=None):
        super().__init__(parent)
        self.fetcher = ArtworkFetcher()
        self.initial_artist = artist
        self.initial_album = album
        self.initial_title = title
        self.search_results: list[ArtworkResult] = []
        self.selected_artwork: Optional[bytes] = None
        self._is_closed = False

        self._search_thread: Optional[QThread] = None
        self._search_worker: Optional[SearchWorker] = None
        self._search_generation: int = 0  # incremented on each new search
        self._active_loaders: dict[int, ThumbnailLoader] = {}  # keep loaders alive
        self._loader_id_to_generation: dict[int, int] = {}
        self._next_loader_id: int = 0

        self._setup_ui()

        # Auto-search if artist and album provided (with small delay for UI to show)
        if artist and album:
            QTimer.singleShot(100, self._on_search)

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Otsi kaanepilti")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Search form
        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Esitaja:"))
        self.artist_edit = QLineEdit(self.initial_artist)
        self.artist_edit.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.artist_edit)

        search_layout.addWidget(QLabel("Album:"))
        self.album_edit = QLineEdit(self.initial_album)
        self.album_edit.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.album_edit)

        self.search_btn = QPushButton("Otsi")
        self.search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Custom search
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Või otsi:"))
        self.custom_edit = QLineEdit()
        self.custom_edit.setPlaceholderText("Sisesta otsisõnad (nt 'Smilers album cover')")

        # Pre-fill custom search with available info
        search_parts = []
        if self.initial_artist:
            search_parts.append(self.initial_artist)
        if self.initial_album:
            search_parts.append(self.initial_album)
        elif self.initial_title:
            search_parts.append(self.initial_title)
        if search_parts:
            search_parts.append("album cover")
            self.custom_edit.setText(" ".join(search_parts))

        self.custom_edit.returnPressed.connect(self._on_custom_search)
        custom_layout.addWidget(self.custom_edit)

        custom_search_btn = QPushButton("Otsi")
        custom_search_btn.clicked.connect(self._on_custom_search)
        custom_layout.addWidget(custom_search_btn)

        layout.addLayout(custom_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Results scroll area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)

        self.results_widget = QWidget()
        self.results_layout = QGridLayout(self.results_widget)
        self.results_layout.setSpacing(10)

        self.results_scroll.setWidget(self.results_widget)
        layout.addWidget(self.results_scroll)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Tühista")
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        self.select_btn = QPushButton("Vali")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self._on_select)
        self.select_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.select_btn)

        layout.addLayout(button_layout)

    def _on_cancel(self):
        """Handle cancel button click."""
        self._stop_search()
        self.reject()

    def _on_search(self):
        """Handle search button click."""
        if self._is_closed:
            return

        artist = self.artist_edit.text().strip()
        album = self.album_edit.text().strip()

        if not artist or not album:
            QMessageBox.warning(
                self, "Hoiatus",
                "Palun sisesta nii esitaja kui albumi nimi."
            )
            return

        self._start_search(artist, album)

    def _on_custom_search(self):
        """Handle custom search."""
        if self._is_closed:
            return

        query = self.custom_edit.text().strip()
        if not query:
            return

        # Use web search provider directly
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Otsin...")
        self.search_btn.setEnabled(False)

        try:
            results = self.fetcher.search_custom(query)
            if not self._is_closed:
                self._display_results([(r, None) for r in results[:12]])
        except Exception as e:
            if not self._is_closed:
                QMessageBox.warning(self, "Viga", f"Otsing ebaõnnestus: {e}")
        finally:
            if not self._is_closed:
                self.progress_bar.hide()
                self.search_btn.setEnabled(True)

    def _start_search(self, artist: str, album: str):
        """Start background search."""
        if self._is_closed:
            return

        # Clean up previous search
        self._stop_search()

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Otsin...")
        self.search_btn.setEnabled(False)

        # Create worker and thread
        self._search_thread = QThread()
        self._search_worker = SearchWorker(self.fetcher, artist, album)
        self._search_worker.moveToThread(self._search_thread)
        active_worker = self._search_worker  # capture for closure check

        # Connect signals with queued connection for thread safety
        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.finished.connect(
            lambda results, w=active_worker: self._on_search_finished(results, w),
            Qt.ConnectionType.QueuedConnection
        )
        self._search_worker.progress.connect(
            self._on_progress, Qt.ConnectionType.QueuedConnection
        )
        self._search_worker.error.connect(
            self._on_search_error, Qt.ConnectionType.QueuedConnection
        )
        self._search_thread.finished.connect(self._on_thread_finished)

        # Start
        self._search_thread.start()

    def _on_progress(self, value: int):
        """Handle progress update."""
        if not self._is_closed:
            self.progress_bar.setValue(value)

    def _stop_search(self):
        """Stop any running search."""
        if self._search_worker:
            self._search_worker.cancel()

        if self._search_thread and self._search_thread.isRunning():
            self._search_thread.quit()
            self._search_thread.wait(3000)  # Wait up to 3s; don't force-terminate

        self._search_thread = None
        self._search_worker = None

    def _on_thread_finished(self):
        """Handle thread finished."""
        # Clean up references
        pass

    def _on_search_finished(self, results, worker=None):
        """Handle search completion."""
        if self._is_closed:
            return
        # Ignore results from a superseded search
        if worker is not None and worker is not self._search_worker:
            return

        self.progress_bar.hide()
        self.search_btn.setEnabled(True)

        if results:
            self.status_label.setText(f"Leiti {len(results)} tulemust")
            self._display_results(results)
        else:
            self.status_label.setText("Tulemusi ei leitud")

    def _on_search_error(self, error_msg: str):
        """Handle search error."""
        if self._is_closed:
            return

        self.progress_bar.hide()
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"Viga: {error_msg}")

    def _display_results(self, results: list[tuple[ArtworkResult, Optional[bytes]]]):
        """Display search results."""
        if self._is_closed:
            return

        # Invalidate any pending thumbnail loaders from previous search
        self._search_generation += 1
        self._active_loaders.clear()
        self._loader_id_to_generation.clear()

        # Clear previous results
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.search_results = [r[0] for r in results]

        # Create grid of results
        for i, (result, thumb_data) in enumerate(results):
            row = i // 4
            col = i % 4

            widget = self._create_result_widget(i, result, thumb_data)
            self.results_layout.addWidget(widget, row, col)

    def _create_result_widget(self, index: int, result: ArtworkResult,
                              thumb_data: Optional[bytes]) -> QWidget:
        """Create widget for a single result."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setFixedSize(150, 180)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        frame.setProperty('index', index)
        frame.setProperty('selected', False)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(130, 130)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("background-color: #f0f0f0;")

        if thumb_data:
            self._set_thumb_pixmap(thumb_label, thumb_data)
        else:
            thumb_label.setText("⏳")
            thumb_label.setStyleSheet("color: gray; background-color: #f0f0f0; font-size: 32px;")
            self._load_thumbnail_async(result, thumb_label, self._search_generation)

        layout.addWidget(thumb_label)

        # Source label
        source_label = QLabel(result.source)
        source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        source_label.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(source_label)

        # Click handler
        frame.mousePressEvent = lambda e, idx=index, f=frame: self._on_result_clicked(idx, f)

        return frame

    def _set_thumb_pixmap(self, thumb_label, data: bytes):
        """Set pixmap on a thumbnail label."""
        image = QImage.fromData(data)
        if not image.isNull():
            pixmap = QPixmap.fromImage(image).scaled(
                130, 130,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            thumb_label.setPixmap(pixmap)
            thumb_label.setStyleSheet("background-color: #f0f0f0;")
        else:
            thumb_label.setText("✗")
            thumb_label.setStyleSheet("color: #aaa; background-color: #f0f0f0; font-size: 32px;")

    def _load_thumbnail_async(self, result: ArtworkResult, thumb_label, generation: int):
        """Schedule async thumbnail load via thread pool."""
        if self._is_closed:
            return
        loader_id = self._next_loader_id
        self._next_loader_id += 1
        loader = ThumbnailLoader(loader_id, self.fetcher, result)
        loader.signals.loaded.connect(self._on_thumb_loaded, Qt.ConnectionType.QueuedConnection)
        loader.signals.failed.connect(self._on_thumb_failed, Qt.ConnectionType.QueuedConnection)
        # Keep strong references so Python GC doesn't collect loader/signals before signals fire
        self._active_loaders[loader_id] = loader
        self._loader_id_to_generation[loader_id] = generation
        # Store thumb_label on the dialog indexed by loader_id (no reference passed to thread)
        setattr(self, f'_thumb_{loader_id}', thumb_label)
        QThreadPool.globalInstance().start(loader)

    def _on_thumb_loaded(self, loader_id: int, data: bytes):
        if self._is_closed:
            return
        # Ignore if the search generation has changed (results were cleared)
        if self._loader_id_to_generation.get(loader_id) != self._search_generation:
            self._active_loaders.pop(loader_id, None)
            return
        thumb_label = getattr(self, f'_thumb_{loader_id}', None)
        self._active_loaders.pop(loader_id, None)
        if thumb_label is None:
            return
        try:
            self._set_thumb_pixmap(thumb_label, data)
        except RuntimeError:
            pass  # C++ widget already deleted

    def _on_thumb_failed(self, loader_id: int):
        if self._is_closed:
            self._active_loaders.pop(loader_id, None)
            return
        if self._loader_id_to_generation.get(loader_id) != self._search_generation:
            self._active_loaders.pop(loader_id, None)
            return
        thumb_label = getattr(self, f'_thumb_{loader_id}', None)
        self._active_loaders.pop(loader_id, None)
        if thumb_label is None:
            return
        try:
            thumb_label.setText("✗")
            thumb_label.setStyleSheet("color: #aaa; background-color: #f0f0f0; font-size: 32px;")
        except RuntimeError:
            pass  # C++ widget already deleted

    def _on_result_clicked(self, index: int, frame: QFrame):
        """Handle result click."""
        if self._is_closed:
            return

        # Deselect all
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.setStyleSheet("")
                widget.setProperty('selected', False)

        # Select clicked
        frame.setStyleSheet("background-color: #c0e0ff; border: 2px solid #0078d7;")
        frame.setProperty('selected', True)

        self.select_btn.setEnabled(True)
        self._selected_index = index

    def _on_select(self):
        """Handle select button click."""
        if self._is_closed:
            return

        if not hasattr(self, '_selected_index'):
            return

        result = self.search_results[self._selected_index]

        # Download full image
        self.status_label.setText("Laen pilti...")
        self.select_btn.setEnabled(False)

        try:
            image_data = self.fetcher.download(result)
            if image_data:
                self.selected_artwork = image_data
                self.accept()
            else:
                if not self._is_closed:
                    QMessageBox.warning(self, "Viga", "Pildi allalaadimine ebaõnnestus.")
                    self.select_btn.setEnabled(True)
        except Exception as e:
            if not self._is_closed:
                QMessageBox.warning(self, "Viga", f"Viga pildi laadimisel: {e}")
                self.select_btn.setEnabled(True)
        finally:
            if not self._is_closed:
                self.status_label.setText("")

    def get_selected_artwork(self) -> Optional[bytes]:
        """Get the selected artwork bytes."""
        return self.selected_artwork

    def closeEvent(self, event):
        """Handle dialog close."""
        self._is_closed = True
        self._stop_search()
        super().closeEvent(event)

    def reject(self):
        """Handle dialog rejection (cancel/escape)."""
        self._is_closed = True
        self._stop_search()
        super().reject()
