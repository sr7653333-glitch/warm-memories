

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
        st.title("🗓 하루 추억 달력")

        left, right = st.columns([1, 3])

        with left:
            year = st.number_input("연도", 2000, 2100, datetime.now().year)
            month = st.number_input("월", 1, 12, datetime.now().month)
            decorate_mode = st.toggle("🎀 꾸미기 모드")

        with right:
            st.subheader(f"{int(year)}년 {int(month)}월")
            cal = calendar.monthcalendar(int(year), int(month))
            decos = load_decos(username)

            css = """
            <style>
            .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
            .cal-cell {
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 10px;
                min-height: 80px;
                position: relative;
                background: white;
                cursor: pointer;
            }
            .cal-cell:hover { background: #ffeef4; }
            .cal-day { font-weight: bold; }
            .cal-stickers { font-size: 20px; margin-top: 5px; }
            a.cal-link { text-decoration: none; color: inherit; }
            </style>
            """

            cal_html = css + "<div class='cal-grid'>"
            for week in cal:
                for day in week:
                    if day == 0:
                        cal_html += "<div></div>"
                    else:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        deco = decos["decos"].get(date_str, {})
                        bg = deco.get("bg", "white")
                        stickers = " ".join(deco.get("stickers", []))

                        cal_html += f"""
                        <a class="cal-link" href="?date={date_str}" target="_top">
                            <div class="cal-cell" style="background:{bg};">
                                <div class="cal-day">{day}</div>
                                <div class="cal-stickers">{stickers}</div>
                            </div>
                        </a>
                        """
            cal_html += "</div>"
            html_component(cal_html, height=600, scrolling=True)

        # ✅ 날짜 클릭 → 모달 표시
        selected = get_query_value("date", None)
        if selected:
            st.session_state.selected_date = selected

            def show_modal():
                with st.modal(f"📅 {selected} 기록"):
                    st.write(f"## {selected}의 추억들")

                    mems = load_mems(username)["memories"].get(selected, [])
                    if mems:
                        for m in mems:
                            st.write(f"- **{m['title']}** : {m['text']}")
                    else:
                        st.info("기록이 없습니다. 첫 기록을 남겨보세요!")

                    with st.form("add_memory"):
                        t = st.text_input("제목")
                        c = st.text_area("내용")
                        if st.form_submit_button("저장"):
                            data = load_mems(username)
                            data["memories"].setdefault(selected, []).append(
                                {"title": t, "text": c, "time": datetime.now().strftime("%H:%M")}
                            )
                            save_mems(username, data)
                            st.success("저장되었습니다!")
                            st.experimental_set_query_params()  # URL 초기화
                            st.rerun()

                    if st.button("닫기"):
                        st.experimental_set_query_params()
                        st.rerun()

            show_modal()


   
