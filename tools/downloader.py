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
_VIET_MAP = str.maketrans(
    'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'
    'ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ',
    'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd'
    'AAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD'
)


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
