# -*- coding: utf-8 -*-
"""JBEXPORT 일일 목록 수집·저장·어제 대비 신규 공고 비교."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONNECTOR_DIR = _PROJECT_ROOT / "connectors" / "connectors_jbexport"
if str(_CONNECTOR_DIR) not in sys.path:
    sys.path.insert(0, str(_CONNECTOR_DIR))

import jbexport_proxy as jb  # noqa: E402

LIST_PAGE_LENGTH = 10
MAX_LIST_PAGES = 2000
JSON_DIR = Path("data") / "jbexport"


def _json_path_for(d: date) -> Path:
    return _PROJECT_ROOT / JSON_DIR / f"{d.isoformat()}.json"


def _row_to_record(row: Any, menu_uuid: str) -> Dict[str, str] | None:
    if not isinstance(row, dict):
        return None
    sp_seq = str(row.get("SP_SEQ") or row.get("spSeq") or row.get("sp_seq") or "").strip()
    if not sp_seq:
        return None
    title = str(row.get("js_title") or row.get("title") or row.get("TITLE") or "").strip()
    org = str(row.get("CODE_K") or row.get("CATEGO") or row.get("ORG") or "전북수출통합지원시스템").strip()
    status = str(row.get("STS_TXT") or row.get("status") or "").strip()
    period = str(row.get("period") or row.get("PERIOD") or "").strip()
    detail_url = jb.jbexport_canonical_detail_url(sp_seq, menu_uuid)
    return {
        "spSeq": sp_seq,
        "title": title,
        "org": org,
        "status": status,
        "period": period,
        "detail_url": detail_url,
    }


def _fetch_all_list_records() -> tuple[List[Dict[str, str]], str]:
    """전체 목록 수집. 실패 시 ([], error_msg)."""
    work_year = str(date.today().year)
    menu_uuid = jb.DEFAULT_MENU_UUID
    session = jb.get_jbexport_session()
    by_sp: Dict[str, Dict[str, str]] = {}
    start = 0
    draw = 1

    for _page in range(MAX_LIST_PAGES):
        j, err = jb.jbexport_post_work1_search(
            session,
            start=start,
            length=LIST_PAGE_LENGTH,
            draw=draw,
            work_year=work_year,
            client_view_url=None,
        )
        if err or j is None:
            return [], err or "empty_response"

        try:
            rt = int(j.get("recordsTotal", j.get("recordsFiltered", j.get("total", 0))) or 0)
        except Exception:
            rt = 0

        rows = j.get("data") or j.get("aaData") or j.get("rows") or []
        if not isinstance(rows, list):
            return [], "list_payload_not_array"

        for row in rows:
            rec = _row_to_record(row, menu_uuid)
            if rec:
                by_sp[rec["spSeq"]] = rec

        if len(rows) == 0:
            break
        if rt > 0 and start + len(rows) >= rt:
            break
        if rt == 0 and len(rows) < LIST_PAGE_LENGTH:
            break
        start += LIST_PAGE_LENGTH
        draw += 1

    ordered = list(by_sp.values())
    return ordered, ""


def _load_yesterday_sp_seqs() -> Set[str]:
    y = date.today() - timedelta(days=1)
    path = _json_path_for(y)
    if not path.is_file():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if not isinstance(raw, list):
        return set()
    out: Set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            s = str(item.get("spSeq") or item.get("SP_SEQ") or "").strip()
            if s:
                out.add(s)
    return out


def run_daily() -> Dict[str, Any]:
    """
    1) 목록 전체 수집 (getWork1Search.do, length=10 페이지 반복)
    2) data/jbexport/YYYY-MM-DD.json 저장
    3) 어제 파일과 spSeq 비교 → 신규만 new_items
    """
    today = date.today()
    today_str = today.isoformat()

    items, fetch_err = _fetch_all_list_records()
    if fetch_err:
        return {"status": "error", "stage": "list_fetch", "error": fetch_err}

    out_dir = _json_path_for(today).parent
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        today_path = _json_path_for(today)
        today_path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        return {"status": "error", "stage": "save", "error": str(e)}

    try:
        yesterday_sp = _load_yesterday_sp_seqs()
        new_full = [x for x in items if x["spSeq"] not in yesterday_sp]
        new_items = [
            {
                "spSeq": x["spSeq"],
                "title": x["title"],
                "detail_url": x["detail_url"],
            }
            for x in new_full
        ]
    except Exception as e:
        return {"status": "error", "stage": "compare", "error": str(e)}

    return {
        "status": "ok",
        "date": today_str,
        "total": len(items),
        "new_count": len(new_items),
        "new_items": new_items,
    }
