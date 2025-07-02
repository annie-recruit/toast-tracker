#!/usr/bin/env python
"""
🍞 토스트 트래커 (Toast Tracker)
Notion 기반 AI 생산성 추적기

사용 방법:
1. 최초 실행: python start.py
2. 설정창에서 Notion 토큰, DB ID, OpenAI API 키 입력
3. 자동으로 메인 앱 실행됨
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """필요 패키지 설치 확인"""
    required_packages = [
        'customtkinter',
        'requests', 
        'notion_client',
        'openai',
        'pandas',
        'matplotlib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 누락된 패키지가 있습니다:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n📦 다음 명령어로 설치해주세요:")
        print("pip install -r requirements.txt")
        input("\n설치 후 엔터키를 누르세요...")
        return False
    
    return True

def main():
    print("🍞 토스트 트래커를 시작합니다...")
    
    # 패키지 확인
    if not check_requirements():
        sys.exit(1)
    
    # .env 파일 존재 확인
    if not Path('.env').exists():
        print("🔧 초기 설정이 필요합니다. 설정창을 실행합니다...")
        try:
            subprocess.run(['python', 'setup_config.py'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 설정창 실행 오류: {e}")
            input("엔터키를 눌러 종료...")
            sys.exit(1)
    else:
        print("✅ 설정 파일을 발견했습니다. 메인 앱을 실행합니다...")
        try:
            subprocess.run(['python', 'toast_tracker.py'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 앱 실행 오류: {e}")
            input("엔터키를 눌러 종료...")
            sys.exit(1)

if __name__ == "__main__":
    main() 