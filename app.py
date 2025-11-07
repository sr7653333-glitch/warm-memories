# app.py — 하루 추억 캘린더 (안정+지속 접속 버전)
# - Streamlit Cloud 환경 대비:
#   * st_autorefresh(있으면 사용)로 15분 keep-alive
#   * 매직 로그인(토큰)으로 세션 초기화 후에도 원클릭 자동접속
# - 모달/iframe 미사용. 버튼 이벤트만 사용.
# - 기존 기능 유지: 로그인/회원가입/그룹/달력 꾸미기/자가진단/모니터링

import os
import json
import hashlib
import calendar
import secrets
import time
from datetime import datetime
import streamlit as st

# -------------------- 기본 설정 & 폴더 --------------------
st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)
os.makedirs("accounts/memories", exist_ok=True)
os.makedirs("accounts/decos", exist_ok=True)

# -------------------- Keep-Alive (있으면 사용, 없으면 무시) --------------------
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15 * 60 * 1000, key="keepalive_15m")  # 15분마다 자동 새로고침
except Exception:
    pass  # 라이브러리 없으면 조용히 패스

# -------------------- 유틸 --------------------
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def is_sha256_hex(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s)

def mem_path(username): return f"accounts/memories/{username}.json"
def load_mems(username): return load_json(mem_path(username), {"memories": {}})
def save_mems(username, data): save_json(mem_path(username), data)

def deco_path(username): return f"accounts/decos/{username}.json"
def load_decos(username): return load_json(deco_path(username), {"decos": {}})
def save_decos(username, data): save_json(deco_path(username), data)

def get_query_params():
    try:
        return dict(st.query_params)
    except Exception:
        try:
            return st.experimental_get_query_params()
        except Exception:
            return {}

def set_query_params(**kwargs):
    try:
        st.query_params.update(kwargs); return
    except Exception:
        try:
            st.experimental_set_query_params(**kwargs)
        except Exception:
            pass

def get_query_value(key, default=None):
    qp = get_query_params()
    if key in qp:
        v = qp[key]
        return v[0] if isinstance(v, list) else v
    return default

# -------------------- 데이터 파일 --------------------
ACCOUNTS_FILE  = "accounts/accounts.json"
GROUPS_FILE    = "accounts/groups.json"
SESSION_FILE   = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"
QUESTIONS_FILE = "accounts/questions.json"
TOKENS_FILE    = "accounts/tokens.json"  # 매직 로그인

accounts       = load_json(ACCOUNTS_FILE, {"users": []})
groups         = load_json(GROUPS_FILE, {"groups": []})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records": []})
questions_data = load_json(QUESTIONS_FILE, {"custom_questions": []})
tokens_db      = load_json(TOKENS_FILE, {"tokens": []})

# 비밀번호 평문 → 해시 마이그레이션
changed = False
for u in accounts["users"]:
    if not is_sha256_hex(u.get("password", "")):
        u["password"] = hash_pw(u.get("password", ""))
        changed = True
if changed:
    save_json(ACCOUNTS_FILE, accounts)

# ---- 매직 링크: 안전한 노출 방식 ----
# secrets.toml 에서 끄고 켤 수 있음:
# [FEATURES]
# MAGIC_LINK = true
enable_magic = False
try:
    enable_magic = bool(st.secrets.get("FEATURES", {}).get("MAGIC_LINK", True))
except Exception:
    enable_magic = True  # secrets 없으면 기본 허용 (원하면 False로)

