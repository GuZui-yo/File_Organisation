#!/usr/bin/env python3
"""
超简化文件整理工具 - 无任何外部依赖
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

class SimpleFileOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("文件整理工具")
        self.root.geometry("600x500")
        
        # 变量
        self.source_dir = tk.StringVar(value=str(Path.home() / "Downloads"))
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 标题
        title = tk.Label(self.root, text="文件整理工具", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # 目录选择
        frame1 = tk.Frame(self.root)
        frame1.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(frame1, text="选择目录:").pack(side=tk.LEFT)
        tk.Entry(frame1, textvariable=self.source_dir, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(frame1, text="浏览", command=self.browse_dir).pack(side=tk.LEFT)
        
        # 选项
        frame2 = tk.Frame(self.root)
        frame2.pack(pady=10, padx=20, fill=tk.X)
        
        self.org_type = tk.StringVar(value="type")
        tk.Label(frame2, text="整理方式:").pack(anchor=tk.W)
        tk.Radiobutton(frame2, text="按文件类型", variable=self.org_type, value="type").pack(anchor=tk.W)
        tk.Radiobutton(frame2, text="按修改日期", variable=self.org_type, value="date").pack(anchor=tk.W)
        
        self.create_backup = tk.BooleanVar(value=True)
        tk.Checkbutton(frame2, text="创建备份", variable=self.create_backup).pack(anchor=tk.W)
        
        # 按钮
        frame3 = tk.Frame(self.root)
        frame3.pack(pady=20)
        
        tk.Button(frame3, text="开始整理", command=self.start_organize, 
                 bg="green", fg="white", font=("Arial", 12), padx=20).pack(side=tk.LEFT, padx=5)
        tk.Button(frame3, text="清理空文件夹", command=self.cleanup).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        frame4 = tk.Frame(self.root)
        frame4.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(frame4, text="操作日志:").pack(anchor=tk.W)
        self.log_text = tk.Text(frame4, height=10)
        scrollbar = tk.Scrollbar(frame4, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        self.status = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.source_dir.get())
        if dir_path:
            self.source_dir.set(dir_path)
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def start_organize(self):
        source_path = Path(self.source_dir.get())
        if not source_path.exists():
            messagebox.showerror("错误", "目录不存在！")
            return
        
        self.status.config(text="正在整理...")
        
        try:
            # 文件分类定义
            categories = {
                '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
                '文档': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'],
                '音频': ['.mp3', '.wav'],
                '视频': ['.mp4', '.avi', '.mkv'],
                '其他': []
            }
            
            # 创建备份
            if self.create_backup.get():
                backup_path = source_path.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.log(f"创建备份: {backup_path}")
                shutil.copytree(source_path, backup_path)
            
            count = 0
            for item in source_path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    
                    if self.org_type.get() == 'date':
                        # 按日期整理
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        folder_name = mtime.strftime("%Y-%m")
                        target_dir = source_path / folder_name
                    else:
                        # 按类型整理
                        category = '其他'
                        for cat, exts in categories.items():
                            if ext in exts:
                                category = cat
                                break
                        target_dir = source_path / category
                    
                    target_dir.mkdir(exist_ok=True)
                    
                    # 移动文件
                    target_file = target_dir / item.name
                    shutil.move(str(item), str(target_file))
                    
                    self.log(f"移动: {item.name} -> {target_dir.name}/")
                    count += 1
            
            self.log(f"\n整理完成！共处理 {count} 个文件")
            self.status.config(text="整理完成")
            
        except Exception as e:
            self.log(f"错误: {e}")
            self.status.config(text="整理出错")
    
    def cleanup(self):
        source_path = Path(self.source_dir.get())
        if not source_path.exists():
            messagebox.showerror("错误", "目录不存在！")
            return
        
        self.status.config(text="正在清理空文件夹...")
        
        try:
            count = 0
            for root, dirs, files in os.walk(source_path, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            self.log(f"删除空文件夹: {dir_path}")
                            count += 1
                    except:
                        pass
            
            self.log(f"\n清理完成！共删除 {count} 个空文件夹")
            self.status.config(text="清理完成")
            
        except Exception as e:
            self.log(f"错误: {e}")
            self.status.config(text="清理出错")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleFileOrganizer(root)
    root.mainloop()