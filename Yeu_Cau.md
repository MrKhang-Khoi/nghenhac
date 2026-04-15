Hãy thiết kế cho tôi một ứng dụng nghe nhạc MP3 bằng HTML/CSS/JavaScript thuần hoặc framework rất nhẹ, ưu tiên chạy mượt trên điện thoại Android, giao diện đẹp, hiện đại, tối ưu cảm ứng, và có thể triển khai toàn bộ mã nguồn lên GitHub/GitHub Pages.



MỤC TIÊU CHÍNH

\- Ứng dụng là một web app dạng PWA.

\- Có thể cài lên màn hình chính điện thoại như app.

\- Khi đã tải dữ liệu cần thiết, app vẫn dùng được khi không có Internet.

\- Khi người dùng tắt màn hình điện thoại, nhạc vẫn tiếp tục phát nếu trình duyệt Android cho phép.

\- Có Media Session đầy đủ để hiện tên bài hát, ảnh bìa, nút play/pause/next/previous trên màn hình khóa và vùng thông báo.

\- Chạy mượt, ít giật, tối ưu cho màn hình dọc điện thoại Android.

\- Toàn bộ code tổ chức gọn gàng, dễ sửa, dễ đưa lên GitHub.



YÊU CẦU KỸ THUẬT QUAN TRỌNG

\- Không làm theo cách trích xuất audio từ link YouTube.

\- Không sử dụng bất kỳ cách nào vi phạm điều khoản YouTube.

\- Kiến trúc phải dùng nguồn âm thanh hợp lệ:

&#x20; 1) file MP3 do tôi sở hữu hoặc được phép sử dụng,

&#x20; 2) hoặc URL MP3 trực tiếp có CORS hợp lệ,

&#x20; 3) hoặc thư mục /songs hay file manifest JSON trong GitHub để tôi chỉ cần thêm bài mới.

\- Hệ thống phải đọc danh sách bài hát tự động từ một file dữ liệu như songs.json hoặc playlist.json.

\- Tôi chỉ cần sửa file JSON hoặc thêm file MP3 vào thư mục quy định rồi push GitHub là app tự cập nhật danh sách bài hát.

\- Nếu muốn hỗ trợ link YouTube thì chỉ dùng để lấy metadata tham khảo hoặc mở YouTube online riêng, KHÔNG dùng làm nguồn offline/audio extraction.



CHỨC NĂNG GIAO DIỆN

\- Trang chủ đẹp, hiện đại, phong cách music player cao cấp.

\- Có ảnh bìa bài hát, tên bài, ca sĩ, thời lượng.

\- Có progress bar mượt, tua bài, next, previous, play, pause.

\- Có danh sách bài hát dạng card đẹp, cuộn mượt trên mobile.

\- Có tìm kiếm bài hát theo tên.

\- Có chế độ phát lặp 1 bài, lặp toàn danh sách, phát ngẫu nhiên.

\- Có điều chỉnh âm lượng.

\- Có mini player cố định ở cạnh dưới màn hình.

\- Có dark mode mặc định, màu sắc sang, hiện đại.

\- Có hiệu ứng mượt nhưng không nặng máy.



CHỨC NĂNG PWA/OFFLINE

\- Tạo manifest.json đầy đủ.

\- Tạo service worker để cache app shell, ảnh bìa, manifest playlist, và các file MP3 đã được người dùng mở hoặc tải sẵn.

\- Có chiến lược cache hợp lý để app mở lại nhanh.

\- Có màn hình thông báo trạng thái offline/online rõ ràng.

\- Có nút “tải sẵn để nghe offline” cho từng bài hoặc toàn bộ playlist, nhưng chỉ áp dụng với file MP3 hợp lệ của ứng dụng.

\- Có xử lý giới hạn bộ nhớ, hiển thị dung lượng cache, và nút xóa cache.



CHỨC NĂNG PHÁT NHẠC NÂNG CAO

\- Dùng thẻ audio HTML5 và Media Session API.

\- Tối ưu để khi khóa màn hình Android vẫn tiếp tục phát nếu môi trường hỗ trợ.

\- Hiện metadata chuẩn trên lock screen: tên bài, ca sĩ, ảnh bìa.

\- Điều khiển từ tai nghe Bluetooth và nút media nếu trình duyệt hỗ trợ.

\- Khi đang phát, chuyển bài không bị khựng quá mạnh.

\- Ưu tiên chất lượng âm thanh cao nhất từ file nguồn MP3/AAC hợp lệ mà ứng dụng có quyền truy cập.

\- Không thêm bộ lọc âm thanh giả tạo nếu không cần.



QUẢN LÝ DỮ LIỆU

\- Tạo cấu trúc file rõ ràng như:

&#x20; /index.html

&#x20; /assets/css/

&#x20; /assets/js/

&#x20; /assets/icons/

&#x20; /assets/covers/

&#x20; /assets/audio/

&#x20; /data/playlist.json

&#x20; /manifest.json

&#x20; /service-worker.js

\- File playlist.json gồm:

&#x20; id, title, artist, album, cover, audioUrl, duration, lyrics(optional), favorite(optional)

\- Viết sẵn ví dụ dữ liệu mẫu để tôi chỉ việc thay tên bài và đường dẫn file.

\- Có kiểm tra lỗi nếu audioUrl hỏng hoặc file không tải được.



YÊU CẦU TRIỂN KHAI

\- Dự án phải deploy được trên GitHub Pages.

\- Viết README.md rất rõ:

&#x20; 1) cách thêm bài hát,

&#x20; 2) cách sửa playlist.json,

&#x20; 3) cách build/deploy lên GitHub Pages,

&#x20; 4) cách test PWA trên Android,

&#x20; 5) giới hạn kỹ thuật của background playback và offline cache.

\- Nếu GitHub Pages không phù hợp cho phần nào thì nêu rõ giải pháp thay thế tối thiểu, nhưng vẫn ưu tiên GitHub Pages.

\- Có icon app, splash screen cơ bản, theme color đẹp.

\- Có hướng dẫn cài app lên Android từ Chrome.



YÊU CẦU CHẤT LƯỢNG MÃ

\- Code sạch, chú thích rõ, tên biến không viết tắt khó hiểu.

\- Tách module hợp lý.

\- Responsive chuẩn mobile-first.

\- Ưu tiên hiệu năng, tải nhanh, thao tác mượt.

\- Không phụ thuộc backend nếu không thật sự cần.

\- Nếu dùng thư viện thì chỉ dùng thư viện nhẹ, phổ biến, dễ bảo trì.

\- Không dùng giải pháp mập mờ liên quan đến tải nhạc từ YouTube.



PHẦN BẮT BUỘC PHẢI GIAO

1\) Mã nguồn hoàn chỉnh.

2\) File playlist.json mẫu.

3\) manifest.json.

4\) service-worker.js.

5\) README.md hướng dẫn từng bước.

6\) Giải thích rõ phần nào hoạt động offline, phần nào cần online.

7\) Giải thích rõ giới hạn thực tế trên Android khi tắt màn hình.

8\) Giao diện hoàn chỉnh, đẹp mắt, có thể dùng ngay.



LƯU Ý CUỐI

Tôi muốn một sản phẩm thực tế, dùng được thật, không vi phạm nền tảng, không nói chung chung. Hãy ưu tiên phương án ổn định nhất cho Android + GitHub Pages + PWA + phát nhạc MP3 offline hợp lệ.

YÊU CẦU SỬ DỤNG THƯ VIỆN GITHUB contex mói nhất https://github.com/upstash/context7

