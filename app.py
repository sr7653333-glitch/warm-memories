# app.py — 하루 추억 캘린더 (iframe 사용 안함 / 날짜 클릭 100% 동작)
# 요구 기능:
# - 로그인/회원가입(해시 저장) + 세션 복원
# - 역할: 보낸이(모니터링/맞춤 질문 생성), 받는이(자가진단)
# - 달력(버튼 기반) + 날짜 클릭 시 모달로 큰 화면 표시
# - 날짜별 꾸미기(배경색/라운드/스티커) 저장 및 반영
# - 그룹 생성(사용자 기준 중복 이름/멤버 구성 방지), 멤버 추가/나가기

import streamlit as st
import os
import json
import hashlib
import base64
import calendar
from datetime import datetime

# -------------------- 기본 설정/폴더 --------------------
st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)
os.makedirs("accounts/memories", exist_ok=True)
os.makedirs("accounts/decos", exist_ok=True)

# -------------------- 유틸/저장/불러오기 --------------------
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

def mem_path(user): return f"accounts/memories/{user}.json"
def load_mems(user): return load_json(mem_path(user), {"memories": {}})
def save_mems(user, data): save_json(mem_path(user), data)

def deco_path(user): return f"accounts/decos/{user}.json"
def load_decos(user): return load_json(deco_path(user), {"decos": {}})
def save_decos(user, data): save_json(deco_path(user), data)

# -------------------- 데이터 파일 --------------------
ACCOUNTS_FILE  = "accounts/accounts.json"
GROUPS_FILE    = "accounts/groups.json"
SESSION_FILE   = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"
QUESTIONS_FILE = "accounts/questions.json"

accounts       = load_json(ACCOUNTS_FILE, {"users": []})
groups         = load_json(GROUPS_FILE, {"groups": []})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records": []})
questions_data = load_json(QUESTIONS_FILE, {"custom_questions": []})

# 비밀번호 평문 → 해시 마이그레이션
changed = False
for u in accounts["users"]:
    if not is_sha256_hex(u.get("password", "")):
        u["password"] = hash_pw(u.get("password", ""))
        changed = True
if changed:
    save_json(ACCOUNTS_FILE, accounts)

