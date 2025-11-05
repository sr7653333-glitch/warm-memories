import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)

for key, default in [("logged_in", False), ("username", ""), ("role", ""), ("selected_date", None)]:
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

    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None

    st.title("💌 하루 추억 캘린더")

    # ------------------ 그룹 연결 UI ------------------
    st.markdown("### 👨‍👩‍👧‍👦 가족 그룹 연결")
    group_name = st.text_input("그룹 이름 입력")
    add_member = st.text_input("추가할 멤버 ID")

    if st.button("그룹 생성 / 멤버 추가"):
        # 그룹 이름이 이미 존재하는지 확인
        grp = next((g for g in groups["groups"] if g["group_name"] == group_name), None)
        # 추가할 멤버가 계정에 존재하는지 확인
        member_exists = any(u["username"] == add_member for u in accounts["users"])

        if grp:  # 기존 그룹
            if add_member:
                if add_member not in grp["members"]:
                    if member_exists:
                        grp["members"].append(add_member)
                        st.success(f"{add_member}님을 기존 그룹에 추가했습니다.")
                    else:
                        st.error(f"'{add_member}' 아이디는 존재하지 않습니다.")
                else:
                    st.warning(f"{add_member}님은 이미 그룹에 속해있습니다.")
            else:
                st.warning("추가할 멤버 ID를 입력해주세요.")
        else:  # 새 그룹 생성
            if not group_name:
                st.warning("그룹 이름을 입력해주세요.")
            elif not add_member:
                st.warning("그룹 생성 시 추가할 멤버 ID를 입력해주세요.")
            elif not member_exists:
                st.error(f"'{add_member}' 아이디는 존재하지 않습니다.")
            else:
                groups["groups"].append({"group_name": group_name, "members": [username, add_member]})
                st.success(f"새 그룹 '{group_name}' 생성 완료!")

        save_groups(groups)

    # ------------------ 그룹 목록 표시 ------------------
    if role == "보낸이":
        st.markdown("#### 내가 만든/속한 그룹")
        for g in groups["groups"]:
            if username in g["members"]:
                st.write(f"{g['group_name']} - 멤버: {', '.join(g['members'])}")
    else:  # 받는이
        st.markdown("#### 내가 속한 그룹")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        if not my_groups:
            st.info("아직 속한 그룹이 없습니다.")
        else:
            for g in my_groups:
                st.write(f"{g['group_name']} - 보낸이: {', '.join([m for m in g['members'] if m != username])}")
