"""
music_manager.py — Desktop Music Manager GUI
Vinyl Noir Music Manager

App phụ chạy trên máy tính:
- Dán link YouTube → preview metadata
- Tải MP3 + cover thumbnail
- Tự động cập nhật playlist.json
- Git push lên GitHub → PWA tự cập nhật
"""

import os
import sys
import json
import threading
import webbrowser
import time
from pathlib import Path
from datetime import datetime

# Thêm thư mục tools vào path
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TOOLS_DIR)

# Import modules
try:
    import customtkinter as ctk
except ImportError:
    print("❌ Thiếu customtkinter! Chạy: pip install customtkinter")
    sys.exit(1)

from downloader import (
    check_dependencies, get_video_info, download_audio,
    download_thumbnail, is_valid_youtube_url, sanitize_filename
)
from github_uploader import (
    check_git_installed, check_repo_status, update_playlist_json,
    git_add_commit_push, get_repo_size, git_pull,
    remove_song_from_playlist, git_remove_and_push
)


# ===== CẤU HÌNH =====
def load_config():
    """Load cấu hình từ config.json."""
    config_path = os.path.join(TOOLS_DIR, 'config.json')
    default_config = {
        'repo_path': REPO_DIR,
        'audio_dir': 'assets/audio',
        'covers_dir': 'assets/covers',
        'playlist_file': 'data/playlist.json',
        'git_branch': 'main',
        'audio_quality': '192',
        'audio_format': 'mp3',
        'max_file_size_mb': 95,
        'auto_push': True,
        'ffmpeg_path': '',
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # Merge với default (để có key mới nếu config cũ thiếu)
            default_config.update(loaded)
        except (json.JSONDecodeError, IOError):
            pass

    # Auto-detect repo_path nếu trống
    if not default_config['repo_path']:
        default_config['repo_path'] = REPO_DIR

    return default_config


def save_config(config):
    """Lưu cấu hình vào config.json."""
    config_path = os.path.join(TOOLS_DIR, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


# ===== APP CHÍNH =====
class MusicManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config
        self.config = load_config()

        # State
        self.current_info = None
        self.is_downloading = False
        self.download_queue = []

        # Window setup
        self.title("🎵 Vinyl Noir — Music Manager")
        self.geometry("820x680")
        self.minsize(700, 580)

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Custom colors
        self.GOLD = "#e8a838"
        self.GOLD_DIM = "#c48820"
        self.BG_DARK = "#0d0d0f"
        self.BG_CARD = "#1a1a2e"

        self.configure(fg_color=self.BG_DARK)

        self._build_ui()
        self._check_initial_status()

    def _build_ui(self):
        """Xây dựng giao diện."""
        # ===== HEADER =====
        header = ctk.CTkFrame(self, fg_color=self.BG_CARD, corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="🎵 Vinyl Noir — Music Manager",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.GOLD
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            header, text="⚙️ Cài đặt", width=90, height=32,
            fg_color="transparent", hover_color="#2a2a3e",
            command=self._open_settings
        ).pack(side="right", padx=8)

        ctk.CTkButton(
            header, text="📋 Quản lý", width=90, height=32,
            fg_color="transparent", hover_color="#2a2a3e",
            command=self._open_song_manager
        ).pack(side="right", padx=0)

        # ===== INPUT SECTION =====
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            input_frame, text="Dán link YouTube:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        input_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_row.pack(fill="x")

        self.url_entry = ctk.CTkEntry(
            input_row, placeholder_text="https://www.youtube.com/watch?v=...",
            height=40, font=ctk.CTkFont(size=13),
            border_color=self.GOLD_DIM
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Bind Enter key
        self.url_entry.bind('<Return>', lambda e: self._fetch_info())

        # Bind Ctrl+V auto-fetch
        self.url_entry.bind('<Control-v>', lambda e: self.after(100, self._auto_fetch_on_paste))

        self.fetch_btn = ctk.CTkButton(
            input_row, text="🔍 Tìm", width=80, height=40,
            fg_color=self.GOLD, hover_color=self.GOLD_DIM,
            text_color="#0d0d0f", font=ctk.CTkFont(size=13, weight="bold"),
            command=self._fetch_info
        )
        self.fetch_btn.pack(side="right")

        # ===== PREVIEW SECTION =====
        self.preview_frame = ctk.CTkFrame(self, fg_color=self.BG_CARD, corner_radius=12)
        self.preview_frame.pack(fill="x", padx=16, pady=6)

        preview_inner = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_inner.pack(fill="x", padx=16, pady=12)

        self.preview_label = ctk.CTkLabel(
            preview_inner, text="📋 Dán link YouTube và nhấn 🔍 để xem trước",
            font=ctk.CTkFont(size=13),
            text_color="#8a8a9a"
        )
        self.preview_label.pack(anchor="w")

        self.info_labels = {}
        for key, label_text in [('title', '🎵 Tên bài'), ('artist', '🎤 Nghệ sĩ'),
                                 ('duration', '⏱ Thời lượng'), ('size', '💾 Kích thước ước tính')]:
            row = ctk.CTkFrame(preview_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{label_text}:", font=ctk.CTkFont(size=12), 
                        text_color="#8a8a9a", width=130, anchor="w").pack(side="left")
            self.info_labels[key] = ctk.CTkLabel(
                row, text="—", font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            self.info_labels[key].pack(side="left", fill="x", expand=True)

        # Nút hành động
        btn_row = ctk.CTkFrame(preview_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8, 0))

        self.listen_btn = ctk.CTkButton(
            btn_row, text="▶ Nghe thử (YouTube)", width=160, height=36,
            fg_color="transparent", border_width=1, border_color="#555",
            hover_color="#2a2a3e", state="disabled",
            command=self._open_youtube
        )
        self.listen_btn.pack(side="left", padx=(0, 8))

        self.download_btn = ctk.CTkButton(
            btn_row, text="⬇️ Tải & Push GitHub", width=180, height=36,
            fg_color=self.GOLD, hover_color=self.GOLD_DIM,
            text_color="#0d0d0f", font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            command=self._start_download
        )
        self.download_btn.pack(side="left")

        # ===== PROGRESS BAR =====
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=16, pady=(2, 4))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, progress_color=self.GOLD, height=6
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="", font=ctk.CTkFont(size=11),
            text_color="#8a8a9a"
        )
        self.progress_label.pack(anchor="w")

        # ===== LOG PANEL =====
        log_label = ctk.CTkLabel(
            self, text="📝 Log", font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        log_label.pack(fill="x", padx=16, pady=(4, 2))

        self.log_text = ctk.CTkTextbox(
            self, height=140, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=self.BG_CARD, border_color="#2a2a3e", border_width=1,
            corner_radius=8
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        # ===== FOOTER STATUS BAR =====
        footer = ctk.CTkFrame(self, fg_color=self.BG_CARD, corner_radius=0, height=36)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            footer, text="📊 Đang kiểm tra...",
            font=ctk.CTkFont(size=11), text_color="#8a8a9a"
        )
        self.status_label.pack(side="left", padx=16)

        self.git_status_label = ctk.CTkLabel(
            footer, text="",
            font=ctk.CTkFont(size=11), text_color="#8a8a9a"
        )
        self.git_status_label.pack(side="right", padx=16)

    def _log(self, message):
        """Thêm log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def _check_initial_status(self):
        """Kiểm tra trạng thái ban đầu."""
        # Kiểm tra dependencies
        missing = check_dependencies()
        if missing:
            self._log(f"⚠️ Thiếu thư viện: {', '.join(missing)}")
            self._log(f"   Chạy: pip install {' '.join(missing)}")

        # Kiểm tra Git
        if check_git_installed():
            self._log("✅ Git đã sẵn sàng")
        else:
            self._log("❌ Git chưa cài! Tải: https://git-scm.com")

        # Kiểm tra repo
        repo_status = check_repo_status(self.config['repo_path'])
        if repo_status['valid']:
            self._log(f"✅ Git repo: {repo_status['remote_url']}")
            self.git_status_label.configure(text=f"🔗 {repo_status['remote_url']}")
        else:
            self._log(f"⚠️ Git repo: {repo_status['error']}")

        # Cập nhật repo size
        self._update_repo_stats()

    def _update_repo_stats(self):
        """Cập nhật thống kê repo."""
        try:
            stats = get_repo_size(self.config['repo_path'])
            self.status_label.configure(
                text=f"📊 Repo: {stats['total_mb']} MB / 1000 MB  |  🎵 {stats['audio_count']} bài ({stats['audio_mb']} MB)"
            )
        except Exception:
            self.status_label.configure(text="📊 Không thể đọc thống kê repo")

    def _auto_fetch_on_paste(self):
        """Tự động tìm kiếm khi paste URL."""
        url = self.url_entry.get().strip()
        if is_valid_youtube_url(url):
            self._fetch_info()

    def _fetch_info(self):
        """Lấy metadata từ URL YouTube."""
        url = self.url_entry.get().strip()

        if not url:
            self._log("⚠️ Vui lòng nhập URL YouTube")
            return

        if not is_valid_youtube_url(url):
            self._log(f"⚠️ URL không hợp lệ: {url}")
            return

        self.fetch_btn.configure(state="disabled", text="⏳...")
        self._log(f"🔍 Đang tìm: {url}")

        def fetch_thread():
            try:
                info = get_video_info(url)
                self.current_info = info
                self.after(0, lambda: self._display_info(info))
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Lỗi: {e}"))
            finally:
                self.after(0, lambda: self.fetch_btn.configure(state="normal", text="🔍 Tìm"))

        threading.Thread(target=fetch_thread, daemon=True).start()

    def _display_info(self, info):
        """Hiện metadata lên preview."""
        if not info:
            self._log("❌ Không lấy được thông tin video")
            return

        self.info_labels['title'].configure(text=info['title'])
        self.info_labels['artist'].configure(text=info['artist'])
        self.info_labels['duration'].configure(text=info['duration_str'])
        self.info_labels['size'].configure(text=f"~{info['filesize_approx']} MB")
        self.preview_label.configure(text="")

        self.listen_btn.configure(state="normal")
        self.download_btn.configure(state="normal")

        self._log(f"✅ Tìm thấy: {info['title']} — {info['artist']} ({info['duration_str']})")

    def _open_youtube(self):
        """Mở link YouTube trong trình duyệt."""
        if self.current_info:
            url = self.current_info.get('webpage_url', '')
            if url:
                webbrowser.open(url)

    def _start_download(self):
        """Bắt đầu tải audio và push lên GitHub."""
        if self.is_downloading:
            self._log("⚠️ Đang tải bài khác, vui lòng đợi")
            return

        if not self.current_info:
            self._log("⚠️ Chưa có thông tin bài hát")
            return

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳ Đang xử lý...")
        self.progress_bar.set(0)

        def download_thread():
            try:
                self._do_download_and_push()
            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Lỗi: {e}"))
            finally:
                self.is_downloading = False
                self.after(0, lambda: self.download_btn.configure(
                    state="normal", text="⬇️ Tải & Push GitHub"
                ))
                self.after(0, lambda: self._update_repo_stats())

        threading.Thread(target=download_thread, daemon=True).start()

    def _do_download_and_push(self):
        """Luồng xử lý tải + push (chạy trên thread riêng)."""
        info = self.current_info
        config = self.config
        repo_path = config['repo_path']

        url = self.url_entry.get().strip()
        audio_dir = os.path.join(repo_path, config['audio_dir'])
        covers_dir = os.path.join(repo_path, config['covers_dir'])

        # Step 1: Tải audio
        self.after(0, lambda: self._log("⬇️ Bước 1/4: Đang tải audio..."))
        self.after(0, lambda: self.progress_label.configure(text="Đang tải audio..."))

        def on_progress(percent, status):
            self.after(0, lambda p=percent: self.progress_bar.set(p / 100 * 0.5))
            self.after(0, lambda s=status: self.progress_label.configure(text=s))

        result = download_audio(
            url, audio_dir,
            quality=config['audio_quality'],
            ffmpeg_path=config.get('ffmpeg_path') or None,
            progress_callback=on_progress
        )

        if not result:
            self.after(0, lambda: self._log("❌ Tải audio thất bại!"))
            return

        mp3_filename = result['filename']
        mp3_relative = f"{config['audio_dir']}/{mp3_filename}"
        self.after(0, lambda: self._log(f"✅ Đã tải: {mp3_filename}"))

        # Step 2: Tải thumbnail
        self.after(0, lambda: self._log("🖼 Bước 2/4: Đang tải ảnh bìa..."))
        self.after(0, lambda: self.progress_bar.set(0.55))

        cover_filename = sanitize_filename(info['title']) + '.jpg'
        cover_path = os.path.join(covers_dir, cover_filename)
        cover_relative = f"{config['covers_dir']}/{cover_filename}"

        cover_result = download_thumbnail(info.get('thumbnail_url', ''), cover_path)
        if cover_result:
            self.after(0, lambda: self._log(f"✅ Ảnh bìa: {cover_filename}"))
        else:
            cover_relative = "assets/covers/default-cover.jpg"
            self.after(0, lambda: self._log("⚠️ Dùng ảnh bìa mặc định"))

        # Step 3: Cập nhật playlist.json
        self.after(0, lambda: self._log("📝 Bước 3/4: Cập nhật playlist.json..."))
        self.after(0, lambda: self.progress_bar.set(0.7))

        song_id = sanitize_filename(info['title']).lower()
        song_data = {
            'id': song_id,
            'title': info['title'],
            'artist': info['artist'],
            'album': info.get('album', ''),
            'cover': cover_relative,
            'audioUrl': mp3_relative,
            'duration': info.get('duration', 0),
            'lyrics': '',
            'favorite': False
        }

        update_playlist_json(repo_path, config['playlist_file'], song_data)
        self.after(0, lambda: self._log("✅ playlist.json đã cập nhật"))

        # Step 4: Git push
        if config.get('auto_push', True):
            self.after(0, lambda: self._log("🚀 Bước 4/4: Đang push lên GitHub..."))
            self.after(0, lambda: self.progress_bar.set(0.8))
            self.after(0, lambda: self.progress_label.configure(text="Đang push lên GitHub..."))

            files_to_push = [
                mp3_relative,
                config['playlist_file'],
            ]
            if cover_result:
                files_to_push.append(cover_relative)

            commit_msg = f"🎵 Add: {info['title']} - {info['artist']}"
            push_result = git_add_commit_push(
                repo_path, files_to_push, commit_msg,
                branch=config['git_branch']
            )

            if push_result['success']:
                self.after(0, lambda: self._log(f"🎉 Đã push thành công! Bài '{info['title']}' đã lên GitHub."))
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.progress_label.configure(text="✅ Hoàn tất!"))
            else:
                self.after(0, lambda e=push_result['error']: self._log(f"❌ Push thất bại: {e}"))
                self.after(0, lambda: self.progress_label.configure(text="❌ Push thất bại"))
        else:
            self.after(0, lambda: self._log("ℹ️ Auto-push tắt. File đã lưu local."))
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.progress_label.configure(text="✅ Đã lưu local"))

    def _open_settings(self):
        """Mở cửa sổ cài đặt."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("⚙️ Cài đặt")
        settings_window.geometry("500x400")
        settings_window.transient(self)
        settings_window.grab_set()

        content = ctk.CTkFrame(settings_window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Repo path
        ctk.CTkLabel(content, text="📁 Đường dẫn Repo:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        repo_entry = ctk.CTkEntry(content, height=36)
        repo_entry.pack(fill="x", pady=(0, 12))
        repo_entry.insert(0, self.config['repo_path'])

        # Git branch
        ctk.CTkLabel(content, text="🔀 Git Branch:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        branch_entry = ctk.CTkEntry(content, height=36)
        branch_entry.pack(fill="x", pady=(0, 12))
        branch_entry.insert(0, self.config['git_branch'])

        # Audio quality
        ctk.CTkLabel(content, text="🎧 Chất lượng MP3:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        quality_var = ctk.StringVar(value=self.config['audio_quality'])
        quality_frame = ctk.CTkFrame(content, fg_color="transparent")
        quality_frame.pack(fill="x", pady=(0, 12))
        for q in ['128', '192', '320']:
            ctk.CTkRadioButton(
                quality_frame, text=f"{q} kbps", variable=quality_var, value=q
            ).pack(side="left", padx=(0, 16))

        # FFmpeg path
        ctk.CTkLabel(content, text="🔧 FFmpeg path (trống = tự tìm):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        ffmpeg_entry = ctk.CTkEntry(content, height=36)
        ffmpeg_entry.pack(fill="x", pady=(0, 12))
        ffmpeg_entry.insert(0, self.config.get('ffmpeg_path', ''))

        # Auto push
        auto_push_var = ctk.BooleanVar(value=self.config.get('auto_push', True))
        ctk.CTkCheckBox(content, text="🚀 Tự động push lên GitHub sau khi tải", variable=auto_push_var).pack(anchor="w", pady=(0, 12))

        # Save button
        def save_settings():
            self.config['repo_path'] = repo_entry.get().strip()
            self.config['git_branch'] = branch_entry.get().strip() or 'main'
            self.config['audio_quality'] = quality_var.get()
            self.config['ffmpeg_path'] = ffmpeg_entry.get().strip()
            self.config['auto_push'] = auto_push_var.get()
            save_config(self.config)
            self._log("✅ Đã lưu cài đặt")
            settings_window.destroy()

        ctk.CTkButton(
            content, text="💾 Lưu cài đặt", height=40,
            fg_color=self.GOLD, hover_color=self.GOLD_DIM,
            text_color="#0d0d0f", font=ctk.CTkFont(size=14, weight="bold"),
            command=save_settings
        ).pack(fill="x", pady=(8, 0))

    def _open_song_manager(self):
        """Mở cửa sổ quản lý bài hát."""
        mgr = ctk.CTkToplevel(self)
        mgr.title("📋 Quản lý bài hát")
        mgr.geometry("650x520")
        mgr.transient(self)
        mgr.grab_set()
        mgr.configure(fg_color=self.BG_DARK)

        # Header
        hdr = ctk.CTkFrame(mgr, fg_color=self.BG_CARD, corner_radius=0, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="📋 Quản lý bài hát trên GitHub",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.GOLD
        ).pack(side="left", padx=16)

        refresh_btn = ctk.CTkButton(
            hdr, text="🔄 Làm mới", width=80, height=28,
            fg_color="transparent", hover_color="#2a2a3e",
            command=lambda: self._load_songs_into_manager(scroll_frame, mgr)
        )
        refresh_btn.pack(side="right", padx=8)

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(
            mgr, fg_color="transparent",
            scrollbar_button_color="#333",
            scrollbar_button_hover_color="#555"
        )
        scroll_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self._load_songs_into_manager(scroll_frame, mgr)

    def _load_songs_into_manager(self, scroll_frame, mgr_window):
        """Load danh sách bài hát vào cửa sổ quản lý."""
        # Xóa nội dung cũ
        for widget in scroll_frame.winfo_children():
            widget.destroy()

        # Đọc playlist.json
        config = self.config
        playlist_path = os.path.join(config['repo_path'], config['playlist_file'])

        if not os.path.exists(playlist_path):
            ctk.CTkLabel(
                scroll_frame, text="❌ Không tìm thấy playlist.json",
                text_color="#f87171"
            ).pack(pady=20)
            return

        try:
            with open(playlist_path, 'r', encoding='utf-8') as f:
                playlist = json.load(f)
        except (json.JSONDecodeError, IOError):
            ctk.CTkLabel(
                scroll_frame, text="❌ Lỗi đọc playlist.json",
                text_color="#f87171"
            ).pack(pady=20)
            return

        if not playlist:
            ctk.CTkLabel(
                scroll_frame, text="📭 Chưa có bài hát nào",
                text_color="#8a8a9a", font=ctk.CTkFont(size=13)
            ).pack(pady=20)
            return

        # Header row
        ctk.CTkLabel(
            scroll_frame,
            text=f"🎵 {len(playlist)} bài hát",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#8a8a9a"
        ).pack(anchor="w", pady=(0, 6))

        # Tạo card cho mỗi bài
        for i, song in enumerate(playlist):
            self._create_song_card(scroll_frame, song, i, mgr_window)

    def _create_song_card(self, parent, song, index, mgr_window):
        """Tạo 1 card bài hát trong cửa sổ quản lý."""
        config = self.config
        repo_path = config['repo_path']

        card = ctk.CTkFrame(parent, fg_color=self.BG_CARD, corner_radius=10, height=60)
        card.pack(fill="x", pady=3)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)

        # Số thứ tự
        ctk.CTkLabel(
            inner, text=f"{index + 1}.",
            font=ctk.CTkFont(size=12), text_color="#55556a", width=24
        ).pack(side="left")

        # Thông tin bài hát
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=(4, 8))

        title = song.get('title', 'Không rõ')
        artist = song.get('artist', '')
        duration = song.get('duration', 0)
        dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "—"

        ctk.CTkLabel(
            info_frame, text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame, text=f"{artist}  •  {dur_str}",
            font=ctk.CTkFont(size=11), text_color="#8a8a9a",
            anchor="w"
        ).pack(anchor="w")

        # File size
        audio_path = os.path.join(repo_path, song.get('audioUrl', ''))
        if os.path.exists(audio_path):
            size_mb = round(os.path.getsize(audio_path) / (1024 * 1024), 1)
            ctk.CTkLabel(
                inner, text=f"{size_mb} MB",
                font=ctk.CTkFont(size=11), text_color="#55556a", width=50
            ).pack(side="left", padx=(0, 8))

        # Nút xóa
        song_id = song.get('id', '')
        song_title = song.get('title', '')

        def do_delete(sid=song_id, stitle=song_title):
            self._delete_song(sid, stitle, parent, mgr_window)

        ctk.CTkButton(
            inner, text="🗑️ Xóa", width=60, height=28,
            fg_color="#7f1d1d", hover_color="#991b1b",
            text_color="#fca5a5", font=ctk.CTkFont(size=11),
            command=do_delete
        ).pack(side="right")

    def _delete_song(self, song_id, song_title, scroll_frame, mgr_window):
        """Xóa bài hát khỏi repo và push."""
        # Xác nhận
        confirm = ctk.CTkToplevel(mgr_window)
        confirm.title("Xác nhận xóa")
        confirm.geometry("420x160")
        confirm.transient(mgr_window)
        confirm.grab_set()
        confirm.configure(fg_color=self.BG_DARK)

        ctk.CTkLabel(
            confirm, text="⚠️ Xóa bài hát?",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#fbbf24"
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            confirm, text=f'"{song_title}"',
            font=ctk.CTkFont(size=12), text_color="#8a8a9a",
            wraplength=380
        ).pack(pady=(0, 12))

        btn_row = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_row.pack(pady=(0, 12))

        ctk.CTkButton(
            btn_row, text="Hủy", width=100, height=32,
            fg_color="transparent", border_width=1, border_color="#555",
            hover_color="#2a2a3e",
            command=confirm.destroy
        ).pack(side="left", padx=8)

        def execute_delete():
            confirm.destroy()
            self._log(f"🗑️ Đang xóa: {song_title}")
            threading.Thread(
                target=self._do_delete, daemon=True,
                args=(song_id, song_title, scroll_frame, mgr_window)
            ).start()

        ctk.CTkButton(
            btn_row, text="🗑️ Xóa & Push", width=120, height=32,
            fg_color="#991b1b", hover_color="#7f1d1d",
            text_color="#fca5a5", font=ctk.CTkFont(weight="bold"),
            command=execute_delete
        ).pack(side="left", padx=8)

    def _do_delete(self, song_id, song_title, scroll_frame, mgr_window):
        """Thực hiện xóa bài hát (chạy trên thread riêng)."""
        config = self.config
        repo_path = config['repo_path']

        # Bước 1: Xóa khỏi playlist.json → lấy info file cần xóa
        removed = remove_song_from_playlist(repo_path, config['playlist_file'], song_id)
        if not removed:
            self.after(0, lambda: self._log(f"❌ Không tìm thấy bài '{song_title}' trong playlist"))
            return

        # Bước 2: Xác định files cần xóa
        files_to_delete = []
        audio_url = removed.get('audioUrl', '')
        cover_url = removed.get('cover', '')

        if audio_url:
            files_to_delete.append(audio_url)
        if cover_url and cover_url != 'assets/covers/default-cover.jpg':
            files_to_delete.append(cover_url)

        self.after(0, lambda: self._log(f"📁 Xóa {len(files_to_delete)} file: {', '.join(files_to_delete)}"))

        # Bước 3: Git remove + push
        commit_msg = f"🗑️ Remove: {song_title}"
        result = git_remove_and_push(
            repo_path, files_to_delete, config['playlist_file'],
            commit_msg, branch=config['git_branch']
        )

        if result['success']:
            self.after(0, lambda: self._log(f"✅ Đã xóa '{song_title}' và push thành công!"))
            # Refresh danh sách
            self.after(100, lambda: self._load_songs_into_manager(scroll_frame, mgr_window))
        else:
            self.after(0, lambda e=result['error']: self._log(f"❌ Xóa thất bại: {e}"))

        self.after(0, lambda: self._update_repo_stats())


# ===== MAIN =====
if __name__ == '__main__':
    app = MusicManagerApp()
    app.mainloop()
