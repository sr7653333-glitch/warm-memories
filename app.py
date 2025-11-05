import streamlit as st
import os
import json

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)

for key, default in [("logged_in", False), ("username", ""), ("role", ""),
                     ("selected_date", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# 계정 로딩/저장
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

# 그룹 로딩/저장
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

groups = load_groups()

# 세션 저장/로드
SESSION_FILE = "accounts/session.json"

def save_session():
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "logged_in": st.session_state.logged_in,
            "username": st.session_state.username,
            "role": st.session_state.role
        }, f, ensure_ascii=False, indent=2)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.logged_in = data.get("logged_in", False)
            st.session_state.username = data.get("username", "")
            st.session_state.role = data.get("role", "")

load_session()

# 로그인/회원가입
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
                save_session()
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")
else:
    username = st.session_state.username
    role = st.session_state.role

    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    st.title("💌 하루 추억 캘린더")

    st.markdown("### 👨‍👩‍👧‍👦 가족 그룹 연결")
    group_name = st.text_input("그룹 이름 입력")
    add_member = st.text_input("추가할 회원 ID")
    if st.button("그룹 생성/멤버 추가"):
        # 존재하지 않는 아이디 체크
        if not any(u["username"] == add_member for u in accounts["users"]):
            st.warning("존재하지 않는 아이디입니다.")
        else:
            # 동일 멤버 그룹 체크
            member_set = set([username, add_member])
            duplicate = next((g for g in groups["groups"] if set(g["members"]) == member_set), None)
            if duplicate:
                st.warning("동일 멤버로 구성된 그룹이 이미 존재합니다.")
            else:
                groups["groups"].append({"group_name": group_name, "members": [username, add_member]})
                save_groups(groups)
                st.success(f"그룹 '{group_name}' 생성 및 {add_member} 추가 완료!")

    st.markdown("#### 내가 속한 그룹")
    my_groups = [g for g in groups["groups"] if username in g["members"]]
    if not my_groups:
        st.info("속한 그룹이 없습니다.")
    else:
        for g in my_groups:
            st.write(f"{g['group_name']} - 멤버: {', '.join(g['members'])}")
