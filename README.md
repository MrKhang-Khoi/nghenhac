# 🎵 Vinyl Noir — Ứng Dụng Nghe Nhạc MP3 PWA

> Progressive Web App nghe nhạc MP3 offline — Giao diện sang trọng, cài trên Android như app.

## Tính năng

- 🎨 Giao diện dark premium với hiệu ứng vinyl xoay
- 📱 PWA — cài lên Android như app native
- 🔊 Media Session — điều khiển trên lock screen / tai nghe Bluetooth
- 📴 Offline — tải bài để nghe khi không có mạng
- 🔍 Tìm kiếm bài hát theo tên, nghệ sĩ
- 🔁 Lặp 1 bài / Lặp tất cả / Ngẫu nhiên
- ❤️ Yêu thích bài hát
- 💾 Quản lý cache offline
- 🖥️ Desktop Manager — tải nhạc từ YouTube, tự push GitHub

## Cấu trúc dự án

```
├── index.html              # Trang chính PWA
├── manifest.json           # PWA manifest
├── service-worker.js       # Offline caching
├── assets/
│   ├── css/style.css       # Giao diện Vinyl Noir
│   ├── js/                 # Modules JavaScript
│   ├── icons/              # PWA icons
│   ├── covers/             # Ảnh bìa album
│   └── audio/              # File MP3
├── data/
│   └── playlist.json       # Danh sách bài hát
└── tools/                  # Desktop Manager (Python)
```

## Hướng dẫn sử dụng

### 1. Thêm bài hát

#### Cách 1: Dùng Desktop Manager (khuyến nghị)
1. Cài đặt: xem `tools/README_TOOLS.md`
2. Chạy: `py tools/music_manager.py`
3. Dán link YouTube → nhấn Tải → app tự push lên GitHub

#### Cách 2: Thêm thủ công
1. Copy file MP3 vào `assets/audio/`
2. Copy ảnh bìa vào `assets/covers/`
3. Sửa `data/playlist.json`:
```json
{
  "id": "ten-bai-hat",
  "title": "Tên Bài Hát",
  "artist": "Tên Ca Sĩ",
  "album": "Tên Album",
  "cover": "assets/covers/anh-bia.jpg",
  "audioUrl": "assets/audio/ten-bai-hat.mp3",
  "duration": 240,
  "lyrics": "",
  "favorite": false
}
```
4. Git push: `git add . && git commit -m "Add song" && git push`

### 2. Deploy GitHub Pages

1. Mở repo trên GitHub: https://github.com/MrKhang-Khoi/nghenhac
2. Vào **Settings** → **Pages**
3. Source: chọn **Deploy from a branch**
4. Branch: chọn **main** → thư mục **/ (root)**
5. Nhấn **Save**
6. Đợi 1-2 phút, app sẽ có tại: `https://mrkhang-khoi.github.io/nghenhac/`

### 3. Cài PWA trên Android

1. Mở Chrome trên Android
2. Truy cập URL GitHub Pages
3. Chrome sẽ hiện banner "Thêm vào Màn hình chính"
   - Hoặc: nhấn ⋮ (menu) → "Cài đặt ứng dụng" / "Thêm vào Màn hình chính"
4. App sẽ xuất hiện trên màn hình như app thường

### 4. Test PWA

1. Mở Chrome DevTools (F12)
2. Tab **Application** → xem Manifest, Service Worker
3. Tab **Network** → tick "Offline" → F5 (kiểm tra offline)
4. Phát nhạc → khóa màn hình → kiểm tra controls

## Giới hạn kỹ thuật

### Background playback (phát khi tắt màn hình)
- ✅ Chrome Android: hoạt động nếu có Media Session active
- ⚠️ Một số ROM (Xiaomi MIUI, Samsung One UI, Huawei EMUI): có thể tắt browser khi khóa màn hình do chế độ tiết kiệm pin
- 💡 Giải pháp: vào Settings điện thoại → Battery → cho phép Chrome chạy nền

### Offline
- Chỉ bài đã nhấn "tải offline" mới có sẵn khi mất mạng
- Dung lượng phụ thuộc bộ nhớ cache của trình duyệt
- Nút "Tải tất cả" trong Settings để cache toàn bộ

### GitHub Pages
- Repository tối đa **1 GB**
- Mỗi file tối đa **100 MB**
- File MP3 trung bình 5-8 MB → khoảng 120-200 bài/repo

## Credits

- **Design**: Vinyl Noir aesthetic by AI
- **Audio Engine**: HTML5 Web Audio + Media Session API
- **Download**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (open source)
- **Desktop GUI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Fonts**: [Outfit](https://fonts.google.com/specimen/Outfit) + [DM Sans](https://fonts.google.com/specimen/DM+Sans)
