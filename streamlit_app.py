"""
Slam-Global · KOC 뷰어 (STEP 4 - 뷰어 기반)
-------------------------------------------------
- 여러 데이터 소스(영상 URL 있는 DB)를 드롭다운으로 선택
- 리스트 보기(빠름) ↔ 썸네일 보기 전환
- 썸네일 URL 있으면 이미지, 없으면 플레이스홀더로 폴백
- 로그인 / 좋아요 / 댓글 기능은 다음 단계에서 추가 예정
"""

import os
import math
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Slam-Global KOC 뷰어", page_icon="💄", layout="wide")

# ── Supabase 연결 ──────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase()

# ── 데이터 소스 정의 ───────────────────────────
# 각 소스마다 테이블/컬럼이 다르므로 매핑을 한곳에 모아둔다.
SOURCES = {
    "🇺🇸 US · KOC 영상 (9,490)": {
        "table": "koc_contents",
        "id_col": "influencer_id",
        "video_col": "video_url",
        "thumb_col": "thumbnail_url",
        "metrics": {
            "조회수": "play_count",
            "좋아요": "like_count",
            "댓글": "comment_count",
            "공유": "share_count",
            "저장": "save_count",
        },
        "date_col": "posted_at",
        "caption_col": "caption",
        "platform": "TikTok",
        "video_filter": ("video_url", "http%"),
    },
    "🇺🇸 US · TOP 영상 (1,342)": {
        "table": "top_contents",
        "id_col": "influencer_ID",
        "video_col": "video_url",
        "thumb_col": "thumbnail_url",
        "metrics": {"조회수": "views", "좋아요": "likes", "댓글": "comments", "저장": "saves"},
        "date_col": "posted_at",
        "caption_col": "title",
        "platform": "TikTok",
        "video_filter": ("video_url", "http%"),
    },
    "🇺🇸 US · 인플루언서 TikTok (1,876)": {
        "table": "US_DB",
        "id_col": "influencer_ID",
        "video_col": "VideoUrl_TT",
        "thumb_col": None,
        "metrics": {"조회수": "views", "좋아요": "likes", "저장": "saves"},
        "date_col": "date",
        "caption_col": None,
        "platform": "TikTok",
        "video_filter": ("VideoUrl_TT", "http%"),
    },
    "🇺🇸 US · 인플루언서 Instagram (618)": {
        "table": "US_DB",
        "id_col": "influencer_ID",
        "video_col": "VideoUrl_IG",
        "thumb_col": None,
        "metrics": {"조회수": "views", "좋아요": "likes", "저장": "saves"},
        "date_col": "date",
        "caption_col": None,
        "platform": "Instagram",
        "video_filter": ("VideoUrl_IG", "http%"),
    },
    "🇯🇵 JP · 인플루언서 TikTok (1,924)": {
        "table": "JP_DB",
        "id_col": "name",
        "video_col": "tiktok_url",
        "thumb_col": None,
        "metrics": {"팔로워": "tiktok_followers", "ER%": "engagement_rate"},
        "date_col": "created_at",
        "caption_col": None,
        "platform": "TikTok",
        "video_filter": ("tiktok_url", "http%"),
    },
}


# ── 데이터 조회 ────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_source(source_key: str) -> pd.DataFrame:
    """선택한 소스의 영상 URL 있는 행을 페이지네이션으로 모두 가져와 정규화한다."""
    cfg = SOURCES[source_key]

    cols = [cfg["id_col"], cfg["video_col"]]
    if cfg["thumb_col"]:
        cols.append(cfg["thumb_col"])
    if cfg["date_col"]:
        cols.append(cfg["date_col"])
    if cfg["caption_col"]:
        cols.append(cfg["caption_col"])
    cols += list(cfg["metrics"].values())
    select_str = ",".join(f'"{c}"' for c in dict.fromkeys(cols))

    rows, page, size = [], 0, 1000
    while True:
        q = supabase.table(cfg["table"]).select(select_str)
        fcol, fpat = cfg["video_filter"]
        q = q.like(fcol, fpat)
        res = q.range(page * size, page * size + size - 1).execute()
        if not res.data:
            break
        rows.extend(res.data)
        if len(res.data) < size:
            break
        page += 1

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    out = pd.DataFrame()
    out["인플루언서"] = df[cfg["id_col"]].astype(str)
    out["영상URL"] = df[cfg["video_col"]]
    out["플랫폼"] = cfg["platform"]
    out["썸네일"] = df[cfg["thumb_col"]] if cfg["thumb_col"] and cfg["thumb_col"] in df else None
    if cfg["date_col"] and cfg["date_col"] in df:
        out["날짜"] = pd.to_datetime(df[cfg["date_col"]], errors="coerce").dt.date.astype(str)
    if cfg["caption_col"] and cfg["caption_col"] in df:
        out["내용"] = df[cfg["caption_col"]].astype(str).str.slice(0, 80)

    for label, col in cfg["metrics"].items():
        if col in df:
            out[label] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False), errors="coerce"
            ).fillna(0)
            if label != "ER%":
                out[label] = out[label].astype("int64")

    return out


