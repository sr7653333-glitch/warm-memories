import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)

for key, default in [("logged_in", False), ("username", ""), ("role", ""),
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
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")

# 로그인 후 화면
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

    # ------------------ 그룹 관리 ------------------
    st.markdown("### 👨‍👩‍👧‍👦 그룹 관리")
    
    # 내가 속한 그룹만 표시
    my_groups = [g for g in groups["groups"] if username in g["members"]]
    
    if my_groups:
        for g in my_groups:
            st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")
            
            # 그룹 나가기
            if st.button(f"그룹 나가기 ({g['group_name']})", key=f"leave_{g['group_name']}"):
                g["members"].remove(username)
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

    # 새 그룹 생성
    st.markdown("### ➕ 새 그룹 생성")
    group_name = st.text_input("그룹 이름 입력", key="new_group")
    add_member = st.text_input("추가할 멤버 ID", key="new_member")
    if st.button("그룹 생성/멤버 추가"):
        if not any(u["username"] == add_member for u in accounts["users"]):
            st.error(f"'{add_member}' 아이디는 존재하지 않습니다.")
        else:
            # 동일 멤버로 기존 그룹 있는지 확인
            members_set = set([username, add_member])
            exists = any(set(g["members"]) == members_set for g in groups["groups"])
            if exists:
                st.warning("이미 동일한 멤버로 구성된 그룹이 존재합니다.")
            else:
                groups["groups"].append({"group_name": group_name, "members": [username, add_member]})
                save_groups(groups)
                st.success(f"새 그룹 '{group_name}' 생성 완료!")
