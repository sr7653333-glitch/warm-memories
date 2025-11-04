import streamlit as st
import calendar
from datetime import datetime

st.set_page_config(layout="wide")

# 상태 초기화
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

now = datetime.now()
year, month = now.year, now.month

# 📅 왼쪽 미니 달력
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

    cal = calendar.monthcalendar(year, month)
    mini_html = f"<div style='text-align:center;'><b>{year}년 {month}월</b></div>"
    mini_html += "<table style='width:100%; text-align:center; border-collapse:collapse;'>"
    mini_html += "<tr>" + "".join([f"<th>{d}</th>" for d in ["일","월","화","수","목","금","토"]]) + "</tr>"
    for week in cal:
        mini_html += "<tr>"
        for day in week:
            if day == 0:
                mini_html += "<td></td>"
            else:
                mini_html += f"<td style='padding:5px; border-radius:6px; background-color:#f2f2f2;'>{day}</td>"
        mini_html += "</tr>"
    mini_html += "</table>"
    st.markdown(mini_html, unsafe_allow_html=True)

# 🌸 오른쪽 큰 달력
with col2:
    st.markdown(
        f"<h2 style='text-align:center; color:#444;'>{month}월의 추억 달력</h2>",
        unsafe_allow_html=True
    )

    cal = calendar.monthcalendar(year, month)

    # CSS 적용 (예쁜 달력 모양)
    st.markdown(
        """
        <style>
        .calendar {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 15px;
            margin-top: 30px;
        }
        .day-tile {
            background: linear-gradient(135deg, #fff9e6 0%, #fffef5 100%);
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            text-align: center;
            padding-top: 25px;
            font-size: 20px;
            font-weight: 600;
            height: 110px;
            transition: 0.2s ease;
            cursor: pointer;
        }
        .day-tile:hover {
            transform: scale(1.05);
            background-color: #ffefd5;
        }
        .empty {
            background: transparent;
            box-shadow: none;
            cursor: default;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 달력 레이아웃
    st.markdown("<div class='calendar'>", unsafe_allow_html=True)
    for week in cal:
        for day in week:
            if day == 0:
                st.markdown("<div class='day-tile empty'></div>", unsafe_allow_html=True)
            else:
                if st.button(f"{day}", key=f"day_{day}"):
                    st.session_state["selected_date"] = day
    st.markdown("</div>", unsafe_allow_html=True)

# 💌 클릭한 날짜의 추억 화면
if st.session_state["selected_date"]:
    d = st.session_state["selected_date"]
    st.markdown(
        f"<hr><h3 style='text-align:center;'>💌 {month}월 {d}일의 추억</h3>",
        unsafe_allow_html=True
    )
    st.text_area("오늘의 추억을 남겨보세요 ✏️", "")
    st.file_uploader("사진이나 파일 업로드")
    st.button("저장하기 💾")