if enable_magic:
    st.sidebar.markdown("### 🔑 자동접속")
    st.sidebar.caption("필요할 때만 생성됩니다. 표시된 토큰은 1회용/짧은 만료를 권장합니다.")

    # 짧은 만료로 재발급 (예: 24시간)
    def issue_short_token(u: str, hours: int = 24):
        toks = load_tokens()
        tok = secrets.token_urlsafe(24)
        exp = int(time.time()) + hours * 3600
        toks["tokens"].append({"t": tok, "u": u, "exp": exp})
        save_tokens(toks)
        return tok

    # 내 토큰 전부 폐기
    def revoke_all_tokens(u: str):
        toks = load_tokens()
        toks["tokens"] = [rec for rec in toks["tokens"] if rec.get("u") != u]
        save_tokens(toks)

    colA, colB = st.sidebar.columns(2)
    if colA.button("만들기"):
        tok = issue_short_token(username, hours=24)
        st.session_state["_last_token"] = tok
        st.sidebar.success("토큰이 생성됐어요. 아래를 복사해 두세요.")
    if colB.button("모두 폐기"):
        revoke_all_tokens(username)
        st.session_state.pop("_last_token", None)
        st.sidebar.info("내 토큰을 모두 폐기했습니다.")

    # 만들어진 토큰만 표시(자동으로 항상 노출하지 않음)
    if "_last_token" in st.session_state:
        tok = st.session_state["_last_token"]
        st.sidebar.markdown("**접속 파라미터**")
        st.sidebar.code(f"?t={tok}", language="text")
        st.sidebar.caption("앱 기본 URL 뒤에 붙여 사용: https://YOUR-APP/?t=...")

    # 토큰 자동 발급/자동 표시 안 함 (기존처럼 로그인 성공 시 바로 노출 X)


