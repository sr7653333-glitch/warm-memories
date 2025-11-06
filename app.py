

# -------------------- app.py (1부 시작) --------------------
import streamlit as st
from streamlit.components.v1 import html as html_component
import os, json, hashlib, base64, calendar
from datetime import datetime

# 기본 설정
st.set_page_config(page_title="하루 추억 캘린더", layout="wide")

# 필요한 폴더 생성
os.makedirs("accounts", exist_ok=True)
os.makedirs("accounts/memories", exist_ok=True)
os.makedirs("accounts/decos", exist_ok=True)

# ✅ JSON 파일 입출력
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ✅ 비밀번호 관련
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def is_sha256_hex(s: str) -> bool:
    return len(s) == 64 and all(c in "0123456789abcdef" for c in s)

# ✅ URL 쿼리(날짜 클릭 감지용) - Streamlit 최신/구버전 모두 지원
def get_query_value(key, default=None):
    try:
        qp = st.experimental_get_query_params()  # 최신 방식
    except:
        return default
    if key in qp:
        value = qp[key]
        return value[0] if isinstance(value, list) else value
    return default

def set_query_params(**kwargs):
    try:
        st.experimental_set_query_params(**kwargs)
    except:
        pass

# ✅ 메모 & 꾸미기 JSON 저장 경로
def mem_path(username): return f"accounts/memories/{username}.json"
def load_mems(username): return load_json(mem_path(username), {"memories":{}})
def save_mems(username, data): save_json(mem_path(username), data)

def deco_path(username): return f"accounts/decos/{username}.json"
def load_decos(username): return load_json(deco_path(username), {"decos":{}})
def save_decos(username, data): save_json(deco_path(username), data)

# ✅ 데이터 파일 경로
ACCOUNTS_FILE  = "accounts/accounts.json"
GROUPS_FILE    = "accounts/groups.json"
SESSION_FILE   = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"
QUESTIONS_FILE = "accounts/questions.json"

# ✅ 기본 데이터 로드
accounts       = load_json(ACCOUNTS_FILE, {"users":[]})
groups         = load_json(GROUPS_FILE, {"groups":[]})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records":[]})
questions_data = load_json(QUESTIONS_FILE, {"custom_questions":[]})

# ✅ 비밀번호가 해시 안 돼 있으면 자동 변환
changed = False
for u in accounts["users"]:
    if not is_sha256_hex(u.get("password","")):
        u["password"] = hash_pw(u["password"])
        changed = True
if changed: save_json(ACCOUNTS_FILE, accounts)

