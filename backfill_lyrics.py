"""
backfill_lyrics.py — Tìm và điền lyrics cho tất cả bài hát trong playlist
Smart search: tự clean YouTube title để match LRCLIB tốt hơn.
V2: Verify trackName khớp trước khi chọn lyrics.
"""
import sys, os, json, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
from downloader import fetch_lyrics

PLAYLIST_PATH = os.path.join(os.path.dirname(__file__), 'data', 'playlist.json')


def clean_title(raw_title):
    """Clean YouTube title -> (song_name, artist)"""
    title = raw_title
    noise_patterns = [
        r'\(Official\s*(MV|Music\s*Video|Video|Audio|Lyric\s*Video)\)',
        r'\[Official\s*(MV|Music\s*Video|Video|Audio)\]',
        r'\(LIVE\)', r'\(Live\s*(?:at|version|concert|in).*?\)',
        r'\bOfficial\s*(MV|Music\s*Video|Video)\b',
        r'\bLyric\s*Video\b', r'\bMV\b',
        r'\bvideo\s*by\s*\w+', r'\bLIVE\s*VERSION\s*AT\b.*$',
        r'\bLive\s*Concert\b.*$', r'\bSáng\s*tác:?\s*.*$',
        r'\bSang\s*tac:?\s*.*$', r'\bst:?\s*\w+.*$',
        r'\|\|.*$', r'Giọng\s*Ca.*$', r'Cặp\s*Song\s*Ca.*$',
        r'Nỗi\s*đau.*$', r'Bản\s*Tình\s*Ca.*$',
        r'Nhạc\s*Vàn?g?.*$', r'Bolero\s*(Ngọt|Hay).*$',
        r'\d{4}$', r'4K\b',
    ]
    for pat in noise_patterns:
        title = re.sub(pat, '', title, flags=re.IGNORECASE)

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

    if artist:
        artist = re.sub(
            r'\s*(Official|Tube|Channel|Music|Entertainment)\s*$',
            '', artist, flags=re.IGNORECASE
        ).strip()

    title = re.sub(r'\s*[\(\[].*?[\)\]]', '', title)
    title = re.sub(r'\s{2,}', ' ', title).strip()
    return title, artist


def main():
    # Force clear ALL existing lyrics to re-fetch with fixed logic
    force_refetch = '--force' in sys.argv

    with open(PLAYLIST_PATH, 'r', encoding='utf-8') as f:
        songs = json.load(f)

    if force_refetch:
        print("=== FORCE MODE: Xoa tat ca lyrics cu, tim lai tu dau ===\n")
        for s in songs:
            s['lyrics'] = ''

    print(f"Tong cong {len(songs)} bai hat.\n")

    updated = 0
    for i, song in enumerate(songs):
        raw_title = song.get('title', '')
        raw_artist = song.get('artist', '')

        if song.get('lyrics'):
            clean_name, _ = clean_title(raw_title)
            print(f"[{i+1}/{len(songs)}] SKIP (da co): {clean_name}")
            continue

        clean_name, extracted_artist = clean_title(raw_title)
        search_artist = extracted_artist or raw_artist

        print(f"[{i+1}/{len(songs)}] Tim: \"{clean_name}\" + \"{search_artist}\"")

        lyrics = fetch_lyrics(raw_title, raw_artist, song.get('duration', 0))

        if lyrics:
            song['lyrics'] = lyrics
            is_synced = '[0' in lyrics
            ltype = 'SYNCED' if is_synced else 'PLAIN'
            # Show first line to verify
            first_line = lyrics.split('\n')[0] if lyrics else ''
            print(f"  -> OK ({ltype}) | {first_line[:60]}")
            updated += 1
        else:
            print(f"  -> Khong tim thay")

    with open(PLAYLIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"Hoan tat! Da cap nhat {updated}/{len(songs)} bai hat.")
    if updated > 0:
        print("Push playlist.json len GitHub de PWA cap nhat.")


if __name__ == '__main__':
    main()
