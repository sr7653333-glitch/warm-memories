import streamlit as st
from datetime import datetime, timedelta
import calendar

# 페이지 설정
st.set_page_config(page_title="따뜻한 추억", layout="wide")

# -----------------------------
# 세션 상태 초기화
# -----------------------------
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "current_year" not in st.session_state:
    st.session_state.current_year = datetime.now().year
if "current_month" not in st.session_state:
    st.session_state.current_month = datetime.now().month

# -----------------------------
# 왼쪽: 달력
# -----------------------------
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 📅 추억 달력")

    # 현재 월/연도 표시
    year = st.session_state.current_year
    month = st.session_state.current_month

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        if st.button("◀"):
            if month == 1:
                st.session_state.current_year -= 1
                st.session_state.current_month = 12
            else:
                st.session_state.current_month -= 1
            st.rerun()

    with col_b:
        st.markdown(f"<div style='text-align:center;font-size:20px;'>{year}년 {month}월</div>", unsafe_allow_html=True)

    with col_c:
        if st.button("▶"):
            if month == 12:
                st.session_state.current_year += 1
                st.session_state.current_month = 1
            else:
                st.session_state.current_month += 1
            st.rerun()

    # 달력 렌더링
    cal = calendar.Calendar()
    days = list(cal.itermonthdates(year, month))
    weeks = [days[i:i+7] for i in range(0, len(days), 7)]

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day.month == month:
                if cols[i].button(str(day.day), key=f"{day}"):
                    st.session_state.selected_date = day
                    st.rerun()
            else:
                cols[i].markdown(" ")

    st.markdown("---")
    st.markdown("이 아래는 추후 메뉴 공간입니다 ✨")

# -----------------------------
# 오른쪽: 선택한 날짜의 추억
# -----------------------------
with col2:
    st.markdown("## 💖 오늘의 기록")

    if st.session_state.selected_date:
        date_obj = st.session_state.selected_date
        month = date_obj.month
        day = date_obj.day

        st.markdown(f"## 💌 {month}월 {day}일의 추억")

        # 제목 입력
        title = st.text_input("추억 제목을 입력하세요")

        # 편지 내용
        content = st.text_area("편지를 작성하세요", height=200)

        # 파일 업로드
        photo = st.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"])
        audio = st.file_uploader("음성 파일 업로드", type=["mp3", "wav"])

        if st.button("추억 저장"):
            st.success(f"✅ {month}월 {day}일의 추억이 저장되었습니다!")
    else:
        st.markdown("<div style='font-size:22px;color:gray;text-align:center;margin-top:150px;'>날짜를 선택해주세요 🌷</div>", unsafe_allow_html=True)