# ✅ 세션 초기화
for key, default in [
   ("logged_in", False),
   ("username", ""),
   ("role", ""),
   ("selected_date", None),
   ("theme", "기본")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ✅ 이전 로그인 세션 복구
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    session_data = load_json(SESSION_FILE, {})
    if session_data:
        st.session_state.logged_in = True
        st.session_state.username  = session_data["username"]
        st.session_state.role      = session_data["role"]

# -------------------- 로그인 / 회원가입 UI --------------------
if not st.session_state.logged_in:
    st.title("💌 하루 추억 캘린더 로그인")
    mode = st.radio("선택하세요", ["로그인", "회원가입"], horizontal=True)

    # ✅ 회원가입
    if mode == "회원가입":
        new_id = st.text_input("아이디")
        new_pw = st.text_input("비밀번호", type="password")
        new_role = st.selectbox("역할", ["보낸이", "받는이"])
        if st.button("회원가입"):
            if not new_id or not new_pw:
                st.warning("아이디와 비밀번호를 입력해주세요.")
            elif any(u["username"] == new_id for u in accounts["users"]):
                st.warning("이미 존재하는 아이디입니다.")
            else:
                accounts["users"].append({
                    "username": new_id,
                    "password": hash_pw(new_pw),
                    "role": new

# -------------------- 메인 화면 (로그인 이후) --------------------
else:
    username = st.session_state.username
    role = st.session_state.role

    # -------------------- 사이드바 --------------------
    st.sidebar.markdown(f"**{username}님 ({role})**")

    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()

    # 메뉴 구성 (역할별)
    menu_items = ["달력"]
    if role == "받는이":
        menu_items.append("자가진단")
    elif role == "보낸이":
        menu_items.append("자가진단 모니터링")
    menu_items.append("그룹 편집")
    menu = st.sidebar.radio("메뉴", menu_items)

    # 테마
    theme_colors = {"기본": "#f0f2f6", "다크": "#1e1e1e", "핑크": "#ffe4ec", "미니멀": "#ffffff"}
    st.session_state.theme = st.sidebar.selectbox("🎨 테마", list(theme_colors.keys()))
    st.markdown(f"<style>body {{ background-color: {theme_colors[st.session_state.theme]}; }}</style>", unsafe_allow_html=True)

    # -------------------- (1) 달력 --------------------
    if menu == "달력":
        st.title("🗓
    # -------------------- (3부 시작) --------------------

    # -------------------- (2) 자가진단 (받는이) --------------------
    if menu == "자가진단" and role == "받는이":
        st.title("📝 오늘의 자가진단")

        today = datetime.now().strftime("%Y-%m-%d")
        already_done = any(r["username"] == username and r["date"] == today for r in diagnosis_data["records"])

        if already_done:
            st.success("✅ 오늘은 이미 자가진단을 완료하셨어요.")
        else:
            st.info("📋 아래 질문에 답해주세요!")

            # 기본 질문 5개
            questions = [
                ("오늘 기분은 어떠세요?", 1, 5, 3),
                ("어젯밤 잠은 편안하셨나요?", 1, 5, 3),
                ("몸의 통증은 어느 정도인가요? (0~10)", 0, 10, 0),
                ("식사는 잘 하셨나요?", ["부족했어요", "보통이에요", "잘 먹었어요"], "보통이에요"),
                ("오늘 움직임이나 활동은 어떠셨어요?", 1, 5, 3)
            ]

            answers = {}
            for q in questions:
                if isinstance(q[1], int):
                    answers[q[0]] = st.slider(q[0], q[1], q[2], q[3])
                else:
                    answers[q[0]] = st.selectbox(q[0], q[1], index=q[1].index(q[2]))

            memo = st.text_area("추가로 남길 메모가 있으신가요?", "")

            if st.button("✔ 자가진단 저장"):
                diagnosis_data["records"].append({
                    "username": username,
                    "date": today,
                    "answers": answers,
                    "memo": memo
                })
                save_json(DIAGNOSIS_FILE, diagnosis_data)
                st.success("저장 완료! 😊")
                st.rerun()

    # -------------------- (3) 자가진단 모니터링 (보낸이) --------------------
    if menu == "자가진단 모니터링" and role == "보낸이":
        st.title("👀 받는이 자가진단 모니터링")

        # 내가 속한 그룹의 다른 사용자 목록
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        receivers = sorted({m for g in my_groups for m in g["members"] if m != username})

        if not receivers:
            st.warning("❗ 아직 연결된 받는이가 없습니다. (그룹 편집 메뉴에서 추가하세요)")
        else:
            data = [r for r in diagnosis_data["records"] if r["username"] in receivers]
            if not data:
                st.info("아직 자가진단 기록이 없습니다.")
            else:
                st.dataframe(
                    [{"날짜": r["date"], "사용자": r["username"], "답변": r.get("answers", ""), "메모": r.get("memo", "")}
                     for r in sorted(data, key=lambda x: (x["date"], x["username"]), reverse=True)],
                    use_container_width=True
                )

    # -------------------- (4) 그룹 편집 --------------------
    if menu == "그룹 편집":
        st.title("👥 그룹 편집")

        my_groups = [g for g in groups["groups"] if username in g["members"]]

        # ✅ 그룹 생성
        with st.expander("➕ 새 그룹 만들기"):
            group_name = st.text_input("그룹 이름")
            members = st.multiselect("추가할 사용자", [u["username"] for u in accounts["users"] if u["username"] != username])
            if st.button("그룹 생성"):
                user_groups = [g for g in my_groups]
                proposed = [username] + members

                if not group_name:
                    st.warning("❗ 그룹 이름을 입력하세요.")
                elif any(g["group_name"] == group_name for g in user_groups):
                    st.warning("❗ 내가 속한 그룹 중 같은 이름이 있어요.")
                elif any(set(g["members"]) == set(proposed) for g in user_groups):
                    st.warning("❗ 같은 멤버 구성이 이미 존재해요.")
                else:
                    groups["groups"].append({"group_name": group_name, "members": proposed})
                    save_json(GROUPS_FILE, groups)
                    st.success(f"✅ 그룹 '{group_name}' 생성 완료!")
                    st.rerun()

        # ✅ 그룹 목록 및 수정
        if my_groups:
            st.subheader("📌 내 그룹 목록")
            for g in my_groups:
                st.markdown(f"**📁 {g['group_name']}** — 멤버: {', '.join(g['members'])}")

                # 멤버 추가
                available = [u["username"] for u in accounts["users"] if u["username"] not in g["members"]]
                new_mem = st.selectbox(f"➕ '{g['group_name']}' 멤버 추가", ["선택 없음"] + available, key=f"add_{g['group_name']}")
                if st.button(f"추가 (→ {g['group_name']})", key=f"btn_add_{g['group_name']}"):
                    if new_mem and new_mem != "선택 없음":
                        g["members"].append(new_mem)
                        save_json(GROUPS_FILE, groups)
                        st.success(f"{new_mem} 님 추가 완료!")
                        st.rerun()

                # 그룹 탈퇴
                if st.button(f"🚪 '{g['group_name']}' 그룹 나가기", key=f"leave_{g['group_name']}"):
                    g["members"].remove(username)
                    if not g["members"]:
                        groups["groups"].remove(g)
                    save_json(GROUPS_FILE, groups)
                    st.success("그룹에서 나갔습니다.")
                    st.rerun()

# -------------------- ✅ 전체 코드 끝! -----

    
