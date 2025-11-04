import streamlit as st
import calendar
from datetime import datetime

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

# 왼쪽 미니 달력
st.markdown(f"### 📅 {year}년 {month}월")

# 이전달 / 다음달 버튼
prev, next = st.columns([1,1])
if prev.button("◀ 이전달"):
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    st.session_state.current_year = year
    st.session_state.current_month = month
    st.session_state.selected_date = None
    st.experimental_rerun()

if next.button("다음달 ▶"):
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    st.session_state.current_year = year
    st.session_state.current_month = month
    st.session_state.selected_date = None
    st.experimental_rerun()

# 달력 그리기
cal = calendar.monthcalendar(year, month)
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown(" ")
        else:
            # 숫자 폰트 줄이고, 버튼 크기 조절
            if cols[i].button(f"{day}", key=f"mini_{day}"):
                st.session_state.selected_date = day

# CSS로 버튼 스타일링
st.markdown("""
<style>
div[data-testid="column"] button {
    width: 50px;
    height: 50px;
    font-size: 14px;
    border-radius: 10px;
    margin: 2px;
}
div[data-testid="column"] button:hover {
    background-color: #ffefd5;
    transform: scale(1.1);
}
</style>
""", unsafe_allow_html=True)
st.button("추억 저장", key="save_memory")
