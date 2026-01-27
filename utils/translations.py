"""Translation system for the application."""

import locale
from typing import Optional, Callable

# Translation dictionaries
TRANSLATIONS = {
    'et': {
        # Main window
        'app_title': 'MP3 Tag Editor',
        'settings': 'Seaded',
        'mode_description': 'Vali režiim: töötlemine üksiku faili või terve kataloogi kaupa.',
        'single_file': 'Üksik fail',
        'directory': 'Kataloog',
        'ready': 'Valmis',

        # Menu
        'menu_file': 'Fail',
        'menu_open_file': 'Ava fail...',
        'menu_open_directory': 'Ava kataloog...',
        'menu_quit': 'Välju',
        'menu_edit': 'Redigeeri',
        'menu_settings': 'Seaded...',
        'menu_help': 'Abi',
        'menu_about': 'Teave...',

        # About dialog
        'about_title': 'Teave',
        'about_text': '''<h2>MP3 Tag Editor</h2>
<p>Versioon 1.0</p>
<p>Rakendus MP3 failide metaandmete haldamiseks.</p>
<p>Funktsioonid:</p>
<ul>
<li>Failinime ja kataloogi analüüs</li>
<li>Audio fingerprinting (AcoustID)</li>
<li>Kaanepiltide otsing mitmetest allikatest</li>
<li>Üksiku faili või terve kataloogi töötlemine</li>
</ul>''',

        # Unsaved changes
        'unsaved_changes': 'Salvestamata muudatused',
        'unsaved_changes_msg': 'Sul on salvestamata muudatusi. Kas oled kindel, et soovid väljuda?',

        # Single file view
        'no_file_selected': 'Faili pole valitud',
        'select_file': 'Vali fail...',
        'analyzing_file': 'Analüüsin faili...',
        'file_loaded': 'Fail laetud',
        'analyze_again': 'Analüüsi uuesti',
        'save': 'Salvesta',
        'changes_unsaved': 'Muudatused salvestamata',
        'saving': 'Salvestan...',
        'saved': 'Salvestatud!',
        'save_failed': 'Salvestamine ebaõnnestus',

        # File dialogs
        'select_mp3_file': 'Vali MP3 fail',
        'mp3_files': 'MP3 failid (*.mp3)',
        'all_files': 'Kõik failid (*)',
        'select_image': 'Vali kaanepilt',
        'image_files': 'Pildifailid (*.jpg *.jpeg *.png *.gif *.bmp)',

        # Errors
        'error': 'Viga',
        'warning': 'Hoiatus',
        'info': 'Info',
        'file_not_found': 'Faili ei leitud',
        'analysis_failed': 'Faili analüüsimine ebaõnnestus',
        'image_load_failed': 'Pildi laadimine ebaõnnestus',

        # Tag editor
        'metadata': 'Metaandmed',
        'tag_info': 'Tag info',
        'artist': 'Esitaja',
        'artist_placeholder': 'Esitaja nimi',
        'title': 'Pealkiri',
        'title_placeholder': 'Loo pealkiri',
        'album': 'Album',
        'album_placeholder': 'Albumi nimi',
        'year': 'Aasta',
        'year_not_set': 'Pole määratud',
        'track': 'Lugu',
        'genre': 'Žanr',
        'data_sources': 'Andmeallikad',
        'reset': 'Lähtesta',
        'apply': 'Rakenda',
        'missing': '(puudub)',
        'not_detected': '(pole tuvastatud)',

        # Artwork
        'album_artwork': 'Albumi kaanepilt',
        'no_image': 'Pilt puudub',
        'invalid_image': 'Vigane pilt',
        'search_images': 'Otsi pilte',
        'select_file_btn': 'Vali fail...',
        'remove': 'Eemalda',
        'search_results': 'Otsingutulemused:',
        'loading_image': 'Laen pilti...',

        # Artwork picker
        'search_artwork': 'Otsi kaanepilti',
        'or_search': 'Või otsi:',
        'search_placeholder': "Sisesta otsisõnad (nt 'Smilers album cover')",
        'search': 'Otsi',
        'cancel': 'Tühista',
        'select': 'Vali',
        'searching': 'Otsin...',
        'found_results': 'Leiti {count} tulemust',
        'no_results': 'Tulemusi ei leitud',
        'search_failed': 'Otsing ebaõnnestus',
        'download_failed': 'Pildi allalaadimine ebaõnnestus',
        'enter_artist_album': 'Palun sisesta nii esitaja kui albumi nimi.',
        'loading': 'Laen...',

        # Conflict dialog
        'resolve_conflicts': 'Lahenda konfliktid',
        'conflicts_found': "Failis '{filename}' leiti vastuolulisi andmeid.",
        'select_correct_value': 'Palun vali iga välja jaoks õige väärtus või sisesta oma:',
        'other': 'Muu:',
        'source_tag': 'Tag',
        'source_filename': 'Failinimi',
        'source_directory': 'Kataloog',
        'source_acoustid': 'AcoustID',
        'source_musicbrainz': 'MusicBrainz',
        'source_user': 'Kasutaja',
        'skip': 'Jäta vahele',
        'previous': 'Eelmine',
        'next': 'Järgmine',
        'finish': 'Lõpeta',
        'file_x_of_y': 'Fail {current}/{total}',

        # Directory view
        'no_directory_selected': 'Kataloogi pole valitud',
        'select_directory': 'Vali kataloog...',
        'album_info': 'Albumi info',
        'artist_label': 'Esitaja: {value}',
        'album_label': 'Album: {value}',
        'year_label': 'Aasta: {value}',
        'tracks_label': 'Lugusid: {value}',
        'analyzing_files': 'Analüüsin faile...',
        'no_mp3_files': 'Kataloogis ei leitud MP3 faile.',
        'files_with_conflicts': 'Leiti {count} faili konfliktidega',
        'loaded_files': 'Laetud {count} faili',
        'resolve_conflicts_btn': 'Lahenda konfliktid',
        'apply_to_all': 'Rakenda kõigile',
        'apply_to_all_tooltip': 'Rakenda praegused metaandmed kõigile lugudele',
        'save_all': 'Salvesta kõik',
        'select_directory_mp3': 'Vali kataloog MP3 failidega',
        'directory_not_found': 'Kataloogi ei leitud',
        'directory_analysis_failed': 'Kataloogi analüüsimine ebaõnnestus',
        'no_conflicts': 'Konflikte ei leitud.',
        'apply_all_confirm': 'Kas oled kindel, et soovid praeguse loo albumi, esitaja ja aasta info rakendada kõigile lugudele?',
        'confirmation': 'Kinnitus',
        'select_track_first': 'Palun vali kõigepealt lugu ja täida metaandmed.',
        'info_applied_to_all': 'Info rakendatud kõigile lugudele',
        'apply_artwork_to_all': 'Rakenda kõigile?',
        'apply_artwork_to_all_msg': 'Kas soovid selle pildi rakendada kõigile lugudele albumis?',
        'no_changes_to_save': 'Muudatusi pole salvestada.',
        'saved_files': 'Salvestatud {count} faili',
        'saved_with_errors': 'Salvestatud {success} faili.\nVigu: {errors}',
        'done': 'Valmis',

        # Preview dialog
        'preview_title': 'Muudatuste eelvaade',
        'preview_header': 'Vaata üle {count} faili muudatused enne salvestamist:',
        'column_select': 'Vali',
        'column_file': 'Fail',
        'column_field': 'Väli',
        'column_current': 'Praegune väärtus',
        'column_new': 'Uus väärtus',
        'select_all': 'Vali kõik',
        'deselect_all': 'Tühista valik',
        'selected_count': 'Valitud: {selected}/{total}',
        'save_selected': 'Salvesta valitud',
        'empty': '(tühi)',
        'track_number': 'Loo nr',
        'artwork': 'Kaanepilt',

        # Settings
        'settings_title': 'Seaded',
        'api_keys': 'API võtmed',
        'get_api_key': 'Hangi {service} API võti',
        'audio_detection': 'Audio tuvastamine',
        'use_fingerprinting': 'Kasuta audio fingerprinting tuvastamist (AcoustID)',
        'fingerprint_note': 'NB: Vajab installitud fpcalc tööriista (Chromaprint).',
        'preview_group': 'Eelvaade',
        'show_preview': 'Näita eelvaadet enne muudatuste salvestamist',
        'tab_api': 'API',
        'tab_general': 'Üldine',
        'tab_artwork': 'Kaanepilt',
        'tab_cache': 'Vahemälu',
        'artwork_settings': 'Kaanepildi seaded',
        'image_size': 'Pildi suurus:',
        'jpeg_quality': 'JPEG kvaliteet:',
        'cache': 'Vahemälu',
        'enable_cache': 'Luba vahemälu',
        'cache_duration': 'Säilitusaeg:',
        'days': 'päeva',
        'clear_cache': 'Tühjenda vahemälu',
        'clear_cache_confirm': 'Kas oled kindel, et soovid tühjendada vahemälu?\nPraegune suurus: {size:.1f} MB',
        'cache_cleared': 'Vahemälu tühjendatud',
        'cache_cleared_msg': 'Vahemälu on edukalt tühjendatud.',

        # Language
        'language': 'Keel',
        'estonian': 'Eesti',
        'english': 'English',
    },

    'en': {
        # Main window
        'app_title': 'MP3 Tag Editor',
        'settings': 'Settings',
        'mode_description': 'Choose mode: process a single file or an entire directory.',
        'single_file': 'Single file',
        'directory': 'Directory',
        'ready': 'Ready',

        # Menu
        'menu_file': 'File',
        'menu_open_file': 'Open file...',
        'menu_open_directory': 'Open directory...',
        'menu_quit': 'Quit',
        'menu_edit': 'Edit',
        'menu_settings': 'Settings...',
        'menu_help': 'Help',
        'menu_about': 'About...',

        # About dialog
        'about_title': 'About',
        'about_text': '''<h2>MP3 Tag Editor</h2>
<p>Version 1.0</p>
<p>Application for managing MP3 file metadata.</p>
<p>Features:</p>
<ul>
<li>Filename and directory analysis</li>
<li>Audio fingerprinting (AcoustID)</li>
<li>Album artwork search from multiple sources</li>
<li>Single file or directory batch processing</li>
</ul>''',

        # Unsaved changes
        'unsaved_changes': 'Unsaved changes',
        'unsaved_changes_msg': 'You have unsaved changes. Are you sure you want to quit?',

        # Single file view
        'no_file_selected': 'No file selected',
        'select_file': 'Select file...',
        'analyzing_file': 'Analyzing file...',
        'file_loaded': 'File loaded',
        'analyze_again': 'Analyze again',
        'save': 'Save',
        'changes_unsaved': 'Changes unsaved',
        'saving': 'Saving...',
        'saved': 'Saved!',
        'save_failed': 'Save failed',

        # File dialogs
        'select_mp3_file': 'Select MP3 file',
        'mp3_files': 'MP3 files (*.mp3)',
        'all_files': 'All files (*)',
        'select_image': 'Select cover image',
        'image_files': 'Image files (*.jpg *.jpeg *.png *.gif *.bmp)',

        # Errors
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Info',
        'file_not_found': 'File not found',
        'analysis_failed': 'File analysis failed',
        'image_load_failed': 'Image loading failed',

        # Tag editor
        'metadata': 'Metadata',
        'tag_info': 'Tag info',
        'artist': 'Artist',
        'artist_placeholder': 'Artist name',
        'title': 'Title',
        'title_placeholder': 'Track title',
        'album': 'Album',
        'album_placeholder': 'Album name',
        'year': 'Year',
        'year_not_set': 'Not set',
        'track': 'Track',
        'genre': 'Genre',
        'data_sources': 'Data sources',
        'reset': 'Reset',
        'apply': 'Apply',
        'missing': '(missing)',
        'not_detected': '(not detected)',

        # Artwork
        'album_artwork': 'Album artwork',
        'no_image': 'No image',
        'invalid_image': 'Invalid image',
        'search_images': 'Search images',
        'select_file_btn': 'Select file...',
        'remove': 'Remove',
        'search_results': 'Search results:',
        'loading_image': 'Loading image...',

        # Artwork picker
        'search_artwork': 'Search artwork',
        'or_search': 'Or search:',
        'search_placeholder': "Enter search terms (e.g. 'Beatles album cover')",
        'search': 'Search',
        'cancel': 'Cancel',
        'select': 'Select',
        'searching': 'Searching...',
        'found_results': 'Found {count} results',
        'no_results': 'No results found',
        'search_failed': 'Search failed',
        'download_failed': 'Image download failed',
        'enter_artist_album': 'Please enter both artist and album name.',
        'loading': 'Loading...',

        # Conflict dialog
        'resolve_conflicts': 'Resolve conflicts',
        'conflicts_found': "Conflicting data found in file '{filename}'.",
        'select_correct_value': 'Please select the correct value for each field or enter your own:',
        'other': 'Other:',
        'source_tag': 'Tag',
        'source_filename': 'Filename',
        'source_directory': 'Directory',
        'source_acoustid': 'AcoustID',
        'source_musicbrainz': 'MusicBrainz',
        'source_user': 'User',
        'skip': 'Skip',
        'previous': 'Previous',
        'next': 'Next',
        'finish': 'Finish',
        'file_x_of_y': 'File {current}/{total}',

        # Directory view
        'no_directory_selected': 'No directory selected',
        'select_directory': 'Select directory...',
        'album_info': 'Album info',
        'artist_label': 'Artist: {value}',
        'album_label': 'Album: {value}',
        'year_label': 'Year: {value}',
        'tracks_label': 'Tracks: {value}',
        'analyzing_files': 'Analyzing files...',
        'no_mp3_files': 'No MP3 files found in directory.',
        'files_with_conflicts': 'Found {count} files with conflicts',
        'loaded_files': 'Loaded {count} files',
        'resolve_conflicts_btn': 'Resolve conflicts',
        'apply_to_all': 'Apply to all',
        'apply_to_all_tooltip': 'Apply current metadata to all tracks',
        'save_all': 'Save all',
        'select_directory_mp3': 'Select directory with MP3 files',
        'directory_not_found': 'Directory not found',
        'directory_analysis_failed': 'Directory analysis failed',
        'no_conflicts': 'No conflicts found.',
        'apply_all_confirm': 'Are you sure you want to apply the current track\'s album, artist and year info to all tracks?',
        'confirmation': 'Confirmation',
        'select_track_first': 'Please select a track first and fill in the metadata.',
        'info_applied_to_all': 'Info applied to all tracks',
        'apply_artwork_to_all': 'Apply to all?',
        'apply_artwork_to_all_msg': 'Do you want to apply this image to all tracks in the album?',
        'no_changes_to_save': 'No changes to save.',
        'saved_files': 'Saved {count} files',
        'saved_with_errors': 'Saved {success} files.\nErrors: {errors}',
        'done': 'Done',

        # Preview dialog
        'preview_title': 'Preview changes',
        'preview_header': 'Review changes to {count} files before saving:',
        'column_select': 'Select',
        'column_file': 'File',
        'column_field': 'Field',
        'column_current': 'Current value',
        'column_new': 'New value',
        'select_all': 'Select all',
        'deselect_all': 'Deselect all',
        'selected_count': 'Selected: {selected}/{total}',
        'save_selected': 'Save selected',
        'empty': '(empty)',
        'track_number': 'Track #',
        'artwork': 'Artwork',

        # Settings
        'settings_title': 'Settings',
        'api_keys': 'API keys',
        'get_api_key': 'Get {service} API key',
        'audio_detection': 'Audio detection',
        'use_fingerprinting': 'Use audio fingerprinting detection (AcoustID)',
        'fingerprint_note': 'Note: Requires fpcalc tool (Chromaprint) to be installed.',
        'preview_group': 'Preview',
        'show_preview': 'Show preview before saving changes',
        'tab_api': 'API',
        'tab_general': 'General',
        'tab_artwork': 'Artwork',
        'tab_cache': 'Cache',
        'artwork_settings': 'Artwork settings',
        'image_size': 'Image size:',
        'jpeg_quality': 'JPEG quality:',
        'cache': 'Cache',
        'enable_cache': 'Enable cache',
        'cache_duration': 'Duration:',
        'days': 'days',
        'clear_cache': 'Clear cache',
        'clear_cache_confirm': 'Are you sure you want to clear the cache?\nCurrent size: {size:.1f} MB',
        'cache_cleared': 'Cache cleared',
        'cache_cleared_msg': 'Cache has been cleared successfully.',

        # Language
        'language': 'Language',
        'estonian': 'Eesti',
        'english': 'English',
    }
}


