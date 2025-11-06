import streamlit as st
import os
import json
from datetime import datetime
import calendar

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)

# ---------------- 기본 세션 설정 ----------------
for key, default in [
    ("logged_in", False), ("username", ""), ("role", ""),
    ("selected_date", None), ("login_cookie", None), ("theme", "기본")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- 파일 로드 및 저장 함수 ----------------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 데이터 파일 경로
ACCOUNTS_FILE = "accounts/accounts.json"
GROUPS_FILE = "accounts/groups.json"
SESSION_FILE = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"

# 데이터 불러오기
accounts = load_json(ACCOUNTS_FILE, {"users": []})
groups = load_json(GROUPS_FILE, {"groups": []})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records": []})

# ---------------- 세션 복원 ----------------
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    session = load_json(SESSION_FILE, {})
    if session:
        st.session_state.logged_in = True
        st.session_state.username = session["username"]
        st.session_state.role = session["role"]
        st.session_state.login_cookie = session

# ---------------- 로그인 / 회원가입 ----------------
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
                save_json(ACCOUNTS_FILE, accounts)
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
                st.session_state.login_cookie = {"username": username, "role": user["role"]}
                save_json(SESSION_FILE, st.session_state.login_cookie)
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")

# ---------------- 로그인 후 화면 ----------------
else:
    username = st.session_state.username
    role = st.session_state.role

    # ---------- 사이드바 ----------
    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None
        st.session_state.login_cookie = {}
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()

    menu = st.sidebar.radio("메뉴", ["그룹 관리", "그룹 편집", "달력"])

    # ---------- 테마 선택 ----------
    st.sidebar.markdown("### 🎨 달력 테마")
    st.session_state.theme = st.sidebar.selectbox("테마 선택", ["기본", "다크", "핑크", "미니멀"])

    # ---------- 받는이: 자가진단 ----------
    today = datetime.now().strftime("%Y-%m-%d")
    if role == "받는이":
        already_done = any(r["username"] == username and r["date"] == today for r in diagnosis_data["records"])
        if not already_done:
            st.info("🩺 오늘의 자가진단을 작성해주세요!")
            mood = st.slider("오늘의 기분 (1=나쁨, 5=아주 좋음)", 1, 5, 3)
            stress = st.slider("스트레스 정도 (1=없음, 5=매우 높음)", 1, 5, 3)
            sleep = st.number_input("수면 시간 (시간 단위)", 0.0, 24.0, 7.0)
            memo = st.text_area("한 줄 메모")

            if st.button("자가진단 제출"):
                diagnosis_data["records"].append({
                    "username": username,
                    "date": today,
                    "mood": mood,
                    "stress": stress,
                    "sleep": sleep,
                    "memo": memo
                })
                save_json(DIAGNOSIS_FILE, diagnosis_data)
                st.success("오늘의 자가진단이 저장되었습니다!")
                st.rerun()
        else:
            st.success("✅ 오늘은 이미 자가진단을 완료했습니다.")

    # ---------- 보낸이: 자가진단 모니터링 ----------
    if role == "보낸이" and menu == "그룹 관리":
        st.title("👀 받는이 자가진단 모니터링")

        my_groups = [g for g in groups["groups"] if username in g["members"]]
        receiver_list = []
        for g in my_groups:
            for member in g["members"]:
                if member != username:
                    receiver_list.append(member)

        if receiver_list:
            recent_records = [
                r for r in diagnosis_data["records"] if r["username"] in receiver_list
            ]
            if recent_records:
                st.dataframe(
                    [{"날짜": r["date"], "아이디": r["username"], "기분": r["mood"],
                      "스트레스": r["stress"], "수면": r["sleep"], "메모": r["memo"]}
                     for r in sorted(recent_records, key=lambda x: x["date"], reverse=True)]
                )
            else:
                st.info("아직 받은이들의 자가진단 기록이 없습니다.")
        else:
            st.warning("아직 연결된 받는이가 없습니다.")

    # ---------- 그룹 관리 ----------
    if menu == "그룹 관리" and role == "받는이":
        st.title("👨‍👩‍👧‍👦 그룹 관리")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        if my_groups:
            for g in my_groups:
                st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")
        else:
            st.info("아직 속한 그룹이 없습니다.")

    elif menu == "그룹 편집":
        st.title("✏️ 그룹 편집")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        if my_groups:
            for g in my_groups:
                st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")
                if st.button(f"그룹 나가기 ({g['group_name']})", key=f"leave_{g['group_name']}"):
                    g["members"].remove(username)
                    if len(g["members"]) == 0:
                        groups["groups"].remove(g)
                    save_json(GROUPS_FILE, groups)
                    st.success(f"'{g['group_name']}' 그룹에서 나갔습니다.")
                    st.rerun()
        else:
            st.info("아직 속한 그룹이 없습니다.")

    # ---------- 달력 ----------
    elif menu == "달력":
        st.title("🗓 하루 추억 달력")

        # 테마별 색상 스타일
        theme_colors = {
            "기본": "#f0f2f6",
            "다크": "#1e1e1e",
            "핑크": "#ffe4ec",
            "미니멀": "#ffffff"
        }
        st.markdown(
            f"""
            <style>
            .stApp {{ background-color: {theme_colors[st.session_state.theme]}; }}
            </style>
            """,
            unsafe_allow_html=True
        )

        left, right = st.columns([1, 3])
        with left:
            st.markdown("#### 📅 달력 조정")
            year = st.number_input("연도", 2000, 2100, datetime.now().year)
            month = st.number_input("월", 1, 12, datetime.now().month)

        with right:
            st.markdown(f"### {year}년 {month}월")
            cal = calendar.monthcalendar(int(year), int(month))
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].write(" ")
                    else:
                        cols[i].button(str(day), key=f"day_{year}_{month}_{day}")
