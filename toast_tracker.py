# Modern AI Scheduler Notion Tracker with Beautiful UI
import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
import tkinter as tk
import requests
import time
from datetime import datetime, timedelta
import winsound
from plyer import notification
import threading
import sqlite3
import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from PIL import Image, ImageTk

# 🎨 CustomTkinter 설정
ctk.set_appearance_mode("light")  # "dark" or "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class SchedulerNotionTracker:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title('토스트 트래커')
        self.root.geometry('950x750')  # 창 크기 조정
        
        # 기존 속성들
        self.token = ''
        self.db_id = ''
        self.openai_key = ''
        self.headers = {}
        self.tasks = []
        self.current_task = None
        self.start_time = None
        self.is_tracking = False
        self.notified_tasks = set()
        
        # 🍅 뽀모도로 관련 속성들
        self.pomodoro_mode = False
        self.pomodoro_duration = 25 * 60  # 25분
        self.break_duration = 5 * 60     # 5분
        self.pomodoro_count = 0
        self.is_break_time = False
        self.pomodoro_start = None
        
        # 📊 AI 분석 관련 속성들
        self.db_path = 'productivity_data.db'
        self.daily_stats = {}
        self.ai_feedback = ''
        self.current_task_id = None
        
        self.load_config()
        self.setup_ui()
        self.init_database()
        self.update_timer()
        self.start_scheduler()  # 🚨 핵심! 스케줄러 시작!
    
    def load_config(self):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('NOTION_TOKEN='):
                        self.token = line.split('=', 1)[1]
                    elif line.startswith('NOTION_DATABASE_ID='):
                        self.db_id = line.split('=', 1)[1]
                    elif line.startswith('OPENAI_API_KEY='):
                        self.openai_key = line.split('=', 1)[1]
            
            if self.token and self.db_id:
                self.headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json',
                    'Notion-Version': '2022-06-28'
                }
            
            if self.openai_key:
                openai.api_key = self.openai_key
                
        except Exception as e:
            print(f'Config error: {e}')
    
    def init_database(self):
        """📊 생산성 데이터 저장을 위한 SQLite 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 업무 기록 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    category TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_minutes INTEGER,
                    status TEXT,
                    pomodoro_count INTEGER DEFAULT 0,
                    break_count INTEGER DEFAULT 0,
                    productivity_score REAL,
                    focus_rating INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 일일 통계 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_work_minutes INTEGER DEFAULT 0,
                    total_break_minutes INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    total_tasks INTEGER DEFAULT 0,
                    avg_focus_rating REAL DEFAULT 0,
                    peak_productivity_hour INTEGER,
                    ai_feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI 피드백 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,  -- daily, weekly, monthly
                    content TEXT NOT NULL,
                    insights TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 🎯 목표 설정 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_type TEXT NOT NULL,  -- daily, weekly, monthly
                    date_range TEXT NOT NULL,  -- 2025-07-01 or 2025-W27 or 2025-07
                    target_work_hours REAL DEFAULT 0,
                    target_tasks INTEGER DEFAULT 0,
                    target_focus_avg REAL DEFAULT 0,
                    target_pomodoros INTEGER DEFAULT 0,
                    actual_work_hours REAL DEFAULT 0,
                    actual_tasks INTEGER DEFAULT 0,
                    actual_focus_avg REAL DEFAULT 0,
                    actual_pomodoros INTEGER DEFAULT 0,
                    achievement_rate REAL DEFAULT 0,
                    status TEXT DEFAULT 'active',  -- active, completed, failed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 🔄 AI 일정 추천 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_schedule_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    suggested_order TEXT NOT NULL,  -- JSON format
                    reasoning TEXT,
                    user_accepted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.add_log('📊 데이터베이스 초기화 완료!')
            
        except Exception as e:
            print(f'Database init error: {e}')
            self.add_log(f'❌ DB 초기화 오류: {e}')
    
    def show_toast(self, title, message, duration=5):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='📅 스케줄러 트래커',
                timeout=duration
            )
            # 시스템 사운드도 재생
            try:
                winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)
            except:
                pass
        except Exception as e:
            self.add_log(f'TOAST ERROR: {e}')

    def start_scheduler(self):
        """🚨 핵심! 10초마다 시간을 체크해서 알림을 보내는 스케줄러"""
        def scheduler_loop():
            while True:
                try:
                    self.check_scheduled_tasks()
                    time.sleep(10)  # 10초마다 체크 (더 정확한 알림)
                except Exception as e:
                    print(f'Scheduler error: {e}')
                    time.sleep(10)
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        self.add_log('⏰ 시간 스케줄러가 시작되었습니다!')

    def check_scheduled_tasks(self):
        """🚨 핵심! 노션의 Time 속성을 확인해서 현재 시간과 비교"""
        if not self.headers:
            return
        
        try:
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            today = now.strftime('%Y-%m-%d')
            
            print(f'[DEBUG] 현재 시간: {current_time}, 오늘: {today}')
            
            # 오늘의 모든 작업 가져오기
            url = f'https://api.notion.com/v1/databases/{self.db_id}/query'
            query = {
                'filter': {
                    'property': 'Date',
                    'date': {
                        'equals': today
                    }
                }
            }
            
            response = requests.post(url, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('results', [])
                print(f'[DEBUG] 찾은 업무 수: {len(tasks)}')
                
                for task in tasks:
                    task_id = task['id']
                    
                    # 이미 알림 보낸 작업은 스킵
                    if task_id in self.notified_tasks:
                        continue
                    
                    # 작업 이름 가져오기
                    task_name = 'Untitled'
                    if (task['properties'].get('Task') and 
                        task['properties']['Task'].get('title') and 
                        len(task['properties']['Task']['title']) > 0):
                        task_name = task['properties']['Task']['title'][0]['plain_text']
                    
                    # Time 속성 확인
                    time_prop = task['properties'].get('Time')
                    if time_prop and time_prop.get('date') and time_prop['date'].get('start'):
                        scheduled_datetime = time_prop['date']['start']
                        print(f'[DEBUG] {task_name} 시간: {scheduled_datetime}')
                        
                        # 시간 부분만 추출 (예: '2025-07-01T03:04:00.000+00:00' -> '03:04')
                        if 'T' in scheduled_datetime:
                            scheduled_time = scheduled_datetime.split('T')[1][:5]  # HH:MM
                            print(f'[DEBUG] 예정 시간: {scheduled_time}, 현재: {current_time}')
                            
                            # 현재 시간과 비교 (더 정확한 알림을 위해 초도 고려)
                            current_datetime = now.strftime('%H:%M')
                            if scheduled_time == current_datetime:
                                # 🚨 알림 발송!
                                self.show_toast(
                                    '🕐 업무 시작 시간!',
                                    f'{task_name} 시작할 시간입니다!'
                                )
                                self.add_log(f'⏰ 알림: {task_name} ({scheduled_time})')
                                self.notified_tasks.add(task_id)
                                print(f'[DEBUG] 알림 발송: {task_name}')
                                
                                # 중요 업무는 사운드도 재생
                                try:
                                    winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
                                except:
                                    pass
                                
        except Exception as e:
            print(f'Schedule check error: {e}')

    def setup_ui(self):
        """🎨 모던한 UI 설정"""
        
        # 스크롤 가능한 메인 컨테이너
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 스크롤바 추가
        self.canvas = tk.Canvas(main_frame, bg='#1a1a1a', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        main_container = ctk.CTkFrame(self.canvas)
        
        main_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=main_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 마우스 휠 스크롤 바인딩
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 🎨 헤더 섹션
        header_frame = ctk.CTkFrame(main_container)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        # 타이틀 프레임 (이미지 + 텍스트용)
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(pady=20)
        
        # 토스트 이미지 로드
        try:
            toast_img = Image.open('toast.png')
            toast_ctk_image = ctk.CTkImage(light_image=toast_img, dark_image=toast_img, size=(36, 36))
            img_label = ctk.CTkLabel(title_frame, image=toast_ctk_image, text="")
            img_label.pack(side="left", padx=(0,10))
        except Exception as e:
            print(f"토스트 이미지 로드 실패: {e}")  # 디버깅용
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="토스트 트래커",
            font=ctk.CTkFont(size=24, weight="normal")
        )
        title_label.pack(side="left")
        
        # 상태 표시
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="연결됨!",
            font=ctk.CTkFont(size=14, weight="normal"),
            text_color="#00cc44"
        )
        self.status_label.pack(pady=(0, 10))
        
        # 🍅 뽀모도로 설정
        pomodoro_frame = ctk.CTkFrame(header_frame)
        pomodoro_frame.pack(fill="x", padx=15, pady=8)
        
        # 토마토 이미지 + 체크박스 배치용 서브프레임
        pomodoro_content_frame = ctk.CTkFrame(pomodoro_frame)
        pomodoro_content_frame.pack(pady=10)
        
        # 토마토 이미지 로드
        try:
            tomato_img = Image.open('tomato.png')
            tomato_ctk_image = ctk.CTkImage(light_image=tomato_img, dark_image=tomato_img, size=(24, 24))
            tomato_label = ctk.CTkLabel(pomodoro_content_frame, image=tomato_ctk_image, text="")
            tomato_label.pack(side="left", padx=(0,8))
        except Exception as e:
            print(f"토마토 이미지 로드 실패: {e}")  # 디버깅용
        
        self.pomodoro_var = ctk.BooleanVar()
        self.pomodoro_check = ctk.CTkCheckBox(
            pomodoro_content_frame,
            text="뽀모도로 모드 (25분 집중 + 5분 휴식)",
            variable=self.pomodoro_var,
            command=self.toggle_pomodoro_mode,
            font=ctk.CTkFont(size=12, weight="normal")
        )
        self.pomodoro_check.pack(side="left")
        
        # 📥 업무 로드 버튼
        load_btn = ctk.CTkButton(
            header_frame,
            text="업무 로드",
            command=self.load_tasks,
            font=ctk.CTkFont(size=14, weight="normal"),
            height=40,
            width=200
        )
        load_btn.pack(pady=15)
        
        # 📋 중간 섹션 (업무 목록 + 타이머)
        middle_frame = ctk.CTkFrame(main_container)
        middle_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        # 왼쪽: 업무 목록
        left_frame = ctk.CTkFrame(middle_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tasks_label = ctk.CTkLabel(
            left_frame,
            text="오늘의 업무",
            font=ctk.CTkFont(size=16, weight="normal")
        )
        tasks_label.pack(pady=(20, 10))
        
        # 업무 표 (ttk.Treeview)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview',
                        background='#f7f7f7',
                        foreground='#222',
                        rowheight=28,
                        fieldbackground='#f7f7f7',
                        font=('Arial', 11))
        style.configure('Treeview.Heading', font=('Arial', 12, 'normal'))
        style.map('Treeview', background=[('selected', '#cce6ff')])

        columns = ("Task", "Type", "Time", "Priority")
        self.task_table = ttk.Treeview(left_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.task_table.heading(col, text=col)
        self.task_table.column("Task", width=180, anchor="w")
        self.task_table.column("Type", width=70, anchor="center")
        self.task_table.column("Time", width=140, anchor="center")
        self.task_table.column("Priority", width=70, anchor="center")
        self.task_table.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 스크롤바
        table_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.task_table.yview)
        self.task_table.configure(yscrollcommand=table_scroll.set)
        table_scroll.pack(side="right", fill="y")
        
        # 오른쪽: 타이머 & 현재 업무
        right_frame = ctk.CTkFrame(middle_frame)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        
        # 현재 업무 표시
        self.current_label = ctk.CTkLabel(
            right_frame,
            text="작업을 선택하세요",
            font=ctk.CTkFont(size=14, weight="normal"),
            wraplength=200
        )
        self.current_label.pack(pady=(20, 10))
        
        # 타이머 표시
        self.timer_label = ctk.CTkLabel(
            right_frame,
            text="00:00:00",
            font=ctk.CTkFont(size=32, weight="normal"),
            text_color="#4a9eff"
        )
        self.timer_label.pack(pady=20)
        
        # 🍅 뽀모도로 상태 표시
        self.pomodoro_status = ctk.CTkLabel(
            right_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color="#ff6b6b"
        )
        self.pomodoro_status.pack(pady=5)
        
        # 🎮 컨트롤 버튼들
        control_frame = ctk.CTkFrame(right_frame)
        control_frame.pack(fill="x", padx=15, pady=15)
        
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="시작",
            command=self.start_task,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#28a745",
            hover_color="#218838",
            height=35
        )
        self.start_btn.pack(fill="x", pady=5)
        
        self.break_btn = ctk.CTkButton(
            control_frame,
            text="휴식",
            command=self.start_break,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#6f42c1",
            hover_color="#5a356b",
            height=35,
            state="disabled"
        )
        self.break_btn.pack(fill="x", pady=5)
        
        self.complete_btn = ctk.CTkButton(
            control_frame,
            text="완료",
            command=self.complete_task,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#fd7e14",
            hover_color="#e06900",
            height=35,
            state="disabled"
        )
        self.complete_btn.pack(fill="x", pady=5)
        
        # 🤖 AI 기능 버튼들
        ai_frame = ctk.CTkFrame(main_container)
        ai_frame.pack(fill="x", padx=15, pady=8)
        
        ai_title = ctk.CTkLabel(
            ai_frame,
            text="AI 기능",
            font=ctk.CTkFont(size=16, weight="normal")
        )
        ai_title.pack(pady=(15, 10))
        
        # AI 버튼들을 그리드로 배치
        ai_buttons_frame = ctk.CTkFrame(ai_frame)
        ai_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 첫 번째 줄
        ai_row1 = ctk.CTkFrame(ai_buttons_frame)
        ai_row1.pack(fill="x", pady=5)
        
        self.feedback_btn = ctk.CTkButton(
            ai_row1,
            text="일일 피드백",
            command=self.get_daily_feedback,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#17a2b8",
            hover_color="#138496",
            width=140,
            height=35
        )
        self.feedback_btn.pack(side="left", padx=5)
        
        self.stats_btn = ctk.CTkButton(
            ai_row1,
            text="통계 보기",
            command=self.show_analytics,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#17a2b8",
            hover_color="#138496",
            width=140,
            height=35
        )
        self.stats_btn.pack(side="left", padx=5)
        
        self.goal_btn = ctk.CTkButton(
            ai_row1,
            text="목표 설정",
            command=self.show_goal_setting,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#17a2b8",
            hover_color="#138496",
            width=140,
            height=35
        )
        self.goal_btn.pack(side="left", padx=5)
        
        self.prediction_btn = ctk.CTkButton(
            ai_row1,
            text="생산성 예측",
            command=self.get_productivity_prediction,
            font=ctk.CTkFont(size=12, weight="normal"),
            fg_color="#17a2b8",
            hover_color="#138496",
            width=140,
            height=35
        )
        self.prediction_btn.pack(side="left", padx=5)
        
        # 📝 로그 섹션
        log_frame = ctk.CTkFrame(main_container)
        log_frame.pack(fill="both", expand=True, padx=15, pady=(8, 15))
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="활동 로그",
            font=ctk.CTkFont(size=16, weight="normal")
        )
        log_title.pack(pady=(15, 10))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=150,
            font=ctk.CTkFont(size=10)
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 초기 로그 메시지
        self.add_log('🍞 토스트 트래커 시작!')
        self.add_log('📥 업무 로드를 눌러주세요')
        self.show_toast('🍞 앱시작', '토스트가 알맞게 구워졌습니다.')
    
    def toggle_pomodoro_mode(self):
        """🍅 뽀모도로 모드 토글"""
        self.pomodoro_mode = self.pomodoro_var.get()
        if self.pomodoro_mode:
            self.add_log('🍅 뽀모도로 모드 활성화!')
            self.pomodoro_status.configure(text='🍅 뽀모도로 모드 ON')
            self.show_toast('🍅 뽀모도로 모드', '25분 집중 + 5분 휴식 모드가 활성화되었습니다!')
        else:
            self.add_log('🍅 뽀모도로 모드 비활성화')
            self.pomodoro_status.configure(text='')
    
    def start_break(self):
        """☕ 휴식 시작"""
        if not self.is_tracking:
            return
        
        self.is_break_time = True
        self.pomodoro_start = time.time()
        self.start_btn.configure(state="disabled")
        self.break_btn.configure(state="disabled")
        self.complete_btn.configure(state="normal")
        
        self.add_log(f'☕ 휴식 시작 ({self.break_duration//60}분)')
        self.show_toast('☕ 휴식 시간', f'{self.break_duration//60}분 휴식을 시작합니다!')
        self.pomodoro_status.configure(text=f'☕ 휴식 중... ({self.break_duration//60}분)')
        
        # 휴식 시간 후 알림
        self.root.after(self.break_duration * 1000, self.break_finished)
    
    def break_finished(self):
        """☕ 휴식 종료"""
        if self.is_break_time:
            self.is_break_time = False
            self.add_log('⏰ 휴식 시간 종료! 다시 집중하세요!')
            self.show_toast('⏰ 휴식 종료', '이제 다시 집중할 시간입니다!')
            self.pomodoro_status.configure(text='🍅 작업 시간!')
            self.break_btn.configure(state="normal")

    def load_tasks(self):
        if not self.headers:
            self.add_log('❌ 오류: 노션 설정이 필요합니다')
            self.show_toast('❌ 오류', '노션이 설정되지 않았습니다')
            return
        try:
            today = datetime.now().date()
            self.add_log(f'업무 로딩중...')
            self.show_toast('로딩중...', '노션에서 업무를 가져오는 중')
            url = f'https://api.notion.com/v1/databases/{self.db_id}/query'
            query = {}
            response = requests.post(url, headers=self.headers, json=query)
            if response.status_code == 200:
                data = response.json()
                self.tasks = data.get('results', [])
                for row in self.task_table.get_children():
                    self.task_table.delete(row)
                for task in self.tasks:
                    time_val = ''
                    is_today = False
                    time_prop = task['properties'].get('Time')
                    if time_prop and time_prop.get('date') and time_prop['date'].get('start'):
                        scheduled_datetime = time_prop['date']['start']
                        try:
                            dt = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
                            time_val = dt.strftime('%Y-%m-%d %H:%M')
                            if dt.date() == today:
                                is_today = True
                        except Exception:
                            pass
                    if not is_today:
                        continue
                    task_name = 'Untitled'
                    if (task['properties'].get('Task') and 
                        task['properties']['Task'].get('title') and 
                        len(task['properties']['Task']['title']) > 0):
                        task_name = task['properties']['Task']['title'][0]['plain_text']
                    type_val = ''
                    if (task['properties'].get('Type') and 
                        task['properties']['Type'].get('select')):
                        type_val = task['properties']['Type']['select']['name']
                    priority_val = ''
                    if (task['properties'].get('Priority') and 
                        task['properties']['Priority'].get('select')):
                        priority_val = task['properties']['Priority']['select']['name']
                    page_id = task['id']
                    self.task_table.insert('', 'end', iid=page_id, values=(task_name, type_val, time_val, priority_val))
                self.add_log(f'성공: {self.task_table.get_children().__len__()}개 업무 로드됨')
                self.show_toast('업무 로드 완료', f'오늘 {self.task_table.get_children().__len__()}개 업무를 찾았습니다')
                if len(self.task_table.get_children()) == 0:
                    self.add_log('업무가 없습니다. 노션에서 업무를 만들어주세요!')
                    self.show_toast('업무 없음', '노션에서 먼저 업무를 만들어주세요!')
            else:
                self.add_log(f'오류: {response.status_code}\n{response.text}')
                self.show_toast('로드 실패', f'오류 코드: {response.status_code}')
        except Exception as e:
            self.add_log(f'예외: {str(e)}')
            self.show_toast('예외 발생', f'오류: {str(e)[:50]}')

    def start_task(self):
        selected = self.task_table.selection()
        if not selected:
            self.add_log('⚠️ 먼저 업무를 선택해주세요!')
            self.show_toast('⚠️ 업무 선택', '먼저 업무를 선택해주세요!')
            return
        page_id = selected[0]
        values = self.task_table.item(page_id, 'values')
        task_name = values[0]
        type_val = values[1]
        time_val = values[2]
        priority_val = values[3]
        self.current_task = {
            'task_name': task_name,
            'type': type_val,
            'time': time_val,
            'priority': priority_val,
            'page_id': page_id
        }
        self.current_label.configure(text=f'진행중: {task_name}')
        self.start_time = time.time()
        self.is_tracking = True
        self.is_break_time = False
        self.start_btn.configure(state="disabled")
        self.complete_btn.configure(state="normal")
        if self.pomodoro_mode:
            self.break_btn.configure(state="normal")
            self.pomodoro_start = time.time()
            self.pomodoro_status.configure(text=f'집중 시간! ({self.pomodoro_duration//60}분)')
            self.root.after(self.pomodoro_duration * 1000, self.pomodoro_break_reminder)
        self.add_log(f'▶️ 시작: {task_name}')
        self.show_toast('업무 시작', f'{task_name} 업무를 시작했습니다!')
        # Notion Status를 In Progress로 업데이트
        self.update_notion_status('In Progress')
        self.save_task_start(task_name)

    def pomodoro_break_reminder(self):
        """🍅 뽀모도로 휴식 시간 알림"""
        if self.is_tracking and not self.is_break_time and self.pomodoro_mode:
            self.add_log('🍅 25분 완료! 5분 휴식을 권장합니다.')
            self.show_toast('🍅 뽀모도로 완료', '25분 집중 완료! 5분 휴식을 하세요.')
            self.pomodoro_count += 1
            self.pomodoro_status.configure(text='🍅 휴식 시간 권장!')
    
    def save_task_start(self, task_name):
        """📊 업무 시작 데이터 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            start_time = datetime.now().strftime('%H:%M:%S')
            
            cursor.execute('''
                INSERT INTO task_records (date, task_name, start_time, status)
                VALUES (?, ?, ?, ?)
            ''', (today, task_name, start_time, 'In Progress'))
            
            self.current_task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f'Save task start error: {e}')

    def complete_task(self):
        if not self.is_tracking or not self.current_task:
            return
        duration = int(time.time() - self.start_time)
        minutes = duration // 60
        task_name = self.current_task.get('task_name', 'Untitled')
        focus_rating = self.get_focus_rating(task_name, minutes)
        self.add_log(f'✅ 완료: {task_name} ({minutes}분 소요)')
        self.show_toast('업무 완료', f'{task_name} 완료! ({minutes}분 소요)')
        # Notion Status를 Done으로 업데이트
        self.update_notion_status('Done', duration)
        self.save_task_completion(task_name, duration, focus_rating)
        self.current_label.configure(text='작업을 선택하세요')
        self.timer_label.configure(text='00:00:00', text_color="#4a9eff")
        self.pomodoro_status.configure(text='')
        self.is_tracking = False
        self.is_break_time = False
        self.current_task = None
        self.start_time = None
        self.start_btn.configure(state="normal")
        self.complete_btn.configure(state="disabled")
        self.break_btn.configure(state="disabled")
        if self.pomodoro_mode:
            self.pomodoro_count = 0

    def get_focus_rating(self, task_name, minutes):
        """💯 집중도 평가 요청"""
        try:
            rating = simpledialog.askinteger(
                "집중도 평가", 
                f"'{task_name}' 작업의 집중도를 평가해주세요\n"
                f"(소요시간: {minutes}분)\n\n"
                f"1 = 매우 낮음\n"
                f"2 = 낮음\n"
                f"3 = 보통\n"
                f"4 = 높음\n"
                f"5 = 매우 높음",
                minvalue=1, maxvalue=5
            )
            return rating if rating else 3  # 기본값 3
        except:
            return 3
    
    def save_task_completion(self, task_name, duration_seconds, focus_rating):
        """📊 업무 완료 데이터 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            end_time = datetime.now().strftime('%H:%M:%S')
            minutes = duration_seconds // 60
            
            # 기존 레코드 업데이트
            cursor.execute('''
                UPDATE task_records 
                SET end_time = ?, duration_minutes = ?, status = ?, 
                    pomodoro_count = ?, focus_rating = ?
                WHERE id = ?
            ''', (end_time, minutes, 'Done', self.pomodoro_count, focus_rating, self.current_task_id))
            
            conn.commit()
            conn.close()
            
            # 일일 통계 업데이트
            self.update_daily_stats()
            
        except Exception as e:
            print(f'Save completion error: {e}')
    
    def update_daily_stats(self):
        """📊 일일 통계 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 오늘의 통계 계산
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'Done' THEN 1 END) as completed_tasks,
                    SUM(CASE WHEN status = 'Done' THEN duration_minutes ELSE 0 END) as total_work_minutes,
                    AVG(CASE WHEN focus_rating > 0 THEN focus_rating END) as avg_focus_rating
                FROM task_records 
                WHERE date = ?
            ''', (today,))
            
            stats = cursor.fetchone()
            
            # 일일 통계 저장/업데이트
            cursor.execute('''
                INSERT OR REPLACE INTO daily_stats 
                (date, total_tasks, completed_tasks, total_work_minutes, avg_focus_rating)
                VALUES (?, ?, ?, ?, ?)
            ''', (today, stats[0], stats[1], stats[2] or 0, stats[3] or 0))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f'Update daily stats error: {e}')

    def update_notion_status(self, status, duration=None):
        if not self.current_task or not self.current_task.get('page_id'):
            return
        try:
            page_id = self.current_task['page_id']
            url = f'https://api.notion.com/v1/pages/{page_id}'
            data = {
                'properties': {
                    'Status': {
                        'select': {
                            'name': status
                        }
                    }
                }
            }
            if duration is not None:
                data['properties']['Duration'] = {
                    'number': duration // 60
                }
            response = requests.patch(url, headers=self.headers, json=data)
            if response.status_code == 200:
                self.add_log(f'노션 업데이트: {status}')
            else:
                self.add_log(f'노션 업데이트 실패: {response.status_code}')
        except Exception as e:
            self.add_log(f'노션 업데이트 오류: {str(e)}')

    def update_timer(self):
        if self.is_tracking and self.start_time:
            if self.is_break_time and self.pomodoro_start:
                # 휴식 시간 카운트다운
                break_elapsed = int(time.time() - self.pomodoro_start)
                remaining = max(0, self.break_duration - break_elapsed)
                if remaining == 0:
                    self.break_finished()
                minutes = remaining // 60
                seconds = remaining % 60
                self.timer_label.configure(text=f'☕ {minutes:02d}:{seconds:02d}', text_color="#6f42c1")
            else:
                # 일반 작업 시간
                elapsed = int(time.time() - self.start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                if self.pomodoro_mode and self.pomodoro_start:
                    # 뽀모도로 모드: 25분 카운트다운
                    pomodoro_elapsed = int(time.time() - self.pomodoro_start)
                    pomodoro_remaining = max(0, self.pomodoro_duration - pomodoro_elapsed)
                    p_minutes = pomodoro_remaining // 60
                    p_seconds = pomodoro_remaining % 60
                    self.timer_label.configure(text=f'🍅 {p_minutes:02d}:{p_seconds:02d}', text_color="#ff6b6b")
                else:
                    self.timer_label.configure(text=f'{hours:02d}:{minutes:02d}:{seconds:02d}', text_color="#4a9eff")
        self.root.after(1000, self.update_timer)

    def get_daily_feedback(self):
        """🤖 AI 일일 피드백 생성"""
        if not self.openai_key:
            self.add_log('❌ OpenAI API 키가 설정되지 않았습니다')
            self.show_toast('❌ AI 설정 필요', 'OpenAI API 키를 .env 파일에 추가해주세요')
            return
        
        try:
            self.add_log('🤖 AI 피드백 생성 중...')
            self.show_toast('🤖 AI 분석 중', '오늘의 업무 패턴을 분석하고 있습니다...')
            
            # 오늘의 데이터 가져오기
            today_data = self.get_today_analytics()
            
            if not today_data:
                self.add_log('📊 오늘의 데이터가 없습니다')
                self.show_toast('📊 데이터 없음', '먼저 업무를 완료해주세요')
                return
            
            # AI 피드백 생성
            feedback = self.generate_ai_feedback(today_data)
            
            # 피드백 창 표시
            self.show_feedback_window(feedback)
            
            # 데이터베이스에 저장
            self.save_ai_feedback(feedback, 'daily')
            
        except Exception as e:
            self.add_log(f'❌ AI 피드백 오류: {e}')
            self.show_toast('❌ AI 오류', f'피드백 생성 실패: {str(e)[:50]}')
    
    def get_today_analytics(self):
        """📊 오늘의 분석 데이터 수집"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 업무 기록들
            cursor.execute('''
                SELECT task_name, start_time, end_time, duration_minutes, 
                       focus_rating, pomodoro_count
                FROM task_records 
                WHERE date = ? AND status = 'Done'
                ORDER BY start_time
            ''', (today,))
            
            tasks = cursor.fetchall()
            
            # 일일 통계
            cursor.execute('''
                SELECT total_tasks, completed_tasks, total_work_minutes, avg_focus_rating
                FROM daily_stats 
                WHERE date = ?
            ''', (today,))
            
            stats = cursor.fetchone()
            conn.close()
            
            if not tasks and not stats:
                return None
            
            return {
                'tasks': tasks,
                'stats': stats,
                'date': today
            }
            
        except Exception as e:
            print(f'Get analytics error: {e}')
            return None
    
    def generate_ai_feedback(self, data):
        """🤖 OpenAI를 사용한 피드백 생성"""
        try:
            tasks_summary = "\n".join([
                f"- {task[0]}: {task[1]}-{task[2] or 'ongoing'} "
                f"({task[3] or 0}분, 집중도: {task[4] or 0}/5, 뽀모도로: {task[5] or 0}회)"
                for task in data['tasks']
            ])
            
            stats = data['stats']
            total_tasks = stats[0] if stats else 0
            completed_tasks = stats[1] if stats else 0
            total_minutes = stats[2] if stats else 0
            avg_focus = stats[3] if stats else 0
            
            prompt = f"""
당신은 생산성 전문가입니다. 다음 사용자의 오늘 업무 데이터를 분석하고 개인맞춤 피드백을 제공해주세요.

**오늘의 업무 현황 ({data['date']})**
- 총 업무: {total_tasks}개
- 완료된 업무: {completed_tasks}개  
- 총 작업 시간: {total_minutes}분 ({total_minutes//60}시간 {total_minutes%60}분)
- 평균 집중도: {avg_focus:.1f}/5.0

**완료된 업무 상세:**
{tasks_summary}

다음 관점에서 분석해주세요:
1. **오늘의 성과 평가** (긍정적인 부분 강조)
2. **시간 관리 패턴 분석** (효율성, 뽀모도로 활용도 등)
3. **집중력 분석** (집중도 점수 기반)
4. **개선 제안** (구체적이고 실행 가능한 조언)
5. **내일을 위한 권장사항**

친근하고 격려하는 톤으로 작성해주세요. 이모지를 적절히 사용하여 읽기 쉽게 만들어주세요.
"""
            
            # OpenAI API 호출 (새로운 클라이언트 방식)
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"AI 피드백 생성 중 오류가 발생했습니다: {str(e)}"
    
    def show_feedback_window(self, feedback):
        """🤖 피드백 창 표시"""
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title('🤖 AI 일일 피드백')
        feedback_window.geometry('600x500')
        
        # 스크롤 가능한 텍스트
        frame = tk.Frame(feedback_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                            font=('Arial', 11), padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert(tk.END, feedback)
        text_widget.config(state=tk.DISABLED)
        
        # 닫기 버튼
        close_btn = tk.Button(feedback_window, text='닫기', 
                            command=feedback_window.destroy,
                            font=('Arial', 12, 'bold'))
        close_btn.pack(pady=10)
    
    def save_ai_feedback(self, feedback, feedback_type):
        """🤖 AI 피드백 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO ai_feedback (date, feedback_type, content)
                VALUES (?, ?, ?)
            ''', (today, feedback_type, feedback))
            
            conn.commit()
            conn.close()
            
            self.add_log('🤖 AI 피드백이 저장되었습니다')
            
        except Exception as e:
            print(f'Save feedback error: {e}')
    
    def show_analytics(self):
        """Show statistics dashboard window (English version)"""
        try:
            analytics_win = tk.Toplevel(self.root)
            analytics_win.title('Statistics Dashboard')
            analytics_win.geometry('1100x800')
            tab_control = ttk.Notebook(analytics_win)
            tab_control.pack(fill='both', expand=True)

            # 1. Hourly Focus Heatmap
            frame1 = tk.Frame(tab_control)
            tab_control.add(frame1, text='Hourly Focus Heatmap')
            self.create_focus_heatmap(frame1)

            # 2. Category Distribution
            frame2 = tk.Frame(tab_control)
            tab_control.add(frame2, text='Category Distribution')
            self.create_type_pie_chart(frame2)

            # 3. Weekly Trend
            frame3 = tk.Frame(tab_control)
            tab_control.add(frame3, text='Weekly Trend')
            self.create_weekly_trend(frame3)

            # 4. AI Feedback
            frame4 = tk.Frame(tab_control)
            tab_control.add(frame4, text='AI Feedback')
            self.create_ai_feedback_tab(frame4)

        except Exception as e:
            self.add_log(f'❌ Error showing statistics: {e}')
    
    def create_focus_heatmap(self, parent):
        import pandas as pd
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM task_records', conn)
        conn.close()
        if df.empty or 'start_time' not in df.columns or 'focus_rating' not in df.columns:
            label = tk.Label(parent, text='Not enough data.', font=('Arial', 14))
            label.pack()
            return
        df['hour'] = pd.to_datetime(df['start_time'], errors='coerce').dt.hour
        heatmap_data = df.groupby('hour')['focus_rating'].mean().reindex(range(24), fill_value=0)
        plt.figure(figsize=(8,2))
        sns.heatmap([heatmap_data.values], cmap='YlGnBu', annot=True, cbar=True, xticklabels=range(24), yticklabels=['Focus'])
        plt.title('Average Focus by Hour')
        fig = plt.gcf()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def create_type_pie_chart(self, parent):
        import pandas as pd
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM task_records', conn)
        conn.close()
        if df.empty or 'type' not in df.columns or 'duration_minutes' not in df.columns:
            label = tk.Label(parent, text='Not enough data.', font=('Arial', 14))
            label.pack()
            return
        type_sum = df.groupby('type')['duration_minutes'].sum()
        plt.figure(figsize=(5,5))
        plt.pie(type_sum, labels=type_sum.index, autopct='%1.1f%%', startangle=90)
        plt.title('Time Spent by Category')
        fig = plt.gcf()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def create_weekly_trend(self, parent):
        import pandas as pd
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM daily_stats', conn)
        conn.close()
        if df.empty or 'date' not in df.columns:
            label = tk.Label(parent, text='Not enough data.', font=('Arial', 14))
            label.pack()
            return
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').tail(7)
        plt.figure(figsize=(8,4))
        plt.plot(df['date'], df['avg_focus_rating'], marker='o', label='Avg. Focus')
        plt.plot(df['date'], df['completed_tasks']/df['total_tasks'], marker='s', label='Goal Achievement Rate')
        plt.ylim(0, 1.1)
        plt.legend()
        plt.title('Last 7 Days: Focus & Goal Achievement')
        plt.xlabel('Date')
        plt.ylabel('Rate/Score')
        fig = plt.gcf()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def create_ai_feedback_tab(self, parent):
        import tkinter as tk
        feedback = self.generate_dashboard_ai_feedback()
        text = tk.Text(parent, wrap='word', font=('Arial', 12))
        if not feedback or '데이터가 부족' in feedback or 'AI 피드백' in feedback:
            feedback = 'No feedback data available.'
        text.insert('1.0', feedback)
        text.config(state='disabled')
        text.pack(fill='both', expand=True, padx=10, pady=10)

    def generate_dashboard_ai_feedback(self):
        # Summarize last 7 days focus, category distribution, golden hour, etc. for GPT
        import pandas as pd
        conn = sqlite3.connect(self.db_path)
        df_task = pd.read_sql_query('SELECT * FROM task_records', conn)
        df_stats = pd.read_sql_query('SELECT * FROM daily_stats', conn)
        conn.close()
        if df_task.empty or df_stats.empty:
            return 'No feedback data available.'
        # Golden hour
        df_task['hour'] = pd.to_datetime(df_task['start_time'], errors='coerce').dt.hour
        focus_by_hour = df_task.groupby('hour')['focus_rating'].mean().dropna()
        if not focus_by_hour.empty:
            golden_hour = focus_by_hour.idxmax()
            golden_score = focus_by_hour.max()
            golden_str = f"Golden hour: {golden_hour}:00 (Avg. focus {golden_score:.2f})"
        else:
            golden_str = "No golden hour data."
        # Category distribution
        type_sum = df_task.groupby('type')['duration_minutes'].sum()
        type_str = ', '.join([f"{k}: {v} min" for k,v in type_sum.items()])
        # Weekly focus/goal
        df_stats['date'] = pd.to_datetime(df_stats['date'])
        df_stats = df_stats.sort_values('date').tail(7)
        avg_focus = df_stats['avg_focus_rating'].mean()
        avg_goal = (df_stats['completed_tasks']/df_stats['total_tasks']).mean()
        # Prompt
        prompt = f"""
You are a productivity coach. Based on the following data, analyze the user's work pattern for today/this week, and summarize golden hour, category time distribution, focus/goal trends, and give friendly feedback and suggestions in 5 lines or less. No emojis.

- {golden_str}
- Category distribution: {type_str}
- Last 7 days avg. focus: {avg_focus:.2f}
- Last 7 days goal achievement: {avg_goal*100:.1f}%
"""
        try:
            import openai
            openai.api_key = self.openai_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            return f'AI feedback generation error: {e}'
    
    def show_goal_setting(self):
        """🎯 목표 설정 창 표시"""
        goal_window = tk.Toplevel(self.root)
        goal_window.title('🎯 목표 설정 & 추적')
        goal_window.geometry('500x600')
        
        # 탭 생성
        notebook = ttk.Notebook(goal_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 일일 목표 탭
        daily_frame = tk.Frame(notebook)
        notebook.add(daily_frame, text='📅 일일 목표')
        
        # 주간 목표 탭
        weekly_frame = tk.Frame(notebook)
        notebook.add(weekly_frame, text='📊 주간 목표')
        
        # 목표 현황 탭
        status_frame = tk.Frame(notebook)
        notebook.add(status_frame, text='📈 달성 현황')
        
        # 각 탭 설정
        self.setup_daily_goal_tab(daily_frame)
        self.setup_weekly_goal_tab(weekly_frame)
        self.setup_goal_status_tab(status_frame)
    
    def setup_daily_goal_tab(self, parent):
        """📅 일일 목표 설정 탭"""
        tk.Label(parent, text='📅 오늘의 목표 설정', 
                font=('Arial', 16, 'bold')).pack(pady=10)
        
        # 목표 입력 프레임
        input_frame = tk.Frame(parent)
        input_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # 작업 시간 목표
        tk.Label(input_frame, text='⏰ 목표 작업 시간 (시간):').pack(anchor=tk.W)
        self.daily_work_hours = tk.Entry(input_frame, font=('Arial', 12))
        self.daily_work_hours.pack(fill=tk.X, pady=5)
        
        # 완료 업무 수 목표
        tk.Label(input_frame, text='✅ 목표 완료 업무 수:').pack(anchor=tk.W)
        self.daily_tasks = tk.Entry(input_frame, font=('Arial', 12))
        self.daily_tasks.pack(fill=tk.X, pady=5)
        
        # 평균 집중도 목표
        tk.Label(input_frame, text='🎯 목표 평균 집중도 (1-5):').pack(anchor=tk.W)
        self.daily_focus = tk.Entry(input_frame, font=('Arial', 12))
        self.daily_focus.pack(fill=tk.X, pady=5)
        
        # 뽀모도로 목표
        tk.Label(input_frame, text='🍅 목표 뽀모도로 횟수:').pack(anchor=tk.W)
        self.daily_pomodoros = tk.Entry(input_frame, font=('Arial', 12))
        self.daily_pomodoros.pack(fill=tk.X, pady=5)
        
        # 버튼들
        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=20)
        
        save_btn = tk.Button(btn_frame, text='💾 목표 저장', 
                           command=self.save_daily_goal, bg='lightgreen',
                           font=('Arial', 12, 'bold'))
        save_btn.pack(side=tk.LEFT, padx=10)
        
        load_btn = tk.Button(btn_frame, text='📥 기존 목표 불러오기', 
                           command=self.load_daily_goal, bg='lightblue',
                           font=('Arial', 12, 'bold'))
        load_btn.pack(side=tk.LEFT, padx=10)
        
        # 현재 목표 불러오기
        self.load_daily_goal()
    
    def setup_weekly_goal_tab(self, parent):
        """📊 주간 목표 설정 탭"""
        tk.Label(parent, text='📊 이번 주 목표 설정', 
                font=('Arial', 16, 'bold')).pack(pady=10)
        
        input_frame = tk.Frame(parent)
        input_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(input_frame, text='⏰ 주간 목표 작업 시간 (시간):').pack(anchor=tk.W)
        self.weekly_work_hours = tk.Entry(input_frame, font=('Arial', 12))
        self.weekly_work_hours.pack(fill=tk.X, pady=5)
        
        tk.Label(input_frame, text='✅ 주간 목표 완료 업무 수:').pack(anchor=tk.W)
        self.weekly_tasks = tk.Entry(input_frame, font=('Arial', 12))
        self.weekly_tasks.pack(fill=tk.X, pady=5)
        
        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=20)
        
        save_btn = tk.Button(btn_frame, text='💾 주간 목표 저장', 
                           command=self.save_weekly_goal, bg='lightgreen',
                           font=('Arial', 12, 'bold'))
        save_btn.pack(side=tk.LEFT, padx=10)
    
    def setup_goal_status_tab(self, parent):
        """📈 목표 달성 현황 탭"""
        tk.Label(parent, text='📈 목표 달성 현황', 
                font=('Arial', 16, 'bold')).pack(pady=10)
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(parent)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 목표 현황 업데이트
        self.update_goal_status(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def save_daily_goal(self):
        """💾 일일 목표 저장"""
        try:
            work_hours = float(self.daily_work_hours.get() or 0)
            tasks = int(self.daily_tasks.get() or 0)
            focus = float(self.daily_focus.get() or 0)
            pomodoros = int(self.daily_pomodoros.get() or 0)
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 기존 목표 업데이트 또는 새로 생성
            cursor.execute('''
                INSERT OR REPLACE INTO goals 
                (goal_type, date_range, target_work_hours, target_tasks, 
                 target_focus_avg, target_pomodoros, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('daily', today, work_hours, tasks, focus, pomodoros, 
                  datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.add_log('💾 일일 목표가 저장되었습니다!')
            self.show_toast('💾 목표 저장', '오늘의 목표가 설정되었습니다!')
            
        except ValueError:
            self.show_toast('❌ 입력 오류', '숫자를 올바르게 입력해주세요!')
    
    def load_daily_goal(self):
        """📥 일일 목표 불러오기"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT target_work_hours, target_tasks, target_focus_avg, target_pomodoros
                FROM goals 
                WHERE goal_type = 'daily' AND date_range = ?
            ''', (today,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.daily_work_hours.delete(0, tk.END)
                self.daily_work_hours.insert(0, str(result[0]))
                
                self.daily_tasks.delete(0, tk.END)
                self.daily_tasks.insert(0, str(result[1]))
                
                self.daily_focus.delete(0, tk.END)
                self.daily_focus.insert(0, str(result[2]))
                
                self.daily_pomodoros.delete(0, tk.END)
                self.daily_pomodoros.insert(0, str(result[3]))
                
        except Exception as e:
            print(f'Load daily goal error: {e}')
    
    def save_weekly_goal(self):
        """💾 주간 목표 저장"""
        try:
            work_hours = float(self.weekly_work_hours.get() or 0)
            tasks = int(self.weekly_tasks.get() or 0)
            
            # 이번 주 계산 (ISO 주 번호)
            today = datetime.now()
            week_str = today.strftime('%Y-W%U')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO goals 
                (goal_type, date_range, target_work_hours, target_tasks, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', ('weekly', week_str, work_hours, tasks, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.add_log('💾 주간 목표가 저장되었습니다!')
            self.show_toast('💾 주간 목표', '이번 주 목표가 설정되었습니다!')
            
        except ValueError:
            self.show_toast('❌ 입력 오류', '숫자를 올바르게 입력해주세요!')
    
    def update_goal_status(self, parent):
        """📈 목표 달성 현황 업데이트"""
        try:
            # 기존 위젯들 제거
            for widget in parent.winfo_children():
                widget.destroy()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 오늘의 실제 성과 가져오기
            cursor.execute('''
                SELECT total_work_minutes, completed_tasks, avg_focus_rating
                FROM daily_stats 
                WHERE date = ?
            ''', (today,))
            
            actual = cursor.fetchone()
            actual_work_hours = (actual[0] / 60) if actual and actual[0] else 0
            actual_tasks = actual[1] if actual and actual[1] else 0
            actual_focus = actual[2] if actual and actual[2] else 0
            
            # 오늘의 목표 가져오기
            cursor.execute('''
                SELECT target_work_hours, target_tasks, target_focus_avg, target_pomodoros
                FROM goals 
                WHERE goal_type = 'daily' AND date_range = ?
            ''', (today,))
            
            target = cursor.fetchone()
            conn.close()
            
            if target:
                target_work, target_tasks_count, target_focus, target_pomodoros = target
                
                # 달성률 계산
                work_rate = (actual_work_hours / target_work * 100) if target_work > 0 else 0
                task_rate = (actual_tasks / target_tasks_count * 100) if target_tasks_count > 0 else 0
                focus_rate = (actual_focus / target_focus * 100) if target_focus > 0 else 0
                
                # 현황 표시
                tk.Label(parent, text='📊 오늘의 목표 달성 현황', 
                        font=('Arial', 14, 'bold')).pack(pady=10)
                
                status_frame = tk.Frame(parent)
                status_frame.pack(fill=tk.X, padx=20, pady=10)
                
                # 작업 시간 현황
                work_color = 'green' if work_rate >= 100 else 'orange' if work_rate >= 80 else 'red'
                tk.Label(status_frame, 
                        text=f'⏰ 작업 시간: {actual_work_hours:.1f}h / {target_work}h ({work_rate:.1f}%)',
                        fg=work_color, font=('Arial', 12)).pack(anchor=tk.W)
                
                # 완료 업무 현황
                task_color = 'green' if task_rate >= 100 else 'orange' if task_rate >= 80 else 'red'
                tk.Label(status_frame, 
                        text=f'✅ 완료 업무: {actual_tasks}개 / {target_tasks_count}개 ({task_rate:.1f}%)',
                        fg=task_color, font=('Arial', 12)).pack(anchor=tk.W)
                
                # 집중도 현황
                focus_color = 'green' if focus_rate >= 100 else 'orange' if focus_rate >= 80 else 'red'
                tk.Label(status_frame, 
                        text=f'🎯 평균 집중도: {actual_focus:.1f} / {target_focus} ({focus_rate:.1f}%)',
                        fg=focus_color, font=('Arial', 12)).pack(anchor=tk.W)
                
                # 전체 달성률
                overall_rate = (work_rate + task_rate + focus_rate) / 3
                overall_color = 'green' if overall_rate >= 90 else 'orange' if overall_rate >= 70 else 'red'
                
                tk.Label(parent, 
                        text=f'🏆 전체 달성률: {overall_rate:.1f}%',
                        fg=overall_color, font=('Arial', 16, 'bold')).pack(pady=20)
                
            else:
                tk.Label(parent, text='🎯 아직 목표가 설정되지 않았습니다\n일일 목표를 설정해보세요!', 
                        font=('Arial', 14)).pack(pady=50)
                
        except Exception as e:
                         tk.Label(parent, text=f'목표 현황 로드 오류: {e}', 
                     font=('Arial', 12)).pack(pady=50)
    
    def get_smart_schedule(self):
        """🔄 AI 스마트 일정 추천"""
        if not self.openai_key:
            self.add_log('❌ OpenAI API 키가 설정되지 않았습니다')
            self.show_toast('❌ AI 설정 필요', 'OpenAI API 키를 .env 파일에 추가해주세요')
            return
        
        try:
            self.add_log('🔄 AI 스마트 일정 생성 중...')
            self.show_toast('🔄 AI 분석 중', '최적의 업무 순서를 분석하고 있습니다...')
            
            # 오늘의 업무 목록 가져오기
            today_tasks = self.get_today_tasks()
            if not today_tasks:
                self.add_log('📝 오늘 등록된 업무가 없습니다')
                self.show_toast('📝 업무 없음', '먼저 노션에 오늘의 업무를 등록해주세요')
                return
            
            # AI 일정 추천 생성
            schedule_suggestion = self.generate_smart_schedule(today_tasks)
            
            # 스마트 일정 창 표시
            self.show_smart_schedule_window(schedule_suggestion, today_tasks)
            
            # 데이터베이스에 저장
            self.save_schedule_suggestion(schedule_suggestion)
            
        except Exception as e:
            self.add_log(f'❌ 스마트 일정 오류: {e}')
            self.show_toast('❌ AI 오류', f'일정 생성 실패: {str(e)[:50]}')
    
    def get_today_tasks(self):
        """📝 오늘의 업무 목록 가져오기"""
        try:
            if not self.tasks:
                return None
            
            tasks_info = []
            for task in self.tasks:
                task_name = 'Untitled'
                if (task['properties'].get('Task') and 
                    task['properties']['Task'].get('title') and 
                    len(task['properties']['Task']['title']) > 0):
                    task_name = task['properties']['Task']['title'][0]['plain_text']
                
                # 예상 소요시간 가져오기
                duration = 30  # 기본값 30분
                if task['properties'].get('Duration') and task['properties']['Duration'].get('number'):
                    duration = task['properties']['Duration']['number']
                
                # 우선순위 가져오기 (없으면 보통으로)
                priority = '보통'
                if (task['properties'].get('Priority') and 
                    task['properties']['Priority'].get('select')):
                    priority = task['properties']['Priority']['select']['name']
                
                # 상태 가져오기
                status = 'Not Started'
                if (task['properties'].get('Status') and 
                    task['properties']['Status'].get('select')):
                    status = task['properties']['Status']['select']['name']
                
                tasks_info.append({
                    'name': task_name,
                    'duration': duration,
                    'priority': priority,
                    'status': status
                })
            
            return tasks_info
            
        except Exception as e:
            print(f'Get today tasks error: {e}')
            return None
    
    def generate_smart_schedule(self, tasks):
        """🔄 AI 기반 스마트 일정 생성"""
        try:
            # 과거 생산성 패턴 분석
            productivity_pattern = self.analyze_productivity_pattern()
            
            # 현재 시간과 남은 시간 계산
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            
            # 업무 목록 정리
            task_list = "\n".join([
                f"- {task['name']} (예상: {task['duration']}분, 우선순위: {task['priority']}, 상태: {task['status']})"
                for task in tasks
            ])
            
            prompt = f"""
당신은 생산성 전문가입니다. 다음 정보를 바탕으로 최적의 업무 순서를 추천해주세요.

**현재 상황**
- 현재 시간: {current_time}
- 오늘 남은 업무들:
{task_list}

**생산성 패턴 분석**
{productivity_pattern}

**추천 기준**
1. 생산성이 높은 시간대에 중요하고 어려운 업무 배치
2. 에너지 소모가 큰 업무 후엔 가벼운 업무 배치
3. 뽀모도로 기법 고려 (25분 단위)
4. 우선순위와 예상 소요시간 고려

다음 형식으로 답변해주세요:

**🔄 추천 업무 순서**
1. [시간] 업무명 (소요시간, 이유)
2. [시간] 업무명 (소요시간, 이유)
...

**📋 추천 이유**
- 전체적인 배치 논리
- 생산성 최적화 포인트

**💡 추가 조언**
- 효율성 향상을 위한 팁
"""
            
            # OpenAI API 호출
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"스마트 일정 생성 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_productivity_pattern(self):
        """📊 개인 생산성 패턴 분석"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 최근 7일간의 시간대별 생산성 데이터
            cursor.execute('''
                SELECT start_time, focus_rating, duration_minutes
                FROM task_records 
                WHERE date >= date('now', '-7 days') AND status = 'Done'
                ORDER BY start_time
            ''')
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return "아직 충분한 데이터가 없습니다. 며칠 더 사용한 후 패턴 분석이 가능합니다."
            
            # 시간대별 평균 집중도 계산
            hourly_focus = {}
            for record in records:
                hour = int(record[0].split(':')[0])
                focus = record[1] or 3
                
                if hour not in hourly_focus:
                    hourly_focus[hour] = []
                hourly_focus[hour].append(focus)
            
            # 최고 생산성 시간대 찾기
            best_hours = []
            for hour, focuses in hourly_focus.items():
                avg_focus = sum(focuses) / len(focuses)
                if avg_focus >= 4.0:
                    best_hours.append(f"{hour:02d}시")
            
            pattern_text = f"""
**개인 생산성 패턴 분석**
- 총 분석 데이터: {len(records)}개 업무
- 고집중 시간대: {', '.join(best_hours) if best_hours else '패턴 분석 중'}
- 평균 업무 지속시간: {sum(r[2] or 0 for r in records) / len(records):.1f}분
"""
            return pattern_text
            
        except Exception as e:
            return f"패턴 분석 오류: {str(e)}"
    
    def show_smart_schedule_window(self, suggestion, tasks):
        """🔄 스마트 일정 창 표시"""
        schedule_window = tk.Toplevel(self.root)
        schedule_window.title('🔄 AI 스마트 일정 추천')
        schedule_window.geometry('700x600')
        
        # 스크롤 가능한 텍스트
        frame = tk.Frame(schedule_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                            font=('Arial', 11), padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert(tk.END, suggestion)
        text_widget.config(state=tk.DISABLED)
        
        # 버튼 프레임
        btn_frame = tk.Frame(schedule_window)
        btn_frame.pack(pady=10)
        
        accept_btn = tk.Button(btn_frame, text='✅ 일정 적용', 
                             command=lambda: self.accept_schedule(schedule_window),
                             bg='lightgreen', font=('Arial', 12, 'bold'))
        accept_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(btn_frame, text='닫기', 
                            command=schedule_window.destroy,
                            font=('Arial', 12, 'bold'))
        close_btn.pack(side=tk.LEFT, padx=10)
    
    def accept_schedule(self, window):
        """✅ AI 추천 일정 적용"""
        self.add_log('✅ AI 추천 일정을 적용했습니다!')
        self.show_toast('✅ 일정 적용', 'AI 추천 일정이 적용되었습니다!')
        window.destroy()
    
    def save_schedule_suggestion(self, suggestion):
        """💾 AI 일정 추천 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO ai_schedule_suggestions (date, suggested_order, reasoning)
                VALUES (?, ?, ?)
            ''', (today, suggestion, 'AI 기반 최적 순서 추천'))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f'Save schedule error: {e}')
    
    def get_productivity_prediction(self):
        """📈 생산성 예측 및 권장사항"""
        if not self.openai_key:
            self.add_log('❌ OpenAI API 키가 설정되지 않았습니다')
            self.show_toast('❌ AI 설정 필요', 'OpenAI API 키를 .env 파일에 추가해주세요')
            return
        
        try:
            self.add_log('📈 생산성 예측 분석 중...')
            self.show_toast('📈 AI 예측 중', '내일의 생산성을 예측하고 있습니다...')
            
            # 예측을 위한 데이터 수집
            prediction_data = self.collect_prediction_data()
            
            # AI 예측 생성
            prediction = self.generate_productivity_prediction(prediction_data)
            
            # 예측 결과 창 표시
            self.show_prediction_window(prediction)
            
        except Exception as e:
            self.add_log(f'❌ 생산성 예측 오류: {e}')
            self.show_toast('❌ AI 오류', f'예측 생성 실패: {str(e)[:50]}')
    
    def collect_prediction_data(self):
        """📊 예측을 위한 데이터 수집"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 최근 7일 데이터
            cursor.execute('''
                SELECT date, total_work_minutes, completed_tasks, avg_focus_rating
                FROM daily_stats 
                WHERE date >= date('now', '-7 days')
                ORDER BY date DESC
            ''', )
            
            daily_data = cursor.fetchall()
            
            # 최근 업무 패턴
            cursor.execute('''
                SELECT task_name, duration_minutes, focus_rating, start_time
                FROM task_records 
                WHERE date >= date('now', '-7 days') AND status = 'Done'
                ORDER BY date DESC
            ''')
            
            task_data = cursor.fetchall()
            
            # 목표 대비 달성률
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT target_work_hours, target_tasks, target_focus_avg
                FROM goals 
                WHERE goal_type = 'daily' AND date_range = ?
            ''', (today,))
            
            goal_data = cursor.fetchone()
            conn.close()
            
            return {
                'daily_stats': daily_data,
                'task_patterns': task_data,
                'current_goals': goal_data,
                'data_points': len(daily_data)
            }
            
        except Exception as e:
            print(f'Collect prediction data error: {e}')
            return None
    
    def generate_productivity_prediction(self, data):
        """📈 AI 기반 생산성 예측"""
        try:
            if not data or data['data_points'] < 3:
                return """📈 생산성 예측

❌ 예측을 위한 데이터가 부족합니다.
최소 3일 이상의 데이터가 필요합니다.

📝 권장사항:
- 며칠 더 꾸준히 사용해주세요
- 업무 완료 시 집중도 평가를 정확히 해주세요
- 목표를 설정하고 추적해보세요"""
            
            # 최근 패턴 분석
            daily_stats = data['daily_stats']
            task_patterns = data['task_patterns']
            
            # 평균값 계산
            avg_work_time = sum(stat[1] or 0 for stat in daily_stats) / len(daily_stats)
            avg_tasks = sum(stat[2] or 0 for stat in daily_stats) / len(daily_stats)
            avg_focus = sum(stat[3] or 0 for stat in daily_stats) / len(daily_stats)
            
            # 트렌드 분석
            recent_3_days = daily_stats[:3]
            recent_avg_focus = sum(stat[3] or 0 for stat in recent_3_days) / len(recent_3_days)
            
            trend = "상승" if recent_avg_focus > avg_focus else "하락" if recent_avg_focus < avg_focus else "안정"
            
            # 요일별 패턴 (간단히)
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_weekday = tomorrow.strftime('%A')
            
            prompt = f"""
당신은 생산성 분석 전문가입니다. 다음 데이터를 바탕으로 내일의 생산성을 예측하고 구체적인 권장사항을 제공해주세요.

**최근 7일 생산성 데이터**
- 평균 작업시간: {avg_work_time:.1f}분/일
- 평균 완료업무: {avg_tasks:.1f}개/일  
- 평균 집중도: {avg_focus:.1f}/5.0
- 최근 3일 집중도 트렌드: {trend}

**내일 정보**
- 요일: {tomorrow_weekday}
- 날짜: {tomorrow.strftime('%Y-%m-%d')}

**분석 요청**
다음 형식으로 예측 보고서를 작성해주세요:

**📈 내일 생산성 예측**
- 예상 집중도: X.X/5.0 (이유)
- 권장 작업시간: X시간 (이유)  
- 완료 가능 업무수: X개 (이유)

**⚡ 생산성 향상 전략**
1. 최적 시간대 활용 방법
2. 에너지 관리 방법
3. 집중력 향상 팁

**⚠️ 주의사항**
- 피해야 할 시간대나 상황
- 번아웃 방지 방법

**🎯 맞춤 권장사항**
- 구체적인 실행 계획
- 목표 조정 제안

친근하고 실용적인 조언을 제공해주세요.
"""
            
            # OpenAI API 호출
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"생산성 예측 생성 중 오류가 발생했습니다: {str(e)}"
    
    def show_prediction_window(self, prediction):
        """📈 생산성 예측 창 표시"""
        prediction_window = tk.Toplevel(self.root)
        prediction_window.title('📈 생산성 예측 & 권장사항')
        prediction_window.geometry('700x600')
        
        # 스크롤 가능한 텍스트
        frame = tk.Frame(prediction_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                            font=('Arial', 11), padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert(tk.END, prediction)
        text_widget.config(state=tk.DISABLED)
        
        # 닫기 버튼
        close_btn = tk.Button(prediction_window, text='닫기', 
                            command=prediction_window.destroy,
                            font=('Arial', 12, 'bold'))
        close_btn.pack(pady=10)

    def add_log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert("end", f'[{timestamp}] {message}\n')
        self.log_text.see("end")

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = SchedulerNotionTracker()
    app.run()
