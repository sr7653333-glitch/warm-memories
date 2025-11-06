# app.py
import streamlit as st
import os
import json
import hashlib
from datetime import datetime
import calendar
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# =========================
# 기본 설정 & 폴더 준비
# =========================
st.set_page_config(page_title="하루 추억 캘린더", layout="wide")
os.makedirs("accounts", exist_ok=True)
os.makedirs("accounts/memories", exist_ok=True)
os.makedirs("assets", exist_ok=True)

# =========================
# 공통 유틸
# =========================
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def is_sha256_hex(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s)

# 파일 경로
ACCOUNTS_FILE  = "accounts/accounts.json"
GROUPS_FILE    = "accounts/groups.json"
SESSION_FILE   = "accounts/sessions.json"
DIAGNOSIS_FILE = "accounts/diagnosis.json"
QUESTIONS_FILE = "accounts/questions.json"   # 보낸이 맞춤 질문
# 구조 예시: {"custom_questions":[{"id":"q_...","creator":"보낸이ID","targets":["받는이ID1"],"text":"물은 6컵?","type":"yesno","opts":[]}]}

# 데이터 로드
accounts       = load_json(ACCOUNTS_FILE, {"users": []})
groups         = load_json(GROUPS_FILE, {"groups": []})
diagnosis_data = load_json(DIAGNOSIS_FILE, {"records": []})
questions_data = load_json(QUESTIONS_FILE, {"custom_questions": []})

# 비밀번호 혼재 자동 정리
changed = False
for u in accounts["users"]:
    pw = u.get("password", "")
    if not is_sha256_hex(pw):
        u["password"] = hash_pw(pw)
        changed = True
if changed:
    save_json(ACCOUNTS_FILE, accounts)

# 메모 파일 유틸
def mem_path(username: str) -> str:
    return f"accounts/memories/{username}.json"

def load_mems(username: str):
    return load_json(mem_path(username), {"memories": {}})

def save_mems(username: str, data):
    save_json(mem_path(username), data)

# =========================
# 어르신 공통 기본 5문항
# =========================
def get_default_questions():
    return [
        {"id":"q_mood","label":"오늘 마음 상태는 어떠세요? (1=매우 안 좋음, 5=매우 좋음)","type":"scale","min":1,"max":5,"default":3},
        {"id":"q_sleep","label":"어젯밤 수면의 질은 어떠셨어요? (1=매우 나쁨, 5=매우 좋음)","type":"scale","min":1,"max":5,"default":3},
        {"id":"q_pain_score","label":"지금 통증 강도는 어느 정도인가요? (0=없음, 10=매우 심함)","type":"scale","min":0,"max":10,"default":0},
        {"id":"q_appetite","label":"오늘 식사와 수분 섭취는 괜찮으셨어요?","type":"choice","options":["부족했어요","보통이에요","좋았어요"],"default":"보통이에요"},
        {"id":"q_activity","label":"오늘 움직임/걷기는 어떠셨어요? (1=매우 힘듦, 5=매우 수월)","type":"scale","min":1,"max":5,"default":3},
    ]

