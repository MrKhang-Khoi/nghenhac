"""
backfill_lyrics.py — Tìm và điền lyrics cho tất cả bài hát trong playlist
Smart search: tự clean YouTube title để match LRCLIB tốt hơn.
"""
import sys, os, json, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
from downloader import fetch_lyrics

PLAYLIST_PATH = os.path.join(os.path.dirname(__file__), 'data', 'playlist.json')


def clean_title(raw_title):
    """
    Làm sạch YouTube title → tên bài hát thuần.
    
    Ví dụ:
      "Như Đã Dấu Yêu - Phú Quí (Official MV) || Bản Tình Ca Hay Nhất"
      → ("Như Đã Dấu Yêu", "Phú Quí")
    """
    title = raw_title

    # Bỏ các cụm rác phổ biến (case-insensitive)
    noise_patterns = [
        r'\(Official\s*(MV|Music\s*Video|Video|Audio|Lyric\s*Video)\)',
        r'\[Official\s*(MV|Music\s*Video|Video|Audio)\]',
        r'\(LIVE\)',
        r'\(Live\s*(?:at|version|concert|in).*?\)',
        r'\bOfficial\s*(MV|Music\s*Video|Video)\b',
        r'\bLyric\s*Video\b',
        r'\bMV\b',
        r'\bvideo\s*by\s*\w+',
        r'\bLIVE\s*VERSION\s*AT\b.*$',
        r'\bLive\s*Concert\b.*$',
        r'\bSáng\s*tác:?\s*.*$',
        r'\bSang\s*tac:?\s*.*$',
        r'\bst:?\s*\w+.*$',
        r'\|\|.*$',  # "|| Bài Hay Nhất..." removed
        r'Giọng\s*Ca.*$',
        r'Cặp\s*Song\s*Ca.*$',
        r'Nỗi\s*đau.*$',
        r'Bản\s*Tình\s*Ca.*$',
        r'Nhạc\s*Vàn?g?.*$',
        r'Bolero\s*(Ngọt|Hay).*$',
        r'\d{4}$',  # trailing year
        r'4K\b',
    ]

    for pat in noise_patterns:
        title = re.sub(pat, '', title, flags=re.IGNORECASE)

    # Extract artist từ patterns: "Title - Artist" hoặc "Title | Artist"
    artist = ''
    for sep in [' - ', ' – ', ' — ']:
        if sep in title:
            parts = title.split(sep, 1)
            title = parts[0].strip()
            artist = parts[1].strip()
            break

    if not artist:
        for sep in [' | ', ' │ ']:
            if sep in title:
                parts = title.split(sep, 1)
                title = parts[0].strip()
                artist = parts[1].strip()
                break

    # Clean up artist: bỏ "ft", "feat", channel suffixes
    if artist:
        artist = re.sub(r'\s*(Official|Tube|Channel|Music|Entertainment)\s*$', '', artist, flags=re.IGNORECASE)
        # Giữ cả phần ft/feat
        artist = artist.strip()

    # Clean up title
    title = re.sub(r'\s*[\(\[].*?[\)\]]', '', title)  # Remove remaining (...)  [...] 
    title = re.sub(r'\s{2,}', ' ', title).strip()

    return title, artist


def main():
    with open(PLAYLIST_PATH, 'r', encoding='utf-8') as f:
        songs = json.load(f)

    print(f"=== Backfill Lyrics ===")
    print(f"Tong cong {len(songs)} bai hat.\n")

    updated = 0
    for i, song in enumerate(songs):
        raw_title = song.get('title', '')
        raw_artist = song.get('artist', '')

        if song.get('lyrics'):
            print(f"[{i+1}/{len(songs)}] SKIP (da co): {raw_title[:50]}")
            continue

        # Clean YouTube title
        clean_name, extracted_artist = clean_title(raw_title)
        # Dùng artist trích từ title nếu có (chính xác hơn channel name)
        search_artist = extracted_artist or raw_artist

        print(f"[{i+1}/{len(songs)}] Tim: \"{clean_name}\" + \"{search_artist}\"")

        # Thử 1: Tìm với title + artist đã clean
        lyrics = fetch_lyrics(clean_name, search_artist, song.get('duration', 0))

        # Thử 2: Nếu không thấy, thử chỉ title (bỏ artist)
        if not lyrics and search_artist:
            print(f"  Retry: chi title \"{clean_name}\"...")
            lyrics = fetch_lyrics(clean_name, '', song.get('duration', 0))

        # Thử 3: Nếu vẫn không, thử artist từ channel name
        if not lyrics and extracted_artist and raw_artist != extracted_artist:
            print(f"  Retry: \"{clean_name}\" + \"{raw_artist}\"...")
            lyrics = fetch_lyrics(clean_name, raw_artist, song.get('duration', 0))

        if lyrics:
            song['lyrics'] = lyrics
            is_synced = '[0' in lyrics
            ltype = 'SYNCED' if is_synced else 'PLAIN'
            print(f"  -> OK ({ltype}, {len(lyrics)} chars)")
            updated += 1
        else:
            print(f"  -> Khong tim thay")

    # Lưu file
    with open(PLAYLIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"Hoan tat! Da cap nhat {updated}/{len(songs)} bai hat.")
    if updated > 0:
        print("Push playlist.json len GitHub de PWA cap nhat.")


if __name__ == '__main__':
    main()