# ── 사이드바 ───────────────────────────────────
st.sidebar.title("💄 KOC 뷰어")
st.sidebar.markdown("---")

source_key = st.sidebar.selectbox("📂 데이터 소스", list(SOURCES.keys()))
cfg = SOURCES[source_key]

metric_labels = list(cfg["metrics"].keys())
sort_label = st.sidebar.selectbox("정렬 기준", metric_labels) if metric_labels else None
sort_desc = st.sidebar.radio("순서", ["높은순", "낮은순"], horizontal=True) == "높은순"

min_val = 0
if metric_labels:
    primary = metric_labels[0]
    min_val = st.sidebar.number_input(f"{primary} 최소", min_value=0, value=0, step=100)

load_btn = st.sidebar.button("🔍 불러오기", use_container_width=True, type="primary")

# ── 메인 헤더 ──────────────────────────────────
st.title("💄 Slam-Global KOC 뷰어")
st.caption("영상 URL이 있는 데이터만 표시 · 썸네일은 수집되는 대로 자동 채워집니다")

# ── 불러오기 실행 ──────────────────────────────
if load_btn:
    with st.spinner("데이터 불러오는 중..."):
        try:
            df = fetch_source(source_key)
            st.session_state["df"] = df
            st.session_state["src"] = source_key
        except Exception as e:
            st.error(f"오류: {e}")
            st.session_state["df"] = pd.DataFrame()

# ── 결과 ───────────────────────────────────────
if "df" in st.session_state and not st.session_state["df"].empty:
    df = st.session_state["df"].copy()

    if metric_labels and min_val > 0 and metric_labels[0] in df:
        df = df[df[metric_labels[0]] >= min_val]
    if sort_label and sort_label in df:
        df = df.sort_values(sort_label, ascending=not sort_desc)
    df = df.reset_index(drop=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("표시 결과", f"{len(df):,}개")
    c2.metric("소스", st.session_state["src"].split(" (")[0])
    has_thumb = int(df["썸네일"].notna().sum()) if "썸네일" in df else 0
    c3.metric("썸네일 보유", f"{has_thumb:,}개")

    view = st.radio(
        "보기 방식", ["📋 리스트 (빠름)", "🖼️ 썸네일"], horizontal=True, label_visibility="collapsed"
    )
    st.markdown("---")

    if view.startswith("📋"):
        col_cfg = {
            "영상URL": st.column_config.LinkColumn("▶️ 영상", display_text="보기"),
        }
        if "썸네일" in df:
            col_cfg["썸네일"] = st.column_config.ImageColumn("썸네일", width="small")
        st.dataframe(df, use_container_width=True, height=620, column_config=col_cfg)

    else:
        PER_PAGE = 60
        total_pages = max(1, math.ceil(len(df) / PER_PAGE))
        page = st.number_input("페이지", 1, total_pages, 1, label_visibility="collapsed")
        chunk = df.iloc[(page - 1) * PER_PAGE : page * PER_PAGE].to_dict("records")
        st.caption(f"페이지 {page}/{total_pages} · {len(df):,}개 중 {len(chunk)}개 표시")

        cols = st.columns(5)
        for i, row in enumerate(chunk):
            with cols[i % 5]:
                with st.container(border=True):
                    thumb = row.get("썸네일")
                    if isinstance(thumb, str) and thumb.startswith("http"):
                        st.image(thumb, use_container_width=True)
                    else:
                        st.markdown(
                            "<div style='aspect-ratio:9/16;background:#f0f0f3;border-radius:8px;"
                            "display:flex;align-items:center;justify-content:center;"
                            "color:#aaa;font-size:28px;'>🎬</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown(f"**@{row['인플루언서']}**")
                    if metric_labels:
                        m = metric_labels[0]
                        st.caption(f"{m} {row.get(m, 0):,}")
                    st.markdown(f"[▶️ 영상 보기]({row['영상URL']})")

else:
    st.info("👈 왼쪽에서 데이터 소스를 고르고 **불러오기**를 눌러주세요.")
    st.markdown(
        """
        **사용법**
        1. 데이터 소스 선택 (미국 KOC 영상 / 일본 / TOP 영상 등)
        2. 정렬·최소값 설정 (선택)
        3. 불러오기 → 리스트로 빠르게 확인, 필요하면 썸네일 보기로 전환
        """
    )
