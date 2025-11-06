# app.py 전체 코드 (Part 1/2)

import streamlit as st
from streamlit.components.v1 import html as html_component
import os, json, hashlib, base64, calendar
from datetime import datetime

st.set_page_config(page_title="하루 추억 캘린더", layout="wide")

# 폴더 생성
os.makedirs("accounts", exist_ok=True)
os.makedirs("accounts/memories", exist_ok=True)
os.makedirs("accounts/decos", exist_ok=True)

# JSON 저장/불러오기
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 암호 해싱
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_sha256(s): return len(s) == 64 and all(c in "0123456789abcdef" for c in s)

# 쿼리 파라미터 (날짜 클릭 감지용)
def get_query_value(key):
    try:
        params = st.experimental_get_query_params()
        return params.get(key, [None])[0]
    except:
        return None

def set_query_params(**kwargs):
    try:
        st.experimental_set_query_params(**kwargs)
    except:
        pass

# 메모 & 꾸미기 파일 경로
def mem_path(u): return f"accounts/memories/{u}.json"
def load_mems(u): return load_json(mem_path(u), {"memories":{}})
def save_mems(u,d): save_json(mem_path(u), d)

def deco_path(u): return f"accounts/decos/{u}.json"
def load_decos(u): return load_json(deco_path(u), {"decos":{}})
def save_decos(u,d): save_json(deco_path(u), d)

# 데이터 파일 정의
ACCOUNTS_FILE  = "accounts/accounts.json"
GROUPS_FILE    = "accounts/groups.json"
SESSION_FILE   = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"

accounts       = load_json(ACCOUNTS_FILE, {"users":[]})
groups         = load_json(GROUPS_FILE, {"groups":[]})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records":[]})

# 비밀번호 평문 → 해시 변환
changed = False
for u in accounts["users"]:
    if not is_sha256(u["password"]):
        u["password"] = hash_pw(u["password"])
        changed = True
if changed: save_json(ACCOUNTS_FILE, accounts)

# Session 초기화
for k,v in [("logged_in",False), ("username",""), ("role",""), ("selected_date",None), ("theme","기본")]:
    st.session_state.setdefault(k, v)

# 세션 복원
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    s = load_json(SESSION_FILE, {})
    if s:
        st.session_state.logged_in = True
        st.session_state.username = s.get("username")
        st.session_state.role = s.get("role")

