import streamlit as st
import os
import json
import hashlib
from datetime import datetime
import calendar

# ---------------- 기본 설정 ----------------
st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)
os.makedirs("accounts/memories", exist_ok=True)

# ---------------- 유틸 ----------------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def is_sha256_hex(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s)

# 데이터 파일 경로
ACCOUNTS_FILE = "accounts/accounts.json"
GROUPS_FILE = "accounts/groups.json"
SESSION_FILE = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"

# 데이터 불러오기
accounts = load_json(ACCOUNTS_FILE, {"users": []})
groups = load_json(GROUPS_FILE, {"groups": []})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records": []})

# ---------------- FIX #2: 비밀번호 혼재 자동 마이그레이션 ----------------
changed = False
for u in accounts["users"]:
    pw = u.get("password", "")
    if not is_sha256_hex(pw):      # 평문이면 → 해시로 변환
        u["password"] = hash_pw(pw)
        changed = True
if changed:
    save_json(ACCOUNTS_FILE, accounts)

# ---------------- 메모리 파일 유틸 ----------------
def mem_path(username: str) -> str:
    return f"accounts/memories/{username}.json"

def load_mems(username: str):
    return load_json(mem_path(username), {"memories": {}})

def save_mems(username: str, data):
    save_json(mem_path(username), data)

