import asyncio
import ipaddress
import mimetypes
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from ..logging_config import get_logger
from ..media_helpers import (
    _convert_silk_to_wav,
    _detect_image_extension,
    _detect_image_media_type,
    _ensure_decrypted_resource_for_md5,
    _fallback_search_media_by_md5,
    _get_decrypted_resource_path,
    _get_resource_dir,
    _guess_media_type_by_path,
    _iter_emoji_source_candidates,
    _read_and_maybe_decrypt_media,
    _resolve_account_db_storage_dir,
    _resolve_account_dir,
    _resolve_account_wxid_dir,
    _resolve_media_path_for_kind,
    _resolve_media_path_from_hardlink,
    _try_find_decrypted_resource,
    _try_strip_media_prefix,
)
from ..path_fix import PathFixRoute

logger = get_logger(__name__)

router = APIRouter(route_class=PathFixRoute)


@router.get("/api/chat/avatar", summary="获取联系人头像")
async def get_chat_avatar(username: str, account: Optional[str] = None):
    if not username:
        raise HTTPException(status_code=400, detail="Missing username.")
    account_dir = _resolve_account_dir(account)
    head_image_db_path = account_dir / "head_image.db"
    if not head_image_db_path.exists():
        raise HTTPException(status_code=404, detail="head_image.db not found.")

    conn = sqlite3.connect(str(head_image_db_path))
    try:
        row = conn.execute(
            "SELECT image_buffer FROM head_image WHERE username = ? ORDER BY update_time DESC LIMIT 1",
            (username,),
        ).fetchone()
    finally:
        conn.close()

    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Avatar not found.")

    data = bytes(row[0]) if isinstance(row[0], (memoryview, bytearray)) else row[0]
    if not isinstance(data, (bytes, bytearray)):
        data = bytes(data)
    media_type = _detect_image_media_type(data)
    return Response(content=data, media_type=media_type)


class EmojiDownloadRequest(BaseModel):
    account: Optional[str] = Field(None, description="账号目录名（可选，默认使用第一个）")
    md5: str = Field(..., description="表情 MD5")
    emoji_url: str = Field(..., description="表情 CDN URL")
    force: bool = Field(False, description="是否强制重新下载并覆盖")


def _is_valid_md5(s: str) -> bool:
    import re

    v = str(s or "").strip().lower()
    return bool(re.fullmatch(r"[0-9a-f]{32}", v))


def _is_safe_http_url(url: str) -> bool:
    u = str(url or "").strip()
    if not u:
        return False
    try:
        p = urlparse(u)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.hostname or "").strip()
    if not host:
        return False
    if host in {"localhost"}:
        return False
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except Exception:
        pass
    return True


def _detect_media_type_and_ext(data: bytes) -> tuple[bytes, str, str]:
    payload = data
    media_type = "application/octet-stream"
    ext = "dat"

    try:
        payload2, mt2 = _try_strip_media_prefix(payload)
        if mt2 != "application/octet-stream":
            payload = payload2
            media_type = mt2
    except Exception:
        pass

    if media_type == "application/octet-stream":
        mt0 = _detect_image_media_type(payload[:32])
        if mt0 != "application/octet-stream":
            media_type = mt0

    if media_type == "application/octet-stream":
        try:
            if len(payload) >= 8 and payload[4:8] == b"ftyp":
                media_type = "video/mp4"
        except Exception:
            pass

    if media_type.startswith("image/"):
        ext = _detect_image_extension(payload)
    elif media_type == "video/mp4":
        ext = "mp4"
    else:
        ext = "dat"

    return payload, media_type, ext


