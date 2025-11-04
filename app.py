import streamlit as st
import os
import json
from datetime import datetime
import calendar

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("temp_uploads", exist_ok=True)
os.makedirs("accounts", exist_ok=True)

# -----------------------------
# 로그인 / 회원가입
# -----------------------------
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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💌 하루 추억 캘린더 로그인")
    option = st.radio("선택하세요", ["로그인", "회원가입"])
    accounts = load_accounts()

    if option == "회원가입":
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        role = st.selectbox("역할", ["보낸이", "받는이"])
        if st.button("가입"):
            if any(u["username"] == username for u in accounts["users"]):
                st.warning("이미 존재하는 아이디입니다.")
            elif not username or not password:
                st.warning("아이디와 비밀번호를 입력해주세요.")
            else:
                accounts["users"].append({"username": username, "password": password, "role": role})
                save_accounts(accounts)
                st.success("가입 완료! 로그인 해주세요.")

    else:  # 로그인
        username = st.text_input("아이디", key="login_id")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            user = next((u for u in accounts["users"] if u["username"] == username and u["password"] == password), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.experimental_rerun()
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")
else:
    # -----------------------------
    # 세션 상태
    # -----------------------------
    if "year" not in st.session_state:
        st.session_state.year = datetime.now().year
    if "month" not in st.session_state:
        st.session_state.month = datetime.now().month
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None

    year = st.session_state.year
    month = st.session_state.month
    username = st.session_state.username
    role = st.session_state.role

    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    st.title("💌 하루 추억 캘린더")

    # -----------------------------
    # 자가진단 질문 불러오기
    # -----------------------------
    question_file = f"temp_uploads/{username}_questions.json"
    if not os.path.exists(question_file):
        with open(question_file, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(question_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # -----------------------------
    # 페이지 분기: 특정 날짜 선택 여부
    # -----------------------------
    query_params = st.experimental_get_query_params()
    selected_date = query_params.get("date", [None])[0]

    if not selected_date:
        # -----------------------------
        # 달력 화면
        # -----------------------------
        left, right = st.columns([1, 3])

        # 왼쪽 미니 달력
        with left:
            st.markdown(f"### 🗓 {year}년 {month}월")
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("←", key="prev"):
                    if st.session_state.month == 1:
                        st.session_state.month = 12
                        st.session_state.year -= 1
                    else:
                        st.session_state.month -= 1
                    st.experimental_rerun()
            with c2:
                st.markdown(f"<p style='text-align:center;font-weight:bold;'>{year}년 {month}월</p>", unsafe_allow_html=True)
            with c3:
                if st.button("→", key="next"):
                    if st.session_state.month == 12:
                        st.session_state.month = 1
                        st.session_state.year += 1
                    else:
                        st.session_state.month += 1
                    st.experimental_rerun()

            cal = calendar.monthcalendar(year, month)
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].write(" ")
                    else:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if cols[i].button(str(day), key=f"left_{date_str}"):
                            st.experimental_set_query_params(date=date_str)
                            st.experimental_rerun()

        # 오른쪽 큰 달력
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
                        btn_label = f"📝 {day}" if os.path.exists(f"temp_uploads/{username}/{date_str}/letter.txt") else str(day)
                        if cols[i].button(btn_label, key=f"right_{date_str}"):
                            st.experimental_set_query_params(date=date_str)
                            st.experimental_rerun()

            st.markdown("---")
            st.markdown("🔧 자가진단 질문 및 편지 미리보기 (추후 확장)")

            # 미리보기
            for folder in sorted(os.listdir(f"temp_uploads/{username}")) if os.path.exists(f"temp_uploads/{username}") else []:
                path = f"temp_uploads/{username}/{folder}/letter.txt"
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        title = f.readline().strip()
                    if st.button(f"📅 {folder} | {title}", key=f"preview_{folder}"):
                        st.experimental_set_query_params(date=folder)
                        st.experimental_rerun()

        st.markdown("---")
        st.info("편지와 사진, 자가진단 체크는 날짜를 클릭해서 확인하세요.")

    else:
        # -----------------------------
        # 특정 날짜 편지 / 자가진단 페이지
        # -----------------------------
        date_str = selected_date
        folder = f"temp_uploads/{username}/{date_str}"
        os.makedirs(folder, exist_ok=True)
        letter_path = os.path.join(folder, "letter.txt")

        st.markdown(f"## 💌 {date_str}의 추억")
        if st.button("⬅️ 달력으로 돌아가기"):
            st.experimental_set_query_params()
            st.experimental_rerun()

        existing_letter = ""
        if os.path.exists(letter_path):
            with open(letter_path, "r", encoding="utf-8") as f:
                existing_letter = f.read()

        # 편지 작성
        with st.form("memory_form"):
            letter = st.text_area("내용", value=existing_letter, height=150)
            photo = st.file_uploader("📸 사진", type=["jpg","png","jpeg"])
            audio = st.file_uploader("🎵 음성", type=["mp3","wav"])
            submitted = st.form_submit_button("저장하기 💾")

        if submitted:
            with open(letter_path, "w", encoding="utf-8") as f:
                f.write(letter)
            if photo:
                with open(os.path.join(folder, photo.name), "wb") as f:
                    f.write(photo.getbuffer())
            if audio:
                with open(os.path.join(folder, audio.name), "wb") as f:
                    f.write(audio.getbuffer())
            st.success("🌸 저장 완료!")
            st.balloons()

        # 자가진단 체크
        if questions:
            st.markdown("### 📝 오늘 자가진단")
            answers_file = os.path.join(folder, "answers.json")
            prev_answers = {}
            if os.path.exists(answers_file):
                with open(answers_file, "r", encoding="utf-8") as f:
                    prev_answers = json.load(f)

            with st.form("self_check"):
                answers = {}
                for i, q in enumerate(questions):
                    ans = st.radio(q, ["좋음", "보통", "나쁨"], index=["좋음","보통","나쁨"].index(prev_answers.get(q,"좋음")), key=f"q_{i}")
                    answers