# -------------------------------- 로그인 / 회원가입 --------------------------------
if not st.session_state.logged_in:
    st.title("💌 하루 추억 캘린더 로그인")
    mode = st.radio("선택", ["로그인", "회원가입"], horizontal=True)

    if mode == "회원가입":
        uid = st.text_input("아이디")
        pw = st.text_input("비밀번호", type="password")
        role = st.selectbox("역할", ["보낸이", "받는이"])
        if st.button("회원가입"):
            if not uid or not pw:
                st.warning("아이디/비밀번호 입력 필요")
            elif any(u["username"] == uid for u in accounts["users"]):
                st.warning("이미 존재하는 아이디")
            else:
                accounts["users"].append({"username":uid, "password":hash_pw(pw), "role":role})
                save_json(ACCOUNTS_FILE, accounts)
                st.success("가입 완료! 로그인 해주세요.")

    else:  # 로그인
        uid = st.text_input("아이디")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            hashed = hash_pw(pw)
            user = next((u for u in accounts["users"] if u["username"] == uid and u["password"] == hashed), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = uid
                st.session_state.role = user["role"]
                save_json(SESSION_FILE, {"username":uid, "role":user["role"]})
                st.rerun()
            else:
                st.warning("아이디 또는 비밀번호 오류")

# -------------------------------- 메인 페이지(로그인 성공) --------------------------------
else:
    username = st.session_state.username
    role = st.session_state.role

    st.sidebar.write(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        st.rerun()

    # 메뉴 설정
    menu = ["달력"]
    if role == "받는이":
        menu.append("자가진단")
    if role == "보낸이":
        menu.append("자가진단 모니터링")
    menu.append("그룹 편집")
    sel_menu = st.sidebar.radio("메뉴", menu)

    # 테마
    theme_colors = {"기본":"#f0f2f6","다크":"#1e1e1e","핑크":"#ffe4ec","미니멀":"#ffffff"}
    st.session_state.theme = st.sidebar.selectbox("🎨 테마", list(theme_colors.keys()))
    st.markdown(f"<style>body {{ background-color: {theme_colors[st.session_state.theme]}; }}</style>", unsafe_allow_html=True)

        # -------------------- 달력 --------------------
    if sel_menu == "달력":
        st.title("🗓 하루 추억 달력")

       with right:
    st.markdown(
        """
        <style>
        .cal-cell {
            border:1px solid rgba(0,0,0,.1);
            border-radius:10px;
            min-height:92px;
            padding:8px;
            background:#fff;
        }
        .cal-day { font-weight:800; margin-bottom:6px; }
        .cal-stickers { font-size:20px; line-height:1.1; }
        .cal-empty { min-height:92px; }
        /* 버튼 평면화 */
        .cal-btn > button {
            width: 100%;
            height: 64px;
            border-radius: 8px;
            background: transparent;
            border: 1px dashed rgba(0,0,0,.15);
        }
        .cal-btn > button:hover { border-color: rgba(0,0,0,.35); }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.subheader(f"{int(year)}년 {int(month)}월")
    cal = calendar.monthcalendar(int(year), int(month))
    decos = load_decos(username)

    # 주 단위로 7열 그리드
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div class='cal-empty'></div>", unsafe_allow_html=True)
                    continue

                date_str = f"{int(year)}-{int(month):02d}-{day:02d}"
                dconf = decos["decos"].get(date_str, {})
                bg = dconf.get("bg", "#ffffff")
                stickers = " ".join(dconf.get("stickers", []))
                radius = dconf.get("radius", "10px")

                # 날짜 카드
                st.markdown(
                    f"<div class='cal-cell' style='background:{bg}; border-radius:{radius};'>"
                    f"<div class='cal-day'>{day}</div>"
                    f"<div class='cal-stickers'>{stickers}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # 클릭 버튼(스트림릿 이벤트로 처리 → iframe 중첩 없음)
                if st.button("열기", key=f"open_{date_str}", help="이 날짜 보기", use_container_width=True):
                    st.session_state.selected_date = date_str
                    # 쿼리파라미터 쓰지 않고 상태로만 처리
                    st.rerun()

# ✅ 날짜 선택 상태가 있으면 모달로 표시
if st.session_state.get("selected_date"):
    sel = st.session_state["selected_date"]
    with st.modal(f"📅 {sel}"):
        st.subheader(f"{sel}의 추억")
        mem = load_mems(username)["memories"].get(sel, [])
        if mem:
            for item in mem:
                st.write(f"- **{item['title']}** — {item['text']}")
        else:
            st.info("아직 기록이 없어요!")

        with st.form("add_memory_form", clear_on_submit=True):
            t = st.text_input("제목")
            c = st.text_area("내용", height=120)
            submitted = st.form_submit_button("저장")
            if submitted:
                data = load_mems(username)
                data["memories"].setdefault(sel, []).append({
                    "title": t, "text": c, "ts": datetime.now().isoformat(timespec="seconds")
                })
                save_mems(username, data)
                st.success("저장되었습니다!")
                st.rerun()

        if st.button("닫기"):
            st.session_state.selected_date = None
            st.rerun()

        # ----------------------------------------------------------------
        # ---------------- (2) 자가진단 - 받는이 ------------------------
        # ----------------------------------------------------------------
    if sel_menu == "자가진단" and role == "받는이":
        st.title("📝 오늘의 자가진단")
        today = datetime.now().strftime("%Y-%m-%d")

        already = any(r["username"] == username and r["date"] == today for r in diagnosis_data["records"])
        if already:
            st.success("✅ 오늘은 이미 자가진단을 완료하셨어요!")
        else:
            st.info("📋 아래 질문에 답해주세요")

            answers = {}
            # 기본 질문 5개
            q1 = st.slider("1️⃣ 오늘 기분은 어떠세요? (1~5)", 1, 5, 3)
            q2 = st.slider("2️⃣ 잠은 편안히 주무셨어요? (1~5)", 1, 5, 3)
            q3 = st.slider("3️⃣ 현재 통증 정도는? (0~10)", 0, 10, 0)
            q4 = st.selectbox("4️⃣ 식사는 잘 하셨어요?", ["부족했어요", "보통이에요", "잘 먹었어요"])
            q5 = st.slider("5️⃣ 오늘 움직임은 괜찮으셨어요? (1~5)", 1, 5, 3)

            answers = {
                "기분": q1, "수면": q2, "통증": q3,
                "식사": q4, "활동": q5
            }
            memo = st.text_area("🗒 추가 메모")

            if st.button("✔ 저장하기"):
                diagnosis_data["records"].append({
                    "username": username,
                    "date": today,
                    "answers": answers,
                    "memo": memo
                })
                save_json(DIAGNOSIS_FILE, diagnosis_data)
                st.success("저장 완료! 내일 또 기록해 주세요 😊")
                st.rerun()

        # ----------------------------------------------------------------
        # ---------------- (3) 자가진단 모니터링 - 보낸이 ----------------
        # ----------------------------------------------------------------
    if sel_menu == "자가진단 모니터링" and role == "보낸이":
        st.title("👀 받는이 자가진단 모니터링")

        # 내가 속한 그룹의 받는이 모으기
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        receivers = sorted({m for g in my_groups for m in g["members"] if m != username})

        if not receivers:
            st.warning("❗ 연결된 받는이가 없습니다. 그룹을 먼저 만들어주세요.")
        else:
            # 해당 받는이 기록만 표시
            data = [r for r in diagnosis_data["records"] if r["username"] in receivers]
            if not data:
                st.info("아직 기록된 자가진단이 없습니다.")
            else:
                st.dataframe(
                    [{"날짜": r["date"], "이름": r["username"], **r.get("answers", {}), "메모": r.get("memo","")} 
                     for r in sorted(data, key=lambda x: (x["date"], x["username"]), reverse=True)],
                    use_container_width=True
                )

        # ----------------------------------------------------------------
        # -------------------------- (4) 그룹 편집 -----------------------
        # ----------------------------------------------------------------
    if sel_menu == "그룹 편집":
        st.title("👥 그룹 편집")

        my_groups = [g for g in groups["groups"] if username in g["members"]]

        # (1) 새 그룹 만들기
        with st.expander("➕ 새 그룹 만들기", expanded=not my_groups):
            new_name = st.text_input("그룹 이름")
            members = st.multiselect("멤버 추가", [u["username"] for u in accounts["users"] if u["username"] != username])

            if st.button("✔ 그룹 생성"):
                if not new_name:
                    st.warning("❗ 그룹 이름을 입력하세요.")
                else:
                    mine = [g for g in my_groups]
                    proposed = [username] + members
                    dup_name = any(g["group_name"] == new_name for g in mine)
                    dup_members = any(set(g["members"]) == set(proposed) for g in mine)

                    if dup_name:
                        st.warning("❗ 같은 그룹 이름이 이미 있습니다.")
                    elif dup_members:
                        st.warning("❗ 같은 멤버 구성의 그룹이 존재합니다.")
                    else:
                        groups["groups"].append({"group_name": new_name, "members": proposed})
                        save_json(GROUPS_FILE, groups)
                        st.success(f"✅ '{new_name}' 그룹이 생성되었습니다!")
                        st.rerun()

        # (2) 기존 그룹 표시 및 수정
        if my_groups:
            st.markdown("### 📌 내 그룹 목록")
            for g in my_groups:
                st.write(f"**📁 {g['group_name']}** — 멤버: {', '.join(g['members'])}")

                # 멤버 추가
                candidates = [u["username"] for u in accounts["users"] if u["username"] not in g["members"]]
                new_member = st.selectbox(f"'{g['group_name']}' 에 멤버 추가", ["선택 없음"] + candidates, key=f"add_{g['group_name']}")

                if st.button("➕ 멤버 추가", key=f"add_btn_{g['group_name']}"):
                    if new_member and new_member != "선택 없음":
                        g["members"].append(new_member)
                        save_json(GROUPS_FILE, groups)
                        st.success(f"{new_member} 님을 추가했습니다!")
                        st.rerun()

                # 그룹 나가기
                if st.button(f"🚪 '{g['group_name']}' 그룹 나가기", key=f"leave_{g['group_name']}"):
                    g["members"].remove(username)
                    if not g["members"]:
                        groups["groups"].remove(g)
                    save_json(GROUPS_FILE, groups)
                    st.success("그룹에서 나갔습니다.")
                    st.rerun()

# -------------------- ✅ 전체 app.py 끝 --------------------

   
