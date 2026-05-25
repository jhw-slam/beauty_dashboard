import streamlit as st
from supabase import create_client
import pandas as pd
import os

# ── 페이지 설정 ──────────────────────────────
st.set_page_config(
    page_title="Beauty Influencer Dashboard",
    page_icon="💄",
    layout="wide"
)

# ── Supabase 연결 ────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://wjvgvydywweqsdwbumxr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_client()

# ── 데이터 로딩 ──────────────────────────────
@st.cache_data(ttl=300)  # 5분 캐시
def load_table(table_name):
    try:
        res = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"{table_name} 로딩 실패: {e}")
        return pd.DataFrame()

# ── UI ───────────────────────────────────────
st.title("💄 Beauty Influencer Dashboard")
st.caption("Supabase 데이터 관리자 뷰")

tab1, tab2, tab3 = st.tabs(["🇺🇸 US", "🇦🇪 UAE", "🌏 SG/PH"])

with tab1:
    st.subheader("US 인플루언서")
    df = load_table("US_DB")
    if not df.empty:
        # 필터
        col1, col2 = st.columns(2)
        with col1:
            platforms = ["전체"] + sorted(df["platform"].dropna().unique().tolist()) if "platform" in df.columns else ["전체"]
            sel_platform = st.selectbox("플랫폼 필터", platforms, key="us_platform")
        with col2:
            if "followers" in df.columns:
                min_f, max_f = int(df["followers"].min()), int(df["followers"].max())
                sel_range = st.slider("팔로워 범위", min_f, max_f, (min_f, max_f), key="us_followers")

        # 필터 적용
        filtered = df.copy()
        if sel_platform != "전체" and "platform" in df.columns:
            filtered = filtered[filtered["platform"] == sel_platform]
        if "followers" in df.columns:
            filtered = filtered[
                (filtered["followers"] >= sel_range[0]) &
                (filtered["followers"] <= sel_range[1])
            ]

        st.metric("표시 인원", len(filtered))
        st.dataframe(filtered, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

with tab2:
    st.subheader("UAE 인플루언서")
    df = load_table("UAE_DB")
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            platforms = ["전체"] + sorted(df["platform"].dropna().unique().tolist()) if "platform" in df.columns else ["전체"]
            sel_platform = st.selectbox("플랫폼 필터", platforms, key="uae_platform")
        with col2:
            if "followers" in df.columns:
                min_f, max_f = int(df["followers"].min()), int(df["followers"].max())
                sel_range = st.slider("팔로워 범위", min_f, max_f, (min_f, max_f), key="uae_followers")

        filtered = df.copy()
        if sel_platform != "전체" and "platform" in df.columns:
            filtered = filtered[filtered["platform"] == sel_platform]
        if "followers" in df.columns:
            filtered = filtered[
                (filtered["followers"] >= sel_range[0]) &
                (filtered["followers"] <= sel_range[1])
            ]

        st.metric("표시 인원", len(filtered))
        st.dataframe(filtered, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

with tab3:
    st.subheader("SG/PH 인플루언서")
    df = load_table("my_sg_ph_DB")
    if not df.empty:
        st.metric("총 인원", len(df))
        st.dataframe(df, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")
