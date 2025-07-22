import os
import logging
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MetadataHandler")

# Try to import audio metadata libraries with fallbacks
try:
    from mutagen import File
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wavpack import WavPack

    MUTAGEN_AVAILABLE = True
    logger.info("Mutagen library loaded successfully")
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen not available. Install with: pip install mutagen")


class MetadataHandler:
    """Enhanced handler for audio file metadata extraction"""

    def __init__(self):
        self.cache = {}  # Cache metadata to avoid re-reading files
        self.art_cache = {}  # Cache album art separately
        self.supported_extensions = ['.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma', '.ape']

    def is_audio_file(self, file_path):
        """Check if a file is a supported audio file based on extension"""
        if not file_path:
            return False
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions

    def extract_metadata(self, file_path):
        """Extract comprehensive metadata from audio file"""
        if not file_path or not os.path.exists(file_path):
            return self._create_basic_metadata(file_path or "Unknown file")

        # Return cached metadata if available and file hasn't changed
        file_mtime = os.path.getmtime(file_path)
        if file_path in self.cache and self.cache[file_path].get('_mtime') == file_mtime:
            return self.cache[file_path]

        # If mutagen isn't available, use basic metadata
        if not MUTAGEN_AVAILABLE:
            basic_metadata = self._create_basic_metadata(file_path)
            self.cache[file_path] = basic_metadata
            return basic_metadata

        try:
            metadata = self._extract_with_mutagen(file_path)
            metadata['_mtime'] = file_mtime  # Store modification time for cache validation
            self.cache[file_path] = metadata
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            basic_metadata = self._create_basic_metadata(file_path)
            self.cache[file_path] = basic_metadata
            return basic_metadata

    def _extract_with_mutagen(self, file_path):
        """Extract metadata using mutagen with format-specific optimizations"""
        metadata = {
            'title': os.path.splitext(os.path.basename(file_path))[0],
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'genre': 'Unknown Genre',
            'year': 'Unknown Year',
            'track': '0',
            'length': 0,
            'bitrate': 0,
            'sample_rate': 0,
            'channels': 2,
            'path': file_path,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }

        # Extract file extension to determine type
        ext = os.path.splitext(file_path)[1].lower()

        # Format-specific extraction
        if ext == '.mp3':
            metadata = self._extract_mp3_metadata(file_path, metadata)
        elif ext == '.flac':
            metadata = self._extract_flac_metadata(file_path, metadata)
        elif ext == '.m4a' or ext == '.aac' or ext == '.mp4':
            metadata = self._extract_mp4_metadata(file_path, metadata)
        elif ext == '.ogg':
            metadata = self._extract_ogg_metadata(file_path, metadata)
        elif ext == '.wma':
            # Generic extraction for WMA
            audio_file = File(file_path)
            if audio_file:
                self._extract_generic_metadata(audio_file, metadata)
        else:
            # Generic extraction for other formats
            audio_file = File(file_path)
            if audio_file:
                self._extract_generic_metadata(audio_file, metadata)

        # Format file size
        metadata['file_size_formatted'] = self._format_file_size(metadata['file_size'])

        # Format track length
        if metadata['length'] > 0:
            minutes = int(metadata['length']) // 60
            seconds = int(metadata['length']) % 60
            metadata['length_formatted'] = f"{minutes}:{seconds:02d}"
        else:
            metadata['length_formatted'] = "0:00"

        # Format bitrate
        if metadata['bitrate'] > 0:
            metadata['bitrate_formatted'] = f"{metadata['bitrate'] // 1000} kbps"
        else:
            metadata['bitrate_formatted'] = "Unknown"

        return metadata

    def _extract_mp3_metadata(self, file_path, metadata):
        """Extract metadata specifically from MP3 files"""
        try:
            mp3 = MP3(file_path)
            audio_file = ID3(file_path)

            # Extract basic audio properties
            metadata['length'] = mp3.info.length
            metadata['bitrate'] = mp3.info.bitrate
            metadata['sample_rate'] = mp3.info.sample_rate
            metadata['channels'] = getattr(mp3.info, 'channels', 2)

            # ID3 tags mapping
            id3_mapping = {
                'TIT2': 'title',
                'TPE1': 'artist',
                'TPE2': 'album_artist',
                'TALB': 'album',
                'TCON': 'genre',
                'TDRC': 'year',
                'TYER': 'year',
                'TRCK': 'track',
                'TPOS': 'disc',
                'TCOM': 'composer',
                'COMM': 'comment'
            }

            for tag, field in id3_mapping.items():
                if tag in audio_file:
                    metadata[field] = str(audio_file[tag].text[0])

            # Handle multiple artists
            if 'TPE1' in audio_file and len(audio_file['TPE1'].text) > 1:
                metadata['artists'] = [str(artist) for artist in audio_file['TPE1'].text]

            # Process track number (often in format '1/12')
            if 'track' in metadata and '/' in metadata['track']:
                track_parts = metadata['track'].split('/')
                metadata['track'] = track_parts[0]
                metadata['track_total'] = track_parts[1]

        except Exception as e:
            logger.error(f"Error processing MP3 metadata: {e}")

        return metadata

    def _extract_flac_metadata(self, file_path, metadata):
        """Extract metadata specifically from FLAC files"""
        try:
            flac = FLAC(file_path)

            # Extract audio properties
            metadata['length'] = flac.info.length
            metadata['bitrate'] = flac.info.bitrate
            metadata['sample_rate'] = flac.info.sample_rate
            metadata['channels'] = flac.info.channels
            metadata['bits_per_sample'] = flac.info.bits_per_sample

            # Map FLAC tags
            flac_mapping = {
                'title': 'title',
                'artist': 'artist',
                'album': 'album',
                'albumartist': 'album_artist',
                'genre': 'genre',
                'date': 'year',
                'tracknumber': 'track',
                'composer': 'composer',
                'discnumber': 'disc'
            }

            for tag, field in flac_mapping.items():
                if tag in flac:
                    metadata[field] = flac[tag][0]

        except Exception as e:
            logger.error(f"Error processing FLAC metadata: {e}")

        return metadata

    def _extract_mp4_metadata(self, file_path, metadata):
        """Extract metadata specifically from M4A/MP4/AAC files"""
        try:
            mp4 = MP4(file_path)

            # Extract audio properties
            metadata['length'] = mp4.info.length
            metadata['bitrate'] = mp4.info.bitrate
            metadata['sample_rate'] = mp4.info.sample_rate
            metadata['channels'] = mp4.info.channels

            # MP4 tags mapping
            mp4_mapping = {
                '\xa9nam': 'title',
                '\xa9ART': 'artist',
                'aART': 'album_artist',
                '\xa9alb': 'album',
                '\xa9gen': 'genre',
                '\xa9day': 'year',
                'trkn': 'track',
                'disk': 'disc',
                '\xa9wrt': 'composer',
                '\xa9cmt': 'comment'
            }

            for tag, field in mp4_mapping.items():
                if tag in mp4:
                    if tag in ['trkn', 'disk']:
                        # Handle tuple format (track_num, total_tracks)
                        if mp4[tag] and len(mp4[tag][0]) > 0:
                            metadata[field] = str(mp4[tag][0][0])
                            if len(mp4[tag][0]) > 1 and mp4[tag][0][1]:
                                metadata[f'{field}_total'] = str(mp4[tag][0][1])
                    else:
                        metadata[field] = str(mp4[tag][0])

        except Exception as e:
            logger.error(f"Error processing MP4 metadata: {e}")

        return metadata

    def _extract_ogg_metadata(self, file_path, metadata):
        """Extract metadata specifically from OGG files"""
        try:
            ogg = OggVorbis(file_path)

            # Extract audio properties
            metadata['length'] = ogg.info.length
            metadata['bitrate'] = ogg.info.bitrate
            metadata['sample_rate'] = ogg.info.sample_rate
            metadata['channels'] = ogg.info.channels

            # OGG tags mapping
            ogg_mapping = {
                'title': 'title',
                'artist': 'artist',
                'album': 'album',
                'albumartist': 'album_artist',
                'genre': 'genre',
                'date': 'year',
                'tracknumber': 'track',
                'composer': 'composer',
                'discnumber': 'disc',
                'comment': 'comment'
            }

            for tag, field in ogg_mapping.items():
                if tag in ogg:
                    metadata[field] = ogg[tag][0]

        except Exception as e:
            logger.error(f"Error processing OGG metadata: {e}")

        return metadata

    def _extract_generic_metadata(self, audio_file, metadata):
        """Extract metadata from generic audio file"""
        try:
            # Get basic audio properties
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                metadata['length'] = getattr(info, 'length', 0)
                metadata['bitrate'] = getattr(info, 'bitrate', 0)
                metadata['sample_rate'] = getattr(info, 'sample_rate', 0)
                metadata['channels'] = getattr(info, 'channels', 2)

            # Handle different tag structures
            if hasattr(audio_file, 'tags') and audio_file.tags:
                for key in audio_file.tags.keys():
                    # Map common tag fields
                    tag_key = key.lower() if hasattr(key, 'lower') else key

                    if 'title' in tag_key:
                        metadata['title'] = str(audio_file.tags[key][0])
                    elif 'artist' in tag_key and 'album' not in tag_key:
                        metadata['artist'] = str(audio_file.tags[key][0])
                    elif 'album' in tag_key and 'artist' not in tag_key:
                        metadata['album'] = str(audio_file.tags[key][0])
                    elif 'genre' in tag_key:
                        metadata['genre'] = str(audio_file.tags[key][0])
                    elif 'year' in tag_key or 'date' in tag_key:
                        metadata['year'] = str(audio_file.tags[key][0])
                    elif 'track' in tag_key:
                        metadata['track'] = str(audio_file.tags[key][0])
        except Exception as e:
            logger.error(f"Error extracting generic metadata: {e}")

        return metadata

    def _create_basic_metadata(self, file_path):
        """Create basic metadata from filename when extraction fails"""
        filename = os.path.splitext(os.path.basename(file_path))[0]

        metadata = {
            'title': filename,
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'genre': 'Unknown Genre',
            'year': 'Unknown Year',
            'track': '0',
            'length': 0,
            'length_formatted': '0:00',
            'bitrate': 0,
            'bitrate_formatted': 'Unknown',
            'sample_rate': 0,
            'channels': 2,
            'path': file_path,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'file_size_formatted': '0 KB'
        }

        # Try to parse artist - title format
        if ' - ' in filename:
            parts = filename.split(' - ', 1)
            metadata['artist'] = parts[0].strip()
            metadata['title'] = parts[1].strip()

            # Try to extract more from the title part (e.g. "Album [2022]")
            title_part = parts[1]
            if '[' in title_part and ']' in title_part:
                bracket_content = title_part[title_part.find('[') + 1:title_part.find(']')]

                # Check if bracket content is a year
                if bracket_content.isdigit() and 1900 <= int(bracket_content) <= 2100:
                    metadata['year'] = bracket_content
                    metadata['title'] = metadata['title'].replace(f'[{bracket_content}]', '').strip()

        return metadata

    def extract_album_art(self, file_path):
        """Extract album art from audio file with better error handling and caching"""
        if not file_path or not os.path.exists(file_path):
            return None

        # Return cached art if available and file hasn't changed
        file_mtime = os.path.getmtime(file_path)
        if file_path in self.art_cache:
            cached_art, cached_mtime = self.art_cache[file_path]
            if cached_mtime == file_mtime:
                return cached_art

        if not MUTAGEN_AVAILABLE:
            return None

        try:
            pixmap = None
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.mp3':
                # MP3 files with ID3 tags
                audio = ID3(file_path)
                for tag in audio.values():
                    if tag.FrameID in ('APIC', 'PIC'):
                        img_data = getattr(tag, 'data', None)
                        if img_data:
                            img = QImage.fromData(img_data)
                            if not img.isNull():
                                pixmap = QPixmap.fromImage(img)
                                break

            elif file_ext == '.flac':
                # FLAC files with embedded pictures
                audio = FLAC(file_path)
                if hasattr(audio, 'pictures') and audio.pictures:
                    img = QImage.fromData(audio.pictures[0].data)
                    if not img.isNull():
                        pixmap = QPixmap.fromImage(img)

            elif file_ext in ['.m4a', '.mp4', '.aac']:
                # MP4/M4A files
                audio = MP4(file_path)
                if 'covr' in audio:
                    for cover in audio['covr']:
                        img = QImage.fromData(cover)
                        if not img.isNull():
                            pixmap = QPixmap.fromImage(img)
                            break

            else:
                # Generic approach for other formats
                audio = File(file_path)
                if hasattr(audio, 'pictures') and audio.pictures:
                    img = QImage.fromData(audio.pictures[0].data)
                    if not img.isNull():
                        pixmap = QPixmap.fromImage(img)

            # Cache the result
            if pixmap and not pixmap.isNull():
                self.art_cache[file_path] = (pixmap, file_mtime)

            return pixmap

        except Exception as e:
            logger.error(f"Error extracting album art: {e}")
            return None

    def get_all_metadata_fields(self, file_path):
        """Get all available metadata fields for a file (for debugging/display)"""
        if not MUTAGEN_AVAILABLE or not file_path or not os.path.exists(file_path):
            return {}

        try:
            audio_file = File(file_path)
            if not audio_file:
                return {}

            all_fields = {}

            # Extract all available tags
            if hasattr(audio_file, 'tags') and audio_file.tags:
                for key in audio_file.tags.keys():
                    key_str = str(key)
                    try:
                        value = audio_file.tags[key]
                        if hasattr(value, 'text'):
                            all_fields[key_str] = str(value.text)
                        else:
                            all_fields[key_str] = str(value)
                    except:
                        all_fields[key_str] = "Error reading tag"

            # For non-ID3 formats
            elif hasattr(audio_file, 'keys'):
                for key in audio_file.keys():
                    try:
                        all_fields[key] = str(audio_file[key])
                    except:
                        all_fields[key] = "Error reading tag"

            return all_fields

        except Exception as e:
            logger.error(f"Error reading all metadata: {e}")
            return {}

    def clear_cache(self):
        """Clear the metadata cache"""
        self.cache = {}
        self.art_cache = {}

    def _format_file_size(self, size_in_bytes):
        """Format file size from bytes to human-readable format"""
        if not size_in_bytes:
            return "0 KB"

        kb_size = size_in_bytes / 1024
        if kb_size < 1024:
            return f"{kb_size:.2f} KB"
        else:
            mb_size = kb_size / 1024
            return f"{mb_size:.2f} MB"