import streamlit as st
import calendar
from datetime import datetime

st.set_page_config(layout="wide")

# 상태 초기화
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

# 오늘 날짜 기준
now = datetime.now()
year, month = now.year, now.month

# 왼쪽 미니 달력
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown(f"### 📅 {year}년 {month}월")
    st.markdown("<hr>", unsafe_allow_html=True)

    # 달력 이동 버튼
    prev, next = st.columns(2)
    if prev.button("◀ 이전달"):
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
    if next.button("다음달 ▶"):
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    st.session_state["current_month"] = month
    st.session_state["current_year"] = year

    # 달력 HTML
    cal = calendar.monthcalendar(year, month)
    cal_html = f"<div style='text-align:center;'><b>{year}년 {month}월</b></div>"
    cal_html += "<table style='width:100%; text-align:center; border-collapse:collapse;'>"
    cal_html += "<tr>" + "".join([f"<th>{d}</th>" for d in ["일","월","화","수","목","금","토"]]) + "</tr>"
    for week in cal:
        cal_html += "<tr>"
        for day in week:
            if day == 0:
                cal_html += "<td></td>"
            else:
                cal_html += f"<td style='padding:6px; border-radius:8px; background-color:#f2f2f2;'>{day}</td>"
        cal_html += "</tr>"
    cal_html += "</table>"
    st.markdown(cal_html, unsafe_allow_html=True)

# 오른쪽 큰 달력
with col2:
    st.markdown(
        f"<h2 style='text-align:center;'>{month}월의 추억 달력</h2>",
        unsafe_allow_html=True
    )

    cal = calendar.monthcalendar(year, month)

    st.markdown(
        """
        <style>
        div[data-testid="column"] > div {
            display: flex;
            justify-content: center;
        }
        .day-box {
            width: 100px;
            height: 100px;
            border-radius: 15px;
            background-color: #fff9e6;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
            text-align: center;
            padding-top: 20px;
            font-size: 20px;
            margin: 5px;
            transition: 0.2s;
        }
        .day-box:hover {
            background-color: #ffefd5;
            transform: scale(1.05);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Streamlit 그리드처럼 배치
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div class='day-box'></div>", unsafe_allow_html=True)
            else:
                if cols[i].button(f"{day}\n추억 제목 예시", key=f"day_{day}"):
                    st.session_state["selected_date"] = day

# 클릭된 날짜의 추억 페이지 표시
if st.session_state["selected_date"]:
    selected_day = st.session_state["selected_date"]
    st.markdown(f"<hr><h3 style='text-align:center;'>💌 {month}월 {selected_day}일의 추억</h3>", unsafe_allow_html=True)
    st.text_area("추억 내용을 남겨보세요", "")
    st.file_uploader("사진이나 파일 업로드")
    st.button("저장하기")

# URL 파라미터로 날짜 받기
query_params = st.experimental_get_query_params()
if "day" in query_params:
    selected_day = query_params["day"][0]
    st.markdown(f"<hr><h3 style='text-align:center;'>💌 {month}월 {selected_day}일의 추억</h3>", unsafe_allow_html=True)
    st.text_area("추억 내용을 남겨보세요", "")
    st.file_uploader("사진이나 파일 업로드")
    st.button("저장하기")
