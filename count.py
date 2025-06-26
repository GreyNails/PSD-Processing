import os
import argparse
from pathlib import Path

def count_files(directory):
    """
    统计指定目录下的压缩包和PSD文件数量
    
    参数:
        directory (str): 要统计的目录路径
    
    返回:
        dict: 包含各种文件类型及其数量的字典
    """
    # 定义压缩包文件扩展名和PSD文件扩展名
    archive_extensions = ('.zip', '.rar', '.7z', '.gz', '.tar', '.bz2', '.xz')
    psd_extension = '.psd'
    
    # 初始化计数器
    counts = {
        'archives': 0,
        'psd': 0,
        'total': 0
    }
    
    # 递归遍历目录
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(file)
            ext = file_path.suffix.lower()
            
            # 统计压缩包
            if ext in archive_extensions:
                counts['archives'] += 1
                counts['total'] += 1
            
            # 统计PSD文件
            elif ext == psd_extension:
                counts['psd'] += 1
                counts['total'] += 1
    
    return counts

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='统计文件夹中的压缩包和PSD文件数量')
    parser.add_argument('directory', help='要统计的目录路径')
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.isdir(args.directory):
        print(f"错误: '{args.directory}' 不是一个有效的目录")
        return
    
    # 统计文件
    counts = count_files(args.directory)
    
    # 输出结果
    print(f"目录: {args.directory}")
    print(f"压缩包数量: {counts['archives']}")
    print(f"PSD文件数量: {counts['psd']}")
    print(f"总计: {counts['total']}")

if __name__ == "__main__":
    main()
