
# 배포 가이드 (Streamlit Community Cloud)

1. 프로젝트를 GitHub에 업로드하세요.
2. Streamlit Community Cloud에서 'New app'을 클릭하고 GitHub 저장소를 연결하세요.
3. `Settings > Secrets`에 서비스계정 JSON을 넣습니다.
   - Key: `FIREBASE_SERVICE_ACCOUNT`
   - Value: (서비스계정 JSON 파일 전체 내용) — **주의: 민감한 정보입니다.**
4. `Secrets`에 `FIREBASE_BUCKET` 값을 추가하세요 (값: b).
5. App entry point를 `app.py`로 설정한 뒤 배포하세요.
