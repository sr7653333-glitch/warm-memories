import os
import streamlit as st
import calendar
from datetime import datetime

# 기본 설정
st.set_page_config(page_title="하루 추억 캘린더", page_icon="📅", layout="wide")

# 데이터 폴더
os.makedirs("temp_uploads", exist_ok=True)

# URL 파라미터
query_params = st.query_params
selected_date = query_params.get("date", [None])[0]

# 세션 초기화
if "year" not in st.session_state:
    st.session_state.year = datetime.now().year
if "month" not in st.session_state:
    st.session_state.month = datetime.now().month

# 함수: 달력 렌더링
def render_calendar(year, month):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    st.markdown(f"### {year}년 {month}월")
    days = ["월", "화", "수", "목", "금", "토", "일"]
    cols = st.columns(7)
    for i, d in enumerate(days):
        cols[i].markdown(f"**{d}**")

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write(" ")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                letter_path = f"temp_uploads/{date_str}/letter.txt"
                has_memory = os.path.exists(letter_path)
                if has_memory:
                    button_label = f"📝 {day}"
                    btn_style = "background-color:#fef3c7;"
                else:
                    button_label = str(day)
                    btn_style = ""
                if cols[i].button(button_label, key=date_str):
                    st.query_params["date"] = date_str
                    st.rerun()

# -----------------------------
# 달력 + 추억 목록 페이지
# -----------------------------
if not selected_date:
    left, right = st.columns([1, 3])

    # 왼쪽: 달력
    with left:
        st.markdown("## 📅 달력")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("←"):
                st.session_state.month -= 1
                if st.session_state.month == 0:
                    st.session_state.month = 12
                    st.session_state.year -= 1
        with col2:
            st.markdown(
                f"<h3 style='text-align:center;'>{st.session_state.year}년 {st.session_state.month}월</h3>",
                unsafe_allow_html=True,
            )
        with col3:
            if st.button("→"):
                st.session_state.month += 1
                if st.session_state.month == 13:
                    st.session_state.month = 1
                    st.session_state.year += 1

        render_calendar(st.session_state.year, st.session_state.month)

    # 오른쪽: 추억 목록
    with right:
        st.markdown(f"# 🌿 {st.session_state.month}월의 추억")
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
            st.info("아직 이 달의 추억이 없어요 💌")
        else:
            for date_str, title in memories:
                if st.button(f"{date_str} — {title}", key=f"btn_{date_str}"):
                    st.query_params["date"] = date_str
                    st.rerun()

# -----------------------------
# 특정 날짜 추억 보기 페이지
# -----------------------------
else:
    date_str = selected_date
    folder = f"temp_uploads/{date_str}"
    os.makedirs(folder, exist_ok=True)
    letter_path = os.path.join(folder, "letter.txt")

    st.markdown(f"## 📆 {date_str}의 추억")
    if st.button("📅 달력으로 돌아가기"):
        st.query_params.clear()
        st.rerun()

    existing_letter = ""
    if os.path.exists(letter_path):
        with open(letter_path, "r", encoding="utf-8") as f:
            existing_letter = f.read()

    with st.form("memory_form"):
        sender = st.text_input("보낸이 이름", placeholder="예: 손주 민수")
        letter = st.text_area("편지 내용", value=existing_letter, height=150)
        photo = st.file_uploader("📸 사진 업로드 (선택)", type=["jpg", "jpeg", "png"])
        audio = st.file_uploader("🎵 음성 파일 업로드 (선택)", type=["mp3", "wav"])
        submitted = st.form_submit_button("저장하기 💌")

    if submitted:
        if not sender:
            st.warning("보낸이 이름을 입력해주세요.")
        elif not letter:
            st.warning("편지 내용을 적어주세요.")
        else:
            with open(letter_path, "w", encoding="utf-8") as f:
                f.write(f"{sender}의 편지\n\n{letter}")
            if photo:
                with open(os.path.join(folder, photo.name), "wb") as f:
                    f.write(photo.getbuffer())
            if audio:
                with open(os.path.join(folder, audio.name), "wb") as f:
                    f.write(audio.getbuffer())
            st.success("🌼 추억이 저장되었어요!")
            st.balloons()

    st.divider()
    st.markdown("### 💞 그날의 추억 보기")
    if os.path.exists(letter_path):
        with open(letter_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<div style='font-size:20px; background-color:#fff5f0; padding:15px; border-radius:12px;'>{f.read()}</div>",
                unsafe_allow_html=True,
            )
    for file in os.listdir(folder):
        if file.endswith((".jpg", ".jpeg", ".png")):
            st.image(os.path.join(folder, file), caption="📸 가족 사진", use_container_width=True)
        if file.endswith((".mp3", ".wav")):
            st.audio(os.path.join(folder, file))
