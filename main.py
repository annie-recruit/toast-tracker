import os
import sys

print("=" * 60)
print(" Notion 업무 생산성 트래커 v1.0")
print("=" * 60)

print("\n 시스템 체크:")

# Python 버전 체크
print(f" Python {sys.version}")

# 패키지 체크
packages = [
    'requests', 'notion_client', 'openai', 'tkinter', 
    'sqlite3', 'win10toast', 'pygame'
]

for package in packages:
    try:
        if package == 'notion_client':
            import notion_client
        elif package == 'win10toast':
            import win10toast
        elif package == 'tkinter':
            import tkinter
        elif package == 'sqlite3':
            import sqlite3
        else:
            __import__(package)
        print(f" {package}")
    except ImportError:
        print(f" {package} - 설치 필요")

# 설정 파일 체크
print(f"\n 파일 상태:")
print(f" .env 파일: {os.path.exists('.env')}")

# 간단한 데이터베이스 테스트
try:
    import sqlite3
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)')
    conn.close()
    os.remove('test.db')
    print(" SQLite 데이터베이스: 정상")
except Exception as e:
    print(f" SQLite 데이터베이스: {e}")

# 알림 테스트
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    print(" Windows 알림: 사용 가능")
    
    print("\n 테스트 알림을 전송합니다...")
    toaster.show_toast(
        "Notion 생산성 트래커",
        "시스템이 정상 작동합니다! ",
        duration=5,
        threaded=True
    )
    print("   (우측 하단에 알림이 표시됩니다)")
    
except Exception as e:
    print(f" Windows 알림: {e}")

print("\n" + "=" * 60)
print(" 다음 단계:")
print("1. .env 파일에 API 키를 설정하세요:")
print("   - NOTION_TOKEN=your_token_here")
print("   - NOTION_DATABASE_ID=your_database_id")
print("   - OPENAI_API_KEY=your_openai_key")
print("")
print("2. 노션에서 업무 데이터베이스를 생성하세요:")
print("   - Task (제목), Date (날짜), Time (날짜+시간)")
print("   - Duration (숫자), Priority (선택), Status (선택)")
print("")
print("3. 프로그램을 실행하세요:")
print("   python main.py --gui    # GUI 버전")
print("   python main.py --demo   # 데모 모드")
print("=" * 60)

# 명령행 인수 처리
if len(sys.argv) > 1:
    if '--demo' in sys.argv:
        print("\n 데모 모드 시작...")
        print("(실제 기능은 API 키 설정 후 사용 가능)")
        
        # 가상 데이터로 데모
        demo_tasks = [
            {"title": "회의 준비", "time": "09:00", "duration": 30},
            {"title": "보고서 작성", "time": "14:00", "duration": 120},
            {"title": "이메일 확인", "time": "16:30", "duration": 20}
        ]
        
        print("\n 오늘의 데모 업무:")
        for i, task in enumerate(demo_tasks, 1):
            print(f"{i}. {task['title']} - {task['time']} ({task['duration']}분)")
        
        print("\n 실제 사용을 위해서는 .env 파일을 설정하세요!")
        
    elif '--gui' in sys.argv:
        print("\n GUI 모드 준비 중...")
        print("GUI 기능은 모든 설정이 완료된 후 사용 가능합니다.")
        print("현재는 데모 모드를 사용해보세요: python main.py --demo")
