import os
import sqlite3
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from ..logging_config import get_logger
from ..chat_helpers import (
    _build_avatar_url,
    _decode_message_content,
    _decode_sqlite_text,
    _extract_sender_from_group_xml,
    _extract_xml_attr,
    _extract_xml_tag_or_attr,
    _extract_xml_tag_text,
    _format_session_time,
    _infer_last_message_brief,
    _infer_message_brief_by_local_type,
    _infer_transfer_status_text,
    _iter_message_db_paths,
    _list_decrypted_accounts,
    _load_contact_rows,
    _load_latest_message_previews,
    _lookup_resource_md5,
    _parse_app_message,
    _parse_pat_message,
    _pick_avatar_url,
    _pick_display_name,
    _query_head_image_usernames,
    _quote_ident,
    _resolve_account_dir,
    _resolve_msg_table_name,
    _resource_lookup_chat_id,
    _should_keep_session,
    _split_group_sender_prefix,
)
from ..media_helpers import _try_find_decrypted_resource
from ..path_fix import PathFixRoute

logger = get_logger(__name__)

_DEBUG_SESSIONS = os.environ.get("WECHAT_TOOL_DEBUG_SESSIONS", "0") == "1"

router = APIRouter(route_class=PathFixRoute)


@router.get("/api/chat/accounts", summary="列出已解密账号")
async def list_chat_accounts():
    """列出 output/databases 下可用于聊天预览的账号目录"""
    accounts = _list_decrypted_accounts()
    if not accounts:
        return {
            "status": "error",
            "accounts": [],
            "default_account": None,
            "message": "No decrypted databases found. Please decrypt first.",
        }

    return {
        "status": "success",
        "accounts": accounts,
        "default_account": accounts[0],
    }