# -------------------- 세션 기본값 --------------------
for k, v in [
    ("logged_in", False),
    ("username", ""),
    ("role", ""),
    ("selected_date", None),
    ("theme", "기본"),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------- 이전 세션 복원 --------------------
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    s = load_json(SESSION_FILE, {})
    if s:
        st.session_state.logged_in = True
        st.session_state.username = s.get("username", "")
        st.session_state.role = s.get("role", "")

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
                st.session_state.logged_in = True
                st.session_state.username = uid
                st.session_state.role = user["role"]
                save_json(SESSION_FILE, {"username": uid, "role": user["role"]})
                st.rerun()
            else:
                st.warning("아이디 또는 비밀번호가 올바르지 않습니다.")

# -------------------- 로그인 후 메인 --------------------
else:
    username = st.session_state.username
    role = st.session_state.role

    # 사이드바
    st.sidebar.markdown(f"**{username}님 ({role})**")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.selected_date = None
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

    # 테마
    st.sidebar.markdown("### 🎨 달력 테마")
    theme_colors = {"기본": "#f0f2f6", "다크": "#1e1e1e", "핑크": "#ffe4ec", "미니멀": "#ffffff"}
    st.session_state.theme = st.sidebar.selectbox("테마 선택", list(theme_colors.keys()))
    st.markdown(f"<style>.stApp{{background-color:{theme_colors[st.session_state.theme]};}}</style>", unsafe_allow_html=True)

    STICKER_PRESETS = ["🌸", "🌼", "🌟", "💖", "✨", "🍀", "🧸", "🎀", "📸", "☕", "🍰", "🎈", "📝", "👣", "🎵"]

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

            # 주 단위 그리드 (Native Streamlit만 사용 → iframe 문제 없음)
            cal_mat = calendar.monthcalendar(int(year), int(month))

            # 간단한 스타일
            st.markdown(
                """
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
                """,
                unsafe_allow_html=True
            )

            for week in cal_mat:
                cols = st.columns(7, gap="small")
                for i, day in enumerate(week):
                    with cols[i]:
                        if day == 0:
                            st.write("")  # 빈 칸
                            continue

                        date_key = f"{int(year)}-{int(month):02d}-{day:02d}"
                        dconf = decos["decos"].get(date_key, {})
                        bg = dconf.get("bg", "#ffffff")
                        radius = dconf.get("radius", "12px")
                        stickers = " ".join(dconf.get("stickers", []))

                        # 카드(꾸미기 반영)
                        st.markdown(
                            f"<div class='cal-card' style='background:{bg}; border-radius:{radius};'>"
                            f"<div class='cal-day'>{day}</div>"
                            f"<div class='cal-stickers'>{stickers}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        # 날짜 클릭(이벤트는 버튼으로만 처리 → 절대 중첩 렌더 안됨)
                        if st.button("열기", key=f"open_{date_key}", use_container_width=True):
                            st.session_state.selected_date = date_key
                            st.rerun()

        # 꾸미기 패널
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
                    radius = st.selectbox("보더 라운드", r_choices, index=r_choices.index(current_radius))
                    picked = st.multiselect("스티커(이모지)", STICKER_PRESETS, default=d.get("stickers", []))
                    extra = st.text_input("추가 이모지/텍스트", value="")
                    if extra and extra not in picked:
                        picked.append(extra)

                    cA, cB, cC = st.columns(3)
                    with cA:
                        if st.button("🗂 꾸미기 저장"):
                            decos["decos"][date_key] = {"bg": bg, "radius": radius, "stickers": picked}
                            save_decos(username, decos)
                            st.success("저장되었습니다! 달력/모달에 즉시 반영됩니다.")
                            st.rerun()
                    with cB:
                        if st.button("♻️ 이 날짜 초기화"):
                            if date_key in decos["decos"]:
                                del decos["decos"][date_key]
                                save_decos(username, decos)
                                st.info("초기화했습니다.")
                                st.rerun()
                    with cC:
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

        # 날짜 선택 시 모달 열기 (URL/iframe 사용 안함)
        if st.session_state.get("selected_date"):
            sel = st.session_state["selected_date"]
            with st.modal(f"📅 {sel}"):
                st.subheader("📔 추억")
                mem = load_mems(username)["memories"].get(sel, [])
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
                            data["memories"].setdefault(sel, []).append(
                                {"title": t, "text": c, "ts": datetime.now().isoformat(timespec="seconds")}
                            )
                            save_mems(username, data)
                            st.success("추억이 저장되었습니다!")
                            st.rerun()

                if st.button("닫기"):
                    st.session_state.selected_date = None
                    st.rerun()

    # -------------------- 자가진단 (받는이) --------------------
    if menu == "자가진단" and role == "받는이":
        st.title("📝 오늘의 자가진단")
        today = datetime.now().strftime("%Y-%m-%d")
        done = any(r.get("username") == username and r.get("date") == today for r in diagnosis_data["records"])

        # 기본 질문 5개
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
                if isinstance(q[1], int):  # scale
                    label, mn, mx, df, keyname = q
                    answers[keyname] = st.slider(label, mn, mx, df)
                else:  # choice
                    label, options, default, keyname = q
                    answers[keyname] = st.selectbox(label, options, index=options.index(default))

            # 보낸이가 만든 맞춤 질문 불러오기
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
        # 맞춤 질문 생성
        with st.form("custom_q_form"):
            q_text = st.text_input("질문 내용 (예: '물을 충분히 드셨나요?')")
            q_type = st.selectbox("질문 유형", ["yesno", "scale", "choice", "text"], index=0)
            colA, colB, colC = st.columns(3)
            with colA:
                minv = st.number_input("scale 최소값", value=1, step=1)
            with colB:
                maxv = st.number_input("scale 최대값", value=5, step=1)
            with colC:
                dflt = st.number_input("scale 기본값", value=3, step=1)
            opts_txt = st.text_input("choice 옵션(쉼표로 구분)", value="아니오,예")
            d_idx = st.number_input("choice 기본 인덱스", value=0, step=1)

            # 타겟 선택
            my_groups = [g for g in groups["groups"] if username in g["members"]]
            receivers = sorted({m for g in my_groups for m in g["members"] if m != username})
            targets = st.multiselect("질문을 받을 받는이", receivers)

            submit_q = st.form_submit_button("질문 생성")
            if submit_q:
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


   
