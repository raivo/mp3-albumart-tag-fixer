"""Settings dialog for application configuration."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QSpinBox,
    QGroupBox, QFormLayout, QTabWidget, QWidget,
    QMessageBox
)

from config import get_config, save_config, AppConfig


class SettingsDialog(QDialog):
    """Dialog for editing application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Seaded")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Tabs
        tabs = QTabWidget()

        # API tab
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        api_group = QGroupBox("API võtmed")
        api_form = QFormLayout(api_group)

        self.acoustid_edit = QLineEdit()
        self.acoustid_edit.setPlaceholderText("AcoustID API võti")
        self.acoustid_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_form.addRow("AcoustID:", self.acoustid_edit)

        acoustid_help = QLabel(
            '<a href="https://acoustid.org/api-key">Hangi AcoustID API võti</a>'
        )
        acoustid_help.setOpenExternalLinks(True)
        api_form.addRow("", acoustid_help)

        self.lastfm_edit = QLineEdit()
        self.lastfm_edit.setPlaceholderText("Last.fm API võti")
        self.lastfm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_form.addRow("Last.fm:", self.lastfm_edit)

        lastfm_help = QLabel(
            '<a href="https://www.last.fm/api/account/create">Hangi Last.fm API võti</a>'
        )
        lastfm_help.setOpenExternalLinks(True)
        api_form.addRow("", lastfm_help)

        self.discogs_edit = QLineEdit()
        self.discogs_edit.setPlaceholderText("Discogs token")
        self.discogs_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_form.addRow("Discogs:", self.discogs_edit)

        discogs_help = QLabel(
            '<a href="https://www.discogs.com/settings/developers">Hangi Discogs token</a>'
        )
        discogs_help.setOpenExternalLinks(True)
        api_form.addRow("", discogs_help)

        api_layout.addWidget(api_group)
        api_layout.addStretch()

        tabs.addTab(api_tab, "API")

        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # Fingerprinting
        fingerprint_group = QGroupBox("Audio tuvastamine")
        fingerprint_layout = QVBoxLayout(fingerprint_group)

        self.fingerprint_check = QCheckBox("Kasuta audio fingerprinting tuvastamist (AcoustID)")
        fingerprint_layout.addWidget(self.fingerprint_check)

        fingerprint_info = QLabel(
            "NB: Vajab installitud fpcalc tööriista (Chromaprint)."
        )
        fingerprint_info.setStyleSheet("color: gray; font-size: 11px;")
        fingerprint_layout.addWidget(fingerprint_info)

        general_layout.addWidget(fingerprint_group)

        # Preview
        preview_group = QGroupBox("Eelvaade")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_check = QCheckBox("Näita eelvaadet enne muudatuste salvestamist")
        preview_layout.addWidget(self.preview_check)

        general_layout.addWidget(preview_group)

        general_layout.addStretch()
        tabs.addTab(general_tab, "Üldine")

        # Artwork tab
        artwork_tab = QWidget()
        artwork_layout = QVBoxLayout(artwork_tab)

        artwork_group = QGroupBox("Kaanepildi seaded")
        artwork_form = QFormLayout(artwork_group)

        self.artwork_size_spin = QSpinBox()
        self.artwork_size_spin.setRange(100, 2000)
        self.artwork_size_spin.setSuffix(" px")
        artwork_form.addRow("Pildi suurus:", self.artwork_size_spin)

        self.artwork_quality_spin = QSpinBox()
        self.artwork_quality_spin.setRange(1, 100)
        self.artwork_quality_spin.setSuffix(" %")
        artwork_form.addRow("JPEG kvaliteet:", self.artwork_quality_spin)

        artwork_layout.addWidget(artwork_group)
        artwork_layout.addStretch()

        tabs.addTab(artwork_tab, "Kaanepilt")

        # Cache tab
        cache_tab = QWidget()
        cache_layout = QVBoxLayout(cache_tab)

        cache_group = QGroupBox("Vahemälu")
        cache_form_layout = QFormLayout(cache_group)

        self.cache_check = QCheckBox("Luba vahemälu")
        cache_form_layout.addRow("", self.cache_check)

        self.cache_days_spin = QSpinBox()
        self.cache_days_spin.setRange(1, 30)
        self.cache_days_spin.setSuffix(" päeva")
        cache_form_layout.addRow("Säilitusaeg:", self.cache_days_spin)

        cache_layout.addWidget(cache_group)

        # Clear cache button
        clear_cache_btn = QPushButton("Tühjenda vahemälu")
        clear_cache_btn.clicked.connect(self._on_clear_cache)
        cache_layout.addWidget(clear_cache_btn)

        cache_layout.addStretch()
        tabs.addTab(cache_tab, "Vahemälu")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Tühista")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        save_btn = QPushButton("Salvesta")
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load current settings into UI."""
        # API
        self.acoustid_edit.setText(self.config.api.acoustid_api_key)
        self.lastfm_edit.setText(self.config.api.lastfm_api_key)
        self.discogs_edit.setText(self.config.api.discogs_token)

        # General
        self.fingerprint_check.setChecked(self.config.use_fingerprinting)
        self.preview_check.setChecked(self.config.show_preview)

        # Artwork
        self.artwork_size_spin.setValue(self.config.artwork_size)
        self.artwork_quality_spin.setValue(self.config.artwork_quality)

        # Cache
        self.cache_check.setChecked(self.config.cache_enabled)
        self.cache_days_spin.setValue(self.config.cache_ttl_days)

    def _on_save(self):
        """Save settings."""
        # Update config
        self.config.api.acoustid_api_key = self.acoustid_edit.text()
        self.config.api.lastfm_api_key = self.lastfm_edit.text()
        self.config.api.discogs_token = self.discogs_edit.text()

        self.config.use_fingerprinting = self.fingerprint_check.isChecked()
        self.config.show_preview = self.preview_check.isChecked()

        self.config.artwork_size = self.artwork_size_spin.value()
        self.config.artwork_quality = self.artwork_quality_spin.value()

        self.config.cache_enabled = self.cache_check.isChecked()
        self.config.cache_ttl_days = self.cache_days_spin.value()

        # Save to file
        save_config(self.config)

        self.accept()

    def _on_clear_cache(self):
        """Clear the cache."""
        from utils.cache import clear_cache, get_cache_size

        size = get_cache_size()
        size_mb = size / (1024 * 1024)

        reply = QMessageBox.question(
            self,
            "Tühjenda vahemälu",
            f"Kas oled kindel, et soovid tühjendada vahemälu?\n"
            f"Praegune suurus: {size_mb:.1f} MB",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            clear_cache()
            QMessageBox.information(
                self,
                "Vahemälu tühjendatud",
                "Vahemälu on edukalt tühjendatud."
            )
