"""
github_uploader.py — Module push Git
Vinyl Noir Music Manager

Dùng Git CLI qua subprocess để:
- Cập nhật playlist.json
- Git add, commit, push file MP3 + cover lên GitHub
"""

import os
import json
import subprocess
import time
from pathlib import Path


def check_git_installed():
    """Kiểm tra Git đã cài trong PATH chưa."""
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_repo_status(repo_path):
    """
    Kiểm tra trạng thái Git repo.
    
    Returns:
        dict: {valid, has_remote, branch, remote_url, error}
    """
    status = {
        'valid': False,
        'has_remote': False,
        'branch': '',
        'remote_url': '',
        'error': None
    }

    if not os.path.isdir(repo_path):
        status['error'] = f"Thư mục không tồn tại: {repo_path}"
        return status

    try:
        # Kiểm tra có phải git repo không
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )
        if result.returncode != 0:
            status['error'] = "Thư mục chưa được init là Git repository"
            return status

        status['valid'] = True

        # Lấy branch hiện tại
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )
        status['branch'] = result.stdout.strip() or 'main'

        # Kiểm tra remote
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )
        if result.stdout.strip():
            status['has_remote'] = True
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].split()
                if len(parts) >= 2:
                    status['remote_url'] = parts[1]

    except subprocess.TimeoutExpired:
        status['error'] = "Git command timeout"
    except Exception as e:
        status['error'] = str(e)

    return status


def update_playlist_json(repo_path, playlist_file, song_data):
    """
    Thêm bài hát mới vào playlist.json.
    
    Args:
        repo_path: Đường dẫn repo
        playlist_file: Đường dẫn tương đối playlist.json (vd: data/playlist.json)
        song_data: dict chứa thông tin bài hát
        
    Returns:
        bool: Thành công hay không
    """
    full_path = os.path.join(repo_path, playlist_file)

    # Đọc playlist hiện tại
    playlist = []
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                playlist = json.load(f)
            if not isinstance(playlist, list):
                playlist = []
        except (json.JSONDecodeError, IOError):
            playlist = []

    # Kiểm tra bài trùng (theo id)
    song_id = song_data.get('id', '')
    existing_ids = {s.get('id') for s in playlist}
    if song_id in existing_ids:
        # Cập nhật bài đã tồn tại
        for i, song in enumerate(playlist):
            if song.get('id') == song_id:
                playlist[i] = song_data
                break
    else:
        # Thêm bài mới
        playlist.append(song_data)

    # Ghi file
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(playlist, f, ensure_ascii=False, indent=2)

    return True


def git_add_commit_push(repo_path, files, message, branch='main'):
    """
    Git add + commit + push các files.
    
    Args:
        repo_path: Đường dẫn repo
        files: List đường dẫn tương đối (vd: ['assets/audio/bai.mp3', 'data/playlist.json'])
        message: Commit message
        branch: Branch name
        
    Returns:
        dict: {success, output, error}
    """
    result = {'success': False, 'output': '', 'error': None}

    try:
        # Git add
        cmd_add = ['git', 'add'] + files
        proc = subprocess.run(
            cmd_add,
            capture_output=True, text=True,
            cwd=repo_path, timeout=60
        )
        if proc.returncode != 0:
            result['error'] = f"Git add failed: {(proc.stderr or '').strip()}"
            return result

        # Kiểm tra có gì để commit không
        proc_status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )
        if not (proc_status.stdout or '').strip():
            result['output'] = "Không có thay đổi nào cần commit"
            result['success'] = True
            return result

        # Git commit
        proc = subprocess.run(
            ['git', 'commit', '-m', message],
            capture_output=True, text=True,
            cwd=repo_path, timeout=30
        )
        if proc.returncode != 0:
            result['error'] = f"Git commit failed: {(proc.stderr or '').strip()}"
            return result

        result['output'] = (proc.stdout or '').strip()

        # Git push
        proc = subprocess.run(
            ['git', 'push', 'origin', branch],
            capture_output=True, text=True,
            cwd=repo_path, timeout=120  # Push có thể mất thời gian nếu file lớn
        )
        if proc.returncode != 0:
            stderr = (proc.stderr or '').strip()
            if 'rejected' in stderr.lower():
                result['error'] = (
                    "Push bị từ chối! Có thể có thay đổi mới trên remote.\n"
                    "Thử: git pull --rebase origin main"
                )
            elif 'authentication' in stderr.lower() or 'permission' in stderr.lower():
                result['error'] = (
                    "Lỗi xác thực Git! Kiểm tra:\n"
                    "1. Git credential đã cấu hình chưa\n"
                    "2. GitHub token có quyền 'repo' không"
                )
            else:
                result['error'] = f"Git push failed: {stderr}"
            return result

        result['success'] = True
        result['output'] += f"\n{(proc.stdout or '').strip()}"

    except subprocess.TimeoutExpired:
        result['error'] = "Git command bị timeout. Kiểm tra kết nối mạng."
    except FileNotFoundError:
        result['error'] = "Git chưa được cài đặt. Tải tại: https://git-scm.com"
    except Exception as e:
        result['error'] = f"Lỗi không xác định: {e}"

    return result


