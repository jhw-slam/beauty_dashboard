import os
import streamlit as st
from supabase import create_client

# ── 페이지 설정 ──────────────────────────────
st.set_page_config(
    page_title="뷰티 인플루언서 데이터",
    page_icon="💄",
    layout="wide"
)

# ── Supabase 연결 ────────────────────────────
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ── 테이블 매핑 ───────────────────────────────
REGION_MAP = {
    "🇺🇸 미국 (US)":        "US_DB",
    "🇦🇪 UAE":              "UAE_DB",
    "🌏 동남아 (MY/SG/PH)":  "my_sg_ph_DB",
}

# ── 사이드바 필터 ────────────────────────────
st.sidebar.title("💄 KOC 필터")
st.sidebar.markdown("---")

region_label    = st.sidebar.selectbox("🌍 지역 선택", list(REGION_MAP.keys()))
platform_filter = st.sidebar.selectbox("📱 플랫폼", ["전체", "TikTok", "Instagram", "YouTube", "X"])
limit           = st.sidebar.slider("표시 개수", 10, 100, 30, 10)
search_btn      = st.sidebar.button("🔍 검색", use_container_width=True)

# ── 메인 화면 ────────────────────────────────
st.title("💄 뷰티 인플루언서 데이터")
st.caption("Supabase 실시간 연결 · 필터링")

# ── 데이터 조회 함수 ──────────────────────────
def fetch_data(table_name, platform, limit):
    try:
        query = supabase.table(table_name).select(
            'influencer_ID, platform, followers, views, likes_comments, save, share'
        )
        if platform != "전체":
            query = query.ilike('platform', f'%{platform}%')

        result = query.limit(limit).execute()
        return result.data, None

    except Exception as e:
        return None, str(e)

# ── 검색 실행 ────────────────────────────────
if search_btn or 'data' not in st.session_state:
    table_name = REGION_MAP[region_label]

    with st.spinner(f"{region_label} 데이터 불러오는 중..."):
        data, error = fetch_data(table_name, platform_filter, limit)

    if error:
        st.error(f"오류 발생: {error}")
        st.info("Supabase 연결 또는 컬럼명을 확인해주세요.")
        st.session_state['data'] = []
    elif data:
        st.session_state['data'] = data
        st.session_state['region_label'] = region_label
        st.session_state['platform'] = platform_filter
    else:
        st.warning(f"{region_label} 조건에 맞는 데이터가 없습니다.")
        st.session_state['data'] = []

# ── 결과 출력 ────────────────────────────────
if 'data' in st.session_state and st.session_state['data']:
    import pandas as pd
    data = st.session_state['data']

    # 상단 메트릭
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("검색 결과", f"{len(data)}명")
    c2.metric("지역", st.session_state.get('region_label', region_label))
    c3.metric("플랫폼", st.session_state.get('platform', platform_filter))
    c4.metric("표시 개수", f"{limit}개")

    st.markdown("---")

    # 탭 구성
    tab1, tab2 = st.tabs(["📋 테이블 뷰", "🃏 카드 뷰"])

    with tab1:
        df = pd.DataFrame(data)
        rename = {
            'influencer_ID':  'ID',
            'platform':       '플랫폼',
            'followers':      '팔로워',
            'views':          '조회수',
            'likes_comments': '좋아요·댓글',
            'save':           '저장',
            'share':          '공유',
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
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
                    st.markdown(f"❤️ 좋아요·댓글 `{inf.get('likes_comments', 'N/A')}`")
                    st.markdown(f"🔖 저장 `{inf.get('save', 'N/A')}`")
                    st.markdown(f"🔄 공유 `{inf.get('share', 'N/A')}`")

else:
    st.markdown("---")
    st.info("👈 왼쪽에서 필터 설정 후 검색 버튼을 눌러주세요.")
    st.markdown("""
    **사용 방법**
    1. 지역 선택 (미국 / UAE / 동남아)
    2. 플랫폼 선택 (선택사항)
    3. 표시 개수 설정
    4. 검색 버튼 클릭
    """)