# -------------------- 세션 --------------------
for k, v in [
    ("logged_in", False),
    ("username", ""),
    ("role", ""),
    ("selected_date", None),
    ("theme", "기본"),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# 매직 링크로 자동 로그인 시도 (로그인 전)
if not st.session_state.logged_in:
    qp = get_query_params()
    t = qp.get("t", None)
    if isinstance(t, list): t = t[0]
    if t:
        u = validate_token(t)
        if u:
            user = next((x for x in accounts["users"] if x["username"] == u), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                save_json(SESSION_FILE, {"username": u, "role": user["role"]})
                st.success(f"{u}님 자동 로그인되었습니다.")
                # query에서 t 제거(보안/미관)
                qp = get_query_params(); qp.pop("t", None)
                set_query_params(**qp)
                st.rerun()

# 이전 세션 복원
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    sess = load_json(SESSION_FILE, {})
    if sess:
        st.session_state.logged_in = True
        st.session_state.username = sess.get("username", "")
        st.session_state.role = sess.get("role", "")

# -------------------- 로그인/회원가입 --------------------
if not st.session_state.logged_in:
    st.title("💌 하루 추억 캘린더 로그인")
    mode = st.radio("선택하세요", ["로그인", "회원가입"], horizontal=True)

    if mode == "회원가입":
        uid = st.text_input("아이디")
        pw = st.text_input("비밀번호", type="password")
        role = st.selectbox("역할", ["보낸이", "받는이"])
        if st.button("회원가입"):
            if not uid or not pw:
                st.warning("아이디와 비밀번호를 입력해주세요.")
            elif any(u["username"] == uid for u in accounts["users"]):
                st.warning("이미 존재하는 아이디입니다.")
            else:
                accounts["users"].append({"username": uid, "password": hash_pw(pw), "role": role})
                save_json(ACCOUNTS_FILE, accounts)
                st.success("가입 완료! 로그인해주세요.")

    else:
        uid = st.text_input("아이디")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            hashed = hash_pw(pw)
            user = next((u for u in accounts["users"] if u["username"] == uid and u["password"] == hashed), None)
            if user:
                # 로그인 성공
                st.session_state.logged_in = True
                st.session_state.username = uid
                st.session_state.role = user["role"]
                save_json(SESSION_FILE, {"username": uid, "role": user["role"]})

                # 매직 링크 발급
                tok = issue_token(uid, days=14)
                st.success("로그인 되었습니다. 자동접속 링크가 사이드바에 생성됩니다.")
                # 사이드바에 링크 표시를 위해 rerun
                st.rerun()
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")

# -------------------- 로그인 후 --------------------
else:
    username = st.session_state.username
    role = st.session_state.role

    # 사이드바: 사용자/로그아웃
    st.sidebar.markdown(f"**{username}님 ({role})**")
    # 매직 링크 안내
    try:
        base_qp = get_query_params()
        tok = issue_token(username, days=14)  # 새 토큰 한 번 더 발급(이전 토큰도 유효)
        st.sidebar.markdown("### 🔑 자동접속 링크")
        st.sidebar.write("아래 링크(또는 토큰)를 즐겨찾기/바탕화면에 저장해두면 로그인 없이 접속돼요. (14일 유효)")
        st.sidebar.code(f"?t={tok}", language="text")
        st.sidebar.caption("앱의 기본 URL 뒤에 그대로 붙여 사용하세요. 예: https://myapp.streamlit.app/?t=...")
    except Exception:
        pass

    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None
        # 세션 파일은 '로그아웃 시'에만 삭제 (의도치 초기화 대비)
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()

    # 메뉴
    menu_items = ["달력"]
    if role == "받는이":
        menu_items.append("자가진단")
    elif role == "보낸이":
        menu_items.append("자가진단 모니터링")
    menu_items.append("그룹 편집")
    menu = st.sidebar.radio("메뉴", menu_items, index=0)

    # 전역 큰 글꼴/버튼(어르신 UI)
    st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size:18px; }
    h1,h2,h3 { font-size:26px; }
    .stButton>button { min-height:44px; font-size:18px; }
    </style>
    """, unsafe_allow_html=True)

    # 테마
    st.sidebar.markdown("### 🎨 달력 테마")
    theme_colors = {"기본": "#f0f2f6", "다크": "#1e1e1e", "핑크": "#ffe4ec", "미니멀": "#ffffff"}
    st.session_state.theme = st.sidebar.selectbox("테마 선택", list(theme_colors.keys()))
    st.markdown(f"<style>.stApp{{background-color:{theme_colors[st.session_state.theme]};}}</style>", unsafe_allow_html=True)

    STICKER_PRESETS = ["🌸", "🌼", "🌟", "💖", "✨", "🍀", "🧸", "🎀", "📸", "☕", "🍰", "🎈", "📝", "👣", "🎵"]

    # -------------------- 상세(상단 고정 오버레이) --------------------
    def render_detail_panel(sel_date: str):
        st.markdown(
            f"""
            <div style="
                position: sticky; top: 0; z-index: 9999;
                background: rgba(255,255,255,0.98);
                backdrop-filter: blur(4px);
                border: 2px solid #eee; border-radius: 16px;
                padding: 16px; box-shadow: 0 8px 24px rgba(0,0,0,.08);
                margin-bottom: 12px;">
                <h3 style="margin: 0;">📅 {sel_date}</h3>
                <div style="font-size: 13px; color: #666;">상단 고정 패널입니다. 닫기를 누르면 사라져요.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader("📔 추억")
        mem = load_mems(username)["memories"].get(sel_date, [])
        if mem:
            for item in mem:
                st.markdown(f"- **{item['title']}** — {item['text']}")
        else:
            st.info("아직 기록이 없어요!")

        with st.form("add_memory_form", clear_on_submit=True):
            t = st.text_input("제목")
            c = st.text_area("내용", height=120)
            save_btn = st.form_submit_button("저장")
            if save_btn:
                if not t or not c:
                    st.warning("제목과 내용을 입력해주세요.")
                else:
                    data = load_mems(username)
                    data["memories"].setdefault(sel_date, []).append(
                        {"title": t, "text": c, "ts": datetime.now().isoformat(timespec="seconds")}
                    )
                    save_mems(username, data)
                    st.success("추억이 저장되었습니다!")
                    st.rerun()

        if st.button("닫기"):
            st.session_state.selected_date = None
            st.rerun()

    # -------------------- 달력 --------------------
    if menu == "달력":
        st.title("🗓 하루 추억 달력")
        decos = load_decos(username)

        left, right = st.columns([1, 3], gap="large")
        with left:
            st.markdown("#### 📅 달력 조정")
            year = st.number_input("연도", 2000, 2100, datetime.now().year, step=1)
            month = st.number_input("월", 1, 12, datetime.now().month, step=1)
            decorate_mode = st.toggle("🎀 꾸미기 모드", value=False, help="날짜별 배경/스티커/모서리 둥글기 저장")

            if st.session_state.selected_date:
                st.info(f"선택된 날짜: **{st.session_state.selected_date}**")
                if st.button("선택 해제"):
                    st.session_state.selected_date = None
                    st.rerun()

        with right:
            st.subheader(f"{int(year)}년 {int(month)}월")

            # 그리드 스타일
            st.markdown("""
            <style>
                .cal-card {
                    border:1px solid rgba(0,0,0,.08);
                    border-radius:12px;
                    min-height:96px;
                    padding:8px;
                    background:#fff;
                }
                .cal-day { font-weight:800; margin-bottom:6px; }
                .cal-stickers { font-size:20px; line-height:1.1; }
            </style>
            """, unsafe_allow_html=True)

            cal_mat = calendar.monthcalendar(int(year), int(month))
            for week in cal_mat:
                cols = st.columns(7, gap="small")
                for i, day in enumerate(week):
                    with cols[i]:
                        if day == 0:
                            st.write("")
                            continue
                        date_key = f"{int(year)}-{int(month):02d}-{day:02d}"
                        dconf = decos["decos"].get(date_key, {})
                        bg = dconf.get("bg", "#ffffff")
                        radius = dconf.get("radius", "12px")
                        stickers = " ".join(dconf.get("stickers", []))

                        st.markdown(
                            f"<div class='cal-card' style='background:{bg}; border-radius:{radius};'>"
                            f"<div class='cal-day'>{day}</div>"
                            f"<div class='cal-stickers'>{stickers}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        if st.button("열기", key=f"open_{date_key}", use_container_width=True):
                            st.session_state.selected_date = date_key
                            st.rerun()

        # 🎀 꾸미기 패널
        if decorate_mode:
            st.markdown("---")
            st.subheader("🎀 달력 꾸미기 (날짜별)")
            if not st.session_state.selected_date:
                st.info("달력에서 날짜를 먼저 선택하세요.")
            else:
                date_key = st.session_state.selected_date
                decos = load_decos(username)  # 최신 로드
                d = decos["decos"].get(date_key, {})
                c1, c2 = st.columns([2, 1], gap="large")
                with c1:
                    st.markdown(f"**꾸미는 날짜:** {date_key}")
                    bg = st.color_picker("배경색", value=d.get("bg", "#ffffff"))
                    r_choices = ["6px", "10px", "12px", "16px", "20px", "999px"]
                    current_radius = d.get("radius", "12px")
                    if current_radius not in r_choices:
                        r_choices.append(current_radius)
                    radius = st.selectbox("모서리 둥글기", r_choices, index=r_choices.index(current_radius))
                    picked = st.multiselect("스티커(이모지)", STICKER_PRESETS, default=d.get("stickers", []))
                    extra = st.text_input("추가 이모지/텍스트", value="")
                    if extra and extra not in picked:
                        picked.append(extra)

                    col_s, col_r, col_c = st.columns(3)
                    with col_s:
                        if st.button("🗂 꾸미기 저장"):
                            decos["decos"][date_key] = {"bg": bg, "radius": radius, "stickers": picked}
                            save_decos(username, decos)
                            st.success("저장되었습니다! 달력/상세에 즉시 반영됩니다.")
                            st.rerun()
                    with col_r:
                        if st.button("♻️ 이 날짜 초기화"):
                            if date_key in decos["decos"]:
                                del decos["decos"][date_key]
                                save_decos(username, decos)
                                st.info("초기화했습니다.")
                                st.rerun()
                    with col_c:
                        if st.button("선택 해제"):
                            st.session_state.selected_date = None
                            st.rerun()

                with c2:
                    st.markdown("**미리보기**")
                    st.markdown(
                        f"<div class='cal-card' style='background:{bg}; border-radius:{radius}; min-height:140px;'>"
                        f"<div class='cal-day'>{date_key[-2:]}</div>"
                        f"<div class='cal-stickers'>{' '.join(picked)}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        # 선택된 날짜가 있으면 상단 오버레이 표시
        if st.session_state.get("selected_date"):
            render_detail_panel(st.session_state["selected_date"])

    # -------------------- 자가진단 (받는이) --------------------
    if menu == "자가진단" and role == "받는이":
        st.title("📝 오늘의 자가진단")
        today = datetime.now().strftime("%Y-%m-%d")
        done = any(r.get("username") == username and r.get("date") == today for r in diagnosis_data["records"])

        # 기본 5문항
        def_qs = [
            ("오늘 기분은 어떠세요? (1~5)", 1, 5, 3, "mood"),
            ("어젯밤 잠은 편안하셨어요? (1~5)", 1, 5, 3, "sleep"),
            ("지금 통증 정도는 얼마나 되세요? (0~10)", 0, 10, 0, "pain"),
            ("오늘 식사/수분 섭취는 괜찮으셨어요?", ["부족했어요", "보통이에요", "좋았어요"], "보통이에요", "appetite"),
            ("오늘 움직임/걷기는 어떠셨어요? (1~5)", 1, 5, 3, "activity"),
        ]

        if done:
            st.success("✅ 오늘은 이미 자가진단을 완료하셨어요.")
        else:
            answers = {}
            for q in def_qs:
                if isinstance(q[1], int):
                    label, mn, mx, df, keyname = q
                    answers[keyname] = st.slider(label, mn, mx, df)
                else:
                    label, options, default, keyname = q
                    answers[keyname] = st.selectbox(label, options, index=options.index(default))

            # 맞춤 질문
            st.markdown("### 📌 맞춤 질문")
            custom_for_me = [q for q in questions_data.get("custom_questions", []) if username in q.get("targets", [])]
            c_ans = {}
            if custom_for_me:
                for i, cq in enumerate(custom_for_me):
                    t = cq.get("type", "text")
                    label = f"{cq['text']} (작성자: {cq['creator']})"
                    if t == "scale":
                        mn = int(cq.get("min", 1)); mx = int(cq.get("max", 5)); df = int(cq.get("default", (mn+mx)//2))
                        c_ans[cq["id"]] = st.slider(label, mn, mx, df, key=f"cq_scale_{i}")
                    elif t == "yesno":
                        c_ans[cq["id"]] = st.radio(label, ["예", "아니오"], horizontal=True, key=f"cq_yesno_{i}")
                    elif t == "choice":
                        opts = cq.get("opts", ["아니오", "예"]); idx = int(cq.get("default_index", 0))
                        idx = max(0, min(idx, len(opts)-1))
                        c_ans[cq["id"]] = st.selectbox(label, opts, index=idx, key=f"cq_choice_{i}")
                    else:
                        c_ans[cq["id"]] = st.text_input(label, key=f"cq_text_{i}")
            else:
                st.info("받는이에게 배포된 맞춤 질문이 없습니다.")

            memo = st.text_area("추가 메모", "")

            if st.button("자가진단 제출", type="primary"):
                diagnosis_data["records"].append({
                    "username": username,
                    "date": today,
                    "answers": {**answers, **{f"custom:{k}": v for k, v in c_ans.items()}},
                    "memo": memo
                })
                save_json(DIAGNOSIS_FILE, diagnosis_data)
                st.success("오늘의 자가진단이 저장되었습니다!")
                st.rerun()

    # -------------------- 자가진단 모니터링 (보낸이) --------------------
    if menu == "자가진단 모니터링" and role == "보낸이":
        st.title("👀 받는이 자가진단 모니터링")
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        receivers = sorted({m for g in my_groups for m in g["members"] if m != username})

        if receivers:
            recent = [r for r in diagnosis_data["records"] if r["username"] in receivers]
            if recent:
                st.dataframe(
                    [{"날짜": r["date"], "아이디": r["username"], **(r.get("answers", {})), "메모": r.get("memo", "")}
                     for r in sorted(recent, key=lambda x: (x["date"], x["username"]), reverse=True)],
                    use_container_width=True
                )
            else:
                st.info("아직 자가진단 기록이 없습니다.")
        else:
            st.warning("아직 연결된 받는이가 없습니다. ‘그룹 편집’에서 그룹을 만들어보세요.")

        st.markdown("---")
        st.subheader("🛠 맞춤 질문 만들기 & 배포")
        with st.form("custom_q_form"):
            q_text = st.text_input("질문 내용 (예: '물을 충분히 드셨나요?')")
            q_type = st.selectbox("질문 유형", ["yesno", "scale", "choice", "text"], index=0)
            colA, colB, colC = st.columns(3)
            with colA: minv = st.number_input("scale 최소값", value=1, step=1)
            with colB: maxv = st.number_input("scale 최대값", value=5, step=1)
            with colC: dflt = st.number_input("scale 기본값", value=3, step=1)
            opts_txt = st.text_input("choice 옵션(쉼표로 구분)", value="아니오,예")
            d_idx = st.number_input("choice 기본 인덱스", value=0, step=1)

            receivers = sorted({m for g in my_groups for m in g["members"] if m != username})
            targets = st.multiselect("질문을 받을 받는이", receivers)

            sub = st.form_submit_button("질문 생성")
            if sub:
                if not q_text.strip():
                    st.warning("질문 내용을 입력하세요.")
                elif not targets:
                    st.warning("타겟 받는이를 선택하세요.")
                else:
                    q_id = f"cq_{int(datetime.now().timestamp())}"
                    item = {"id": q_id, "creator": username, "targets": targets, "text": q_text.strip(), "type": q_type}
                    if q_type == "scale":
                        item.update({"min": int(minv), "max": int(maxv), "default": int(dflt)})
                    elif q_type == "choice":
                        opts = [o.strip() for o in opts_txt.split(",") if o.strip()] or ["아니오", "예"]
                        item.update({"opts": opts, "default_index": int(d_idx)})
                    questions_data.setdefault("custom_questions", []).append(item)
                    save_json(QUESTIONS_FILE, questions_data)
                    st.success("맞춤 질문이 생성되어 배포되었습니다!")

        st.markdown("### 📋 내가 만든 질문")
        my_qs = [q for q in questions_data.get("custom_questions", []) if q.get("creator") == username]
        if my_qs:
            for q in sorted(my_qs, key=lambda x: x["id"], reverse=True):
                st.markdown(f"- **{q['text']}** *(유형: {q['type']}, 대상: {', '.join(q.get('targets', []))})*")
        else:
            st.info("아직 만든 질문이 없습니다.")

    # -------------------- 그룹 편집 --------------------
    if menu == "그룹 편집":
        st.title("✏️ 그룹 편집")
        my_groups = [g for g in groups["groups"] if username in g["members"]]

        with st.expander("➕ 새 그룹 만들기", expanded=not my_groups):
            new_name = st.text_input("그룹 이름")
            all_users = sorted([u["username"] for u in accounts["users"] if u["username"] != username])
            add_members = st.multiselect("멤버 추가", all_users)
            if st.button("그룹 생성"):
                mine = [g for g in groups["groups"] if username in g["members"]]
                proposed = [username] + add_members
                dup_name = any(g["group_name"] == new_name for g in mine)
                dup_members = any(set(g["members"]) == set(proposed) for g in mine)
                if not new_name:
                    st.warning("그룹 이름을 입력하세요.")
                elif dup_name:
                    st.warning("내가 속한 그룹 중 같은 이름의 그룹이 이미 있어요.")
                elif dup_members:
                    st.warning("같은 멤버 구성의 그룹이 이미 있어요.")
                else:
                    groups["groups"].append({"group_name": new_name, "members": proposed})
                    save_json(GROUPS_FILE, groups)
                    st.success(f"그룹 '{new_name}'이(가) 생성되었습니다.")
                    st.rerun()

        if my_groups:
            st.markdown("### 내 그룹")
            for idx, g in enumerate(my_groups):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"**{g['group_name']}** - 멤버: {', '.join(g['members'])}")
                with c2:
                    candidates = [u["username"] for u in accounts["users"] if u["username"] not in g["members"]]
                    add_user = st.selectbox(f"멤버 추가 ({g['group_name']})", ["선택 없음"] + candidates, key=f"add_{g['group_name']}_{idx}")
                with c3:
                    if st.button("멤버 추가", key=f"add_btn_{g['group_name']}_{idx}"):
                        if add_user and add_user != "선택 없음":
                            g["members"].append(add_user)
                            save_json(GROUPS_FILE, groups)
                            st.success(f"{add_user} 님을 추가했습니다.")
                            st.rerun()
                if st.button(f"그룹 나가기 ({g['group_name']})", key=f"leave_{g['group_name']}_{idx}"):
                    g["members"].remove(username)
                    if len(g["members"]) == 0:
                        groups["groups"].remove(g)
                    save_json(GROUPS_FILE, groups)
                    st.success(f"'{g['group_name']}' 그룹에서 나갔습니다.")
                    st.rerun()
        else:
            st.info("아직 속한 그룹이 없습니다. 위에서 새 그룹을 만들어보세요.")

            st.info("아직 속한 그룹이 없습니다. 위에서 새 그룹을 만들어보세요.")