class TranslationManager:
    """Manages translations and language switching."""

    _instance: Optional['TranslationManager'] = None
    _language: str = 'et'
    _listeners: list[Callable[[], None]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = []
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'TranslationManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def detect_system_language(cls) -> str:
        """Detect system language and return 'et' or 'en'."""
        try:
            system_locale = locale.getdefaultlocale()[0] or ''
            if system_locale.startswith('et'):
                return 'et'
        except Exception:
            pass
        return 'en'

    @property
    def language(self) -> str:
        """Get current language."""
        return self._language

    @language.setter
    def language(self, value: str):
        """Set current language and notify listeners."""
        if value in TRANSLATIONS and value != self._language:
            self._language = value
            self._notify_listeners()

    def get(self, key: str, **kwargs) -> str:
        """Get translated string by key with optional formatting."""
        translations = TRANSLATIONS.get(self._language, TRANSLATIONS['en'])
        text = translations.get(key, key)

        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return text

    def add_listener(self, callback: Callable[[], None]):
        """Add a listener to be notified when language changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]):
        """Remove a listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        """Notify all listeners of language change."""
        for callback in self._listeners:
            try:
                callback()
            except Exception:
                pass


# Convenience function
def tr(key: str, **kwargs) -> str:
    """Get translated string."""
    return TranslationManager.get_instance().get(key, **kwargs)


def get_language() -> str:
    """Get current language code."""
    return TranslationManager.get_instance().language


def set_language(lang: str):
    """Set current language."""
    TranslationManager.get_instance().language = lang


def add_language_listener(callback: Callable[[], None]):
    """Add listener for language changes."""
    TranslationManager.get_instance().add_listener(callback)


def remove_language_listener(callback: Callable[[], None]):
    """Remove language change listener."""
    TranslationManager.get_instance().remove_listener(callback)