@router.post("/api/chat/media/emoji/download", summary="下载表情消息资源到本地 resource")
async def download_chat_emoji(req: EmojiDownloadRequest):
    md5 = str(req.md5 or "").strip().lower()
    emoji_url = str(req.emoji_url or "").strip()

    if not _is_valid_md5(md5):
        raise HTTPException(status_code=400, detail="Invalid md5.")
    if not _is_safe_http_url(emoji_url):
        raise HTTPException(status_code=400, detail="Invalid emoji_url (only public http/https allowed).")

    account_dir = _resolve_account_dir(req.account)

    existing = _try_find_decrypted_resource(account_dir, md5)
    if existing and existing.exists() and (not req.force):
        return {
            "status": "success",
            "account": account_dir.name,
            "md5": md5,
            "saved": True,
            "already_exists": True,
            "path": str(existing),
            "resource_dir": str(existing.parent),
        }

    def _download_bytes() -> bytes:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "*/*",
        }
        r = requests.get(emoji_url, headers=headers, timeout=20, stream=True)
        try:
            r.raise_for_status()
            max_bytes = 30 * 1024 * 1024
            chunks: list[bytes] = []
            total = 0
            for ch in r.iter_content(chunk_size=64 * 1024):
                if not ch:
                    continue
                chunks.append(ch)
                total += len(ch)
                if total > max_bytes:
                    raise HTTPException(status_code=400, detail="Emoji download too large (>30MB).")
            return b"".join(chunks)
        finally:
            try:
                r.close()
            except Exception:
                pass

    try:
        data = await asyncio.to_thread(_download_bytes)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"emoji_download failed: md5={md5} url={emoji_url} err={e}")
        raise HTTPException(status_code=500, detail=f"Emoji download failed: {e}")

    if not data:
        raise HTTPException(status_code=500, detail="Emoji download returned empty body.")

    payload, media_type, ext = _detect_media_type_and_ext(data)
    out_path = _get_decrypted_resource_path(account_dir, md5, ext)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and (not req.force):
        return {
            "status": "success",
            "account": account_dir.name,
            "md5": md5,
            "saved": True,
            "already_exists": True,
            "path": str(out_path),
            "resource_dir": str(out_path.parent),
            "media_type": media_type,
            "bytes": len(payload),
        }

    try:
        out_path.write_bytes(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write emoji file: {e}")

    logger.info(f"emoji_download: md5={md5} url={emoji_url} -> {out_path} bytes={len(payload)} mt={media_type}")
    return {
        "status": "success",
        "account": account_dir.name,
        "md5": md5,
        "saved": True,
        "already_exists": False,
        "path": str(out_path),
        "resource_dir": str(out_path.parent),
        "media_type": media_type,
        "bytes": len(payload),
    }


@router.get("/api/chat/media/image", summary="获取图片消息资源")
async def get_chat_image(md5: str, account: Optional[str] = None, username: Optional[str] = None):
    if not md5:
        raise HTTPException(status_code=400, detail="Missing md5.")
    account_dir = _resolve_account_dir(account)

    # 优先从解密资源目录读取（更快）
    decrypted_path = _try_find_decrypted_resource(account_dir, md5.lower())
    if decrypted_path:
        data = decrypted_path.read_bytes()
        media_type = _detect_image_media_type(data[:32])
        if media_type == "application/octet-stream":
            guessed = mimetypes.guess_type(str(decrypted_path))[0]
            if guessed:
                media_type = guessed
        return Response(content=data, media_type=media_type)

    # 回退到原始逻辑：从微信数据目录实时解密
    wxid_dir = _resolve_account_wxid_dir(account_dir)
    hardlink_db_path = account_dir / "hardlink.db"
    extra_roots: list[Path] = []
    db_storage_dir = _resolve_account_db_storage_dir(account_dir)
    if db_storage_dir:
        extra_roots.append(db_storage_dir)

    roots: list[Path] = []
    if wxid_dir:
        roots.append(wxid_dir)
        roots.append(wxid_dir / "msg" / "attach")
        roots.append(wxid_dir / "msg" / "file")
        roots.append(wxid_dir / "msg" / "video")
        roots.append(wxid_dir / "cache")
    if db_storage_dir:
        roots.append(db_storage_dir)
    if not roots:
        raise HTTPException(
            status_code=404,
            detail="wxid_dir/db_storage_path not found. Please decrypt with db_storage_path to enable media lookup.",
        )
    p = _resolve_media_path_from_hardlink(
        hardlink_db_path,
        roots[0],
        md5=str(md5),
        kind="image",
        username=username,
        extra_roots=roots[1:],
    )
    if (not p) and wxid_dir:
        hit = _fallback_search_media_by_md5(str(wxid_dir), str(md5))
        if hit:
            p = Path(hit)
    if not p:
        raise HTTPException(status_code=404, detail="Image not found.")

    logger.info(f"chat_image: md5={md5} resolved_source={p}")

    data, media_type = _read_and_maybe_decrypt_media(p, account_dir=account_dir, weixin_root=wxid_dir)
    if media_type.startswith("image/"):
        try:
            out_md5 = str(md5).lower()
            ext = _detect_image_extension(data)
            out_path = _get_decrypted_resource_path(account_dir, out_md5, ext)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if not out_path.exists():
                out_path.write_bytes(data)
        except Exception:
            pass
    logger.info(f"chat_image: md5={md5} media_type={media_type} bytes={len(data)}")
    return Response(content=data, media_type=media_type)


@router.get("/api/chat/media/emoji", summary="获取表情消息资源")
async def get_chat_emoji(md5: str, account: Optional[str] = None, username: Optional[str] = None):
    if not md5:
        raise HTTPException(status_code=400, detail="Missing md5.")
    account_dir = _resolve_account_dir(account)

    # 优先从解密资源目录读取（更快）
    decrypted_path = _try_find_decrypted_resource(account_dir, md5.lower())
    if decrypted_path:
        data = decrypted_path.read_bytes()
        media_type = _detect_image_media_type(data[:32])
        if media_type == "application/octet-stream":
            guessed = mimetypes.guess_type(str(decrypted_path))[0]
            if guessed:
                media_type = guessed
        return Response(content=data, media_type=media_type)

    wxid_dir = _resolve_account_wxid_dir(account_dir)
    p = _resolve_media_path_for_kind(account_dir, kind="emoji", md5=str(md5), username=username)
    if not p:
        raise HTTPException(status_code=404, detail="Emoji not found.")

    data, media_type = _read_and_maybe_decrypt_media(p, account_dir=account_dir, weixin_root=wxid_dir)
    if media_type.startswith("image/"):
        try:
            out_md5 = str(md5).lower()
            ext = _detect_image_extension(data)
            out_path = _get_decrypted_resource_path(account_dir, out_md5, ext)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if not out_path.exists():
                out_path.write_bytes(data)
        except Exception:
            pass
    return Response(content=data, media_type=media_type)


@router.get("/api/chat/media/video_thumb", summary="获取视频缩略图资源")
async def get_chat_video_thumb(md5: str, account: Optional[str] = None, username: Optional[str] = None):
    if not md5:
        raise HTTPException(status_code=400, detail="Missing md5.")
    account_dir = _resolve_account_dir(account)

    # 优先从解密资源目录读取（更快）
    decrypted_path = _try_find_decrypted_resource(account_dir, md5.lower())
    if decrypted_path:
        data = decrypted_path.read_bytes()
        media_type = _detect_image_media_type(data[:32])
        return Response(content=data, media_type=media_type)

    # 回退到原始逻辑
    wxid_dir = _resolve_account_wxid_dir(account_dir)
    hardlink_db_path = account_dir / "hardlink.db"
    extra_roots: list[Path] = []
    db_storage_dir = _resolve_account_db_storage_dir(account_dir)
    if db_storage_dir:
        extra_roots.append(db_storage_dir)

    roots: list[Path] = []
    if wxid_dir:
        roots.append(wxid_dir)
    if db_storage_dir:
        roots.append(db_storage_dir)
    if not roots:
        raise HTTPException(
            status_code=404,
            detail="wxid_dir/db_storage_path not found. Please decrypt with db_storage_path to enable media lookup.",
        )
    p = _resolve_media_path_from_hardlink(
        hardlink_db_path,
        roots[0],
        md5=str(md5),
        kind="video_thumb",
        username=username,
        extra_roots=roots[1:],
    )
    if (not p) and wxid_dir:
        hit = _fallback_search_media_by_md5(str(wxid_dir), str(md5))
        if hit:
            p = Path(hit)
    if not p:
        raise HTTPException(status_code=404, detail="Video thumbnail not found.")

    data, media_type = _read_and_maybe_decrypt_media(p, account_dir=account_dir, weixin_root=wxid_dir)
    return Response(content=data, media_type=media_type)


@router.get("/api/chat/media/video", summary="获取视频资源")
async def get_chat_video(md5: str, account: Optional[str] = None, username: Optional[str] = None):
    if not md5:
        raise HTTPException(status_code=400, detail="Missing md5.")
    account_dir = _resolve_account_dir(account)
    wxid_dir = _resolve_account_wxid_dir(account_dir)
    hardlink_db_path = account_dir / "hardlink.db"
    extra_roots: list[Path] = []
    db_storage_dir = _resolve_account_db_storage_dir(account_dir)
    if db_storage_dir:
        extra_roots.append(db_storage_dir)

    roots: list[Path] = []
    if wxid_dir:
        roots.append(wxid_dir)
    if db_storage_dir:
        roots.append(db_storage_dir)
    if not roots:
        raise HTTPException(
            status_code=404,
            detail="wxid_dir/db_storage_path not found. Please decrypt with db_storage_path to enable media lookup.",
        )
    p = _resolve_media_path_from_hardlink(
        hardlink_db_path,
        roots[0],
        md5=str(md5),
        kind="video",
        username=username,
        extra_roots=roots[1:],
    )
    if (not p) and wxid_dir:
        hit = _fallback_search_media_by_md5(str(wxid_dir), str(md5))
        if hit:
            p = Path(hit)
    if not p:
        raise HTTPException(status_code=404, detail="Video not found.")
    media_type = _guess_media_type_by_path(p, fallback="video/mp4")
    return FileResponse(str(p), media_type=media_type)


@router.get("/api/chat/media/voice", summary="获取语音消息资源")
async def get_chat_voice(server_id: int, account: Optional[str] = None):
    if not server_id:
        raise HTTPException(status_code=400, detail="Missing server_id.")
    account_dir = _resolve_account_dir(account)
    media_db_path = account_dir / "media_0.db"
    if not media_db_path.exists():
        raise HTTPException(status_code=404, detail="media_0.db not found.")

    conn = sqlite3.connect(str(media_db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT voice_data FROM VoiceInfo WHERE svr_id = ? ORDER BY create_time DESC LIMIT 1",
            (int(server_id),),
        ).fetchone()
    except Exception:
        row = None
    finally:
        conn.close()

    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Voice not found.")

    data = bytes(row[0]) if isinstance(row[0], (memoryview, bytearray)) else row[0]
    if not isinstance(data, (bytes, bytearray)):
        data = bytes(data)

    # Try to convert SILK to WAV for browser playback
    wav_data = _convert_silk_to_wav(data)
    if wav_data != data:
        return Response(
            content=wav_data,
            media_type="audio/wav",
        )

    # Fallback to raw SILK if conversion fails
    return Response(
        content=data,
        media_type="audio/silk",
        headers={"Content-Disposition": f"attachment; filename=voice_{int(server_id)}.silk"},
    )


@router.post("/api/chat/media/open_folder", summary="在资源管理器中打开媒体文件所在位置")
async def open_chat_media_folder(
    kind: str,
    md5: Optional[str] = None,
    server_id: Optional[int] = None,
    account: Optional[str] = None,
    username: Optional[str] = None,
):
    account_dir = _resolve_account_dir(account)

    kind_key = str(kind or "").strip().lower()
    if kind_key not in {"image", "emoji", "video", "video_thumb", "file", "voice"}:
        raise HTTPException(status_code=400, detail="Unsupported kind.")

    p: Optional[Path] = None
    if kind_key == "voice":
        if not server_id:
            raise HTTPException(status_code=400, detail="Missing server_id.")

        media_db_path = account_dir / "media_0.db"
        if not media_db_path.exists():
            raise HTTPException(status_code=404, detail="media_0.db not found.")

        conn = sqlite3.connect(str(media_db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT voice_data FROM VoiceInfo WHERE svr_id = ? ORDER BY create_time DESC LIMIT 1",
                (int(server_id),),
            ).fetchone()
        except Exception:
            row = None
        finally:
            conn.close()

        if not row or row[0] is None:
            raise HTTPException(status_code=404, detail="Voice not found.")

        data = bytes(row[0]) if isinstance(row[0], (memoryview, bytearray)) else row[0]
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)

        export_dir = account_dir / "_exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        p = export_dir / f"voice_{int(server_id)}.silk"
        try:
            p.write_bytes(data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to export voice: {e}")
    else:
        if not md5:
            raise HTTPException(status_code=400, detail="Missing md5.")
        p = _resolve_media_path_for_kind(account_dir, kind=kind_key, md5=str(md5), username=username)

        resolved_before_materialize = p
        materialized_ok = False
        opened_kind = "resolved"

        if p and kind_key in {"image", "emoji", "video_thumb"}:
            wxid_dir = _resolve_account_wxid_dir(account_dir)
            source_path = p
            if kind_key == "emoji":
                candidates: list[Path] = []
                try:
                    md5s = str(md5 or "").lower().strip()
                except Exception:
                    md5s = str(md5)

                try:
                    if p is not None and p.exists() and p.is_file():
                        if (not str(p.suffix or "")) and md5s and str(p.name).lower() == md5s:
                            candidates.extend(_iter_emoji_source_candidates(p.parent, md5s))
                            if p not in candidates:
                                candidates.append(p)
                        else:
                            candidates.append(p)
                            candidates.extend(_iter_emoji_source_candidates(p.parent, md5s))
                    else:
                        candidates = _iter_emoji_source_candidates(p, md5s)
                except Exception:
                    candidates = _iter_emoji_source_candidates(p, str(md5))

                # de-dup while keeping order
                seen: set[str] = set()
                uniq: list[Path] = []
                for c in candidates:
                    try:
                        k = str(c.resolve())
                    except Exception:
                        k = str(c)
                    if k in seen:
                        continue
                    seen.add(k)
                    uniq.append(c)
                candidates = uniq

                try:
                    preferred: list[Path] = []
                    if md5s:
                        for c in candidates:
                            try:
                                if md5s in str(c.name).lower():
                                    preferred.append(c)
                            except Exception:
                                continue
                    if preferred:
                        rest = [c for c in candidates if c not in preferred]
                        candidates = preferred + rest
                except Exception:
                    pass
                if not candidates and p is not None:
                    candidates = [p]
                for cand in candidates:
                    source_path = cand
                    materialized = _ensure_decrypted_resource_for_md5(
                        account_dir,
                        md5=str(md5),
                        source_path=source_path,
                        weixin_root=wxid_dir,
                    )
                    if materialized:
                        p = materialized
                        materialized_ok = True
                        opened_kind = "decrypted"
                        break

                if not materialized_ok:
                    try:
                        sz = -1
                        head_hex = ""
                        try:
                            if source_path and source_path.exists() and source_path.is_file():
                                sz = int(source_path.stat().st_size)
                                with open(source_path, "rb") as f:
                                    head_hex = f.read(32).hex()
                        except Exception:
                            pass
                        logger.info(
                            f"open_folder: emoji materialize failed: resolved={str(resolved_before_materialize)} source={str(source_path)} size={sz} head32={head_hex}"
                        )
                    except Exception:
                        pass

                    try:
                        resource_dir = _get_resource_dir(account_dir)
                        sub_dir = str(md5).lower()[:2] if len(str(md5)) >= 2 else "00"
                        fallback_dir = resource_dir / sub_dir
                        fallback_dir.mkdir(parents=True, exist_ok=True)
                        p = fallback_dir
                        opened_kind = "resource_dir"
                    except Exception:
                        try:
                            resource_dir = _get_resource_dir(account_dir)
                            sub_dir = str(md5).lower()[:2] if len(str(md5)) >= 2 else "00"
                            fallback_dir = resource_dir / sub_dir
                            fallback_dir.mkdir(parents=True, exist_ok=True)
                            p = fallback_dir
                            opened_kind = "resource_dir"
                        except Exception:
                            pass
            else:
                materialized = _ensure_decrypted_resource_for_md5(
                    account_dir,
                    md5=str(md5),
                    source_path=source_path,
                    weixin_root=wxid_dir,
                )
                if materialized:
                    p = materialized
                    materialized_ok = True
                    opened_kind = "decrypted"

        if kind_key == "emoji" and md5:
            try:
                existing2 = _try_find_decrypted_resource(account_dir, str(md5).lower())
                if existing2:
                    p = existing2
                    opened_kind = "decrypted"
            except Exception:
                pass

    if not p:
        if kind_key == "emoji":
            wxid_dir = _resolve_account_wxid_dir(account_dir)
            resource_dir = _get_resource_dir(account_dir)
            candidates: list[Path] = []
            if md5:
                sub_dir = str(md5).lower()[:2] if len(str(md5)) >= 2 else "00"
                c1 = resource_dir / sub_dir
                if c1.exists() and c1.is_dir():
                    candidates.append(c1)
            if resource_dir.exists() and resource_dir.is_dir():
                candidates.append(resource_dir)
            if wxid_dir:
                for c in [
                    wxid_dir / "msg" / "emoji",
                    wxid_dir / "msg" / "emoticon",
                    wxid_dir / "emoji",
                    wxid_dir,
                ]:
                    try:
                        if c.exists() and c.is_dir():
                            candidates.append(c)
                    except Exception:
                        continue
            candidates.append(account_dir)
            p = candidates[0]
        else:
            raise HTTPException(status_code=404, detail="File not found.")

    try:
        target = str(p.resolve())
    except Exception:
        target = str(p)

    logger.info(f"open_folder: kind={kind_key} md5={md5} server_id={server_id} -> {target}")

    if os.name != "nt":
        raise HTTPException(status_code=400, detail="open_folder is only supported on Windows.")

    try:
        tp = Path(target)
        if tp.exists() and tp.is_dir():
            subprocess.Popen(["explorer.exe", str(tp)])
        elif tp.exists():
            subprocess.Popen(["explorer.exe", "/select,", str(tp)])
        else:
            subprocess.Popen(["explorer.exe", str(tp.parent)])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open explorer: {e}")

    file_found = False
    try:
        tp2 = Path(target)
        if kind_key == "emoji":
            file_found = bool(tp2.exists())
        else:
            if tp2.exists() and tp2.is_file():
                file_found = True
    except Exception:
        pass

    resp = {"status": "success", "path": target}
    if kind_key == "emoji":
        resp["file_found"] = bool(file_found)
        resp["materialized"] = bool(materialized_ok) if "materialized_ok" in locals() else bool(file_found)
        resp["opened"] = str(opened_kind) if "opened_kind" in locals() else "unknown"
    return resp
