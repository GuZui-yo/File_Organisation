#!/usr/bin/env python3
"""
文件整理工具 - GUI版本
功能：图形化文件整理工具，支持拖拽、批量整理、预览等功能
"""

import os
import sys
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import hashlib

# GUI库 - 使用tkinter，Python标准库
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkfont
from PIL import Image, ImageTk
import queue

# 文件类型分类配置
FILE_CATEGORIES = {
    '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
    '文档': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.md', '.rtf'],
    '音频': ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.wma', '.ogg'],
    '视频': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v', '.webm'],
    '压缩包': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
    '程序代码': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.html', '.css', '.php', '.json', '.xml', '.yml'],
    '安装包': ['.msi', '.dmg', '.pkg', '.deb', '.rpm', '.apk'],
    '字体': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
    '电子书': ['.epub', '.mobi', '.azw3'],
    '设计文件': ['.psd', '.ai', '.sketch', '.fig', '.xd'],
    'exe程序': ['.exe'],
    '其他': []  # 未分类文件
}

# 分类颜色配置
CATEGORY_COLORS = {
    '图片': '#FF6B6B',
    '文档': '#4ECDC4',
    '音频': '#45B7D1',
    '视频': '#96CEB4',
    '压缩包': '#FFEAA7',
    '程序代码': '#DDA0DD',
    '安装包': '#F8C291',
    '字体': '#C7CEEA',
    '电子书': '#B5EAD7',
    '设计文件': '#FFDAC1',
    '其他': '#E0E0E0'
}

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("智能文件整理工具 v2.0")
        self.root.geometry("1000x700")
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 初始化变量
        self.source_dir = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.dest_dir = tk.StringVar(value=str(Path.home() / "Downloads" / "已整理"))
        self.org_mode = tk.StringVar(value="type")
        self.create_backup = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=False)
        self.thread_running = False
        self.log_queue = queue.Queue()
        self.files_to_process = []
        self.stats = defaultdict(int)
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 启动日志更新定时器
        self.update_log()
        
        # 加载示例图片
        self.load_sample_images()

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 尝试加载图标文件，如果没有则创建简单图标
            icon_image = tk.PhotoImage(width=16, height=16)
            self.root.iconphoto(True, icon_image)
        except:
            pass

    def setup_styles(self):
        """设置自定义样式"""
        # 创建样式对象
        style = ttk.Style()
        
        # 配置按钮样式
        style.configure('Primary.TButton', font=('微软雅黑', 10, 'bold'))
        style.configure('Success.TButton', font=('微软雅黑', 10), foreground='green')
        style.configure('Warning.TButton', font=('微软雅黑', 10), foreground='orange')
        
        # 配置标签页样式
        style.configure('TNotebook.Tab', font=('微软雅黑', 10))
        style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'))

    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(4, weight=1)
        
        # 标题
        title_label = ttk.Label(main_container, 
                               text="📁 智能文件整理工具", 
                               font=('微软雅黑', 18, 'bold'),
                               foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 创建标签页
        notebook = ttk.Notebook(main_container)
        notebook.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 基本整理标签页
        self.setup_basic_tab(notebook)
        
        # 高级功能标签页
        self.setup_advanced_tab(notebook)
        
        # 文件统计标签页
        self.setup_stats_tab(notebook)
        
        # 日志区域
        self.setup_log_area(main_container)
        
        # 状态栏
        self.setup_status_bar(main_container)

    def setup_basic_tab(self, notebook):
        """创建基本整理标签页"""
        basic_frame = ttk.Frame(notebook, padding="15")
        notebook.add(basic_frame, text="基本整理")
        
        # 目录选择区域
        dir_frame = ttk.LabelFrame(basic_frame, text="目录设置", padding="10")
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 源目录
        ttk.Label(dir_frame, text="源目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.source_dir, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=self.browse_source_dir, 
                  style='Primary.TButton').grid(row=0, column=2, padx=5)
        
        # 目标目录
        ttk.Label(dir_frame, text="目标目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.dest_dir, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=self.browse_dest_dir).grid(row=1, column=2, padx=5)
        
        # 整理选项区域
        options_frame = ttk.LabelFrame(basic_frame, text="整理选项", padding="10")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 整理方式
        ttk.Label(options_frame, text="整理方式:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Radiobutton(options_frame, text="按文件类型", variable=self.org_mode, value="type").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="按修改日期", variable=self.org_mode, value="date").grid(row=0, column=2, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="按文件大小", variable=self.org_mode, value="size").grid(row=0, column=3, sticky=tk.W)
        
        # 额外选项
        ttk.Checkbutton(options_frame, text="创建备份", variable=self.create_backup).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Checkbutton(options_frame, text="模拟运行（不实际移动文件）", variable=self.dry_run).grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=5)
        
        # 文件预览区域
        preview_frame = ttk.LabelFrame(basic_frame, text="文件预览", padding="10")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), pady=(0, 15))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        
        # 文件列表
        columns = ('name', 'type', 'size', 'date')
        self.file_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=10)
        
        # 设置列
        self.file_tree.heading('name', text='文件名')
        self.file_tree.heading('type', text='类型')
        self.file_tree.heading('size', text='大小')
        self.file_tree.heading('date', text='修改日期')
        
        self.file_tree.column('name', width=200)
        self.file_tree.column('type', width=80)
        self.file_tree.column('size', width=80)
        self.file_tree.column('date', width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 分类预览区域
        category_frame = ttk.LabelFrame(basic_frame, text="分类预览", padding="10")
        category_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        category_frame.rowconfigure(0, weight=1)
        category_frame.columnconfigure(0, weight=1)
        
        # 分类标签容器
        self.category_canvas = tk.Canvas(category_frame, bg='white', height=250)
        self.category_scrollbar = ttk.Scrollbar(category_frame, orient=tk.VERTICAL, command=self.category_canvas.yview)
        self.category_frame = ttk.Frame(self.category_canvas)
        
        self.category_canvas.create_window((0, 0), window=self.category_frame, anchor=tk.NW)
        self.category_canvas.configure(yscrollcommand=self.category_scrollbar.set)
        
        # 布局
        self.category_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.category_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 按钮区域
        button_frame = ttk.Frame(basic_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="📁 扫描目录", 
                  command=self.scan_directory,
                  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 开始整理", 
                  command=self.start_organize,
                  style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ 清空列表", 
                  command=self.clear_file_list).pack(side=tk.LEFT, padx=5)

    def setup_advanced_tab(self, notebook):
        """创建高级功能标签页"""
        advanced_frame = ttk.Frame(notebook, padding="15")
        notebook.add(advanced_frame, text="高级功能")
        
        # 重复文件查找
        dup_frame = ttk.LabelFrame(advanced_frame, text="重复文件查找", padding="10")
        dup_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(dup_frame, text="查找方式:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dup_method = tk.StringVar(value="name_size")
        ttk.Radiobutton(dup_frame, text="文件名+大小", variable=self.dup_method, value="name_size").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(dup_frame, text="文件内容(MD5)", variable=self.dup_method, value="content").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Button(dup_frame, text="🔍 开始查找", 
                  command=self.find_duplicates,
                  style='Warning.TButton').grid(row=1, column=0, columnspan=3, pady=10)
        
        # 空文件夹清理
        cleanup_frame = ttk.LabelFrame(advanced_frame, text="空文件夹清理", padding="10")
        cleanup_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(cleanup_frame, text="清理选项:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cleanup_preview = tk.BooleanVar(value=True)
        ttk.Checkbutton(cleanup_frame, text="先预览再清理", variable=self.cleanup_preview).grid(row=0, column=1, columnspan=2, sticky=tk.W)
        
        ttk.Button(cleanup_frame, text="🧹 清理空文件夹", 
                  command=self.cleanup_empty_folders).grid(row=1, column=0, columnspan=3, pady=10)
        
        # 批量重命名
        rename_frame = ttk.LabelFrame(advanced_frame, text="批量重命名", padding="10")
        rename_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(rename_frame, text="命名规则:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.rename_pattern = tk.StringVar(value="file_{num:03d}{ext}")
        ttk.Entry(rename_frame, textvariable=self.rename_pattern, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(rename_frame, text="起始编号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_num = tk.IntVar(value=1)
        ttk.Spinbox(rename_frame, from_=1, to=9999, textvariable=self.start_num, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(rename_frame, text="✏️ 批量重命名", 
                  command=self.batch_rename).grid(row=2, column=0, columnspan=2, pady=10)

    def setup_stats_tab(self, notebook):
        """创建文件统计标签页"""
        stats_frame = ttk.Frame(notebook, padding="15")
        notebook.add(stats_frame, text="文件统计")
        
        # 统计图区域
        self.stats_canvas = tk.Canvas(stats_frame, bg='white', width=600, height=300)
        self.stats_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 详细信息区域
        details_frame = ttk.LabelFrame(stats_frame, text="详细信息", padding="10")
        details_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建文本区域显示详细信息
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10, width=70)
        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 统计按钮
        ttk.Button(stats_frame, text="📊 生成统计", 
                  command=self.generate_stats).grid(row=2, column=0, pady=10)

    def setup_log_area(self, parent):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 创建滚动文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        parent.rowconfigure(4, weight=1)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # 添加日志工具栏
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(log_toolbar, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_toolbar, text="保存日志", command=self.save_log).pack(side=tk.LEFT, padx=2)

    def setup_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN)
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)

    def load_sample_images(self):
        """加载示例图标"""
        try:
            # 这里可以加载一些图标图像
            pass
        except Exception as e:
            self.log_message(f"加载图标时出错: {e}")

    def browse_source_dir(self):
        """浏览源目录"""
        directory = filedialog.askdirectory(initialdir=self.source_dir.get())
        if directory:
            self.source_dir.set(directory)
            self.scan_directory()

    def browse_dest_dir(self):
        """浏览目标目录"""
        directory = filedialog.askdirectory(initialdir=self.dest_dir.get())
        if directory:
            self.dest_dir.set(directory)

    def scan_directory(self):
        """扫描目录并显示文件列表"""
        source_path = Path(self.source_dir.get())
        if not source_path.exists():
            messagebox.showerror("错误", "源目录不存在！")
            return
        
        # 清空现有文件列表
        self.file_tree.delete(*self.file_tree.get_children())
        self.files_to_process = []
        
        # 更新状态
        self.status_label.config(text="正在扫描目录...")
        self.progress_var.set(0)
        
        # 在新线程中扫描
        threading.Thread(target=self._scan_directory_thread, args=(source_path,), daemon=True).start()

    def _scan_directory_thread(self, source_path):
        """扫描目录的线程函数"""
        try:
            file_count = 0
            max_files = 1000  # 限制显示的文件数量
            
            # 遍历目录
            for item in source_path.rglob('*'):
                if item.is_file():
                    if file_count >= max_files:
                        self.log_message(f"已显示 {max_files} 个文件，停止扫描更多文件")
                        break
                    
                    # 获取文件信息
                    file_info = {
                        'path': item,
                        'name': item.name,
                        'size': self.format_file_size(item.stat().st_size),
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'category': self.get_file_category(item.suffix)
                    }
                    
                    self.files_to_process.append(file_info)
                    file_count += 1
                    
                    # 每100个文件更新一次UI
                    if file_count % 100 == 0:
                        self.root.after(0, self._update_file_tree, file_count)
                        time.sleep(0.01)  # 防止UI卡死
            
            # 最终更新UI
            self.root.after(0, self._update_file_tree, file_count)
            self.root.after(0, self._update_category_preview)
            
            self.log_message(f"扫描完成，找到 {file_count} 个文件")
            self.root.after(0, lambda: self.status_label.config(text="扫描完成"))
            
        except Exception as e:
            self.log_message(f"扫描目录时出错: {e}")
            self.root.after(0, lambda: self.status_label.config(text="扫描出错"))

    def _update_file_tree(self, file_count):
        """更新文件树显示"""
        # 只显示最新的文件
        start_index = max(0, len(self.files_to_process) - 100)
        
        for file_info in self.files_to_process[start_index:]:
            self.file_tree.insert('', 'end', values=(
                file_info['name'],
                file_info['category'],
                file_info['size'],
                file_info['modified']
            ))
        
        self.progress_var.set(min(100, file_count / 10))

    def _update_category_preview(self):
        """更新分类预览"""
        # 清空现有分类预览
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        # 统计各分类文件数量
        category_counts = defaultdict(int)
        for file_info in self.files_to_process:
            category_counts[file_info['category']] += 1
        
        # 显示分类标签
        row = 0
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            color = CATEGORY_COLORS.get(category, '#E0E0E0')
            
            # 创建分类标签
            category_label = tk.Label(self.category_frame, 
                                     text=f"{category}: {count} 个文件",
                                     bg=color,
                                     fg='black' if self.get_brightness(color) > 128 else 'white',
                                     font=('微软雅黑', 10),
                                     padx=10,
                                     pady=5,
                                     relief=tk.RAISED,
                                     borderwidth=2)
            category_label.grid(row=row, column=0, sticky=tk.W, pady=2, padx=2)
            row += 1
        
        # 更新画布滚动区域
        self.category_frame.update_idletasks()
        self.category_canvas.configure(scrollregion=self.category_canvas.bbox("all"))

    def get_brightness(self, hex_color):
        """计算颜色亮度"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r * 299 + g * 587 + b * 114) / 1000

    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def get_file_category(self, extension):
        """根据扩展名获取文件分类"""
        extension = extension.lower()
        for category, extensions in FILE_CATEGORIES.items():
            if extension in extensions:
                return category
        return '其他'

    def start_organize(self):
        """开始整理文件"""
        if not self.files_to_process:
            messagebox.showwarning("警告", "请先扫描目录！")
            return
        
        if self.thread_running:
            messagebox.showwarning("警告", "已有任务正在运行！")
            return
        
        # 在新线程中运行整理
        self.thread_running = True
        threading.Thread(target=self._organize_thread, daemon=True).start()

    def _organize_thread(self):
        """整理文件的线程函数"""
        try:
            source_path = Path(self.source_dir.get())
            dest_path = Path(self.dest_dir.get())
            
            # 创建目标目录
            if not self.dry_run.get():
                dest_path.mkdir(parents=True, exist_ok=True)
            
            # 创建备份
            if self.create_backup.get() and not self.dry_run.get():
                backup_path = source_path.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.log_message(f"创建备份: {backup_path}")
                shutil.copytree(source_path, backup_path)
            
            total = len(self.files_to_process)
            processed = 0
            
            for file_info in self.files_to_process:
                try:
                    if self.org_mode.get() == 'date':
                        # 按日期整理
                        file_date = datetime.fromtimestamp(file_info['path'].stat().st_mtime)
                        folder_name = file_date.strftime("%Y-%m")
                        target_dir = dest_path / folder_name
                    elif self.org_mode.get() == 'size':
                        # 按大小整理
                        size = file_info['path'].stat().st_size
                        if size < 1024 * 1024:  # < 1MB
                            folder_name = "小于1MB"
                        elif size < 1024 * 1024 * 10:  # < 10MB
                            folder_name = "1MB-10MB"
                        elif size < 1024 * 1024 * 100:  # < 100MB
                            folder_name = "10MB-100MB"
                        else:
                            folder_name = "大于100MB"
                        target_dir = dest_path / folder_name
                    else:
                        # 按类型整理
                        target_dir = dest_path / file_info['category']
                    
                    if not self.dry_run.get():
                        target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 移动文件
                    target_file = target_dir / file_info['path'].name
                    
                    if not self.dry_run.get():
                        # 处理文件名冲突
                        counter = 1
                        while target_file.exists():
                            name_parts = file_info['path'].stem.split('_')
                            if len(name_parts) > 1 and name_parts[-1].isdigit():
                                base_name = '_'.join(name_parts[:-1])
                            else:
                                base_name = file_info['path'].stem
                            new_name = f"{base_name}_{counter}{file_info['path'].suffix}"
                            target_file = target_dir / new_name
                            counter += 1
                        
                        shutil.move(str(file_info['path']), str(target_file))
                        self.log_message(f"✓ 移动: {file_info['name']} -> {target_dir.name}/")
                    else:
                        self.log_message(f"[模拟] 移动: {file_info['name']} -> {target_dir.name}/")
                    
                    processed += 1
                    progress = (processed / total) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                    time.sleep(0.01)  # 防止UI卡死
                    
                except Exception as e:
                    self.log_message(f"✗ 错误: {file_info['name']} - {e}")
            
            self.log_message(f"\n整理完成！共处理 {processed}/{total} 个文件")
            self.root.after(0, lambda: self.status_label.config(text="整理完成"))
            
        except Exception as e:
            self.log_message(f"整理过程中出错: {e}")
        finally:
            self.thread_running = False

    def find_duplicates(self):
        """查找重复文件"""
        source_path = Path(self.source_dir.get())
        if not source_path.exists():
            messagebox.showerror("错误", "目录不存在！")
            return
        
        # 在新线程中查找
        threading.Thread(target=self._find_duplicates_thread, args=(source_path,), daemon=True).start()

    def _find_duplicates_thread(self, source_path):
        """查找重复文件的线程函数"""
        try:
            self.log_message("开始查找重复文件...")
            
            if self.dup_method.get() == 'content':
                duplicates = self.find_duplicates_by_content(source_path)
            else:
                duplicates = self.find_duplicates_by_name_size(source_path)
            
            if duplicates:
                self.log_message(f"\n找到 {len(duplicates)} 组重复文件:")
                for i, (original, dups) in enumerate(duplicates.items(), 1):
                    self.log_message(f"\n{i}. {original}:")
                    for dup in dups:
                        self.log_message(f"   - {dup}")
            else:
                self.log_message("未找到重复文件")
            
            self.root.after(0, lambda: self.status_label.config(text="重复文件查找完成"))
            
        except Exception as e:
            self.log_message(f"查找重复文件时出错: {e}")

    def find_duplicates_by_name_size(self, directory):
        """通过文件名和大小查找重复文件"""
        file_dict = {}
        duplicates = {}
        
        for item in directory.rglob('*'):
            if item.is_file():
                key = (item.name.lower(), item.stat().st_size)
                if key in file_dict:
                    if file_dict[key] not in duplicates:
                        duplicates[file_dict[key]] = []
                    duplicates[file_dict[key]].append(str(item))
                else:
                    file_dict[key] = str(item)
        
        return duplicates

    def find_duplicates_by_content(self, directory):
        """通过文件内容(MD5)查找重复文件"""
        file_hashes = {}
        duplicates = {}
        
        for item in directory.rglob('*'):
            if item.is_file():
                try:
                    file_hash = self.calculate_md5(item)
                    if file_hash in file_hashes:
                        if file_hashes[file_hash] not in duplicates:
                            duplicates[file_hashes[file_hash]] = []
                        duplicates[file_hashes[file_hash]].append(str(item))
                    else:
                        file_hashes[file_hash] = str(item)
                except Exception as e:
                    self.log_message(f"计算文件哈希时出错 {item}: {e}")
        
        return duplicates

    def calculate_md5(self, filepath):
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def cleanup_empty_folders(self):
        """清理空文件夹"""
        source_path = Path(self.source_dir.get())
        if not source_path.exists():
            messagebox.showerror("错误", "目录不存在！")
            return
        
        # 在新线程中清理
        threading.Thread(target=self._cleanup_thread, args=(source_path,), daemon=True).start()

    def _cleanup_thread(self, source_path):
        """清理空文件夹的线程函数"""
        try:
            empty_folders = []
            
            for root, dirs, files in os.walk(source_path, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                            empty_folders.append(str(dir_path))
                    except Exception as e:
                        self.log_message(f"无法访问 {dir_path}: {e}")
            
            if empty_folders:
                self.log_message(f"\n找到 {len(empty_folders)} 个空文件夹:")
                for folder in empty_folders:
                    self.log_message(f"  - {folder}")
                
                if not self.cleanup_preview.get():
                    for folder in empty_folders:
                        try:
                            Path(folder).rmdir()
                            self.log_message(f"✓ 删除: {folder}")
                        except Exception as e:
                            self.log_message(f"✗ 删除失败 {folder}: {e}")
                else:
                    self.log_message("\n预览模式，未实际删除")
            else:
                self.log_message("未找到空文件夹")
            
            self.root.after(0, lambda: self.status_label.config(text="空文件夹清理完成"))
            
        except Exception as e:
            self.log_message(f"清理空文件夹时出错: {e}")

    def batch_rename(self):
        """批量重命名文件"""
        if not self.files_to_process:
            messagebox.showwarning("警告", "请先扫描目录！")
            return
        
        # 在新线程中重命名
        threading.Thread(target=self._rename_thread, daemon=True).start()

    def _rename_thread(self):
        """批量重命名的线程函数"""
        try:
            pattern = self.rename_pattern.get()
            start_num = self.start_num.get()
            
            for i, file_info in enumerate(self.files_to_process):
                try:
                    old_path = file_info['path']
                    new_name = pattern.format(
                        num=start_num + i,
                        name=old_path.stem,
                        ext=old_path.suffix
                    )
                    
                    new_path = old_path.parent / new_name
                    
                    if not self.dry_run.get():
                        old_path.rename(new_path)
                        self.log_message(f"✓ 重命名: {old_path.name} -> {new_name}")
                    else:
                        self.log_message(f"[模拟] 重命名: {old_path.name} -> {new_name}")
                    
                    time.sleep(0.01)
                    
                except Exception as e:
                    self.log_message(f"✗ 重命名失败 {file_info['name']}: {e}")
            
            self.log_message("\n批量重命名完成")
            self.root.after(0, lambda: self.status_label.config(text="重命名完成"))
            
        except Exception as e:
            self.log_message(f"批量重命名时出错: {e}")

    def generate_stats(self):
        """生成文件统计"""
        if not self.files_to_process:
            messagebox.showwarning("警告", "请先扫描目录！")
            return
        
        # 统计文件信息
        total_size = 0
        category_stats = defaultdict(lambda: {'count': 0, 'size': 0})
        
        for file_info in self.files_to_process:
            size = file_info['path'].stat().st_size
            total_size += size
            category_stats[file_info['category']]['count'] += 1
            category_stats[file_info['category']]['size'] += size
        
        # 更新详细信息
        self.details_text.delete(1.0, tk.END)
        
        self.details_text.insert(tk.END, "文件统计报告\n")
        self.details_text.insert(tk.END, "="*50 + "\n\n")
        self.details_text.insert(tk.END, f"总文件数: {len(self.files_to_process)}\n")
        self.details_text.insert(tk.END, f"总大小: {self.format_file_size(total_size)}\n\n")
        
        self.details_text.insert(tk.END, "按类型统计:\n")
        for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            percentage = (stats['count'] / len(self.files_to_process)) * 100
            self.details_text.insert(tk.END, 
                f"  {category}: {stats['count']} 个文件 ({percentage:.1f}%), "
                f"大小: {self.format_file_size(stats['size'])}\n")
        
        # 绘制统计图
        self.draw_stats_chart(category_stats)
        
        self.log_message("统计报告已生成")
        self.root.after(0, lambda: self.status_label.config(text="统计完成"))

    def draw_stats_chart(self, category_stats):
        """绘制统计图表"""
        self.stats_canvas.delete("all")
        
        if not category_stats:
            return
        
        # 图表尺寸
        canvas_width = 600
        canvas_height = 300
        margin = 50
        chart_width = canvas_width - 2 * margin
        chart_height = canvas_height - 2 * margin
        
        # 绘制坐标轴
        self.stats_canvas.create_line(margin, canvas_height - margin, 
                                      canvas_width - margin, canvas_height - margin, width=2)
        self.stats_canvas.create_line(margin, margin, margin, canvas_height - margin, width=2)
        
        # 获取数据
        categories = list(category_stats.keys())
        counts = [stats['count'] for stats in category_stats.values()]
        max_count = max(counts) if counts else 1
        
        # 绘制柱状图
        bar_width = chart_width / len(categories) * 0.7
        gap = chart_width / len(categories) * 0.3
        
        for i, (category, count) in enumerate(zip(categories, counts)):
            x0 = margin + gap/2 + i * (bar_width + gap)
            y0 = canvas_height - margin
            bar_height = (count / max_count) * chart_height
            y1 = y0 - bar_height
            
            color = CATEGORY_COLORS.get(category, '#E0E0E0')
            
            # 绘制柱状
            self.stats_canvas.create_rectangle(x0, y0, x0 + bar_width, y1, fill=color, outline='black')
            
            # 绘制数量标签
            self.stats_canvas.create_text(x0 + bar_width/2, y1 - 10, 
                                         text=str(count), font=('微软雅黑', 9, 'bold'))
            
            # 绘制分类标签（旋转45度）
            self.stats_canvas.create_text(x0 + bar_width/2, canvas_height - margin + 15, 
                                         text=category, angle=45, font=('微软雅黑', 8))
        
        # 绘制标题
        self.stats_canvas.create_text(canvas_width/2, 20, 
                                     text="文件分类统计", 
                                     font=('微软雅黑', 12, 'bold'))

    def clear_file_list(self):
        """清空文件列表"""
        self.file_tree.delete(*self.file_tree.get_children())
        self.files_to_process = []
        
        # 清空分类预览
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        self.log_message("文件列表已清空")

    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_queue.put(formatted_message)

    def update_log(self):
        """更新日志显示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # 每100毫秒检查一次
        self.root.after(100, self.update_log)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")

    def save_log(self):
        """保存日志到文件"""
        filename = f"file_organizer_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=filename,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"日志已保存到: {filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志时出错: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置窗口图标和标题
    root.title("智能文件整理工具")
    
    # 设置窗口最小尺寸
    root.minsize(800, 600)
    
    # 创建应用程序
    app = FileOrganizerGUI(root)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()
