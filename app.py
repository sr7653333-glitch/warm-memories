import streamlit as st
import calendar
from datetime import datetime

# 페이지 레이아웃
st.set_page_config(layout="wide")

# 상태 초기화
if "current_year" not in st.session_state:
    st.session_state.current_year = datetime.now().year
if "current_month" not in st.session_state:
    st.session_state.current_month = datetime.now().month
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

year = st.session_state.current_year
month = st.session_state.current_month

# 좌우 컬럼: 왼쪽 1/4, 오른쪽 3/4
col1, col2 = st.columns([1, 3])

# -----------------------------
# 왼쪽 미니 달력
# -----------------------------
with col1:
    st.markdown(f"### 📅 {year}년 {month}월")
    prev, next = st.columns(2)
    if prev.button("◀"):
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        st.session_state.current_year = year
        st.session_state.current_month = month
        st.session_state.selected_date = None
        st.experimental_rerun()
    if next.button("▶"):
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        st.session_state.current_year = year
        st.session_state.current_month = month
        st.session_state.selected_date = None
        st.experimental_rerun()

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown(" ")
            else:
                if cols[i].button(str(day), key=f"mini_{day}"):
                    st.session_state.selected_date = day
                    st.experimental_rerun()

# -----------------------------
# 오른쪽 큰 달력
# -----------------------------
with col2:
    st.markdown(f"### {month}월의 추억 달력")
    cal = calendar.monthcalendar(year, month)

    # 그리드 스타일 CSS
    st.markdown("""
    <style>
    div[data-testid="column"] button {
        height: 120px;
        font-size: 18px;
        border-radius: 15px;
        margin: 3px;
        background-color: #fff9e6;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
    }
    div[data-testid="column"] button:hover {
        background-color: #ffefd5;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

    # 달력 버튼 배치 (7xN)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown(" ")
            else:
                if cols[i].button(str(day), key=f"big_{day}"):
                    st.session_state.selected_date = day

# -----------------------------
# 클릭한 날짜의 추억 표시
# -----------------------------
if st.session_state.selected_date:
    selected_day = st.session_state.selected_date
    st.markdown(f"## 💌 {month}월 {selected_day}일의 추억")
    st.text_input("추억 제목", key="title_input")
    st.text_area("편지 내용", key="content_input", height=200)
    st.file_uploader("사진 업로드", type=["jpg","png","jpeg"], key="photo")
    st.file_uploader("음성 업로드", type=["mp3","wav"], key="audio")
    st.button("추억 저장", key="save_memory")
