#!/usr/bin/env python3
"""
文件整理工具 - 自动按类型整理文件
功能：将杂乱的文件按类型自动整理到对应文件夹
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# 定义文件类型分类
FILE_CATEGORIES = {
    '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
    '文档': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.md'],
    '音频': ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.wma'],
    '视频': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v'],
    '压缩包': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    '程序': ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.php', '.json','.exe'],
    '安装包': ['.msi', '.dmg', '.pkg', '.deb', '.rpm'],
    '字体': ['.ttf', '.otf', '.woff', '.woff2'],
    '其他': []  # 未分类文件
}

def get_file_category(file_extension):
    """根据文件扩展名获取分类"""
    file_extension = file_extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if file_extension in extensions:
            return category
    return '其他'

def organize_files(source_dir, organize_by='type', dry_run=False, create_backup=False):
    """
    整理文件
    
    Args:
        source_dir: 源目录路径
        organize_by: 整理方式 ('type'按类型, 'date'按日期)
        dry_run: 模拟运行，不实际移动文件
        create_backup: 是否创建备份
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"错误: 目录 {source_dir} 不存在")
        return
    
    if not source_path.is_dir():
        print(f"错误: {source_dir} 不是目录")
        return
    
    # 创建备份
    backup_path = None
    if create_backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = source_path.parent / f"backup_{timestamp}"
        print(f"创建备份到: {backup_path}")
        if not dry_run:
            shutil.copytree(source_path, backup_path)
    
    # 统计信息
    stats = {
        'total': 0,
        'moved': 0,
        'skipped': 0,
        'categories': {}
    }
    
    print(f"\n开始整理目录: {source_path}")
    print(f"整理方式: {organize_by}")
    print(f"模拟运行: {dry_run}")
    print("-" * 50)
    
    # 遍历源目录中的所有文件
    for item in source_path.rglob('*'):
        if item.is_file():
            stats['total'] += 1
            
            # 跳过隐藏文件和系统文件
            if item.name.startswith('.') or item.name.startswith('~'):
                continue
            
            # 获取文件信息
            file_extension = item.suffix
            file_size = item.stat().st_size
            modified_time = datetime.fromtimestamp(item.stat().st_mtime)
            
            # 确定目标文件夹
            if organize_by == 'date':
                # 按日期整理：年/月
                folder_name = modified_time.strftime("%Y-%m")
                target_dir = source_path / "按日期整理" / folder_name
            else:
                # 按类型整理
                category = get_file_category(file_extension)
                target_dir = source_path / category
                
                # 更新统计
                if category not in stats['categories']:
                    stats['categories'][category] = 0
                stats['categories'][category] += 1
            
            # 创建目标目录
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
            
            # 处理文件名冲突
            target_file = target_dir / item.name
            counter = 1
            while target_file.exists():
                name_parts = item.stem.split('_')
                if len(name_parts) > 1 and name_parts[-1].isdigit():
                    base_name = '_'.join(name_parts[:-1])
                else:
                    base_name = item.stem
                new_name = f"{base_name}_{counter}{item.suffix}"
                target_file = target_dir / new_name
                counter += 1
            
            # 移动文件
            try:
                if dry_run:
                    print(f"[模拟] 移动: {item.name} -> {target_dir.name}/")
                else:
                    shutil.move(str(item), str(target_file))
                    print(f"✓ 移动: {item.name} -> {target_dir.name}/")
                stats['moved'] += 1
            except Exception as e:
                print(f"✗ 错误移动 {item.name}: {e}")
                stats['skipped'] += 1
    
    # 打印统计信息
    print("\n" + "=" * 50)
    print("整理完成！")
    print(f"总计文件: {stats['total']}")
    print(f"成功移动: {stats['moved']}")
    print(f"跳过文件: {stats['skipped']}")
    
    if stats['categories']:
        print("\n文件分类统计:")
        for category, count in sorted(stats['categories'].items()):
            print(f"  {category}: {count} 个文件")
    
    if backup_path and not dry_run:
        print(f"\n备份已创建: {backup_path}")
    
    return stats

def find_duplicate_files(source_dir):
    """查找重复文件（基于文件名和大小）"""
    print(f"\n查找重复文件: {source_dir}")
    print("-" * 50)
    
    file_dict = {}
    duplicates = []
    
    for item in Path(source_dir).rglob('*'):
        if item.is_file():
            key = (item.name.lower(), item.stat().st_size)
            if key in file_dict:
                duplicates.append((file_dict[key], item))
            else:
                file_dict[key] = item
    
    if duplicates:
        print(f"找到 {len(duplicates)} 组重复文件:")
        for i, (original, duplicate) in enumerate(duplicates, 1):
            print(f"\n{i}. 重复文件:")
            print(f"   原始: {original}")
            print(f"   副本: {duplicate}")
    else:
        print("未找到重复文件")
    
    return duplicates

def cleanup_empty_folders(source_dir):
    """清理空文件夹"""
    print(f"\n清理空文件夹: {source_dir}")
    print("-" * 50)
    
    empty_folders = []
    for root, dirs, files in os.walk(source_dir, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    empty_folders.append(dir_path)
                    print(f"删除空文件夹: {dir_path}")
                    dir_path.rmdir()
            except Exception as e:
                print(f"无法删除 {dir_path}: {e}")
    
    print(f"\n清理了 {len(empty_folders)} 个空文件夹")
    return empty_folders

def main():
    parser = argparse.ArgumentParser(description='文件整理工具')
    parser.add_argument('path', nargs='?', default='.', help='要整理的目录路径（默认当前目录）')
    parser.add_argument('--type', choices=['type', 'date'], default='type',
                       help='整理方式：type（按类型，默认）或 date（按日期）')
    parser.add_argument('--dry-run', action='store_true',
                       help='模拟运行，不实际移动文件')
    parser.add_argument('--backup', action='store_true',
                       help='整理前创建备份')
    parser.add_argument('--find-duplicates', action='store_true',
                       help='查找重复文件')
    parser.add_argument('--cleanup', action='store_true',
                       help='清理空文件夹')
    
    args = parser.parse_args()
    
    # 执行功能
    if args.find_duplicates:
        find_duplicate_files(args.path)
    elif args.cleanup:
        cleanup_empty_folders(args.path)
    else:
        organize_files(
            source_dir=args.path,
            organize_by=args.type,
            dry_run=args.dry_run,
            create_backup=args.backup
        )

if __name__ == "__main__":
    main()
