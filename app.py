import os
import streamlit as st
import calendar
from datetime import datetime

st.set_page_config(page_title="하루 추억 캘린더", page_icon="📅", layout="wide")
os.makedirs("temp_uploads", exist_ok=True)

# 세션 초기값
if "year" not in st.session_state:
    st.session_state.year = datetime.now().year
if "month" not in st.session_state:
    st.session_state.month = datetime.now().month

# 날짜 선택 상태
query_params = st.query_params
selected_date = query_params.get("date", [None])[0]

# 달력 렌더링 함수
def render_calendar(year, month, small=False):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    day_labels = ["월", "화", "수", "목", "금", "토", "일"]

    if small:
        st.markdown(f"##### {year}년 {month}월")
    else:
        st.markdown(f"### 📅 {year}년 {month}월")

    cols = st.columns(7)
    for i, d in enumerate(day_labels):
        cols[i].markdown(f"**{d}**")

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                letter_path = f"temp_uploads/{date_str}/letter.txt"
                has_memory = os.path.exists(letter_path)
                btn_label = f"📝 {day}" if has_memory else str(day)
                btn_style = "color:#d97706;" if has_memory else ""
                if cols[i].button(btn_label, key=f"{small}_{date_str}"):
                    st.query_params["date"] = date_str
                    st.rerun()

# 페이지 분기
if not selected_date:
    left, right = st.columns([1, 3])

    # ---------------- 왼쪽 작은 달력 ----------------
    with left:
        st.markdown("### 🗓 빠른 달력")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("←", key="left_prev"):
                st.session_state.month -= 1
                if st.session_state.month == 0:
                    st.session_state.month = 12
                    st.session_state.year -= 1
        with c2:
            st.markdown(
                f"<p style='text-align:center;font-weight:bold;'>{st.session_state.year}년 {st.session_state.month}월</p>",
                unsafe_allow_html=True,
            )
        with c3:
            if st.button("→", key="left_next"):
                st.session_state.month += 1
                if st.session_state.month == 13:
                    st.session_state.month = 1
                    st.session_state.year += 1
        render_calendar(st.session_state.year, st.session_state.month, small=True)
        st.markdown("---")
        st.markdown("🔧 **이 공간은 추후 업데이트 예정입니다.**")

    # ---------------- 오른쪽 메인 ----------------
    with right:
        st.markdown(f"## 🌿 {st.session_state.month}월의 추억 달력")
        render_calendar(st.session_state.year, st.session_state.month)

        st.markdown("### 📖 이번 달의 추억 미리보기")

        memories = []
        for folder in sorted(os.listdir("temp_uploads")):
            if folder.startswith(f"{st.session_state.year}-{st.session_state.month:02d}"):
                letter_path = os.path.join("temp_uploads", folder, "letter.txt")
                if os.path.exists(letter_path):
                    with open(letter_path, "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()
                    title = first_line if first_line else "제목 없는 추억"
                    memories.append((folder, title))

        if not memories:
            st.info("이 달엔 아직 추억이 없어요 💌")
        else:
            for date_str, title in memories:
                if st.button(f"📅 {date_str} | {title}", key=f"preview_{date_str}"):
                    st.query_params["date"] = date_str
                    st.rerun()

        st.divider()
        st.markdown("⬇️ 아래는 추후 확장 공간입니다 (사진 요약, 명언, 가족 메시지 등)")

# ---------------- 특정 날짜 페이지 ----------------
else:
    date_str = selected_date
    folder = f"temp_uploads/{date_str}"
    os.makedirs(folder, exist_ok=True)
    letter_path = os.path.join(folder, "letter.txt")

    st.markdown(f"## 💌 {date_str}의 추억")
    if st.button("⬅️ 달력으로 돌아가기"):
        st.query_params.clear()
        st.rerun()

    existing_letter = ""
    if os.path.exists(letter_path):
        with open(letter_path, "r", encoding="utf-8") as f:
            existing_letter = f.read()

    with st.form("memory_form"):
        sender = st.text_input("보낸이", placeholder="예: 손주 민수")
        letter = st.text_area("내용", value=existing_letter, height=150)
        photo = st.file_uploader("📸 사진 (선택)", type=["jpg", "jpeg", "png"])
        audio = st.file_uploader("🎵 음성 (선택)", type=["mp3", "wav"])
        submitted = st.form_submit_button("저장하기 💾")

    if submitted:
        if not sender:
            st.warning("보낸이를 입력해주세요.")
        elif not letter:
            st.warning("내용을 적어주세요.")
        else:
            with open(letter_path, "w", encoding="utf-8") as f:
                f.write(f"{sender}의 편지\n\n{letter}")
            if photo:
                with open(os.path.join(folder, photo.name), "wb") as f:
                    f.write(photo.getbuffer())
            if audio:
                with open(os.path.join(folder, audio.name), "wb") as f:
                    f.write(audio.getbuffer())
            st.success("🌸 저장 완료!")
            st.balloons()

    if os.path.exists(letter_path):
        st.markdown("### ✨ 편지 내용")
        with open(letter_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<div style='padding:15px; background-color:#fff8f2; border-radius:12px;'>{f.read()}</div>",
                unsafe_allow_html=True,
            )

        for file in os.listdir(folder):
            if file.endswith((".jpg", ".jpeg", ".png")):
                st.image(os.path.join(folder, file), caption="📸 사진", use_container_width=True)
            elif file.endswith((".mp3", ".wav")):
                st.audio(os.path.join(folder, file))
