import os
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="따뜻한 추억 남기기", page_icon="💌", layout="centered")

st.title("💌 하루 한 번, 따뜻한 추억 남기기")
st.markdown("가족에게 오늘의 마음을 사진, 음성, 편지로 전해보세요 ☀️")

# 임시 저장 폴더 생성
os.makedirs("temp_uploads", exist_ok=True)

# 입력 폼
with st.form("memory_form"):
    sender = st.text_input("보낸이 이름")
    letter = st.text_area("편지 내용", placeholder="오늘 있었던 따뜻한 일을 적어보세요.")
    photo = st.file_uploader("사진 업로드 (선택)", type=["jpg", "jpeg", "png"])
    audio = st.file_uploader("음성 파일 업로드 (선택)", type=["mp3", "wav"])
    submitted = st.form_submit_button("오늘의 추억 남기기")

# 제출 시 동작
if submitted:
    if not sender:
        st.warning("보낸이 이름을 입력해주세요.")
    elif not letter:
        st.warning("편지 내용을 적어주세요.")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = f"temp_uploads/{timestamp}_{sender}"
        os.makedirs(save_dir, exist_ok=True)

        with open(f"{save_dir}/letter.txt", "w", encoding="utf-8") as f:
            f.write(letter)

        if photo:
            with open(f"{save_dir}/{photo.name}", "wb") as f:
                f.write(photo.getbuffer())

        if audio:
            with open(f"{save_dir}/{audio.name}", "wb") as f:
                f.write(audio.getbuffer())

        st.success("오늘의 따뜻한 추억이 저장되었어요 💕")
        st.balloons()

# 저장된 추억 불러오기
if st.button("📜 지난 추억 보기"):
    if not os.listdir("temp_uploads"):
        st.info("아직 저장된 추억이 없어요 🌱")
    else:
        for folder in sorted(os.listdir("temp_uploads"), reverse=True):
            folder_path = os.path.join("temp_uploads", folder)
            st.subheader(f"📅 {folder.replace('_', ' ')}")
            if os.path.exists(f"{folder_path}/letter.txt"):
                with open(f"{folder_path}/letter.txt", "r", encoding="utf-8") as f:
                    st.write(f.read())
            for file in os.listdir(folder_path):
                if file.endswith((".jpg", ".jpeg", ".png")):
                    st.image(os.path.join(folder_path, file))
                if file.endswith((".mp3", ".wav")):
                    st.audio(os.path.join(folder_path, file))
            st.divider()
