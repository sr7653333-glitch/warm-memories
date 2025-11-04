import os
from datetime import datetime
import streamlit as st
import calendar

# 🌿 기본 설정
st.set_page_config(page_title="하루 추억 캘린더", page_icon="📅", layout="centered")
st.title("📅 하루 한 번, 따뜻한 추억 남기기")
st.markdown("#### 날짜를 눌러 오늘의 추억을 남기거나, 그날의 추억을 다시 만나보세요 🌿")

# 📁 저장 폴더 생성
os.makedirs("temp_uploads", exist_ok=True)

# 📆 달력 표시
year = datetime.now().year
month = datetime.now().month
cal = calendar.Calendar()

st.markdown("### 🗓️ 이번 달")
cols = st.columns(7)
days = ["월", "화", "수", "목", "금", "토", "일"]
for i, d in enumerate(days):
    cols[i].markdown(f"**{d}**")

month_days = cal.monthdayscalendar(year, month)
clicked_date = st.session_state.get("clicked_date", None)

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
        else:
            date_str = f"{year}-{month:02d}-{day:02d}"
            folder_exists = any(date_str in folder for folder in os.listdir("temp_uploads"))
            btn_label = f"🌸 {day}" if folder_exists else str(day)
            if cols[i].button(btn_label, key=date_str):
                st.session_state.clicked_date = date_str
                clicked_date = date_str

st.divider()

# 📖 날짜 선택 후 추억 남기기 / 보기
if clicked_date:
    st.markdown(f"## 📆 {clicked_date}의 추억")
    folder = f"temp_uploads/{clicked_date}"
    os.makedirs(folder, exist_ok=True)

    # 이미 저장된 추억 불러오기
    letter_path = os.path.join(folder, "letter.txt")
    existing_letter = ""
    if os.path.exists(letter_path):
        with open(letter_path, "r", encoding="utf-8") as f:
            existing_letter = f.read()

    st.markdown("### ✉️ 추억 남기기")

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
            st.success("🌸 추억이 저장되었어요! 어르신이 다시 보실 수 있습니다.")
            st.balloons()

    # 저장된 추억 보기
    st.markdown("### 💞 그날의 추억 보기")
    if os.path.exists(letter_path):
        with open(letter_path, "r", encoding="utf-8") as f:
            st.markdown(f"<div style='font-size:20px; background-color:#fff5f0; padding:15px; border-radius:12px;'>{f.read()}</div>", unsafe_allow_html=True)
    for file in os.listdir(folder):
        if file.endswith((".jpg", ".jpeg", ".png")):
            st.image(os.path.join(folder, file), caption="📸 가족 사진", use_container_width=True)
        if file.endswith((".mp3", ".wav")):
            st.audio(os.path.join(folder, file))
