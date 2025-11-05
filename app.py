import streamlit as st
import os
import json
from datetime import datetime
import calendar

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("temp_uploads", exist_ok=True)
os.makedirs("accounts", exist_ok=True)

# 세션 초기화
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

def load_checkup(username):
    folder = f"temp_uploads/{username}/checkups"
    os.makedirs(folder, exist_ok=True)
    return folder

def save_checkup(username, date_str, data):
    folder = load_checkup(username)
    with open(os.path.join(folder,f"{date_str}.json"),"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def load_checkup_data(username, date_str):
    folder = load_checkup(username)
    path = os.path.join(folder,f"{date_str}.json")
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)
    return None

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

    if role == "receiver":
        # ----------------- 받는이 출석체크 -----------------
        today_str = datetime.now().strftime("%Y-%m-%d")
        checkup = load_checkup_data(username,today_str)
        if not checkup:
            st.markdown("### 📝 오늘의 자가진단")
            mood = st.radio("기분을 선택하세요", ["😄 좋음","😐 보통","😔 안좋음"], horizontal=True)
            scores = []
            questions = [f"건강 상태 {i}" for i in range(1,6)]
            for q in questions:
                scores.append(st.slider(q,1,3,2))
            submitted = st.button("체크 완료")
            if submitted:
                save_checkup(username, today_str, {"mood": mood, "scores": scores})
                st.success("오늘의 자가진단 완료!")
        # ----------------- 달력 표시 -----------------
        st.markdown("### 📅 자가진단 달력")
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day==0:
                    cols[i].write(" ")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    data = load_checkup_data(username,date_str)
                    label = str(day)
                    color = "white"
                    if data:
                        avg = sum(data["scores"])/len(data["scores"])
                        if avg>=2.5:
                            color="#a2fca2"
                        elif avg>=1.5:
                            color="#fffaa2"
                        else:
                            color="#ffb3b3"
                        mood_icon = data.get("mood","")
                        label = f"{day} {mood_icon}"
                        cols[i].markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px;text-align:center;'>{label}</div>",unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px;text-align:center;'>{label}</div>",unsafe_allow_html=True)
    else:
        # ----------------- 보내는이 조회 -----------------
        st.markdown("### 📅 받는이 자가진단 확인")
        receivers = [u["username"] for u in accounts["users"] if u["role"]=="receiver"]
        selected_receiver = st.selectbox("조회할 받는이 선택", receivers)
        if selected_receiver:
            cal = calendar.monthcalendar(year, month)
            st.markdown(f"### {selected_receiver}님 {month}월 자가진단 달력")
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day==0:
                        cols[i].write(" ")
                    else:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        data = load_checkup_data(selected_receiver,date_str)
                        label = str(day)
                        color="white"
                        if data:
                            avg = sum(data["scores"])/len(data["scores"])
                            if avg>=2.5:
                                color="#a2fca2"
                            elif avg>=1.5:
                                color="#fffaa2"
                            else:
                                color="#ffb3b3"
                            mood_icon = data.get("mood","")
                            label = f"{day} {mood_icon}"
                            cols[i].markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px;text-align:center;'>{label}</div>",unsafe_allow_html=True)
                        else:
                            cols[i].markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px;text-align:center;'>{label}</div>",unsafe_allow_html=True)
