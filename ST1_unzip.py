import os
import zipfile
import tarfile
import argparse
import shutil
from pathlib import Path
import rarfile
import py7zr

# 设置RAR文件支持
rarfile.UNRAR_TOOL = "unrar"  # 确保系统中已安装unrar工具

def extract_zip(file_path, extract_to):
    """解压ZIP文件"""
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def extract_tar(file_path, extract_to):
    """解压TAR文件"""
    with tarfile.open(file_path, 'r:*') as tar_ref:
        tar_ref.extractall(extract_to)

def extract_rar(file_path, extract_to):
    """解压RAR文件"""
    with rarfile.RarFile(file_path, 'r') as rar_ref:
        rar_ref.extractall(extract_to)

def extract_7z(file_path, extract_to):
    """解压7Z文件"""
    with py7zr.SevenZipFile(file_path, 'r') as sz_ref:
        sz_ref.extractall(extract_to)

def extract_file(file_path, extract_to):
    """根据文件扩展名选择合适的解压方法"""
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    
    try:
        if ext == '.zip':
            extract_zip(file_path, extract_to)
            return True
        elif ext in ['.tar', '.gz', '.bz2', '.xz']:
            extract_tar(file_path, extract_to)
            return True
        elif ext == '.rar':
            extract_rar(file_path, extract_to)
            return True
        elif ext == '.7z':
            extract_7z(file_path, extract_to)
            return True
        return False
    except Exception as e:
        print(f"解压 {file_path} 时出错: {e}")
        return False

def unzip_directory(directory, delete_after=False):
    """递归解压目录中的所有压缩文件"""
    # 支持的压缩文件扩展名
    archive_extensions = ('.zip', '.rar', '.7z', '.gz', '.tar', '.bz2', '.xz')
    
    total_files = 0
    success_files = 0
    
    # 首先收集所有压缩文件路径，避免在解压过程中修改目录结构导致问题
    archive_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(archive_extensions):
                archive_files.append(os.path.join(root, file))
    
    # 然后解压收集到的所有文件
    for file_path in archive_files:
        total_files += 1
        file_path = Path(file_path)
        
        # 创建与压缩文件同名的文件夹作为解压目标
        extract_dir = file_path.parent / file_path.stem
        extract_dir.mkdir(exist_ok=True)
        
        print(f"正在解压: {file_path} -> {extract_dir}")
        
        if extract_file(file_path, extract_dir):
            success_files += 1
            print(f"成功解压: {file_path}")
            
            # 如果设置了删除选项，解压后删除原文件
            if delete_after:
                try:
                    os.remove(file_path)
                    print(f"已删除: {file_path}")
                except Exception as e:
                    print(f"删除 {file_path} 时出错: {e}")
    
    print(f"\n解压完成!")
    print(f"处理文件总数: {total_files}")
    print(f"成功解压: {success_files}")
    print(f"解压失败: {total_files - success_files}")

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='递归解压文件夹中的所有压缩包')
    parser.add_argument('--directory',default='/storage/human_psd/orin/freepik_v3', help='要处理的目录路径')
    parser.add_argument('-d', '--delete', action='store_true', 
                        help='解压后删除原压缩文件')
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.isdir(args.directory):
        print(f"错误: '{args.directory}' 不是一个有效的目录")
        return
    
    # 解压文件
    unzip_directory(args.directory, args.delete)

if __name__ == "__main__":
    main()
