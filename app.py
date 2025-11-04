
""" 
Streamlit 앱: 하루 한 번 사진·음성·편지로 따뜻한 추억 공유
환경변수 예시(.env 또는 Streamlit secrets):
FIREBASE_SERVICE_ACCOUNT=c
FIREBASE_BUCKET=b
LOCAL_SAVE_DIR=shared_memories
"""

import streamlit as st
from datetime import datetime
import os
from pathlib import Path
import uuid
from PIL import Image
import io
import qrcode
from dotenv import load_dotenv

# Firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

load_dotenv()

# 설정 (환경변수 또는 Streamlit secrets 사용 가능)
SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT", "c")
FIREBASE_BUCKET = os.getenv("FIREBASE_BUCKET", "b")
LOCAL_SAVE_DIR = os.getenv("LOCAL_SAVE_DIR", "shared_memories")

# 로컬 저장 폴더 생성
Path(LOCAL_SAVE_DIR).mkdir(parents=True, exist_ok=True)

# Firebase 초기화 (중복 초기화 방지)
def init_firebase():
    if not firebase_admin._apps:
        if not Path(SERVICE_ACCOUNT_PATH).exists():
            st.warning("Firebase 서비스 계정 파일이 존재하지 않습니다. 로컬에서 업로드 또는 .env 설정을 확인하세요.")
            return None
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        try:
            firebase_admin.initialize_app(cred, {
                'storageBucket': FIREBASE_BUCKET
            })
        except Exception as e:
            st.error(f"Firebase 초기화 실패: {e}")
            return None
    return storage.bucket()

bucket = init_firebase()

st.set_page_config(page_title="따뜻한 추억 공유앱", layout="centered")
st.title("하루 한 번, 따뜻한 추억 공유하기")
st.write("사진·음성·편지로 가족과 따뜻한 순간을 나누세요. 로컬 저장 및 Firebase Storage 업로드 지원")

# 입력 폼
with st.form("memory_form"):
    st.subheader("새 추억 추가")
    name = st.text_input("보낸 사람 이름", max_chars=50)
    relation = st.text_input("관계(예: 손주, 자녀)")
    date = st.date_input("기억 날짜", value=datetime.today())
    time = st.time_input("시간", value=datetime.now().time())
    photo = st.file_uploader("사진 업로드 (jpg, png)", type=["jpg","jpeg","png"])
    audio = st.file_uploader("음성 메시지 업로드 (mp3, wav)", type=["mp3","wav"])
    letter = st.text_area("편지 내용", height=150)
    private = st.checkbox("비공개(로컬만 저장)", value=False)
    submitted = st.form_submit_button("저장 및 공유하기")

# 저장 및 업로드 함수
def save_locally(data_bytes, filename):
    path = Path(LOCAL_SAVE_DIR) / filename
    with open(path, "wb") as f:
        f.write(data_bytes)
    return str(path)

def upload_to_firebase(local_path, dest_path):
    if not bucket:
        st.info("Firebase 버킷이 초기화되지 않았습니다. 로컬에만 저장됩니다.")
        return None
    try:
        blob = bucket.blob(dest_path)
        blob.upload_from_filename(local_path)
        try:
            blob.make_public()
            return blob.public_url
        except Exception:
            return f"gs://{}/{}".format(FIREBASE_BUCKET, dest_path)
    except Exception as e:
        st.error(f"Firebase 업로드 실패: {e}")
        return None

# 제출 처리
if submitted:
    if not name:
        st.error("보낸 사람 이름을 입력해주세요.")
    else:
        uid = uuid.uuid4().hex[:10]
        base_folder = f"memory_{datetime.now().strftime('%Y%m%d')}_{uid}"
        meta = {
            'id': uid,
            'name': name,
            'relation': relation,
            'datetime': f"{date} {time}",
            'letter': letter,
            'local_files': [],
            'uploaded_urls': []
        }

        # 사진 저장
        if photo:
            photo_bytes = photo.read()
            photo_fname = f"{base_folder}/photo_{photo.name}"
            local_photo_path = save_locally(photo_bytes, photo_fname.replace('/','_'))
            meta['local_files'].append(local_photo_path)
            if not private:
                public_url = upload_to_firebase(local_photo_path, photo_fname)
                if public_url:
                    meta['uploaded_urls'].append({'type':'photo','url':public_url})

        # 오디오 저장
        if audio:
            audio_bytes = audio.read()
            audio_fname = f"{base_folder}/audio_{audio.name}"
            local_audio_path = save_locally(audio_bytes, audio_fname.replace('/','_'))
            meta['local_files'].append(local_audio_path)
            if not private:
                public_url = upload_to_firebase(local_audio_path, audio_fname)
                if public_url:
                    meta['uploaded_urls'].append({'type':'audio','url':public_url})

        # 편지 저장 (텍스트 파일)
        if letter:
            letter_bytes = letter.encode('utf-8')
            letter_fname = f"{base_folder}/letter_{name}_{uid}.txt"
            local_letter_path = save_locally(letter_bytes, letter_fname.replace('/','_'))
            meta['local_files'].append(local_letter_path)
            if not private:
                public_url = upload_to_firebase(local_letter_path, letter_fname)
                if public_url:
                    meta['uploaded_urls'].append({'type':'letter','url':public_url})

        # 메타데이터 저장
        import json
        meta_fname = f"{base_folder}/meta_{uid}.json"
        local_meta_path = save_locally(json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8'), meta_fname.replace('/','_'))
        st.success("저장 완료")
        st.write("로컬 저장 파일 목록:")
        for fpath in meta['local_files']:
            st.write(f"- {fpath}")

        if meta['uploaded_urls']:
            st.write("업로드된 공개 URL:")
            for item in meta['uploaded_urls']:
                st.write(f"- {item['type']}: {item['url']}")

        # QR 코드 생성: 공유 링크(가장 먼저 업로드된 파일 사용)
        share_url = None
        if meta['uploaded_urls']:
            share_url = meta['uploaded_urls'][0]['url']
        else:
            share_url = None

        if share_url:
            qr = qrcode.make(share_url)
            buf = io.BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="공유용 QR 코드")
            st.markdown(f"**공유 링크:** {share_url}")
        else:
            st.info("공개 업로드 URL이 없습니다. 로컬에만 저장되었습니다.")

# 간단 갤러리(로컬 폴더에서 사진 불러오기)
st.markdown('---')
st.subheader("저장된 추억 갤러리 (로컬)")
files = list(Path(LOCAL_SAVE_DIR).glob("**/*"))
image_files = [f for f in files if f.suffix.lower() in ['.jpg','.jpeg','.png']]
if image_files:
    cols = st.columns(3)
    for i, imgp in enumerate(image_files):
        try:
            img = Image.open(imgp)
            cols[i%3].image(img, caption=imgp.name, use_column_width=True)
        except Exception:
            continue
else:
    st.write("저장된 사진이 없습니다.")

st.info("앱 설정: FIREBASE_SERVICE_ACCOUNT, FIREBASE_BUCKET, LOCAL_SAVE_DIR 을 환경변수로 설정하세요. Streamlit Cloud 사용 시 secrets에 서비스계정 JSON 내용을 넣고 파일로 저장해 초기화할 수 있습니다.")

if st.checkbox("(개발용) 환경 정보 보기"):
    st.write({
        'SERVICE_ACCOUNT_PATH': SERVICE_ACCOUNT_PATH,
        'FIREBASE_BUCKET': FIREBASE_BUCKET,
        'LOCAL_SAVE_DIR': LOCAL_SAVE_DIR
    })
