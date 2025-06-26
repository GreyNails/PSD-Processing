import os
import argparse
import uuid
import random
import string
from pathlib import Path

def generate_unique_id(length=10):
    """生成指定长度的唯一ID"""
    # 使用UUID确保唯一性，然后截取前length位
    unique_id = str(uuid.uuid4()).replace('-', '')
    return unique_id[:length]

def rename_psd_files(directory, dry_run=False):
    """
    递归重命名目录中的所有PSD文件
    
    参数:
        directory (str): 要处理的目录路径
        dry_run (bool): 是否执行干运行，只显示重命名计划但不实际重命名
    
    返回:
        int: 重命名的文件数量
    """
    psd_extension = '.psd'
    prefix = '0612_tao_wu_'
    
    renamed_count = 0
    processed_ids = set()
    
    # 遍历目录
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(psd_extension):
                original_path = os.path.join(root, file)
                file_stem = Path(file).stem  # 获取文件名(不含扩展名)
                
                # 生成唯一ID，确保不重复
                unique_id = generate_unique_id()
                while unique_id in processed_ids:
                    unique_id = generate_unique_id()
                processed_ids.add(unique_id)
                
                # 构建新文件名
                new_name = f"{prefix}{unique_id}{psd_extension}"
                new_path = os.path.join(root, new_name)
                
                # 显示重命名计划
                print(f"将 {original_path} 重命名为 {new_path}")
                
                # 如果不是干运行，则执行重命名
                if not dry_run:
                    try:
                        os.rename(original_path, new_path)
                        renamed_count += 1
                    except Exception as e:
                        print(f"重命名 {original_path} 时出错: {e}")
    
    return renamed_count

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='递归重命名文件夹中的所有PSD文件')
    parser.add_argument('directory', help='要处理的目录路径')
    parser.add_argument('-n', '--dry-run', action='store_true', 
                        help='执行干运行，只显示重命名计划但不实际重命名')
    args = parser.parse_args()
    
    # 检查目录是否存在
    if not os.path.isdir(args.directory):
        print(f"错误: '{args.directory}' 不是一个有效的目录")
        return
    
    # 重命名文件
    renamed_count = rename_psd_files(args.directory, args.dry_run)
    
    # 显示结果
    if args.dry_run:
        print(f"\n干运行完成! 计划重命名 {renamed_count} 个PSD文件。")
        print("使用不带 --dry-run 参数的命令执行实际重命名。")
    else:
        print(f"\n重命名完成! 成功重命名了 {renamed_count} 个PSD文件。")

if __name__ == "__main__":
    main()
