import os
import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="뷰티 인플루언서 데이터", page_icon="💄", layout="wide")

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ── 사이드바 ──────────────────────────────────
st.sidebar.title("💄 KOC 필터")
st.sidebar.markdown("---")
platform_label = st.sidebar.selectbox("📱 플랫폼", ["전체", "Tiktok", "Instagram"])
limit          = st.sidebar.slider("표시 개수", 100, 5000, 1000, 100)
search_btn     = st.sidebar.button("🔍 검색", use_container_width=True)

# ── 메인 ──────────────────────────────────────
st.title("💄 뷰티 인플루언서 데이터")
st.caption("미국 KOC · 컨텐츠 URL + 인게이지먼트")

RENAME_MAP = {
    'influencer_ID': 'ID',
    'platform':      '플랫폼',
    'likes':         '좋아요',
    'views':         '조회수',
    'saves':         '저장',
    'VideoUrl_TT':   'TikTok URL',
    'VideoUrl_IG':   'Instagram URL',
}

def fetch_data(platform_label, limit):
    try:
        query = supabase.table('koc_contents_view').select('*')

        if platform_label != "전체":
            query = query.eq('platform', platform_label)

        result = query.limit(limit).execute()
        return result.data, None
    except Exception as e:
        return None, str(e)

# ── 검색 실행 ─────────────────────────────────
if search_btn:
    with st.spinner("데이터 불러오는 중..."):
        data, error = fetch_data(platform_label, limit)

    if error:
        st.error(f"오류: {error}")
        st.session_state['data'] = []
    elif data and len(data) > 0:
        st.session_state['data'] = data
        st.session_state['platform'] = platform_label
        st.success(f"✅ {len(data)}개 로드 완료!")
    else:
        st.warning("데이터가 없습니다.")
        st.session_state['data'] = []

# ── 결과 출력 ─────────────────────────────────
if 'data' in st.session_state and st.session_state['data']:
    data = st.session_state['data']

    c1, c2, c3 = st.columns(3)
    c1.metric("검색 결과", f"{len(data)}개")
    c2.metric("플랫폼", st.session_state.get('platform', '전체'))
    c3.metric("전체 보유", "1,800개")

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
                    st.markdown(f"👀 조회수 `{inf.get('views', 'N/A')}`")
                    st.markdown(f"❤️ 좋아요 `{inf.get('likes', 'N/A')}`")
                    st.markdown(f"🔖 저장 `{inf.get('saves', 'N/A')}`")
                    tt = inf.get('VideoUrl_TT', '')
                    ig = inf.get('VideoUrl_IG', '')
                    if tt:
                        st.markdown(f"[🎵 TikTok]({tt})")
                    if ig:
                        st.markdown(f"[📸 Instagram]({ig})")

else:
    st.markdown("---")
    st.info("👈 왼쪽 필터 설정 후 검색 버튼을 눌러주세요.")
    st.markdown("""
    **데이터 구성**
    - 미국 KOC 1,800개
    - 컨텐츠 URL + 인게이지먼트 보유
    - TikTok / Instagram 필터 가능
    """)
