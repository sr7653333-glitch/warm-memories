import streamlit as st
import os
import json
from datetime import datetime
import calendar

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("temp_uploads", exist_ok=True)
os.makedirs("accounts", exist_ok=True)

for key, default in [("logged_in", False), ("username", ""), ("role", ""),
                     ("year", datetime.now().year), ("month", datetime.now().month),
                     ("selected_date", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

def load_accounts():
    path = "accounts/accounts.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": []}

def save_accounts(data):
    path = "accounts/accounts.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

accounts = load_accounts()

if not st.session_state.logged_in:
    st.title("💌 하루 추억 캘린더 로그인")
    option = st.radio("선택하세요", ["로그인", "회원가입"])

    if option == "회원가입":
        username = st.text_input("아이디", key="signup_id")
        password = st.text_input("비밀번호", type="password", key="signup_pw")
        role = st.selectbox("역할", ["보낸이", "받는이"])
        if st.button("가입"):
            if not username or not password:
                st.warning("아이디와 비밀번호를 입력해주세요.")
            elif any(u["username"] == username for u in accounts["users"]):
                st.warning("이미 존재하는 아이디입니다.")
            else:
                accounts["users"].append({"username": username, "password": password, "role": role})
                save_accounts(accounts)
                st.success("가입 완료! 로그인해주세요.")
    else:
        username = st.text_input("아이디", key="login_id")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            user = next((u for u in accounts["users"] if u["username"] == username and u["password"] == password), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")

else:
    username = st.session_state.username
    role = st.session_state.role
    year = st.session_state.year
    month = st.session_state.month
    selected_date = st.session_state.selected_date

    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None

    st.title("💌 하루 추억 캘린더")

    left, right = st.columns([1,3])

    with left:
        st.markdown(f"### 🗓 {year}년 {month}월")
        c1, c2, c3 = st.columns([1,2,1])
        with c1:
            if st.button("←", key="prev"):
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
                st.session_state.month = month
                st.session_state.year = year
        with c2:
            st.markdown(f"<p style='text-align:center;font-weight:bold;'>{year}년 {month}월</p>", unsafe_allow_html=True)
        with c3:
            if st.button("→", key="next"):
                month += 1
                if month == 13:
                    month = 1
                    year += 1
                st.session_state.month = month
                st.session_state.year = year

        cal = calendar.monthcalendar(year, month)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write(" ")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if cols[i].button(str(day), key=f"left_{date_str}"):
                        st.session_state.selected_date = date_str

    with right:
        st.markdown(f"### 🌿 {month}월의 추억 달력")
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write(" ")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    label = f"📝 {day}" if os.path.exists(f"temp_uploads/{username}/{date_str}/letter.txt") else str(day)
                    if cols[i].button(label, key=f"right_{date_str}"):
                        st.session_state.selected_date = date_str

    if st.session_state.selected_date:
        date_str = st.session_state.selected_date
        folder = f"temp_uploads/{username}/{date_str}"
        os.makedirs(folder, exist_ok=True)
        letter_path = os.path.join(folder, "letter.txt")

        st.markdown(f"## 💌 {date_str}의 추억")
        if st.button("⬅️ 달력으로 돌아가기"):
            st.session_state.selected_date = None

        existing_letter = ""
        if os.path.exists(letter_path):
            with open(letter_path,"r",encoding="utf-8") as f:
                existing_letter = f.read()

        with st.form("memory_form"):
            letter = st.text_area("내용", value=existing_letter, height=150)
            photo = st.file_uploader("📸 사진", type=["jpg","png","jpeg"])
            audio = st.file_uploader("🎵 음성", type=["mp3","wav"])
            submitted = st.form_submit_button("저장하기 💾")

        if submitted:
            with open(letter_path,"w",encoding="utf-8") as f:
                f.write(letter)
            if photo:
                with open(os.path.join(folder,photo.name),"wb") as f:
                    f.write(photo.getbuffer())
            if audio:
                with open(os.path.join(folder,audio.name),"wb") as f:
                    f.write(audio.getbuffer())
            st.success("🌸 저장 완료!")
            st.balloons()