# =========================
# 전신 통증 선택 위젯
# =========================
def pain_selector(image_path: str, key: str = "painmap"):
    """
    전신 이미지 위 클릭 → 통증 좌표 + 대략 부위 라벨 반환
    이미지 해상도에 맞게 regions 히트박스 좌표를 조정 가능.
    """
    if not os.path.exists(image_path):
        st.warning(f"전신 이미지가 없어요: {image_path} (assets/body_front.png, assets/body_back.png 준비)")
        return {"points": [], "regions": []}

    st.markdown("#### 🧍 아픈 부위를 클릭해주세요")
    img = Image.open(image_path)
    cw, ch = img.size

    canvas = st_canvas(
        stroke_width=3,
        stroke_color="#ff0000",
        background_image=img,
        update_streamlit=True,
        height=ch,
        width=cw,
        drawing_mode="point",
        point_display_radius=10,  # 어르신용 크게
        key=key,
    )

    # 간단한 히트박스 (600x1200 근방 기준 예시)
    regions = [
        (250,  60, 350, 160, "머리/목"),
        (220, 160, 380, 300, "어깨/가슴"),
        (220, 300, 380, 420, "복부"),
        (230, 420, 370, 520, "골반/허리"),
        (120, 190, 220, 420, "왼팔"),
        (380, 190, 480, 420, "오른팔"),
        (200, 520, 280, 900, "왼다리"),
        (320, 520, 400, 900, "오른다리"),
        (260, 900, 340, 1150, "발/발목"),
    ]

    def match_region(x, y):
        for (x1, y1, x2, y2, label) in regions:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return label
        return "기타"

    points, labels = [], []
    if canvas and canvas.json_data is not None:
        for obj in canvas.json_data.get("objects", []):
            if obj.get("type") == "circle":
                x = obj["left"] + obj.get("radius", 0)
                y = obj["top"] + obj.get("radius", 0)
                points.append((int(x), int(y)))
                labels.append(match_region(x, y))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("마지막 점 지우기", key=f"{key}_undo") and (points or labels):
            st.session_state[key] = None
            st.rerun()
    with col2:
        if st.button("모두 지우기", key=f"{key}_clear") and (points or labels):
            st.session_state[key] = None
            st.rerun()

    if labels:
        st.success(f"선택된 부위: {', '.join(labels)}")

    return {"points": points, "regions": labels}

# =========================
# 인증 세션 기본값
# =========================
for key, default in [
    ("logged_in", False), ("username", ""), ("role", ""),
    ("selected_date", None), ("login_cookie", None), ("theme", "기본")
]:
    if key not in st.session_state:
        st.session_state[key] = default

# 세션 복원
if not st.session_state.logged_in and os.path.exists(SESSION_FILE):
    session = load_json(SESSION_FILE, {})
    if session:
        st.session_state.logged_in = True
        st.session_state.username = session["username"]
        st.session_state.role = session["role"]
        st.session_state.login_cookie = session

# =========================
# 로그인 / 회원가입
# =========================
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
                (u for u in accounts["users"]
                 if u["username"] == in_username
                 and (u["password"] == in_hash or u["password"] == password)),
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

