# Ultimate Notion Tracker
import tkinter as tk
import requests
import time
from datetime import datetime
import winsound


class AwesomeNotionTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Awesome Notion Tracker')
        self.root.geometry('600x700')
        
        self.token = ''
        self.db_id = ''
        self.headers = {}
        self.tasks = []
        self.current_task = None
        self.start_time = None
        self.is_tracking = False
        
        self.load_config()
        self.setup_ui()
        self.update_timer()
    
    def load_config(self):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('NOTION_TOKEN='):
                        self.token = line.split('=', 1)[1]
                    elif line.startswith('NOTION_DATABASE_ID='):
                        self.db_id = line.split('=', 1)[1]
            
            if self.token and self.db_id:
                self.headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json',
                    'Notion-Version': '2022-06-28'
                }
        except Exception as e:
            print(f'Config error: {e}')

    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text=' Awesome Notion Tracker', 
                        font=('Arial', 16, 'bold'), fg='blue')
        title.pack(pady=15)
        
        # Status
        self.status_label = tk.Label(self.root, text=' Connected!', 
                                   fg='green', font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=5)
        
        # Load button
        load_btn = tk.Button(self.root, text=' Load Tasks', 
                           command=self.load_tasks, bg='lightblue', 
                           font=('Arial', 11, 'bold'))
        load_btn.pack(pady=10)
        
        # Task list
        self.task_listbox = tk.Listbox(self.root, height=8, font=('Arial', 10))
        self.task_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Current task
        self.current_label = tk.Label(self.root, text='No task selected', 
                                    font=('Arial', 11, 'bold'))
        self.current_label.pack(pady=5)
        
        # Timer
        self.timer_label = tk.Label(self.root, text='00:00:00', 
                                  font=('Arial', 20, 'bold'), fg='red')
        self.timer_label.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(btn_frame, text=' START', 
                                 command=self.start_task, bg='green', fg='white',
                                 font=('Arial', 12, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.complete_btn = tk.Button(btn_frame, text=' DONE', 
                                    command=self.complete_task, bg='orange', fg='white',
                                    font=('Arial', 12, 'bold'), state='disabled')
        self.complete_btn.pack(side=tk.LEFT, padx=10)
        
        # Log
        self.log_text = tk.Text(self.root, height=8, font=('Arial', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.add_log(' App started!')
        self.add_log('Click Load Tasks to begin')

    def load_tasks(self):
        if not self.headers:
            self.add_log('ERROR: Not configured')
            return
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            self.add_log(f'Loading tasks for {today}...')
            
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
                self.tasks = data.get('results', [])
                
                self.task_listbox.delete(0, tk.END)
                for task in self.tasks:
                    task_name = 'Untitled'
                    if (task['properties'].get('Task') and 
                        task['properties']['Task'].get('title') and 
                        len(task['properties']['Task']['title']) > 0):
                        task_name = task['properties']['Task']['title'][0]['plain_text']
                    
                    status = 'Not Started'
                    if (task['properties'].get('Status') and 
                        task['properties']['Status'].get('select')):
                        status = task['properties']['Status']['select']['name']
                    
                    emoji = '' if status == 'Done' else '' if status == 'In Progress' else ''
                    self.task_listbox.insert(tk.END, f'{emoji} {task_name} ({status})')
                
                self.add_log(f'SUCCESS: Loaded {len(self.tasks)} tasks')
                if len(self.tasks) == 0:
                    self.add_log('No tasks found. Create some in Notion!')
            else:
                self.add_log(f'ERROR: {response.status_code}')
        except Exception as e:
            self.add_log(f'ERROR: {str(e)}')

    def start_task(self):
        selection = self.task_listbox.curselection()
        if not selection:
            self.add_log('Please select a task first!')
            return
        
        if self.is_tracking:
            self.add_log('Already tracking a task!')
            return
        
        task_index = selection[0]
        self.current_task = self.tasks[task_index]
        
        task_name = 'Untitled'
        if (self.current_task['properties'].get('Task') and 
            self.current_task['properties']['Task'].get('title') and 
            len(self.current_task['properties']['Task']['title']) > 0):
            task_name = self.current_task['properties']['Task']['title'][0]['plain_text']
        
        self.current_label.config(text=f'Working: {task_name}')
        self.start_time = time.time()
        self.is_tracking = True
        
        self.start_btn.config(state='disabled')
        self.complete_btn.config(state='normal')
        
        try:
            winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)
        except:
            pass
        
        self.add_log(f'STARTED: {task_name}')
        self.update_notion_status('In Progress')
    
    def complete_task(self):
        if not self.is_tracking or not self.current_task:
            return
        
        duration_seconds = int(time.time() - self.start_time)
        duration_minutes = max(1, duration_seconds // 60)
        
        task_name = 'Untitled'
        if (self.current_task['properties'].get('Task') and 
            self.current_task['properties']['Task'].get('title') and 
            len(self.current_task['properties']['Task']['title']) > 0):
            task_name = self.current_task['properties']['Task']['title'][0]['plain_text']
        
        self.is_tracking = False
        self.current_label.config(text='Task completed!')
        self.timer_label.config(text='00:00:00')
        
        self.start_btn.config(state='normal')
        self.complete_btn.config(state='disabled')
        
        try:
            winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
        except:
            pass
        
        self.add_log(f'COMPLETED: {task_name} ({duration_minutes} min)')
        self.update_notion_status('Done', duration_minutes)
        
        self.current_task = None
        self.start_time = None
        
        from tkinter import messagebox
        messagebox.showinfo('Success!', f'Task completed!\nTime: {duration_minutes} minutes')

    def update_notion_status(self, status, duration=None):
        if not self.current_task or not self.headers:
            return
        
        try:
            page_id = self.current_task['id']
            url = f'https://api.notion.com/v1/pages/{page_id}'
            
            update_data = {
                'properties': {
                    'Status': {
                        'select': {
                            'name': status
                        }
                    }
                }
            }
            
            if duration is not None:
                update_data['properties']['Duration'] = {
                    'number': duration
                }
            
            response = requests.patch(url, headers=self.headers, json=update_data)
            
            if response.status_code == 200:
                self.add_log(f'NOTION: Status  {status}')
                if duration:
                    self.add_log(f'NOTION: Duration  {duration} min')
            else:
                self.add_log(f'NOTION ERROR: {response.status_code}')
        except Exception as e:
            self.add_log(f'NOTION ERROR: {str(e)}')
    
    def update_timer(self):
        if self.is_tracking and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            time_str = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
            self.timer_label.config(text=time_str)
            
            if elapsed < 1800:
                self.timer_label.config(fg='green')
            elif elapsed < 3600:
                self.timer_label.config(fg='orange')
            else:
                self.timer_label.config(fg='red')
        
        self.root.after(1000, self.update_timer)
    
    def add_log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f'[{timestamp}] {message}\n')
        self.log_text.see(tk.END)
        self.root.update()
    
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = AwesomeNotionTracker()
    app.run()
