import streamlit as st
import os
import json
from datetime import datetime
import calendar

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")

os.makedirs("temp_uploads", exist_ok=True)
os.makedirs("accounts", exist_ok=True)
os.makedirs("groups", exist_ok=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "year" not in st.session_state:
    st.session_state.year = datetime.now().year
if "month" not in st.session_state:
    st.session_state.month = datetime.now().month

ACCOUNTS_FILE = "accounts/accounts.json"
GROUPS_FILE = "groups/groups.json"

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {"users":[]}

def save_accounts(data):
    with open(ACCOUNTS_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {"groups":[]}

def save_groups(data):
    with open(GROUPS_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

def show_login():
    st.header("로그인 / 가입")
    tab = st.radio("선택", ["로그인","가입"], index=0)
    accounts = load_accounts()

    if tab == "로그인":
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            success = False
            for user in accounts["users"]:
                if user["username"]==username and user["password"]==password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user["role"]
                    st.success("로그인 성공!")
                    success = True
                    break
            if not success:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")
    else:
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        role = st.selectbox("역할 선택", ["receiver","sender"])
        if st.button("가입"):
            if username=="" or password=="":
                st.warning("아이디와 비밀번호를 입력해주세요.")
            elif any(u["username"]==username for u in accounts["users"]):
                st.warning("이미 존재하는 아이디입니다.")
            else:
                accounts["users"].append({"username":username,"password":password,"role":role})
                save_accounts(accounts)
                st.success("가입 완료! 로그인 해주세요.")

def receiver_check(username):
    st.header(f"{username}님 출석체크 / 자가진단")
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder = f"temp_uploads/{username}/{date_str}"
    os.makedirs(folder, exist_ok=True)
    answers_file = os.path.join(folder,"answers.json")

    mood = st.selectbox("오늘 기분은?", ["😄 좋음","🙂 괜찮음","😐 보통","😞 안좋음","😢 매우 안좋음"])
    health = [st.radio(f"건강 상태 {i}", [1,2,3], index=1, horizontal=True) for i in range(1,6)]

    q_file = f"temp_uploads/{username}/questions.json"
    extra_answers = {}
    if os.path.exists(q_file):
        with open(q_file,"r",encoding="utf-8") as f:
            questions = json.load(f)
        for q in questions.get("questions",[]):
            extra_answers[q] = st.radio(q,[1,2,3], index=1, horizontal=True)

    if st.button("저장하기"):
        data = {"mood":mood,"health":health,"extra_answers":extra_answers}
        with open(answers_file,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
        st.success("저장 완료!")

def render_calendar(year, month, username=None, receiver=False):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    days = ["월","화","수","목","금","토","일"]
    cols = st.columns(7)
    for i,d in enumerate(days):
        cols[i].markdown(f"**{d}**")
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day==0:
                cols[i].write("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                color_style = ""
                emoji = ""
                if username and receiver:
                    folder = f"temp_uploads/{username}/{date_str}"
                    ans_path = os.path.join(folder,"answers.json")
                    if os.path.exists(ans_path):
                        with open(ans_path,"r",encoding="utf-8") as f:
                            data = json.load(f)
                            avg_health = sum(data["health"])/len(data["health"])
                            if avg_health>=2.5:
                                color_style="background-color:#ff9999;"
                            elif avg_health>=1.5:
                                color_style="background-color:#ffff99;"
                            else:
                                color_style="background-color:#99ff99;"
                            emoji = data.get("mood","")
                if color_style:
                    st.markdown(f"<div style='{color_style} padding:5px; border-radius:5px; text-align:center;'>{emoji} {day}</div>", unsafe_allow_html=True)
                else:
                    st.button(f"{emoji} {day}", key=f"{username}_{date_str}")

def sender_dashboard(username):
    st.header(f"{username}님 가족 자가진단 관리")
    groups_data = load_groups()
    my_groups = [g for g in groups_data["groups"] if username in g["members"]]
    for g in my_groups:
        st.subheader(f"가족 그룹: {g['name']}")
        for member in g["members"]:
            st.markdown(f"### {member}님 달력")
            render_calendar(datetime.now().year, datetime.now().month, member, receiver=True)
            st.markdown("---")
        st.subheader("추가 질문 작성")
        new_q = st.text_input("질문 추가", key=f"q_{g['name']}")
        if new_q.strip() != "":
            if st.button("추가", key=f"add_q_{g['name']}"):
                for member in g["members"]:
                    q_file = f"temp_uploads/{member}/questions.json"
                    questions = {"questions":[]}
                    if os.path.exists(q_file):
                        with open(q_file,"r",encoding="utf-8") as f:
                            questions = json.load(f)
                    if new_q not in questions["questions"]:
                        questions["questions"].append(new_q)
                        with open(q_file,"w",encoding="utf-8") as f:
                            json.dump(questions,f,ensure_ascii=False,indent=2)
                st.success("추가 완료!")

if st.session_state.logged_in:
    if st.session_state.role=="receiver":
        receiver_check(st.session_state.username)
    elif st.session_state.role=="sender":
        sender_dashboard(st.session_state.username)
else:
    show_login()
