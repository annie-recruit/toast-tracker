# 🍞 토스트 트래커 (Toast Tracker)

Notion 기반 AI 생산성 추적 및 분석 도구

![토스트 트래커](https://img.shields.io/badge/Toast%20Tracker-v1.0-orange?style=for-the-badge&logo=notion)

## ✨ 주요 기능

### 📊 생산성 추적
- **실시간 작업 시간 측정**: 시작/중지 버튼으로 간편한 시간 기록
- **Notion 데이터베이스 연동**: 자동으로 작업 내용을 Notion에 저장
- **🍅 포모도로 타이머**: 25분 집중 + 5분 휴식 사이클

### 🤖 AI 기반 분석
- **일일 생산성 피드백**: OpenAI가 분석한 맞춤형 조언
- **생산성 예측**: 패턴 분석을 통한 향후 성과 예측
- **목표 설정 및 추적**: 색상으로 구분된 진행률 표시

### 📈 시각적 대시보드
- **시간대별 집중도 히트맵**: 언제 가장 집중하는지 한눈에 파악
- **카테고리별 작업 분포**: 파이차트로 작업 비중 확인
- **주간 트렌드 분석**: 생산성 변화 추이 그래프
- **AI 피드백 탭**: 개인화된 생산성 조언

## 🚀 설치 및 실행

### 1. 요구사항
- Python 3.8 이상
- Notion 계정 및 데이터베이스
- OpenAI API 키

### 2. 설치
```bash
# 저장소 클론
git clone https://github.com/yourusername/toast-tracker.git
cd toast-tracker

# 패키지 설치
pip install -r requirements.txt
```

### 3. 실행
```bash
python start.py
```

## ⚙️ 초기 설정

### Notion 설정
1. **Integration 생성**
   - [Notion Integrations](https://www.notion.so/my-integrations) 접속
   - "New integration" 클릭
   - 이름 입력 후 토큰 복사

2. **데이터베이스 준비**
   - Notion에서 새 데이터베이스 생성
   - 필수 속성 추가:
     - `Task` (제목/Title)
     - `Type` (선택/Select): Work, Study, Personal 등
     - `Time` (날짜/Date)
     - `Priority` (선택/Select): High, Medium, Low
     - `Status` (선택/Select): Todo, In Progress, Done
   - Integration을 데이터베이스에 연결

3. **Database ID 확인**
   - 데이터베이스 URL에서 ID 추출
   - 예: `notion.so/workspace/[DATABASE_ID]?v=...`

### OpenAI 설정
1. [OpenAI API Keys](https://platform.openai.com/api-keys) 접속
2. "Create new secret key" 클릭
3. 생성된 키 복사

### 첫 실행
1. `python start.py` 실행
2. 설정창에서 위에서 준비한 정보 입력:
   - Notion Integration Token
   - Database ID
   - OpenAI API Key
3. "설정 저장 & 시작" 클릭

## 🎯 사용법

### 기본 작업 추적
1. **작업 시작**: "시작" 버튼 클릭 후 작업명 입력
2. **작업 완료**: "완료" 버튼으로 시간 기록 및 Notion 저장
3. **포모도로**: 체크박스 활성화 시 25분 타이머 자동 실행

### AI 기능 활용
- **📊 일일 피드백**: 하루 작업을 AI가 분석하여 조언 제공
- **📈 통계 보기**: 시각적 대시보드로 생산성 패턴 확인
- **🎯 목표 설정**: 주간/월간 목표 설정 및 진행률 추적
- **🔮 생산성 예측**: 과거 데이터 기반 미래 성과 예측

### 작업 관리
- **작업 목록**: 실시간으로 Notion과 동기화
- **상태 변경**: 테이블에서 직접 진행 상황 업데이트
- **우선순위**: High/Medium/Low 단계별 관리

## 📱 주요 화면

### 메인 화면
- 🍞 토스트 아이콘과 함께 하는 직관적인 인터페이스
- 실시간 작업 타이머와 Notion 연동 상태 표시
- 🍅 포모도로 모드 토글

### 통계 대시보드
- **Hourly Focus Heatmap**: 시간대별 집중도 시각화
- **Category Distribution**: 작업 유형별 시간 분배
- **Weekly Trend**: 7일간 생산성 변화 추이
- **AI Feedback**: 개인화된 생산성 분석 및 조언

## 🛠️ 기술 스택

- **UI Framework**: CustomTkinter (Modern UI)
- **Database**: SQLite (로컬 데이터 저장)
- **API Integration**: 
  - Notion API (notion-client)
  - OpenAI API (openai)
- **Data Analysis**: pandas, matplotlib, seaborn
- **Notifications**: plyer, toastnotifier

## 📂 파일 구조

```
toast-tracker/
├── start.py              # 진입점
├── setup_config.py       # 초기 설정 GUI
├── toast_tracker.py      # 메인 애플리케이션
├── requirements.txt      # 패키지 의존성
├── README.md            # 이 파일
├── .env                 # 환경설정 (자동생성)
├── productivity_data.db # SQLite 데이터베이스 (자동생성)
├── toast.png           # 앱 아이콘
└── tomato.png          # 포모도로 아이콘
```

## 🔐 보안 및 개인정보

- 모든 API 키는 로컬 `.env` 파일에 저장
- 개인 데이터는 사용자 컴퓨터에만 보관
- Notion과 OpenAI는 공식 API를 통해서만 통신

## 🐛 문제 해결

### 자주 발생하는 오류

1. **"Notion API 연결 실패"**
   - Integration이 데이터베이스에 연결되었는지 확인
   - 토큰이 올바른지 재확인

2. **"OpenAI API 오류"**
   - API 키가 유효한지 확인
   - 계정에 충분한 크레딧이 있는지 확인

3. **"패키지 설치 오류"**
   - Python 버전 확인 (3.8+ 필요)
   - `pip install --upgrade pip` 실행 후 재시도

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

- 📧 연락처: rkdhs326@gmail.com

---

**🍞 완벽하게 구워진 토스트처럼, 당신의 생산성도 완벽하게 관리하세요!**
