import streamlit as st
from datetime import datetime
import calendar

# 페이지 설정
st.set_page_config(page_title="따뜻한 추억", layout="wide")

# 세션 초기화
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "current_year" not in st.session_state:
    st.session_state.current_year = datetime.now().year
if "current_month" not in st.session_state:
    st.session_state.current_month = datetime.now().month
if "memories" not in st.session_state:
    st.session_state.memories = {}

# -----------------------------
# CSS 스타일
# -----------------------------
st.markdown("""
<style>
/* 왼쪽 미니 달력 버튼 */
button[kind="secondary"] {
    border: 1px solid #ccc !important;
    border-radius: 8px !important;
    width: 45px !important;
    height: 45px !important;
    font-size: 16px !important;
    margin: 2px !important;
}

/* 오른쪽 큰 달력 버튼 */
div[data-testid="column"] button[kind="secondary"] {
    border-radius: 10px !important;
    width: 100% !important;
    height: 110px !important;
    font-size: 18px !important;
    white-space: pre-wrap !important;
    text-align: center !important;
    margin: 3px !important;
}

/* 큰 달력 제목 */
.big-calendar-title {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 25px;
}

/* 왼쪽 컬럼 최소 너비 */
[data-testid="column"]:nth-of-type(1) {
    min-width: 230px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 왼쪽 미니 달력
# -----------------------------
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 📅 추억 달력")

    year = st.session_state.current_year
    month = st.session_state.current_month

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("◀", key="prev"):
            if month == 1:
                st.session_state.current_year -= 1
                st.session_state.current_month = 12
            else:
                st.session_state.current_month -= 1
            st.rerun()

    with c2:
        st.markdown(f"<div style='text-align:center;font-size:18px;'>{year}년 {month}월</div>", unsafe_allow_html=True)

    with c3:
        if st.button("▶", key="next"):
            if month == 12:
                st.session_state.current_year += 1
                st.session_state.current_month = 1
            else:
                st.session_state.current_month += 1
            st.rerun()

    cal = calendar.Calendar()
    days = list(cal.itermonthdates(year, month))
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day.month == month:
                if cols[i].button(str(day.day), key=f"{day}mini"):
                    st.session_state.selected_date = day
                    st.rerun()
            else:
                cols[i].markdown(" ")

    st.markdown("---")
    st.write("🌿 추후 메뉴 공간")

# -----------------------------
# 오른쪽 큰 달력 + 추억
# -----------------------------
with col2:
    year = st.session_state.current_year
    month = st.session_state.current_month
    st.markdown(f"<div class='big-calendar-title'>{year}년 {month}월</div>", unsafe_allow_html=True)

    cal = calendar.Calendar()
    days = list(cal.itermonthdates(year, month))
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    # 큰 달력 네모칸
    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day.month == month:
                day_key = day.strftime("%Y-%m-%d")
                title = st.session_state.memories.get(day_key, {}).get("title", "")
                btn_label = f"{day.day}\n\n{title}" if title else str(day.day)
                if cols[i].button(btn_label, key=f"{day}big"):
                    st.session_state.selected_date = day
                    st.rerun()
            else:
                cols[i].markdown(" ")

    st.markdown("---")

    if st.session_state.selected_date:
        date_obj = st.session_state.selected_date
        month = date_obj.month
        day = date_obj.day
        date_key = date_obj.strftime("%Y-%m-%d")

        st.markdown(f"## 💌 {month}월 {day}일의 추억")

        title = st.text_input("추억 제목", value=st.session_state.memories.get(date_key, {}).get("title", ""))
        content = st.text_area("편지 내용", value=st.session_state.memories.get(date_key, {}).get("content", ""), height=200)
        photo = st.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"])
        audio = st.file_uploader("음성 업로드", type=["mp3", "wav"])

        if st.button("추억 저장", key="save_memory"):
            st.session_state.memories[date_key] = {"title": title, "content": content}
            st.success(f"✅ {month}월 {day}일의 추억이 저장되었습니다!")
            st.rerun()
    else:
        st.markdown("<div style='font-size:22px;color:gray;text-align:center;margin-top:150px;'>날짜를 선택해주세요 🌷</div>", unsafe_allow_html=True)
