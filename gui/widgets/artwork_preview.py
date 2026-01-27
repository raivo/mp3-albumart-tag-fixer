"""Artwork preview and selection widget."""

from typing import Optional
from io import BytesIO

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QFrame,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

from models.track import Track
from artwork.providers.base import ArtworkResult
from utils.translations import tr


class ArtworkPreviewWidget(QWidget):
    """Widget for displaying and selecting album artwork."""

    artwork_selected = Signal(bytes)  # Emitted when artwork is selected
    search_requested = Signal(str, str)  # Emitted to search (artist, album)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_artwork: Optional[bytes] = None
        self._search_results: list[ArtworkResult] = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel(tr('album_artwork'))
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # Current artwork display
        self.current_frame = QFrame()
        self.current_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.current_frame.setFixedSize(200, 200)

        frame_layout = QVBoxLayout(self.current_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)

        self.artwork_label = QLabel()
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setText(tr('no_image'))
        self.artwork_label.setStyleSheet("color: gray;")
        frame_layout.addWidget(self.artwork_label)

        layout.addWidget(self.current_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Artwork info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.search_btn = QPushButton(tr('search_images'))
        self.search_btn.clicked.connect(self._on_search_clicked)
        button_layout.addWidget(self.search_btn)

        self.browse_btn = QPushButton(tr('select_file_btn'))
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        button_layout.addWidget(self.browse_btn)

        self.remove_btn = QPushButton(tr('remove'))
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        button_layout.addWidget(self.remove_btn)

        layout.addLayout(button_layout)

        # Search results area
        self.results_label = QLabel(tr('search_results'))
        self.results_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.results_label.hide()
        layout.addWidget(self.results_label)

        # Scroll area for search results
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFixedHeight(150)
        self.results_scroll.hide()

        self.results_widget = QWidget()
        self.results_layout = QHBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.results_scroll.setWidget(self.results_widget)

        layout.addWidget(self.results_scroll)

        layout.addStretch()

    def set_artwork(self, artwork_data: Optional[bytes]):
        """Set the current artwork to display."""
        self._current_artwork = artwork_data

        if artwork_data:
            pixmap = self._bytes_to_pixmap(artwork_data)
            if pixmap:
                scaled = pixmap.scaled(
                    190, 190,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.artwork_label.setPixmap(scaled)

                # Show dimensions
                img = QImage.fromData(artwork_data)
                self.info_label.setText(f"{img.width()}x{img.height()} px")
            else:
                self.artwork_label.setText(tr('invalid_image'))
                self.info_label.setText("")
        else:
            self.artwork_label.setText(tr('no_image'))
            self.artwork_label.setPixmap(QPixmap())
            self.info_label.setText("")

    def set_search_results(self, results: list[tuple[ArtworkResult, Optional[bytes]]]):
        """Set search results to display."""
        self._search_results = [r[0] for r in results]

        # Clear previous results
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if results:
            self.results_label.show()
            self.results_scroll.show()

            for i, (result, thumbnail_data) in enumerate(results):
                result_widget = self._create_result_widget(i, result, thumbnail_data)
                self.results_layout.addWidget(result_widget)
        else:
            self.results_label.hide()
            self.results_scroll.hide()

    def _create_result_widget(self, index: int, result: ArtworkResult,
                              thumbnail_data: Optional[bytes]) -> QWidget:
        """Create a widget for a single search result."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        widget.setFixedSize(120, 140)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(100, 100)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if thumbnail_data:
            pixmap = self._bytes_to_pixmap(thumbnail_data)
            if pixmap:
                scaled = pixmap.scaled(
                    100, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                thumb_label.setPixmap(scaled)
        else:
            thumb_label.setText("...")
            thumb_label.setStyleSheet("color: gray;")

        layout.addWidget(thumb_label)

        # Source label
        source_label = QLabel(result.source)
        source_label.setStyleSheet("font-size: 10px; color: gray;")
        source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(source_label)

        # Make clickable
        widget.mousePressEvent = lambda e, idx=index: self._on_result_clicked(idx)

        return widget

    def _bytes_to_pixmap(self, data: bytes) -> Optional[QPixmap]:
        """Convert image bytes to QPixmap."""
        try:
            image = QImage.fromData(data)
            if not image.isNull():
                return QPixmap.fromImage(image)
        except Exception:
            pass
        return None

    def _on_search_clicked(self):
        """Handle search button click."""
        # Will be connected to main window to perform search
        self.search_requested.emit("", "")  # Empty strings signal to use current track info

    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr('select_image'),
            "",
            f"{tr('image_files')};;{tr('all_files')}"
        )

        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    image_data = f.read()

                self.set_artwork(image_data)
                self.artwork_selected.emit(image_data)
            except Exception as e:
                QMessageBox.warning(self, tr('error'), f"{tr('image_load_failed')}: {e}")

    def _on_remove_clicked(self):
        """Handle remove button click."""
        self.set_artwork(None)
        self.artwork_selected.emit(b'')  # Empty bytes signals removal

    def _on_result_clicked(self, index: int):
        """Handle click on a search result."""
        if 0 <= index < len(self._search_results):
            # Signal that this result was selected
            # The main window will handle downloading the full image
            result = self._search_results[index]
            # For now, just emit that we want to download this
            # The parent will need to handle the actual download
            self.search_requested.emit(result.image_url, result.source)

    def get_current_artwork(self) -> Optional[bytes]:
        """Get the current artwork bytes."""
        return self._current_artwork

    def clear(self):
        """Clear the widget."""
        self.set_artwork(None)
        self.set_search_results([])

    def update_translations(self):
        """Update all translatable text."""
        self.title_label.setText(tr('album_artwork'))
        self.search_btn.setText(tr('search_images'))
        self.browse_btn.setText(tr('select_file_btn'))
        self.remove_btn.setText(tr('remove'))
        self.results_label.setText(tr('search_results'))
        if not self._current_artwork:
            self.artwork_label.setText(tr('no_image'))