@router.get("/api/chat/sessions", summary="获取会话列表（聊天左侧列表）")
async def list_chat_sessions(
    request: Request,
    account: Optional[str] = None,
    limit: int = 400,
    include_hidden: bool = False,
    include_official: bool = False,
):
    """从 session.db + contact.db 读取会话列表，用于前端聊天界面动态渲染联系人"""
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Invalid limit.")
    if limit > 2000:
        limit = 2000

    account_dir = _resolve_account_dir(account)
    session_db_path = account_dir / "session.db"
    contact_db_path = account_dir / "contact.db"
    head_image_db_path = account_dir / "head_image.db"
    base_url = str(request.base_url).rstrip("/")

    sconn = sqlite3.connect(str(session_db_path))
    sconn.row_factory = sqlite3.Row
    try:
        rows = sconn.execute(
            """
            SELECT
                username,
                unread_count,
                is_hidden,
                summary,
                draft,
                last_timestamp,
                sort_timestamp,
                last_msg_type,
                last_msg_sub_type
            FROM SessionTable
            ORDER BY sort_timestamp DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    finally:
        sconn.close()

    filtered: list[sqlite3.Row] = []
    usernames: list[str] = []
    for r in rows:
        username = r["username"] or ""
        if not username:
            continue
        if not include_hidden and int(r["is_hidden"] or 0) == 1:
            continue
        if not _should_keep_session(username, include_official=include_official):
            continue
        filtered.append(r)
        usernames.append(username)

    contact_rows = _load_contact_rows(contact_db_path, usernames)
    local_avatar_usernames = _query_head_image_usernames(head_image_db_path, usernames)
    latest_previews = _load_latest_message_previews(account_dir, usernames)
    if _DEBUG_SESSIONS:
        logger.info(
            f"[sessions.preview] endpoint account={account_dir.name} sessions={len(usernames)} previews={len(latest_previews)}"
        )

    sessions: list[dict[str, Any]] = []
    for r in filtered:
        username = r["username"]
        c_row = contact_rows.get(username)

        display_name = _pick_display_name(c_row, username)
        avatar_url = _pick_avatar_url(c_row)
        if not avatar_url and username in local_avatar_usernames:
            avatar_url = base_url + _build_avatar_url(account_dir.name, username)

        if str(latest_previews.get(username) or "").strip():
            last_message = str(latest_previews.get(username) or "").strip()
        else:
            last_message = _infer_last_message_brief(r["last_msg_type"], r["last_msg_sub_type"])

        last_time = _format_session_time(r["sort_timestamp"] or r["last_timestamp"])

        sessions.append(
            {
                "id": username,
                "username": username,
                "name": display_name,
                "avatar": avatar_url,
                "lastMessage": last_message,
                "lastMessageTime": last_time,
                "unreadCount": int(r["unread_count"] or 0),
                "isGroup": bool(username.endswith("@chatroom")),
            }
        )

    return {
        "status": "success",
        "account": account_dir.name,
        "total": len(sessions),
        "sessions": sessions,
    }


@router.get("/api/chat/messages", summary="获取会话消息列表")
async def list_chat_messages(
    request: Request,
    username: str,
    account: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    order: str = "asc",
):
    if not username:
        raise HTTPException(status_code=400, detail="Missing username.")
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Invalid limit.")
    if limit > 500:
        limit = 500
    if offset < 0:
        offset = 0

    account_dir = _resolve_account_dir(account)
    db_paths = _iter_message_db_paths(account_dir)
    contact_db_path = account_dir / "contact.db"
    head_image_db_path = account_dir / "head_image.db"
    message_resource_db_path = account_dir / "message_resource.db"
    base_url = str(request.base_url).rstrip("/")
    if not db_paths:
        return {
            "status": "error",
            "account": account_dir.name,
            "username": username,
            "total": 0,
            "messages": [],
            "message": "No message databases found for this account.",
        }

    resource_conn: Optional[sqlite3.Connection] = None
    resource_chat_id: Optional[int] = None
    try:
        if message_resource_db_path.exists():
            resource_conn = sqlite3.connect(str(message_resource_db_path))
            resource_conn.row_factory = sqlite3.Row
            resource_chat_id = _resource_lookup_chat_id(resource_conn, username)
    except Exception:
        if resource_conn is not None:
            try:
                resource_conn.close()
            except Exception:
                pass
        resource_conn = None
        resource_chat_id = None

    want_asc = str(order or "").lower() != "desc"
    take = int(limit) + int(offset)
    take_probe = take + 1
    merged: list[dict[str, Any]] = []
    sender_usernames: list[str] = []
    pat_usernames: set[str] = set()
    is_group = bool(username.endswith("@chatroom"))
    has_more_any = False

    for db_path in db_paths:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            table_name = _resolve_msg_table_name(conn, username)
            if not table_name:
                continue

            my_wxid = account_dir.name
            my_rowid = None
            try:
                r = conn.execute(
                    "SELECT rowid FROM Name2Id WHERE user_name = ? LIMIT 1",
                    (my_wxid,),
                ).fetchone()
                if r is not None:
                    my_rowid = int(r[0])
            except Exception:
                my_rowid = None

            quoted_table = _quote_ident(table_name)
            sql_with_join = (
                "SELECT "
                "m.local_id, m.server_id, m.local_type, m.sort_seq, m.real_sender_id, m.create_time, "
                "m.message_content, m.compress_content, n.user_name AS sender_username "
                f"FROM {quoted_table} m "
                "LEFT JOIN Name2Id n ON m.real_sender_id = n.rowid "
                "ORDER BY m.create_time DESC, m.sort_seq DESC, m.local_id DESC "
                "LIMIT ?"
            )
            sql_no_join = (
                "SELECT "
                "m.local_id, m.server_id, m.local_type, m.sort_seq, m.real_sender_id, m.create_time, "
                "m.message_content, m.compress_content, '' AS sender_username "
                f"FROM {quoted_table} m "
                "ORDER BY m.create_time DESC, m.sort_seq DESC, m.local_id DESC "
                "LIMIT ?"
            )

            # Force sqlite3 to return TEXT as raw bytes for this query, so we can zstd-decompress
            # compress_content reliably.
            conn.text_factory = bytes

            try:
                rows = conn.execute(sql_with_join, (take_probe,)).fetchall()
            except Exception:
                rows = conn.execute(sql_no_join, (take_probe,)).fetchall()
            if len(rows) > take:
                has_more_any = True
                rows = rows[:take]

            for r in rows:
                local_id = int(r["local_id"] or 0)
                create_time = int(r["create_time"] or 0)
                sort_seq = int(r["sort_seq"] or 0) if r["sort_seq"] is not None else 0
                local_type = int(r["local_type"] or 0)
                sender_username = _decode_sqlite_text(r["sender_username"]).strip()

                is_sent = False
                if my_rowid is not None:
                    try:
                        is_sent = int(r["real_sender_id"] or 0) == int(my_rowid)
                    except Exception:
                        is_sent = False

                raw_text = _decode_message_content(r["compress_content"], r["message_content"])
                raw_text = raw_text.strip()

                sender_prefix = ""
                if is_group and not raw_text.startswith("<") and not raw_text.startswith('"<'):
                    sender_prefix, raw_text = _split_group_sender_prefix(raw_text)

                if is_group and sender_prefix:
                    sender_username = sender_prefix

                if is_group and (raw_text.startswith("<") or raw_text.startswith('"<')):
                    xml_sender = _extract_sender_from_group_xml(raw_text)
                    if xml_sender:
                        sender_username = xml_sender

                if is_sent:
                    sender_username = account_dir.name
                elif (not is_group) and (not sender_username):
                    sender_username = username

                if sender_username:
                    sender_usernames.append(sender_username)

                render_type = "text"
                content_text = raw_text
                title = ""
                url = ""
                image_md5 = ""
                emoji_md5 = ""
                emoji_url = ""
                thumb_url = ""
                image_url = ""
                image_file_id = ""
                video_md5 = ""
                video_thumb_md5 = ""
                video_file_id = ""
                video_thumb_file_id = ""
                video_url = ""
                video_thumb_url = ""
                voice_length = ""
                quote_title = ""
                quote_content = ""
                amount = ""
                cover_url = ""
                file_size = ""
                pay_sub_type = ""
                transfer_status = ""
                file_md5 = ""
                transfer_id = ""
                voip_type = ""

                if local_type == 10000:
                    render_type = "system"
                    if "revokemsg" in raw_text:
                        content_text = "撤回了一条消息"
                    else:
                        import re

                        content_text = re.sub(r"</?[_a-zA-Z0-9]+[^>]*>", "", raw_text)
                        content_text = re.sub(r"\s+", " ", content_text).strip() or "[系统消息]"
                elif local_type == 49:
                    parsed = _parse_app_message(raw_text)
                    render_type = str(parsed.get("renderType") or "text")
                    content_text = str(parsed.get("content") or "")
                    title = str(parsed.get("title") or "")
                    url = str(parsed.get("url") or "")
                    quote_title = str(parsed.get("quoteTitle") or "")
                    quote_content = str(parsed.get("quoteContent") or "")
                    amount = str(parsed.get("amount") or "")
                    cover_url = str(parsed.get("coverUrl") or "")
                    thumb_url = str(parsed.get("thumbUrl") or "")
                    file_size = str(parsed.get("size") or "")
                    pay_sub_type = str(parsed.get("paySubType") or "")
                    file_md5 = str(parsed.get("fileMd5") or "")
                    transfer_id = str(parsed.get("transferId") or "")

                    if render_type == "transfer":
                        # 直接从原始 XML 提取 transferid（可能在 wcpayinfo 内）
                        if not transfer_id:
                            transfer_id = _extract_xml_tag_or_attr(raw_text, "transferid") or ""
                        transfer_status = _infer_transfer_status_text(
                            is_sent=is_sent,
                            paysubtype=pay_sub_type,
                            receivestatus=str(parsed.get("receiveStatus") or ""),
                            sendertitle=str(parsed.get("senderTitle") or ""),
                            receivertitle=str(parsed.get("receiverTitle") or ""),
                            senderdes=str(parsed.get("senderDes") or ""),
                            receiverdes=str(parsed.get("receiverDes") or ""),
                        )
                        if not content_text:
                            content_text = transfer_status or "转账"
                elif local_type == 266287972401:
                    render_type = "system"
                    template = _extract_xml_tag_text(raw_text, "template")
                    if template:
                        import re

                        pat_usernames.update({m.group(1) for m in re.finditer(r"\$\{([^}]+)\}", template) if m.group(1)})
                        content_text = "[拍一拍]"
                    else:
                        content_text = "[拍一拍]"
                elif local_type == 244813135921:
                    render_type = "quote"
                    parsed = _parse_app_message(raw_text)
                    content_text = str(parsed.get("content") or "[引用消息]")
                    quote_title = str(parsed.get("quoteTitle") or "")
                    quote_content = str(parsed.get("quoteContent") or "")
                elif local_type == 3:
                    render_type = "image"
                    # 先尝试从 XML 中提取 md5（不同版本字段可能不同）
                    image_md5 = _extract_xml_attr(raw_text, "md5") or _extract_xml_tag_text(raw_text, "md5")
                    if not image_md5:
                        for k in [
                            "cdnthumbmd5",
                            "cdnthumd5",
                            "cdnmidimgmd5",
                            "cdnbigimgmd5",
                            "hdmd5",
                            "hevc_mid_md5",
                            "hevc_md5",
                            "imgmd5",
                            "filemd5",
                        ]:
                            image_md5 = _extract_xml_attr(raw_text, k) or _extract_xml_tag_text(raw_text, k)
                            if image_md5:
                                break

                    # Extract CDN URL (some versions store a non-HTTP "file id" string here)
                    _cdn_url_or_id = (
                        _extract_xml_attr(raw_text, "cdnthumburl")
                        or _extract_xml_attr(raw_text, "cdnthumurl")
                        or _extract_xml_attr(raw_text, "cdnmidimgurl")
                        or _extract_xml_attr(raw_text, "cdnbigimgurl")
                        or _extract_xml_tag_text(raw_text, "cdnthumburl")
                        or _extract_xml_tag_text(raw_text, "cdnthumurl")
                        or _extract_xml_tag_text(raw_text, "cdnmidimgurl")
                        or _extract_xml_tag_text(raw_text, "cdnbigimgurl")
                    )
                    _cdn_url_or_id = str(_cdn_url_or_id or "").strip()
                    image_url = _cdn_url_or_id if _cdn_url_or_id.startswith(("http://", "https://")) else ""
                    if (not image_url) and _cdn_url_or_id:
                        image_file_id = _cdn_url_or_id

                    if (not image_md5) and resource_conn is not None:
                        image_md5 = _lookup_resource_md5(
                            resource_conn,
                            resource_chat_id,
                            message_local_type=local_type,
                            server_id=int(r["server_id"] or 0),
                            local_id=local_id,
                            create_time=create_time,
                        )
                    content_text = "[图片]"
                elif local_type == 34:
                    render_type = "voice"
                    duration = _extract_xml_attr(raw_text, "voicelength")
                    voice_length = duration
                    content_text = f"[语音 {duration}秒]" if duration else "[语音]"
                elif local_type == 43 or local_type == 62:
                    render_type = "video"
                    video_md5 = _extract_xml_attr(raw_text, "md5")
                    video_thumb_md5 = _extract_xml_attr(raw_text, "cdnthumbmd5")
                    video_thumb_url_or_id = _extract_xml_attr(raw_text, "cdnthumburl") or _extract_xml_tag_text(
                        raw_text, "cdnthumburl"
                    )
                    video_url_or_id = _extract_xml_attr(raw_text, "cdnvideourl") or _extract_xml_tag_text(
                        raw_text, "cdnvideourl"
                    )

                    video_thumb_url = (
                        video_thumb_url_or_id
                        if str(video_thumb_url_or_id or "").strip().lower().startswith(("http://", "https://"))
                        else ""
                    )
                    video_url = (
                        video_url_or_id
                        if str(video_url_or_id or "").strip().lower().startswith(("http://", "https://"))
                        else ""
                    )
                    video_thumb_file_id = "" if video_thumb_url else (str(video_thumb_url_or_id or "").strip() or "")
                    video_file_id = "" if video_url else (str(video_url_or_id or "").strip() or "")
                    if (not video_thumb_md5) and resource_conn is not None:
                        video_thumb_md5 = _lookup_resource_md5(
                            resource_conn,
                            resource_chat_id,
                            message_local_type=local_type,
                            server_id=int(r["server_id"] or 0),
                            local_id=local_id,
                            create_time=create_time,
                        )
                    content_text = "[视频]"
                elif local_type == 47:
                    render_type = "emoji"
                    emoji_md5 = _extract_xml_attr(raw_text, "md5")
                    if not emoji_md5:
                        emoji_md5 = _extract_xml_tag_text(raw_text, "md5")
                    emoji_url = _extract_xml_attr(raw_text, "cdnurl")
                    if not emoji_url:
                        emoji_url = _extract_xml_tag_text(raw_text, "cdn_url")
                    if (not emoji_md5) and resource_conn is not None:
                        emoji_md5 = _lookup_resource_md5(
                            resource_conn,
                            resource_chat_id,
                            message_local_type=local_type,
                            server_id=int(r["server_id"] or 0),
                            local_id=local_id,
                            create_time=create_time,
                        )
                    content_text = "[表情]"
                elif local_type == 50:
                    render_type = "voip"
                    try:
                        import re

                        block = raw_text
                        m_voip = re.search(
                            r"(<VoIPBubbleMsg[^>]*>.*?</VoIPBubbleMsg>)",
                            raw_text,
                            flags=re.IGNORECASE | re.DOTALL,
                        )
                        if m_voip:
                            block = m_voip.group(1) or raw_text
                        room_type = str(_extract_xml_tag_text(block, "room_type") or "").strip()
                        if room_type == "0":
                            voip_type = "video"
                        elif room_type == "1":
                            voip_type = "audio"

                        voip_msg = str(_extract_xml_tag_text(block, "msg") or "").strip()
                        content_text = voip_msg or "通话"
                    except Exception:
                        content_text = "通话"
                elif local_type != 1:
                    if not content_text:
                        content_text = _infer_message_brief_by_local_type(local_type)
                    else:
                        if content_text.startswith("<") or content_text.startswith('"<'):
                            if "<appmsg" in content_text.lower():
                                parsed = _parse_app_message(content_text)
                                rt = str(parsed.get("renderType") or "")
                                if rt and rt != "text":
                                    render_type = rt
                                    content_text = str(parsed.get("content") or content_text)
                                    title = str(parsed.get("title") or title)
                                    url = str(parsed.get("url") or url)
                                    quote_title = str(parsed.get("quoteTitle") or quote_title)
                                    quote_content = str(parsed.get("quoteContent") or quote_content)
                                    amount = str(parsed.get("amount") or amount)
                                    cover_url = str(parsed.get("coverUrl") or cover_url)
                                    thumb_url = str(parsed.get("thumbUrl") or thumb_url)
                                    file_size = str(parsed.get("size") or file_size)
                                    pay_sub_type = str(parsed.get("paySubType") or pay_sub_type)
                                    file_md5 = str(parsed.get("fileMd5") or file_md5)
                                    transfer_id = str(parsed.get("transferId") or transfer_id)

                                    if render_type == "transfer":
                                        # 如果 transferId 仍为空，尝试从原始 XML 提取
                                        if not transfer_id:
                                            transfer_id = _extract_xml_tag_or_attr(content_text, "transferid") or ""
                                        transfer_status = _infer_transfer_status_text(
                                            is_sent=is_sent,
                                            paysubtype=pay_sub_type,
                                            receivestatus=str(parsed.get("receiveStatus") or ""),
                                            sendertitle=str(parsed.get("senderTitle") or ""),
                                            receivertitle=str(parsed.get("receiverTitle") or ""),
                                            senderdes=str(parsed.get("senderDes") or ""),
                                            receiverdes=str(parsed.get("receiverDes") or ""),
                                        )
                                        if not content_text:
                                            content_text = transfer_status or "转账"
                            t = _extract_xml_tag_text(content_text, "title")
                            d = _extract_xml_tag_text(content_text, "des")
                            content_text = t or d or _infer_message_brief_by_local_type(local_type)

                if not content_text:
                    content_text = _infer_message_brief_by_local_type(local_type)

                merged.append(
                    {
                        "id": f"{db_path.stem}:{table_name}:{local_id}",
                        "localId": local_id,
                        "serverId": int(r["server_id"] or 0),
                        "type": local_type,
                        "createTime": create_time,
                        "sortSeq": sort_seq,
                        "senderUsername": sender_username,
                        "isSent": bool(is_sent),
                        "renderType": render_type,
                        "content": content_text,
                        "title": title,
                        "url": url,
                        "imageMd5": image_md5,
                        "imageFileId": image_file_id,
                        "emojiMd5": emoji_md5,
                        "emojiUrl": emoji_url,
                        "thumbUrl": thumb_url,
                        "imageUrl": image_url,
                        "videoMd5": video_md5,
                        "videoThumbMd5": video_thumb_md5,
                        "videoFileId": video_file_id,
                        "videoThumbFileId": video_thumb_file_id,
                        "videoUrl": video_url,
                        "videoThumbUrl": video_thumb_url,
                        "voiceLength": voice_length,
                        "voipType": voip_type,
                        "quoteTitle": quote_title,
                        "quoteContent": quote_content,
                        "amount": amount,
                        "coverUrl": cover_url,
                        "fileSize": file_size,
                        "fileMd5": file_md5,
                        "paySubType": pay_sub_type,
                        "transferStatus": transfer_status,
                        "transferId": transfer_id,
                        "_rawText": raw_text if local_type == 266287972401 else "",
                    }
                )
        finally:
            conn.close()

    if resource_conn is not None:
        try:
            resource_conn.close()
        except Exception:
            pass

    # 后处理：关联转账消息的最终状态
    # 策略：优先使用 transferId 精确匹配，回退到金额+时间窗口匹配
    # paysubtype 含义：1=不明确 3=已收款 4=对方退回给你 8=发起转账 9=被对方退回 10=已过期

    # 收集已退还和已收款的转账ID和金额
    returned_transfer_ids: set[str] = set()  # 退还状态的 transferId
    received_transfer_ids: set[str] = set()  # 已收款状态的 transferId
    returned_amounts_with_time: list[tuple[str, int]] = []  # (金额, 时间戳) 用于退还回退匹配
    received_amounts_with_time: list[tuple[str, int]] = []  # (金额, 时间戳) 用于收款回退匹配

    for m in merged:
        if m.get("renderType") == "transfer":
            pst = str(m.get("paySubType") or "")
            tid = str(m.get("transferId") or "").strip()
            amt = str(m.get("amount") or "")
            ts = int(m.get("createTime") or 0)

            if pst in ("4", "9"):  # 退还状态
                if tid:
                    returned_transfer_ids.add(tid)
                if amt:
                    returned_amounts_with_time.append((amt, ts))
            elif pst == "3":  # 已收款状态
                if tid:
                    received_transfer_ids.add(tid)
                if amt:
                    received_amounts_with_time.append((amt, ts))

    # 更新原始转账消息的状态
    for m in merged:
        if m.get("renderType") == "transfer":
            pst = str(m.get("paySubType") or "")
            # 只更新未确定状态的原始转账消息（paysubtype=1 或 8）
            if pst in ("1", "8"):
                tid = str(m.get("transferId") or "").strip()
                amt = str(m.get("amount") or "")
                ts = int(m.get("createTime") or 0)

                # 优先检查退还状态（退还优先于收款）
                should_mark_returned = False
                should_mark_received = False

                # 策略1：精确 transferId 匹配
                if tid:
                    if tid in returned_transfer_ids:
                        should_mark_returned = True
                    elif tid in received_transfer_ids:
                        should_mark_received = True

                # 策略2：回退到金额+时间窗口匹配（24小时内同金额）
                if not should_mark_returned and not should_mark_received and amt:
                    for ret_amt, ret_ts in returned_amounts_with_time:
                        if ret_amt == amt and abs(ret_ts - ts) <= 86400:
                            should_mark_returned = True
                            break
                    if not should_mark_returned:
                        for rec_amt, rec_ts in received_amounts_with_time:
                            if rec_amt == amt and abs(rec_ts - ts) <= 86400:
                                should_mark_received = True
                                break

                if should_mark_returned:
                    m["paySubType"] = "9"
                    m["transferStatus"] = "已被退还"
                elif should_mark_received:
                    m["paySubType"] = "3"
                    # 根据 isSent 判断：发起方显示"已收款"，收款方显示"已被接收"
                    is_sent = m.get("isSent", False)
                    m["transferStatus"] = "已收款" if is_sent else "已被接收"

    uniq_senders = list(dict.fromkeys([u for u in (sender_usernames + list(pat_usernames)) if u]))
    sender_contact_rows = _load_contact_rows(contact_db_path, uniq_senders)
    local_sender_avatars = _query_head_image_usernames(head_image_db_path, uniq_senders)

    for m in merged:
        su = str(m.get("senderUsername") or "")
        if not su:
            continue
        row = sender_contact_rows.get(su)
        m["senderDisplayName"] = _pick_display_name(row, su)
        avatar_url = _pick_avatar_url(row)
        if not avatar_url and su in local_sender_avatars:
            avatar_url = base_url + _build_avatar_url(account_dir.name, su)
        m["senderAvatar"] = avatar_url

        # Media URL fallback: if CDN URLs missing, use local media endpoints.
        try:
            rt = str(m.get("renderType") or "")
            if rt == "image":
                if not str(m.get("imageUrl") or ""):
                    md5 = str(m.get("imageMd5") or "").strip()
                    file_id = str(m.get("imageFileId") or "").strip()
                    if md5:
                        m["imageUrl"] = (
                            base_url
                            + f"/api/chat/media/image?account={quote(account_dir.name)}&md5={quote(md5)}&username={quote(username)}"
                        )
                    elif file_id:
                        m["imageUrl"] = (
                            base_url
                            + f"/api/chat/media/image?account={quote(account_dir.name)}&file_id={quote(file_id)}&username={quote(username)}"
                        )
            elif rt == "emoji":
                md5 = str(m.get("emojiMd5") or "")
                if md5:
                    existing_local: Optional[Path] = None
                    try:
                        existing_local = _try_find_decrypted_resource(account_dir, str(md5).lower())
                    except Exception:
                        existing_local = None

                    if existing_local:
                        try:
                            import re

                            cur = str(m.get("emojiUrl") or "")
                            if cur and re.match(r"^https?://", cur, flags=re.I) and ("/api/chat/media/emoji" not in cur):
                                m["emojiRemoteUrl"] = cur
                        except Exception:
                            pass

                        m["emojiUrl"] = (
                            base_url
                            + f"/api/chat/media/emoji?account={quote(account_dir.name)}&md5={quote(md5)}&username={quote(username)}"
                        )
                    elif (not str(m.get("emojiUrl") or "")):
                        m["emojiUrl"] = (
                            base_url
                            + f"/api/chat/media/emoji?account={quote(account_dir.name)}&md5={quote(md5)}&username={quote(username)}"
                        )
            elif rt == "video":
                video_thumb_url = str(m.get("videoThumbUrl") or "").strip()
                video_thumb_md5 = str(m.get("videoThumbMd5") or "").strip()
                video_thumb_file_id = str(m.get("videoThumbFileId") or "").strip()
                if (not video_thumb_url) or (
                    not video_thumb_url.lower().startswith(("http://", "https://"))
                ):
                    if video_thumb_md5:
                        m["videoThumbUrl"] = (
                            base_url
                            + f"/api/chat/media/video_thumb?account={quote(account_dir.name)}&md5={quote(video_thumb_md5)}&username={quote(username)}"
                        )
                    elif video_thumb_file_id:
                        m["videoThumbUrl"] = (
                            base_url
                            + f"/api/chat/media/video_thumb?account={quote(account_dir.name)}&file_id={quote(video_thumb_file_id)}&username={quote(username)}"
                        )

                video_url = str(m.get("videoUrl") or "").strip()
                video_md5 = str(m.get("videoMd5") or "").strip()
                video_file_id = str(m.get("videoFileId") or "").strip()
                if (not video_url) or (not video_url.lower().startswith(("http://", "https://"))):
                    if video_md5:
                        m["videoUrl"] = (
                            base_url
                            + f"/api/chat/media/video?account={quote(account_dir.name)}&md5={quote(video_md5)}&username={quote(username)}"
                        )
                    elif video_file_id:
                        m["videoUrl"] = (
                            base_url
                            + f"/api/chat/media/video?account={quote(account_dir.name)}&file_id={quote(video_file_id)}&username={quote(username)}"
                        )
            elif rt == "voice":
                if str(m.get("serverId") or ""):
                    sid = int(m.get("serverId") or 0)
                    if sid:
                        m["voiceUrl"] = base_url + f"/api/chat/media/voice?account={quote(account_dir.name)}&server_id={sid}"
        except Exception:
            pass

        if int(m.get("type") or 0) == 266287972401:
            raw = str(m.get("_rawText") or "")
            if raw:
                m["content"] = _parse_pat_message(raw, sender_contact_rows)

        if "_rawText" in m:
            m.pop("_rawText", None)

    def sort_key(m: dict[str, Any]) -> tuple[int, int, int]:
        sseq = int(m.get("sortSeq") or 0)
        cts = int(m.get("createTime") or 0)
        lid = int(m.get("localId") or 0)
        return (cts, sseq, lid)

    merged.sort(key=sort_key, reverse=True)
    has_more_global = bool(has_more_any or (len(merged) > (int(offset) + int(limit))))
    page = merged[int(offset) : int(offset) + int(limit)]
    if want_asc:
        page = list(reversed(page))

    return {
        "status": "success",
        "account": account_dir.name,
        "username": username,
        "total": int(offset) + len(page) + (1 if has_more_global else 0),
        "hasMore": bool(has_more_global),
        "messages": page,
    }
