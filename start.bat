@echo off
title 토스트 트래커 실행기
echo.
echo 🍞 토스트 트래커를 시작합니다...
echo.

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo 📥 https://python.org 에서 Python을 설치해주세요.
    pause
    exit /b 1
)

REM Python으로 start.py 실행
python start.py

REM 종료 시 대기
if errorlevel 1 (
    echo.
    echo ❌ 실행 중 오류가 발생했습니다.
    pause
) 