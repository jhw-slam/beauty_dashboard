import os
import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="뷰티 인플루언서 데이터", page_icon="💄", layout="wide")

# ── Supabase 연결 ─────────────────────────────
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ── 테이블별 실제 컬럼 정의 ───────────────────
TABLE_COLUMNS = {
    'US_DB':        'influencer_ID, platform, followers, likes, views, saves, VideoUrl_TT, VideoUrl_IG',
    'UAE_DB':       'influencer_ID, platform, followers, likes_comments, views, saves',
    'my_sg_ph_DB':  'influencer_ID, platform, followers, likes_comments, views, saves',
}

REGION_MAP = {
    "🇺🇸 미국 (US)":        "US_DB",
    "🇦🇪 UAE":              "UAE_DB",
    "🌏 동남아 (MY/SG/PH)":  "my_sg_ph_DB",
}

RENAME_MAP = {
    'influencer_ID':  'ID',
    'platform':       '플랫폼',
    'followers':      '팔로워',
    'likes':          '좋아요',
    'likes_comments': '좋아요·댓글',
    'views':          '조회수',
    'saves':          '저장',
    'VideoUrl_TT':    'TikTok URL',
    'VideoUrl_IG':    'Instagram URL',
}

# ── 사이드바 ──────────────────────────────────
st.sidebar.title("💄 KOC 필터")
st.sidebar.markdown("---")
region_label    = st.sidebar.selectbox("🌍 지역 선택", list(REGION_MAP.keys()))
platform_filter = st.sidebar.selectbox("📱 플랫폼", ["전체", "Tiktok", "Instagram", "YouTube", "X"])
limit           = st.sidebar.slider("표시 개수", 10, 100, 30, 10)
search_btn      = st.sidebar.button("🔍 검색", use_container_width=True)

# ── 메인 ──────────────────────────────────────
st.title("💄 뷰티 인플루언서 데이터")
st.caption("Supabase 실시간 연결 · 필터링")

# ── 데이터 조회 ───────────────────────────────
def fetch_data(table_name, platform, limit):
    try:
        columns = TABLE_COLUMNS.get(table_name, '*')
        query = supabase.table(table_name).select(columns)

        if platform != "전체":
            query = query.ilike('platform', f'%{platform}%')

        result = query.limit(limit).execute()
        return result.data, None
    except Exception as e:
        return None, str(e)

# ── 검색 실행 ─────────────────────────────────
if search_btn:
    table_name = REGION_MAP[region_label]
    with st.spinner(f"{region_label} 데이터 불러오는 중..."):
        data, error = fetch_data(table_name, platform_filter, limit)

    if error:
        st.error(f"오류: {error}")
        st.session_state['data'] = []
    elif data and len(data) > 0:
        st.session_state['data'] = data
        st.session_state['region_label'] = region_label
        st.session_state['platform'] = platform_filter
        st.session_state['table_name'] = table_name
    else:
        st.warning(f"데이터가 없습니다. 플랫폼 필터를 '전체'로 바꿔서 다시 검색해보세요.")
        st.session_state['data'] = []

# ── 결과 출력 ─────────────────────────────────
if 'data' in st.session_state and st.session_state['data']:
    data = st.session_state['data']

    c1, c2, c3 = st.columns(3)
    c1.metric("검색 결과", f"{len(data)}명")
    c2.metric("지역", st.session_state.get('region_label', ''))
    c3.metric("플랫폼", st.session_state.get('platform', '전체'))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 테이블 뷰", "🃏 카드 뷰"])

    with tab1:
        df = pd.DataFrame(data)
        df = df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns})
        st.dataframe(df, use_container_width=True, height=600)

    with tab2:
        cols = st.columns(3)
        for i, inf in enumerate(data):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**@{inf.get('influencer_ID', 'N/A')}**")
                    st.caption(f"📱 {inf.get('platform', 'N/A')}")
                    st.markdown(f"👥 팔로워 `{inf.get('followers', 'N/A')}`")
                    st.markdown(f"👀 조회수 `{inf.get('views', 'N/A')}`")
                    likes = inf.get('likes') or inf.get('likes_comments', 'N/A')
                    st.markdown(f"❤️ 좋아요 `{likes}`")
                    st.markdown(f"🔖 저장 `{inf.get('saves', 'N/A')}`")

else:
    st.markdown("---")
    st.info("👈 왼쪽 필터 설정 후 검색 버튼을 눌러주세요.")
    st.markdown("""
    **사용 방법**
    1. 지역 선택 (미국 / UAE / 동남아)
    2. 플랫폼 선택 — **일단 '전체'로 먼저 검색해보세요**
    3. 검색 버튼 클릭
    """)
