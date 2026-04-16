"""
downloader.py — Module tải nhạc từ YouTube
Vinyl Noir Music Manager

Sử dụng yt-dlp (open source) để:
- Trích xuất metadata (title, artist, thumbnail, duration)
- Tải audio và convert sang MP3 qua FFmpeg
- Tải thumbnail làm ảnh bìa album
"""

import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from PIL import Image
except ImportError:
    Image = None


def check_dependencies():
    """Kiểm tra các dependency cần thiết đã cài chưa."""
    missing = []
    if yt_dlp is None:
        missing.append("yt-dlp")
    if Image is None:
        missing.append("Pillow")
    return missing


# Bảng chuyển đổi tiếng Việt → ASCII
_VIET_PAIRS = (
    ('àáảãạ', 'a'), ('ăắằẳẵặ', 'a'), ('âấầẩẫậ', 'a'),
    ('èéẻẽẹ', 'e'), ('êếềểễệ', 'e'),
    ('ìíỉĩị', 'i'),
    ('òóỏõọ', 'o'), ('ôốồổỗộ', 'o'), ('ơớờởỡợ', 'o'),
    ('ùúủũụ', 'u'), ('ưứừửữự', 'u'),
    ('ỳýỷỹỵ', 'y'), ('đ', 'd'),
    ('ÀÁẢÃẠ', 'A'), ('ĂẮẰẲẴẶ', 'A'), ('ÂẤẦẨẪẬ', 'A'),
    ('ÈÉẺẼẸ', 'E'), ('ÊẾỀỂỄỆ', 'E'),
    ('ÌÍỈĨỊ', 'I'),
    ('ÒÓỎÕỌ', 'O'), ('ÔỐỒỔỖỘ', 'O'), ('ƠỚỜỞỠỢ', 'O'),
    ('ÙÚỦŨỤ', 'U'), ('ƯỨỪỬỮỰ', 'U'),
    ('ỲÝỶỸỴ', 'Y'), ('Đ', 'D'),
)
_VIET_MAP = {}
for chars, replacement in _VIET_PAIRS:
    for c in chars:
        _VIET_MAP[ord(c)] = replacement


def sanitize_filename(text):
    """
    Chuyển đổi tên bài hát thành tên file an toàn.
    - Chuyển tiếng Việt → ASCII (tránh URL-encode dài)
    - Bỏ ký tự đặc biệt
    - Giới hạn 60 ký tự
    """
    # Bước 1: Chuyển tiếng Việt → ASCII
    cleaned = text.translate(_VIET_MAP)
    # Bước 2: Bỏ ký tự không hợp lệ (giữ chữ, số, dấu gạch, dấu chấm)
    cleaned = re.sub(r'[<>:"/\\|?*\[\]{}()!@#$%^&+=~`\',:;]', '', cleaned)
    # Bước 3: Thay khoảng trắng / ký tự lạ bằng gạch dưới
    cleaned = re.sub(r'[^a-zA-Z0-9._-]', '_', cleaned)
    # Bước 4: Bỏ gạch dưới liên tiếp
    cleaned = re.sub(r'_+', '_', cleaned)
    # Bước 5: Giới hạn 60 ký tự (tránh URL quá dài trên GitHub Pages)
    cleaned = cleaned.strip('_.- ')[:60].rstrip('_.- ')
    return cleaned if cleaned else 'untitled'


