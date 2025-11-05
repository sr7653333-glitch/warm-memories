import streamlit as st
import os
import json
from datetime import datetime
import calendar

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)
os.makedirs("temp_uploads", exist_ok=True)

# ------------------ 세션 초기값 ------------------
for key, default in [("logged_in", False), ("username", ""), ("role", ""),
                     ("selected_date", None), ("login_cookie", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

SESSION_FILE = "accounts/sessions.json"

# ------------------ 계정 로딩/저장 ------------------
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

# ------------------ 그룹 로딩/저장 ------------------
def load_groups():
    path = "accounts/groups.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"groups": []}

def save_groups(data):
    path = "accounts/groups.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

accounts = load_accounts()
groups = load_groups()

# ------------------ 세션 파일 기반 새로고침 유지 ------------------
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        session = json.load(f)
        st.session_state.logged_in = True
        st.session_state.username = session["username"]
        st.session_state.role = session["role"]
        st.session_state.login_cookie = {"username": session["username"], "role": session["role"]}

# ------------------ 로그인/회원가입 ------------------
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
                st.session_state.login_cookie = {"username": username, "role": user["role"]}
                # 세션 파일 저장
                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(st.session_state.login_cookie, f)
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")

# ------------------ 로그인 후 화면 ------------------
else:
    username = st.session_state.username
    role = st.session_state.role

    # 사이드바: 계정정보 + 로그아웃 + 메뉴
    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None
        st.session_state.login_cookie = {}
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    menu = st.sidebar.radio("메뉴", ["그룹 관리", "그룹 편집", "달력"])

    # ------------------ 그룹 관리 ------------------
    if menu == "그룹 관리":
        st.title("👨‍👩‍👧‍👦 그룹 관리")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        if my_groups:
            for g in my_groups:
                st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")
        else:
            st.info("아직 속한 그룹이 없습니다.")

        st.markdown("### ➕ 새 그룹 생성")
        group_name = st.text_input("그룹 이름 입력", key="new_group")
        add_member = st.text_input("추가할 멤버 ID", key="new_member")
        if st.button("그룹 생성/멤버 추가"):
            if not any(u["username"] == add_member for u in accounts["users"]):
                st.error(f"'{add_member}' 아이디는 존재하지 않습니다.")
            else:
                members_set = set([username, add_member])
                exists = any(set(g["members"]) == members_set for g in groups["groups"])
                if exists:
                    st.warning("이미 동일한 멤버로 구성된 그룹이 존재합니다.")
                else:
                    groups["groups"].append({"group_name": group_name, "members": [username, add_member]})
                    save_groups(groups)
                    st.success(f"새 그룹 '{group_name}' 생성 완료!")

    # ------------------ 그룹 편집 ------------------
    elif menu == "그룹 편집":
        st.title("✏️ 그룹 편집")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        if my_groups:
            for g in my_groups:
                st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")

                # 그룹 나가기
                if st.button(f"그룹 나가기 ({g['group_name']})", key=f"leave_{g['group_name']}"):
                    g["members"].remove(username)
                    if len(g["members"]) == 0:
                        groups["groups"].remove(g)
                    save_groups(groups)
                    st.success(f"'{g['group_name']}' 그룹에서 나갔습니다.")

                # 멤버 추가
                new_member = st.text_input(f"{g['group_name']}에 추가할 멤버 ID", key=f"add_{g['group_name']}")
                if st.button(f"멤버 추가 ({g['group_name']})", key=f"add_btn_{g['group_name']}"):
                    if not any(u["username"] == new_member for u in accounts["users"]):
                        st.error(f"'{new_member}' 아이디는 존재하지 않습니다.")
                    elif new_member in g["members"]:
                        st.warning(f"{new_member}님은 이미 그룹에 속해있습니다.")
                    else:
                        g["members"].append(new_member)
                        save_groups(groups)
                        st.success(f"{new_member}님을 '{g['group_name']}' 그룹에 추가했습니다.")
        else:
            st.info("아직 속한 그룹이 없습니다.")

    # ------------------ 달력 ------------------
    elif menu == "달력":
        st.title("🗓 하루 추억 달력")
        year, month = datetime.now().year, datetime.now().month
        cal = calendar.monthcalendar(year, month)

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write(" ")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    label = f"📝 {day}" if os.path.exists(f"temp_uploads/{username}/{date_str}/letter.txt") else str(day)
                    if cols[i].button(label, key=f"day_{day}"):
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