# =========================
# 로그인 후 화면
# =========================
else:
    username = st.session_state.username
    role = st.session_state.role

    # 사이드바 공통
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

    # 메뉴: 달력(최상위) → 자가진단 → 모니터링(보낸이만) → 그룹 편집
    menu_items = ["달력", "자가진단"]
    if role == "보낸이":
        menu_items.append("자가진단 모니터링")
    menu_items.append("그룹 편집")
    menu = st.sidebar.radio("메뉴", menu_items, index=0)

    # 테마
    st.sidebar.markdown("### 🎨 달력 테마")
    st.session_state.theme = st.sidebar.selectbox("테마 선택", ["기본", "다크", "핑크", "미니멀"])
    theme_colors = {"기본":"#f0f2f6","다크":"#1e1e1e","핑크":"#ffe4ec","미니멀":"#ffffff"}
    st.markdown(f"<style>.stApp{{background-color:{theme_colors[st.session_state.theme]};}}</style>", unsafe_allow_html=True)

    # -----------------------------
    # 달력
    # -----------------------------
    if menu == "달력":
        st.title("🗓 하루 추억 달력")
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
                        new_list.append({"title": title, "text": text, "ts": datetime.now().isoformat(timespec="seconds")})
                        mems["memories"][st.session_state.selected_date] = new_list
                        save_mems(username, mems)
                        st.success("추억이 저장되었습니다!")
                        st.rerun()

    # -----------------------------
    # 자가진단 (받는이)
    # -----------------------------
    if menu == "자가진단" and role == "받는이":
        st.title("📝 오늘의 자가진단")
        today = datetime.now().strftime("%Y-%m-%d")

        already_done = any(r.get("username")==username and r.get("date")==today for r in diagnosis_data["records"])
        with st.expander("어르신 건강 기본 질문 5가지", expanded=not already_done):
            dq = get_default_questions()
            answers = {}

            # 스케일/선택 UI
            for q in dq:
                if q["type"] == "scale":
                    answers[q["id"]] = st.slider(q["label"], q["min"], q["max"], q["default"])
                elif q["type"] == "choice":
                    answers[q["id"]] = st.selectbox(q["label"], q["options"], index=q["options"].index(q["default"]))

            # 보낸이가 추가한 맞춤 질문(타겟에 본인이 포함된 것만)
            st.markdown("### 📌 맞춤 질문")
            my_custom = [q for q in questions_data.get("custom_questions", []) if username in q.get("targets", [])]
            custom_answers = {}
            if my_custom:
                for i, cq in enumerate(my_custom):
                    q_label = f"{cq['text']}  (작성자: {cq['creator']})"
                    qtype = cq.get("type", "text")
                    if qtype == "scale":
                        minv = int(cq.get("min", 1)); maxv = int(cq.get("max", 5)); default = int(cq.get("default", (minv+maxv)//2))
                        custom_answers[cq["id"]] = st.slider(q_label, minv, maxv, default, key=f"c_scale_{i}")
                    elif qtype == "yesno":
                        custom_answers[cq["id"]] = st.radio(q_label, ["예", "아니오"], horizontal=True, key=f"c_yesno_{i}")
                    elif qtype == "choice":
                        opts = cq.get("opts", ["아니오","예"])
                        idx = int(cq.get("default_index", 0))
                        idx = max(0, min(idx, len(opts)-1))
                        custom_answers[cq["id"]] = st.selectbox(q_label, opts, index=idx, key=f"c_choice_{i}")
                    else:
                        custom_answers[cq["id"]] = st.text_input(q_label, key=f"c_text_{i}")
            else:
                st.info("받는이에게 배포된 맞춤 질문이 없습니다.")

            # 통증 부위 선택 (앞/뒤)
            st.markdown("### 🧍 통증 위치 표시")
            view = st.radio("신체 방향", ["앞", "뒤"], horizontal=True)
            img_path = "assets/body_front.png" if view == "앞" else "assets/body_back.png"
            pain = pain_selector(img_path, key=f"pain_{view}")

            memo = st.text_area("기록하고 싶은 메모가 있으면 남겨주세요.", "")

            if already_done:
                st.success("✅ 오늘은 이미 자가진단을 완료하셨어요.")
            if st.button("자가진단 제출", disabled=already_done):
                record = {
                    "username": username,
                    "date": today,
                    "answers": {
                        **answers,
                        **{f"custom:{k}": v for k, v in custom_answers.items()},
                        "pain_regions": pain["regions"],
                        "pain_points": pain["points"],
                    },
                    "memo": memo
                }
                diagnosis_data["records"].append(record)
                save_json(DIAGNOSIS_FILE, diagnosis_data)
                st.success("오늘의 자가진단이 저장되었습니다!")
                st.rerun()

    # -----------------------------
    # 자가진단 모니터링 (보낸이)
    # + 맞춤 질문 만들기/배포
    # -----------------------------
    if menu == "자가진단 모니터링" and role == "보낸이":
        st.title("👀 받는이 자가진단 모니터링")

        # 내가 속한 그룹의 받는이 목록
        my_groups = [g for g in groups["groups"] if username in g["members"]]
        receivers = sorted({m for g in my_groups for m in g["members"] if m != username})

        if receivers:
            # 최근 기록 테이블
            recent = [r for r in diagnosis_data["records"] if r["username"] in receivers]
            if recent:
                st.dataframe(
                    [{"날짜": r["date"], "아이디": r["username"], **(r.get("answers", {})), "메모": r.get("memo","")} for r in sorted(recent, key=lambda x:(x["date"], x["username"]), reverse=True)],
                    use_container_width=True
                )
            else:
                st.info("아직 자가진단 기록이 없습니다.")

            st.markdown("---")
            st.subheader("🛠 맞춤 질문 만들기 & 배포")

            with st.form("custom_q_form"):
                q_text = st.text_input("질문 내용 (예: '물을 충분히 드셨나요?')")
                q_type = st.selectbox("질문 유형", ["yesno", "scale", "choice", "text"], index=0)
                colA, colB, colC = st.columns(3)
                with colA:
                    minv = st.number_input("scale 최소값", value=1, step=1)
                with colB:
                    maxv = st.number_input("scale 최대값", value=5, step=1)
                with colC:
                    default_scale = st.number_input("scale 기본값", value=3, step=1)

                choice_opts = st.text_input("choice 옵션(쉼표로 구분)", value="아니오,예")
                default_idx = st.number_input("choice 기본 인덱스", value=0, step=1)

                targets = st.multiselect("질문을 받을 받는이(복수 선택)", receivers)

                submitted = st.form_submit_button("질문 생성")
                if submitted:
                    if not q_text.strip():
                        st.warning("질문 내용을 입력하세요.")
                    elif not targets:
                        st.warning("타겟 받는이를 선택하세요.")
                    else:
                        q_id = f"cq_{int(datetime.now().timestamp())}"
                        item = {
                            "id": q_id,
                            "creator": username,
                            "targets": targets,
                            "text": q_text.strip(),
                            "type": q_type
                        }
                        if q_type == "scale":
                            item.update({"min": int(minv), "max": int(maxv), "default": int(default_scale)})
                        elif q_type == "choice":
                            opts = [o.strip() for o in choice_opts.split(",") if o.strip()]
                            if not opts:
                                opts = ["아니오","예"]
                            item.update({"opts": opts, "default_index": int(default_idx)})
                        questions_data.setdefault("custom_questions", []).append(item)
                        save_json(QUESTIONS_FILE, questions_data)
                        st.success("맞춤 질문이 생성되어 배포되었습니다!")

            # 현재 배포된 질문 목록
            st.markdown("### 📋 내가 만든 질문")
            my_qs = [q for q in questions_data.get("custom_questions", []) if q.get("creator")==username]
            if my_qs:
                for q in sorted(my_qs, key=lambda x: x["id"], reverse=True):
                    st.markdown(f"- **{q['text']}**  *(유형: {q['type']}, 대상: {', '.join(q.get('targets', []))})*")
            else:
                st.info("아직 만든 질문이 없습니다.")
        else:
            st.warning("아직 연결된 받는이가 없습니다. ‘그룹 편집’에서 그룹을 만들어보세요.")

    # -----------------------------
    # 그룹 편집 (양쪽 공용)
    # -----------------------------
    if menu == "그룹 편집":
        st.title("✏️ 그룹 편집")
        my_groups = [g for g in groups["groups"] if username in g["members"]]

        with st.expander("➕ 새 그룹 만들기", expanded=not my_groups):
            new_name = st.text_input("그룹 이름")
            all_users = sorted([u["username"] for u in accounts["users"] if u["username"] != username])
            add_members = st.multiselect("멤버 추가", all_users)
            if st.button("그룹 생성"):
                # 내가 속한 그룹에서만 중복 검사(이름/멤버구성)
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
                    candidates = [u["username"] for u in accounts["users"] if u["username"] not in g["members"]]
                    add_user = st.selectbox(f"멤버 추가 ({g['group_name']})", ["선택 없음"] + candidates, key=f"add_{g['group_name']}")
                with col3:
                    if st.button("멤버 추가", key=f"add_btn_{g['group_name']}"):
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