def get_video_info(url):
    """
    Trích xuất metadata từ video YouTube mà KHÔNG tải video.
    
    Args:
        url: URL video YouTube
        
    Returns:
        dict với keys: title, artist, duration, duration_str, 
              thumbnail_url, video_id, filesize_approx
        hoặc None nếu lỗi
    """
    if yt_dlp is None:
        raise RuntimeError("yt-dlp chưa được cài. Chạy: pip install yt-dlp")

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            return None

        # Lấy thời lượng
        duration = info.get('duration', 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        # Ước lượng file size (bitrate * duration)
        # MP3 192kbps ~ 24KB/s
        approx_size_mb = round((24 * duration) / 1024, 1)

        # Lấy thumbnail chất lượng cao nhất
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = ''
        if thumbnails:
            # Lọc thumbnail có URL hợp lệ, ưu tiên chất lượng cao
            valid_thumbs = [t for t in thumbnails if t.get('url')]
            if valid_thumbs:
                thumbnail_url = valid_thumbs[-1]['url']

        # Xác định artist
        artist = (
            info.get('artist') or
            info.get('creator') or
            info.get('uploader') or
            info.get('channel') or
            'Không rõ'
        )

        # Xác định title
        title = info.get('track') or info.get('title') or 'Không rõ tên'

        return {
            'title': title,
            'artist': artist,
            'duration': duration,
            'duration_str': f"{minutes}:{seconds:02d}",
            'thumbnail_url': thumbnail_url,
            'video_id': info.get('id', ''),
            'filesize_approx': approx_size_mb,
            'album': info.get('album', ''),
            'webpage_url': info.get('webpage_url', url),
            '_raw_formats': info.get('formats', []),
        }

    except yt_dlp.utils.DownloadError as e:
        raise RuntimeError(f"Không thể truy cập video: {e}")
    except Exception as e:
        raise RuntimeError(f"Lỗi trích xuất metadata: {e}")


def download_audio(url, output_dir, quality='192', ffmpeg_path=None, progress_callback=None):
    """
    Tải audio từ YouTube và convert sang MP3.
    
    Args:
        url: URL video YouTube
        output_dir: Thư mục lưu file MP3
        quality: Bitrate MP3 (128, 192, 320)
        ffmpeg_path: Đường dẫn FFmpeg (None = dùng PATH)
        progress_callback: Hàm callback(percent, status_text)
        
    Returns:
        dict: {filepath, filename, title, artist} hoặc None nếu lỗi
    """
    if yt_dlp is None:
        raise RuntimeError("yt-dlp chưa được cài. Chạy: pip install yt-dlp")

    # Đảm bảo output dir tồn tại
    os.makedirs(output_dir, exist_ok=True)

    # Lấy info trước để tạo tên file
    info = get_video_info(url)
    if not info:
        raise RuntimeError("Không lấy được thông tin video")

    filename_base = sanitize_filename(info['title'])
    output_template = os.path.join(output_dir, f"{filename_base}.%(ext)s")

    # Cấu hình yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': str(quality),
        }],
        'postprocessor_args': [
            '-metadata', f'title={info["title"]}',
            '-metadata', f'artist={info["artist"]}',
        ],
    }

    # Thêm FFmpeg path nếu có
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path

    # Progress hook
    def progress_hook(d):
        if progress_callback and d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                progress_callback(percent, f"Đang tải... {percent:.0f}%")
        elif progress_callback and d['status'] == 'finished':
            progress_callback(100, "Đang convert sang MP3...")

    ydl_opts['progress_hooks'] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Tìm file MP3 đã tạo
        mp3_path = os.path.join(output_dir, f"{filename_base}.mp3")
        if not os.path.exists(mp3_path):
            # Thử tìm file với tên gần giống
            for f in os.listdir(output_dir):
                if f.startswith(filename_base[:20]) and f.endswith('.mp3'):
                    mp3_path = os.path.join(output_dir, f)
                    break

        if not os.path.exists(mp3_path):
            raise RuntimeError("Không tìm thấy file MP3 sau khi convert")

        return {
            'filepath': mp3_path,
            'filename': os.path.basename(mp3_path),
            'title': info['title'],
            'artist': info['artist'],
            'duration': info['duration'],
            'album': info.get('album', ''),
        }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
            raise RuntimeError(
                "FFmpeg chưa được cài đặt!\n"
                "Tải FFmpeg tại: https://ffmpeg.org/download.html\n"
                "Hoặc chạy: winget install ffmpeg"
            )
        raise RuntimeError(f"Lỗi tải audio: {e}")


# ===== LYRICS =====

