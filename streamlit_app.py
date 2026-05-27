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

# ── 사이드바 필터 ──────────────────────────────
st.sidebar.title("💄 KOC 필터")
st.sidebar.markdown("---")

platform_label = st.sidebar.selectbox("📱 플랫폼", ["전체", "Tiktok", "Instagram"])

st.sidebar.markdown("**❤️ 좋아요 최소**")
min_likes = st.sidebar.number_input("좋아요", min_value=0, value=0, step=10, label_visibility="collapsed")

st.sidebar.markdown("**👀 조회수 최소**")
min_views = st.sidebar.number_input("조회수", min_value=0, value=0, step=100, label_visibility="collapsed")

st.sidebar.markdown("**🔖 저장 최소**")
min_saves = st.sidebar.number_input("저장", min_value=0, value=0, step=5, label_visibility="collapsed")

st.sidebar.markdown("**정렬 기준**")
sort_col = st.sidebar.selectbox("정렬", ["views", "likes", "saves"], format_func=lambda x: {"views":"조회수","likes":"좋아요","saves":"저장"}[x])
sort_desc = st.sidebar.radio("순서", ["높은순", "낮은순"]) == "높은순"

search_btn = st.sidebar.button("🔍 검색", use_container_width=True)

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

def fetch_all_data(platform_label):
    """전체 데이터 페이지네이션으로 가져오기"""
    try:
        all_data = []
        page_size = 1000
        offset = 0

        while True:
            query = supabase.table('koc_contents_view').select('*')
            if platform_label != "전체":
                query = query.eq('platform', platform_label)
            result = query.range(offset, offset + page_size - 1).execute()

            if not result.data:
                break
            all_data.extend(result.data)
            if len(result.data) < page_size:
                break
            offset += page_size

        return all_data, None
    except Exception as e:
        return None, str(e)

# ── 검색 실행 ─────────────────────────────────
if search_btn:
    with st.spinner("전체 데이터 불러오는 중... (잠시만요)"):
        data, error = fetch_all_data(platform_label)

    if error:
        st.error(f"오류: {error}")
        st.session_state['data'] = []
    elif data and len(data) > 0:
        st.session_state['raw_data'] = data
        st.session_state['platform'] = platform_label
        st.success(f"✅ 총 {len(data)}개 로드 완료!")
    else:
        st.warning("데이터가 없습니다.")
        st.session_state['raw_data'] = []

# ── 결과 출력 ─────────────────────────────────
if 'raw_data' in st.session_state and st.session_state['raw_data']:
    raw = st.session_state['raw_data']
    df = pd.DataFrame(raw)

    # 숫자 변환
    for col in ['likes','views','saves']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # 필터 적용
    if min_likes > 0:
        df = df[df['likes'] >= min_likes]
    if min_views > 0:
        df = df[df['views'] >= min_views]
    if min_saves > 0:
        df = df[df['saves'] >= min_saves]

    # 정렬
    if sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=not sort_desc)

    df = df.reset_index(drop=True)

    # 상단 메트릭
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("필터 결과", f"{len(df)}개")
    c2.metric("전체 로드", f"{len(raw)}개")
    c3.metric("플랫폼", st.session_state.get('platform', '전체'))
    c4.metric("정렬", f"{'↓' if sort_desc else '↑'} {RENAME_MAP.get(sort_col, sort_col)}")

    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 테이블 뷰", "🃏 카드 뷰"])

    with tab1:
        # 액션 컬럼 추가
        df_display = df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns}).copy()

        # 승인/거절/재생 컬럼
        df_display['액션'] = '✅ ❌ ▶️'

        # TikTok URL 클릭 가능하게
        st.dataframe(
            df_display,
            use_container_width=True,
            height=600,
            column_config={
                "TikTok URL": st.column_config.LinkColumn("🎵 TikTok", display_text="▶️ 보기"),
                "Instagram URL": st.column_config.LinkColumn("📸 Instagram", display_text="▶️ 보기"),
                "액션": st.column_config.TextColumn("액션", width="small"),
            }
        )

        # 승인/거절 버튼 (선택된 인플루언서용)
        st.markdown("---")
        st.markdown("**개별 액션** — ID 입력 후 처리")
        col_a, col_b, col_c = st.columns(3)
        selected_id = st.text_input("influencer_ID 입력", placeholder="예: fanny.gla")
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("✅ 승인", use_container_width=True):
                if selected_id:
                    if 'approved' not in st.session_state:
                        st.session_state['approved'] = []
                    st.session_state['approved'].append(selected_id)
                    st.success(f"✅ {selected_id} 승인됨!")
        with btn_col2:
            if st.button("❌ 거절", use_container_width=True):
                if selected_id:
                    if 'rejected' not in st.session_state:
                        st.session_state['rejected'] = []
                    st.session_state['rejected'].append(selected_id)
                    st.error(f"❌ {selected_id} 거절됨!")
        with btn_col3:
            if st.button("📋 목록 보기", use_container_width=True):
                approved = st.session_state.get('approved', [])
                rejected = st.session_state.get('rejected', [])
                st.write(f"✅ 승인: {approved}")
                st.write(f"❌ 거절: {rejected}")

    with tab2:
        cols = st.columns(3)
        for i, row in enumerate(df.head(100).to_dict('records')):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**@{row.get('influencer_ID', 'N/A')}**")
                    st.caption(f"📱 {row.get('platform', 'N/A')}")
                    st.markdown(f"👀 조회수 `{row.get('views', 'N/A')}`")
                    st.markdown(f"❤️ 좋아요 `{row.get('likes', 'N/A')}`")
                    st.markdown(f"🔖 저장 `{row.get('saves', 'N/A')}`")
                    tt = row.get('VideoUrl_TT', '')
                    ig = row.get('VideoUrl_IG', '')
                    if tt:
                        st.markdown(f"[▶️ TikTok 보기]({tt})")
                    if ig:
                        st.markdown(f"[▶️ Instagram 보기]({ig})")

else:
    st.markdown("---")
    st.info("👈 왼쪽 필터 설정 후 검색 버튼을 눌러주세요.")
    st.markdown("""
    **사용 방법**
    1. 플랫폼 선택
    2. 좋아요 / 조회수 / 저장 최솟값 설정
    3. 정렬 기준 선택
    4. 검색 버튼 클릭
    """)