# ---------------- 세션 기본값 ----------------
for key, default in [
    ("logged_in", False), ("username", ""), ("role", ""),
    ("selected_date", None), ("login_cookie", None), ("theme", "기본")
]:
    if key not in st.session_state:
        st.session_state[key] = default

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
    option = st.radio("선택하세요", ["로그인", "회원가입"], horizontal=True)

    if option == "회원가입":
        username = st.text_input("아이디", key="signup_id")
        password = st.text_input("비밀번호", type="password", key="signup_pw")
        role = st.selectbox("역할", ["보낸이", "받는이"])
        if st.button("가입"):
            in_username = username.strip()
            if not in_username or not password:
                st.warning("아이디와 비밀번호를 입력해주세요.")
            elif any(u["username"] == in_username for u in accounts["users"]):
                st.warning("이미 존재하는 아이디입니다.")
            else:
                accounts["users"].append({
                    "username": in_username,
                    "password": hash_pw(password),
                    "role": role
                })
                save_json(ACCOUNTS_FILE, accounts)
                st.success("가입 완료! 로그인해주세요.")
    else:
        username = st.text_input("아이디", key="login_id")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            in_username = username.strip()
            in_hash = hash_pw(password)
            user = next(
                (
                    u for u in accounts["users"]
                    if u["username"] == in_username
                    and (u["password"] == in_hash or u["password"] == password)  # 해시/평문 둘 다 허용
                ),
                None
            )
            if user:
                st.session_state.logged_in = True
                st.session_state.username = in_username
                st.session_state.role = user["role"]
                st.session_state.login_cookie = {"username": in_username, "role": user["role"]}
                save_json(SESSION_FILE, st.session_state.login_cookie)
                st.rerun()
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

    # 메뉴 (원하면 이름 바꿔도 OK)
    menu = st.sidebar.radio("메뉴", ["자가진단 모니터링", "그룹 편집", "달력"], index=0)

    # ---------- 테마 선택 ----------
    st.sidebar.markdown("### 🎨 달력 테마")
    st.session_state.theme = st.sidebar.selectbox("테마 선택", ["기본", "다크", "핑크", "미니멀"])

    # ---------- 받는이: 오늘의 자가진단 ----------
    today = datetime.now().strftime("%Y-%m-%d")
    if role == "받는이":
        already_done = any(r["username"] == username and r["date"] == today for r in diagnosis_data["records"])
        with st.expander("🩺 오늘의 자가진단", expanded=not already_done):
            if not already_done:
                mood = st.slider("오늘의 기분 (1=나쁨, 5=아주 좋음)", 1, 5, 3)
                stress = st.slider("스트레스 정도 (1=없음, 5=매우 높음)", 1, 5, 3)
                sleep = st.number_input("수면 시간 (시간 단위)", 0.0, 24.0, 7.0, step=0.5)
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

    # ---------- 자가진단 모니터링 (보낸이) ----------
    if role == "보낸이" and menu == "자가진단 모니터링":
        st.title("👀 받는이 자가진단 모니터링")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        receiver_list = []
        for g in my_groups:
            for member in g["members"]:
                if member != username:
                    receiver_list.append(member)
        receiver_list = sorted(set(receiver_list))
        if receiver_list:
            recent = [r for r in diagnosis_data["records"] if r["username"] in receiver_list]
            if recent:
                st.dataframe(
                    [{"날짜": r["date"], "아이디": r["username"], "기분": r["mood"],
                      "스트레스": r["stress"], "수면": r["sleep"], "메모": r["memo"]}
                     for r in sorted(recent, key=lambda x: (x["date"], x["username"]), reverse=True)],
                    use_container_width=True
                )
            else:
                st.info("아직 받는이들의 자가진단 기록이 없습니다.")
        else:
            st.warning("아직 연결된 받는이가 없습니다. '그룹 편집'에서 그룹을 만들어보세요.")

    # ---------- 그룹 편집 ----------
    if menu == "그룹 편집":
        st.title("✏️ 그룹 편집")
        my_groups = [g for g in groups["groups"] if username in g["members"]]

        with st.expander("➕ 새 그룹 만들기", expanded=not my_groups):
            new_name = st.text_input("그룹 이름")
            all_users = sorted([u["username"] for u in accounts["users"] if u["username"] != username])
            add_members = st.multiselect("멤버 추가", all_users)
            if st.button("그룹 생성"):
                # ---------------- FIX #1: 내 그룹에서만 중복 검사 ----------------
                my_groups_for_dup = [g for g in groups["groups"] if username in g["members"]]
                proposed_members = [username] + add_members

                dup_name = any(g["group_name"] == new_name for g in my_groups_for_dup)
                dup_members = any(set(g["members"]) == set(proposed_members) for g in my_groups_for_dup)

                if not new_name:
                    st.warning("그룹 이름을 입력하세요.")
                elif dup_name:
                    st.warning("내가 속한 그룹 중 같은 이름의 그룹이 이미 있어요.")
                elif dup_members:
                    st.warning("같은 멤버 구성의 그룹이 이미 있어요.")
                else:
                    new_group = {"group_name": new_name, "members": proposed_members}
                    groups["groups"].append(new_group)
                    save_json(GROUPS_FILE, groups)
                    st.success(f"그룹 '{new_name}'이(가) 생성되었습니다.")
                    st.rerun()

        if my_groups:
            st.markdown("### 내 그룹")
            for g in my_groups:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")
                with col2:
                    candidates = [u["username"] for u in accounts["users"]
                                  if u["username"] not in g["members"]]
                    add_user = st.selectbox(
                        f"멤버 추가 ({g['group_name']})",
                        ["선택 없음"] + candidates,
                        key=f"add_{g['group_name']}"
                    )
                with col3:
                    if st.button(f"멤버 추가", key=f"add_btn_{g['group_name']}"):
                        if add_user and add_user != "선택 없음":
                            g["members"].append(add_user)
                            save_json(GROUPS_FILE, groups)
                            st.success(f"{add_user} 님을 추가했습니다.")
                            st.rerun()

                if st.button(f"그룹 나가기 ({g['group_name']})", key=f"leave_{g['group_name']}"):
                    g["members"].remove(username)
                    if len(g["members"]) == 0:
                        groups["groups"].remove(g)
                    save_json(GROUPS_FILE, groups)
                    st.success(f"'{g['group_name']}' 그룹에서 나갔습니다.")
                    st.rerun()
        else:
            st.info("아직 속한 그룹이 없습니다. 위에서 새 그룹을 만들어보세요.")

    # ---------- 달력 ----------
    if menu == "달력":
        st.title("🗓 하루 추억 달력")

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
            .day-btn button {{ width: 100%; }}
            </style>
            """,
            unsafe_allow_html=True
        )

        left, right = st.columns([1, 3])
        with left:
            st.markdown("#### 📅 달력 조정")
            year = st.number_input("연도", 2000, 2100, datetime.now().year, step=1)
            month = st.number_input("월", 1, 12, datetime.now().month, step=1)

            if st.session_state.selected_date:
                st.info(f"선택된 날짜: **{st.session_state.selected_date}**")
                if st.button("선택 해제"):
                    st.session_state.selected_date = None
                    st.rerun()

        with right:
            st.markdown(f"### {int(year)}년 {int(month)}월")
            cal = calendar.monthcalendar(int(year), int(month))
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].write(" ")
                    else:
                        date_str = f"{int(year)}-{int(month):02d}-{day:02d}"
                        if cols[i].button(str(day), key=f"day_{int(year)}_{int(month)}_{day}"):
                            st.session_state.selected_date = date_str
                            st.rerun()

        if st.session_state.selected_date:
            st.markdown("---")
            st.subheader(f"📔 {st.session_state.selected_date} 의 추억")
            mems = load_mems(username)
            todays = mems["memories"].get(st.session_state.selected_date, [])

            if todays:
                for entry in todays:
                    st.markdown(f"- **{entry['title']}** — {entry['text']}")
            else:
                st.info("아직 기록이 없어요. 아래에 첫 추억을 남겨보세요!")

            with st.form("add_memory_form", clear_on_submit=True):
                title = st.text_input("제목")
                text = st.text_area("내용", height=100)
                submitted = st.form_submit_button("추억 저장")
                if submitted:
                    if not title or not text:
                        st.warning("제목과 내용을 입력해주세요.")
                    else:
                        new_list = mems["memories"].get(st.session_state.selected_date, [])
                        new_list.append({
                            "title": title,
                            "text": text,
                            "ts": datetime.now().isoformat(timespec="seconds")
                        })
                        mems["memories"][st.session_state.selected_date] = new_list
                        save_mems(username, mems)
                        st.success("추억이 저장되었습니다!")
                        st.rerun()
