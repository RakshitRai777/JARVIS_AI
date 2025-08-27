import json
import os
import yt_dlp
import vlc
import threading
from datetime import datetime
from typing import List, Dict, Optional


class Track:
    """Represents a single music track with metadata"""

    def __init__(self, title: str, artist: str = "", album: str = "", duration: int = 0,
                 youtube_url: str = "", thumbnail: str = "", video_id: str = ""):
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.youtube_url = youtube_url
        self.thumbnail = thumbnail
        self.video_id = video_id
        self.added_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "youtube_url": self.youtube_url,
            "thumbnail": self.thumbnail,
            "video_id": self.video_id,
            "added_at": self.added_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Track':
        track = cls(
            title=data["title"],
            artist=data.get("artist", ""),
            album=data.get("album", ""),
            duration=data.get("duration", 0),
            youtube_url=data.get("youtube_url", ""),
            thumbnail=data.get("thumbnail", ""),
            video_id=data.get("video_id", "")
        )
        track.added_at = data.get("added_at", datetime.now().isoformat())
        return track


class PlaylistManager:
    """Manages playlist with auto-play and YouTube suggestions"""

    def __init__(self):
        self.current_track: Optional[Track] = None
        self.queue: List[Track] = []
        self.history: List[Track] = []
        self.is_playing = False
        self.auto_play = True
        self.player = None
        self.instance = None
        self.current_index = 0
        self.playlist_file = "playlist_state.json"
        self.lock = threading.Lock()
        self.load_state()

    def load_state(self):
        """Load saved playlist state"""
        if os.path.exists(self.playlist_file):
            try:
                with open(self.playlist_file, 'r') as f:
                    data = json.load(f)
                    self.queue = [Track.from_dict(track) for track in data.get("queue", [])]
                    self.history = [Track.from_dict(track) for track in data.get("history", [])]
                    self.current_index = data.get("current_index", 0)
                    self.auto_play = data.get("auto_play", True)
                    if data.get("current_track"):
                        self.current_track = Track.from_dict(data["current_track"])
            except Exception as e:
                print(f"Error loading playlist state: {e}")

    def save_state(self):
        """Save current playlist state"""
        try:
            data = {
                "queue": [track.to_dict() for track in self.queue],
                "history": [track.to_dict() for track in self.history[-20:]],
                "current_index": self.current_index,
                "auto_play": self.auto_play,
                "current_track": self.current_track.to_dict() if self.current_track else None
            }
            with open(self.playlist_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving playlist state: {e}")

    def add_track(self, title: str, artist: str = "", play_next: bool = False):
        """Add track to queue"""
        with self.lock:
            track = self.fetch_youtube_track(title, artist)
            if track:
                if play_next:
                    self.queue.insert(self.current_index, track)
                else:
                    self.queue.append(track)
                self.save_state()
                return track
            return None

    def fetch_youtube_track(self, title: str, artist: str = "") -> Optional[Track]:
        """Search YouTube for track"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'default_search': 'ytsearch1'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"{title} {artist}", download=False)
                if info and 'entries' in info and info['entries']:
                    entry = info['entries'][0]
                    return Track(
                        title=entry.get('title', 'Unknown'),
                        artist=entry.get('uploader', ''),
                        duration=entry.get('duration', 0),
                        youtube_url=entry.get('webpage_url', ''),
                        thumbnail=entry.get('thumbnail', ''),
                        video_id=entry.get('id', '')
                    )
        except Exception as e:
            print(f"Error fetching YouTube track: {e}")
        return None

    def get_youtube_suggestions(self, current_track: Track) -> List[Track]:
        """Get YouTube suggested videos for auto-play"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'default_search': 'ytsearch',
                'noplaylist': False
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = f"{current_track.title} {current_track.artist}".strip()
                info = ydl.extract_info(f"ytsearch5:{search_query}", download=False)
                suggestions = []
                if info and 'entries' in info:
                    for entry in info['entries'][1:6]:
                        if entry:
                            track = Track(
                                title=entry.get('title', 'Unknown'),
                                artist=entry.get('uploader', ''),
                                duration=entry.get('duration', 0),
                                youtube_url=entry.get('webpage_url', ''),
                                thumbnail=entry.get('thumbnail', ''),
                                video_id=entry.get('id', '')
                            )
                            suggestions.append(track)
                return suggestions
        except Exception as e:
            print(f"Error getting YouTube suggestions: {e}")
            return []

    def play_track(self, track: Track):
        """Play a specific track using VLC"""
        try:
            if not self.instance:
                self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
            media = self.instance.media_new(track.youtube_url)
            self.player.set_media(media)
            self.player.play()
            self.is_playing = True
            self.current_track = track
            self.save_state()
        except Exception as e:
            print(f"Error playing track: {e}")
            self.is_playing = False

    def play_next_track(self):
        """Play the next track in queue or suggestions"""
        with self.lock:
            if self.current_index < len(self.queue):
                track = self.queue[self.current_index]
                self.current_index += 1
                self.history.append(track)
                self.play_track(track)
                return track
            elif self.auto_play and self.current_track:
                suggestions = self.get_youtube_suggestions(self.current_track)
                if suggestions:
                    self.queue.extend(suggestions)
                    track = suggestions[0]
                    self.current_index = len(self.queue) - len(suggestions) + 1
                    self.history.append(track)
                    self.play_track(track)
                    return track
        return None

    def pause(self):
        if self.player:
            self.player.pause()

    def resume(self):
        if self.player:
            self.player.play()

    def skip(self):
        self.play_next_track()

    def clear_queue(self):
        with self.lock:
            self.queue.clear()
            self.current_index = 0
            self.save_state()

    def get_queue_info(self) -> Dict:
        return {
            "current_track": self.current_track.to_dict() if self.current_track else None,
            "queue_length": len(self.queue) - self.current_index,
            "total_queued": len(self.queue),
            "auto_play": self.auto_play,
            "is_playing": self.is_playing
        }


playlist_manager = PlaylistManager()
