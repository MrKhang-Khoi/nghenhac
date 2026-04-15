# 🎵 Vinyl Noir — Music Manager Desktop Tool

## Hướng dẫn cài đặt

### Yêu cầu hệ thống
- **Python 3.10+** (kiểm tra: `py --version`)
- **Git** đã cài và cấu hình credential GitHub
- **FFmpeg** để convert audio → MP3

### Bước 1: Cài FFmpeg

**Cách nhanh nhất (Windows):**
```bash
winget install ffmpeg
```

**Hoặc tải thủ công:**
1. Tải FFmpeg từ: https://ffmpeg.org/download.html
2. Chọn "Windows builds" → tải bản release
3. Giải nén vào thư mục, ví dụ: `C:\ffmpeg`
4. Thêm `C:\ffmpeg\bin` vào biến môi trường PATH:
   - Tìm "Environment Variables" trong Start menu
   - Trong "System variables" → chọn "Path" → "Edit"
   - Thêm đường dẫn `C:\ffmpeg\bin`
   - Nhấn OK và khởi động lại terminal
5. Kiểm tra: `ffmpeg -version`

### Bước 2: Cài Python packages

Mở terminal trong thư mục `tools`:
```bash
cd "c:\Users\HPZBook\Desktop\NGHE NHẠC\tools"
pip install -r requirements.txt
```

### Bước 3: Cấu hình Git

Đảm bảo Git đã được cấu hình credential:
```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"
```

Nếu dùng HTTPS, cần lưu credential:
```bash
git config --global credential.helper store
```

Sau đó push thử 1 lần để lưu mật khẩu.

## Sử dụng

### Khởi động
```bash
cd "c:\Users\HPZBook\Desktop\NGHE NHẠC\tools"
py music_manager.py
```

### Quy trình
1. **Dán link YouTube** vào ô nhập (Ctrl+V tự động tìm)
2. **Nhấn 🔍 Tìm** — xem trước tên bài, nghệ sĩ, thời lượng
3. **Nhấn ▶ Nghe thử** — mở YouTube trong trình duyệt
4. **Nhấn ⬇️ Tải & Push GitHub** — app sẽ:
   - Tải audio MP3 vào `assets/audio/`
   - Tải ảnh bìa vào `assets/covers/`
   - Cập nhật `data/playlist.json`
   - Git commit + push lên GitHub
5. **PWA tự cập nhật** danh sách bài mới!

### Cài đặt (⚙️)
- **Đường dẫn Repo**: thư mục chứa code PWA
- **Git Branch**: mặc định `main`
- **Chất lượng MP3**: 128 / 192 / 320 kbps
- **FFmpeg path**: để trống = tự tìm trong PATH
- **Auto push**: bật/tắt tự động push GitHub

## Troubleshooting

### "FFmpeg chưa được cài đặt"
→ Cài FFmpeg theo hướng dẫn Bước 1 ở trên

### "Git push bị từ chối"
→ Chạy: `git pull --rebase origin main` rồi thử lại

### "Lỗi xác thực Git"
→ Kiểm tra Git credential: `git config --global credential.helper`

### "yt-dlp lỗi"
→ Cập nhật: `pip install --upgrade yt-dlp`

### Video bị chặn / không tải được
→ Một số video có bản quyền nghiêm ngặt, không thể tải
