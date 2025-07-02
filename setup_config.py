import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import os
from pathlib import Path

class SetupWindow:
    def __init__(self):
        # CustomTkinter 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("토스트 트래커 - 초기 설정")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 설정값 저장용
        self.config_data = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        # 헤더
        header_label = ctk.CTkLabel(
            self.root,
            text="🍞 토스트 트래커 초기 설정",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header_label.pack(pady=30)
        
        # 설명
        desc_label = ctk.CTkLabel(
            self.root,
            text="Notion과 OpenAI 연동을 위해 아래 정보를 입력해주세요.",
            font=ctk.CTkFont(size=14)
        )
        desc_label.pack(pady=(0, 30))
        
        # 입력 프레임
        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(fill="x", padx=30, pady=20)
        
        # Notion Token
        notion_label = ctk.CTkLabel(
            input_frame,
            text="Notion Integration Token:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        notion_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        self.notion_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="secret_xxxxxxxxxxxxxxxx",
            width=400,
            height=35
        )
        self.notion_entry.pack(padx=20, pady=(0, 15))
        
        # Database ID
        db_label = ctk.CTkLabel(
            input_frame,
            text="Notion Database ID:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        db_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.db_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            width=400,
            height=35
        )
        self.db_entry.pack(padx=20, pady=(0, 15))
        
        # OpenAI API Key
        openai_label = ctk.CTkLabel(
            input_frame,
            text="OpenAI API Key:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        openai_label.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.openai_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            width=400,
            height=35
        )
        self.openai_entry.pack(padx=20, pady=(0, 20))
        
        # 버튼들
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(fill="x", padx=30, pady=20)
        
        # 도움말 버튼
        help_btn = ctk.CTkButton(
            button_frame,
            text="📋 설정 도움말",
            command=self.show_help,
            font=ctk.CTkFont(size=12),
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=120,
            height=35
        )
        help_btn.pack(side="left", padx=20, pady=20)
        
        # 저장 버튼
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 설정 저장 & 시작",
            command=self.save_config,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            width=200,
            height=35
        )
        save_btn.pack(side="right", padx=20, pady=20)
        
    def show_help(self):
        help_text = """
🔧 설정 도움말

1. Notion Integration Token:
   - https://www.notion.so/my-integrations 에서 새 통합 생성
   - 생성된 토큰을 복사하여 입력

2. Notion Database ID:
   - 업무 관리용 Notion 데이터베이스 URL에서 추출
   - 예: notion.so/myworkspace/database_id?v=...
   - 필요한 속성: Task(제목), Type(선택), Time(날짜), Priority(선택), Status(선택)

3. OpenAI API Key:
   - https://platform.openai.com/api-keys 에서 생성
   - AI 피드백 기능에 사용됩니다
        """
        
        messagebox.showinfo("설정 도움말", help_text)
    
    def save_config(self):
        notion_token = self.notion_entry.get().strip()
        db_id = self.db_entry.get().strip()
        openai_key = self.openai_entry.get().strip()
        
        # 유효성 검사
        if not notion_token:
            messagebox.showerror("오류", "Notion Token을 입력해주세요.")
            return
        if not db_id:
            messagebox.showerror("오류", "Database ID를 입력해주세요.")
            return
        if not openai_key:
            messagebox.showerror("오류", "OpenAI API Key를 입력해주세요.")
            return
            
        # .env 파일 생성
        env_content = f"""NOTION_TOKEN={notion_token}
NOTION_DATABASE_ID={db_id}
OPENAI_API_KEY={openai_key}
"""
        
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            messagebox.showinfo("완료", "설정이 저장되었습니다!\n토스트 트래커를 시작합니다.")
            self.root.destroy()
            
            # 메인 앱 실행
            import subprocess
            subprocess.Popen(['python', 'toast_tracker.py'])
            
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {str(e)}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SetupWindow()
    app.run() 