def get_repo_size(repo_path):
    """
    Ước lượng dung lượng repo (không tính .git).
    
    Returns:
        dict: {total_bytes, total_mb, audio_bytes, audio_count}
    """
    total_bytes = 0
    audio_bytes = 0
    audio_count = 0

    for root, dirs, files in os.walk(repo_path):
        # Bỏ qua thư mục .git
        dirs[:] = [d for d in dirs if d != '.git']
        for f in files:
            filepath = os.path.join(root, f)
            try:
                size = os.path.getsize(filepath)
                total_bytes += size
                if f.lower().endswith(('.mp3', '.mp4', '.m4a', '.aac', '.ogg', '.wav', '.flac')):
                    audio_bytes += size
                    audio_count += 1
            except OSError:
                pass

    return {
        'total_bytes': total_bytes,
        'total_mb': round(total_bytes / (1024 * 1024), 1),
        'audio_bytes': audio_bytes,
        'audio_mb': round(audio_bytes / (1024 * 1024), 1),
        'audio_count': audio_count,
    }


def git_pull(repo_path, branch='main'):
    """Pull changes mới nhất từ remote."""
    try:
        proc = subprocess.run(
            ['git', 'pull', 'origin', branch],
            capture_output=True, text=True,
            cwd=repo_path, timeout=60
        )
        return {
            'success': proc.returncode == 0,
            'output': (proc.stdout or '').strip(),
            'error': (proc.stderr or '').strip() if proc.returncode != 0 else None
        }
    except Exception as e:
        return {'success': False, 'output': '', 'error': str(e)}


def remove_song_from_playlist(repo_path, playlist_file, song_id):
    """
    Xóa bài hát khỏi playlist.json theo ID.
    
    Returns:
        dict hoặc None: thông tin bài đã xóa (để biết file cần xóa)
    """
    full_path = os.path.join(repo_path, playlist_file)
    
    if not os.path.exists(full_path):
        return None

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            playlist = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    if not isinstance(playlist, list):
        return None

    # Tìm và xóa bài hát
    removed_song = None
    new_playlist = []
    for song in playlist:
        if song.get('id') == song_id:
            removed_song = song
        else:
            new_playlist.append(song)

    if removed_song is None:
        return None

    # Ghi lại playlist
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(new_playlist, f, ensure_ascii=False, indent=2)

    return removed_song


def git_remove_and_push(repo_path, files_to_delete, playlist_file, message, branch='main'):
    """
    Xóa files khỏi repo và push.
    
    Args:
        repo_path: Đường dẫn repo
        files_to_delete: List đường dẫn tương đối cần xóa
        playlist_file: Đường dẫn tương đối playlist.json (đã được cập nhật)
        message: Commit message
        branch: Branch name
        
    Returns:
        dict: {success, output, error}
    """
    result = {'success': False, 'output': '', 'error': None}

    try:
        # Xóa file vật lý + git rm
        for f in files_to_delete:
            full_path = os.path.join(repo_path, f)
            if os.path.exists(full_path):
                os.remove(full_path)
            # Git rm (bỏ qua lỗi nếu file không tracked)
            subprocess.run(
                ['git', 'rm', '--cached', '--ignore-unmatch', f],
                capture_output=True, text=True,
                cwd=repo_path, timeout=10
            )

        # Git add playlist.json (đã cập nhật) + staged deletions
        subprocess.run(
            ['git', 'add', playlist_file],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )
        subprocess.run(
            ['git', 'add', '-A'],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )

        # Kiểm tra có gì để commit
        proc_status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True,
            cwd=repo_path, timeout=10
        )
        if not (proc_status.stdout or '').strip():
            result['output'] = "Không có thay đổi nào cần commit"
            result['success'] = True
            return result

        # Git commit
        proc = subprocess.run(
            ['git', 'commit', '-m', message],
            capture_output=True, text=True,
            cwd=repo_path, timeout=30
        )
        if proc.returncode != 0:
            result['error'] = f"Git commit failed: {(proc.stderr or '').strip()}"
            return result

        # Git push
        proc = subprocess.run(
            ['git', 'push', 'origin', branch],
            capture_output=True, text=True,
            cwd=repo_path, timeout=120
        )
        if proc.returncode != 0:
            result['error'] = f"Git push failed: {(proc.stderr or '').strip()}"
            return result

        result['success'] = True
        result['output'] = f"Đã xóa {len(files_to_delete)} file và push thành công"

    except subprocess.TimeoutExpired:
        result['error'] = "Git command bị timeout"
    except Exception as e:
        result['error'] = f"Lỗi: {e}"

    return result