def fetch_lyrics(title, artist, duration=0):
    """
    Lấy lyrics từ LRCLIB API (miễn phí, không cần API key).
    
    Tự động clean YouTube title để tìm chính xác hơn.
    Thử nhiều chiến lược tìm kiếm.
    
    Args:
        title: Tên bài hát (có thể là YouTube title dài)
        artist: Tên nghệ sĩ (có thể là channel name)
        duration: Thời lượng (giây), để match chính xác hơn
    
    Returns:
        str: Lyrics text (LRC format nếu có, plain text nếu không) hoặc ''
    """
    import re as _re

    def _clean_title(raw):
        """Clean YouTube title → (song_name, extracted_artist)"""
        t = raw
        noise = [
            r'\(Official\s*(MV|Music\s*Video|Video|Audio|Lyric\s*Video)\)',
            r'\[Official\s*(MV|Music\s*Video|Video|Audio)\]',
            r'\(LIVE\)', r'\(Live\s*(?:at|version|concert|in).*?\)',
            r'\bOfficial\s*(MV|Music\s*Video|Video)\b',
            r'\bLyric\s*Video\b', r'\bMV\b',
            r'\bvideo\s*by\s*\w+', r'\bLIVE\s*VERSION\s*AT\b.*$',
            r'\bLive\s*Concert\b.*$', r'\bSáng\s*tác:?\s*.*$',
            r'\|\|.*$', r'Giọng\s*Ca.*$', r'Bản\s*Tình\s*Ca.*$',
            r'Nhạc\s*Vàn?g?.*$', r'\d{4}$', r'4K\b',
        ]
        for p in noise:
            t = _re.sub(p, '', t, flags=_re.IGNORECASE)
        
        ext_artist = ''
        for sep in [' - ', ' – ', ' — ']:
            if sep in t:
                parts = t.split(sep, 1)
                t = parts[0].strip()
                ext_artist = parts[1].strip()
                break
        if not ext_artist:
            for sep in [' | ', ' │ ']:
                if sep in t:
                    parts = t.split(sep, 1)
                    t = parts[0].strip()
                    ext_artist = parts[1].strip()
                    break
        
        if ext_artist:
            ext_artist = _re.sub(
                r'\s*(Official|Tube|Channel|Music|Entertainment)\s*$',
                '', ext_artist, flags=_re.IGNORECASE
            ).strip()

        t = _re.sub(r'\s*[\(\[].*?[\)\]]', '', t)
        t = _re.sub(r'\s{2,}', ' ', t).strip()
        return t, ext_artist

    def _search_lrclib(q_title, q_artist, dur=0):
        """Gọi LRCLIB API, trả về lyrics string hoặc ''"""
        try:
            query = urllib.parse.urlencode({'q': f'{q_title} {q_artist}'.strip()})
            url = f'https://lrclib.net/api/search?{query}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'VinylNoir/1.0 (https://github.com)',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            if not data or not isinstance(data, list):
                return ''
            
            best = None
            for item in data:
                if item.get('syncedLyrics'):
                    if dur > 0:
                        item_dur = item.get('duration', 0)
                        if item_dur and abs(item_dur - dur) < 15:
                            best = item
                            break
                    else:
                        best = item
                        break
            if not best:
                for item in data:
                    if item.get('syncedLyrics'):
                        best = item
                        break
            if not best:
                for item in data:
                    if item.get('plainLyrics'):
                        best = item
                        break
            
            if not best:
                return ''
            return best.get('syncedLyrics') or best.get('plainLyrics') or ''
        except Exception:
            return ''

    try:
        clean_name, extracted_artist = _clean_title(title)
        search_artist = extracted_artist or artist

        # Thử 1: Title đã clean + artist
        result = _search_lrclib(clean_name, search_artist, duration)
        if result:
            return result

        # Thử 2: Chỉ title (bỏ artist)
        if search_artist:
            result = _search_lrclib(clean_name, '', duration)
            if result:
                return result

        # Thử 3: Title + channel name (nếu khác extracted_artist)
        if extracted_artist and artist != extracted_artist:
            result = _search_lrclib(clean_name, artist, duration)
            if result:
                return result

        return ''
    except Exception as e:
        print(f"[Downloader] Lỗi lấy lyrics: {e}")
        return ''


# ===== FORMAT CHOICES =====

def build_format_choices(raw_formats, duration=0):
    """
    Tạo danh sách lựa chọn format cho user.

    Args:
        raw_formats: list format từ get_video_info()['_raw_formats']
        duration: Thời lượng video (giây), dùng ước tính file size

    Returns:
        list of dict — mỗi dict chứa: key, label, category,
                       ydl_format, postprocessors, output_ext
    """
    choices = []

    # --- MP3 PRESETS (luôn có sẵn) ---
    for quality, suffix in [('320', 'cao nhất'), ('192', 'tiêu chuẩn'), ('128', 'nhỏ gọn')]:
        est_kb = int(quality) * duration // 8 if duration else 0
        est_mb = round(est_kb / 1024, 1) if est_kb else 0
        size_str = f" (~{est_mb} MB)" if est_mb else ""
        choices.append({
            'key': f'mp3_{quality}',
            'label': f"\U0001f3b5 MP3 {quality}kbps \u2014 {suffix}{size_str}",
            'category': 'audio',
            'ydl_format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'output_ext': 'mp3',
        })

    if not raw_formats:
        return choices

    # --- AUDIO GỐC (Opus, AAC — không convert, giữ chất lượng) ---
    seen_audio = set()
    for f in raw_formats:
        vcodec = f.get('vcodec', 'none') or 'none'
        acodec = f.get('acodec', 'none') or 'none'
        if vcodec != 'none' or acodec == 'none':
            continue

        abr = f.get('abr') or f.get('tbr') or 0
        ext = f.get('ext', '')
        if abr < 30:
            continue

        codec_name = ('Opus' if 'opus' in acodec.lower() else
                      'AAC/M4A' if 'mp4a' in acodec.lower() else
                      ext.upper())

        dedup = f"{codec_name}_{int(abr)}"
        if dedup in seen_audio:
            continue
        seen_audio.add(dedup)

        filesize = f.get('filesize') or f.get('filesize_approx') or 0
        size_mb = round(filesize / (1024 * 1024), 1) if filesize else 0
        size_str = f" ({size_mb} MB)" if size_mb else ""

        choices.append({
            'key': f'original_{f.get("format_id", "")}',
            'label': f"\U0001f3b5 {codec_name} {int(abr)}kbps \u2014 g\u1ed1c, kh\u00f4ng convert{size_str}",
            'category': 'audio_original',
            'ydl_format': f.get('format_id', ''),
            'postprocessors': [],
            'output_ext': ext,
        })

    # --- VIDEO (muxed + merge) ---
    available_heights = {}
    for f in raw_formats:
        vcodec = f.get('vcodec', 'none') or 'none'
        acodec = f.get('acodec', 'none') or 'none'
        height = f.get('height', 0) or 0
        if vcodec == 'none' or height < 144:
            continue

        is_muxed = acodec != 'none'
        filesize = f.get('filesize') or f.get('filesize_approx') or 0

        # Ưu tiên muxed stream (đã có audio sẵn)
        if height not in available_heights or is_muxed:
            available_heights[height] = {
                'format_id': f.get('format_id', ''),
                'is_muxed': is_muxed,
                'filesize': filesize,
            }

    for h in sorted(available_heights.keys(), reverse=True):
        v = available_heights[h]
        if v['is_muxed']:
            ydl_fmt = v['format_id']
            merge_note = ""
        else:
            ydl_fmt = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
            merge_note = " \u26a1gh\u00e9p"

        size_mb = round(v['filesize'] / (1024 * 1024), 1) if v['filesize'] else 0
        size_str = f" (~{size_mb} MB)" if size_mb else ""

        choices.append({
            'key': f'video_{h}p',
            'label': f"\U0001f3ac Video {h}p MP4{merge_note}{size_str}",
            'category': 'video',
            'ydl_format': ydl_fmt,
            'postprocessors': [],
            'output_ext': 'mp4',
            'merge_output_format': 'mp4',
        })

    return choices


def download_with_format(url, format_choice, output_dir, info=None,
                         ffmpeg_path=None, progress_callback=None):
    """
    Tải media từ YouTube với format đã chọn.

    Args:
        url: URL YouTube
        format_choice: dict từ build_format_choices()
        output_dir: Thư mục lưu output
        info: metadata dict (từ get_video_info), None = tự fetch
        ffmpeg_path: Đường dẫn FFmpeg
        progress_callback: callback(percent, status_text)

    Returns:
        dict: {filepath, filename, title, artist, duration, ext, category}
    """
    if yt_dlp is None:
        raise RuntimeError("yt-dlp ch\u01b0a \u0111\u01b0\u1ee3c c\u00e0i.")

    os.makedirs(output_dir, exist_ok=True)

    if not info:
        info = get_video_info(url)
    if not info:
        raise RuntimeError("Kh\u00f4ng l\u1ea5y \u0111\u01b0\u1ee3c th\u00f4ng tin video")

    filename_base = sanitize_filename(info['title'])
    output_ext = format_choice.get('output_ext', 'mp3')
    output_template = os.path.join(output_dir, f"{filename_base}.%(ext)s")

    ydl_opts = {
        'format': format_choice['ydl_format'],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }

    # Postprocessors (convert MP3, etc.)
    if format_choice.get('postprocessors'):
        ydl_opts['postprocessors'] = format_choice['postprocessors']
        ydl_opts['postprocessor_args'] = [
            '-metadata', f'title={info["title"]}',
            '-metadata', f'artist={info["artist"]}',
        ]

    # Merge format cho video (ghép video-only + audio-only)
    if format_choice.get('merge_output_format'):
        ydl_opts['merge_output_format'] = format_choice['merge_output_format']

    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path

    # Progress hook
    def progress_hook(d):
        if progress_callback and d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                progress_callback(percent, f"\u0110ang t\u1ea3i... {percent:.0f}%")
        elif progress_callback and d['status'] == 'finished':
            progress_callback(100, "\u0110ang x\u1eed l\u00fd file...")

    ydl_opts['progress_hooks'] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Tìm file output
        expected_path = os.path.join(output_dir, f"{filename_base}.{output_ext}")
        if os.path.exists(expected_path):
            final_path = expected_path
        else:
            # Tìm file mới nhất có tên khớp
            final_path = None
            for fname in sorted(
                os.listdir(output_dir),
                key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
                reverse=True
            ):
                fpath = os.path.join(output_dir, fname)
                if (fname.startswith(filename_base[:20])
                        and not fname.endswith(('.tmp', '.part'))
                        and os.path.isfile(fpath)):
                    final_path = fpath
                    break

            if not final_path:
                raise RuntimeError("Kh\u00f4ng t\u00ecm th\u1ea5y file sau khi t\u1ea3i")

        actual_ext = os.path.splitext(final_path)[1].lstrip('.')

        return {
            'filepath': final_path,
            'filename': os.path.basename(final_path),
            'title': info['title'],
            'artist': info['artist'],
            'duration': info.get('duration', 0),
            'album': info.get('album', ''),
            'ext': actual_ext,
            'category': format_choice.get('category', 'audio'),
        }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
            raise RuntimeError(
                "FFmpeg ch\u01b0a \u0111\u01b0\u1ee3c c\u00e0i \u0111\u1eb7t!\n"
                "C\u1ea7n FFmpeg \u0111\u1ec3 convert audio ho\u1eb7c gh\u00e9p video.\n"
                "T\u1ea3i: https://ffmpeg.org/download.html"
            )
        raise RuntimeError(f"L\u1ed7i t\u1ea3i: {e}")


def download_thumbnail(thumbnail_url, output_path, size=(500, 500)):
    """
    Tải thumbnail và resize làm ảnh bìa album.
    
    Args:
        thumbnail_url: URL ảnh thumbnail
        output_path: Đường dẫn lưu ảnh
        size: Kích thước target (width, height)
        
    Returns:
        str: Đường dẫn file ảnh đã lưu
    """
    if not thumbnail_url:
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Tải ảnh
        temp_path = output_path + '.tmp'
        urllib.request.urlretrieve(thumbnail_url, temp_path)

        # Resize bằng Pillow nếu có
        if Image is not None:
            img = Image.open(temp_path)
            img = img.convert('RGB')

            # Crop square từ center
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))

            # Resize
            img = img.resize(size, Image.LANCZOS)
            img.save(output_path, 'JPEG', quality=85)
            os.remove(temp_path)
        else:
            # Không có Pillow, giữ nguyên ảnh gốc
            os.rename(temp_path, output_path)

        return output_path

    except Exception as e:
        # Dọn file tạm nếu lỗi
        for f in [temp_path, output_path + '.tmp']:
            if os.path.exists(f):
                os.remove(f)
        print(f"[Downloader] Lỗi tải thumbnail: {e}")
        return None


def is_valid_youtube_url(url):
    """Kiểm tra URL có phải YouTube hợp lệ không."""
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?music\.youtube\.com/watch\?v=[\w-]+',
    ]
    return any(re.match(pattern, url.strip()) for pattern in youtube_patterns)
