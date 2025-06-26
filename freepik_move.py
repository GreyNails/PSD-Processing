import os
import shutil
import argparse
from pathlib import Path

def find_psd_files(folder_path):
    """递归查找指定文件夹中的所有PSD文件"""
    psd_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.psd'):
                psd_files.append(os.path.join(root, file))
    return psd_files

def merge_psd_files(source_folder1, source_folder2, target_folder, dry_run=False):
    """合并两个源文件夹中的PSD文件到目标文件夹，自动处理重复文件"""
    # 确保目标文件夹存在
    os.makedirs(target_folder, exist_ok=True)
    
    # 查找所有PSD文件
    print(f"正在查找 {source_folder1} 中的PSD文件...")
    psd_files1 = find_psd_files(source_folder1)
    print(f"找到 {len(psd_files1)} 个PSD文件")
    
    print(f"正在查找 {source_folder2} 中的PSD文件...")
    psd_files2 = find_psd_files(source_folder2)
    print(f"找到 {len(psd_files2)} 个PSD文件")
    
    # 合并文件列表并处理重复
    merged_files = []
    file_names = set()
    
    # 先添加第一个文件夹的所有文件
    for file_path in psd_files1:
        file_name = os.path.basename(file_path)
        file_names.add(file_name)
        merged_files.append((file_path, file_name))
    
    # 添加第二个文件夹中不重复的文件
    for file_path in psd_files2:
        file_name = os.path.basename(file_path)
        if file_name not in file_names:
            file_names.add(file_name)
            merged_files.append((file_path, file_name))
    
    print(f"合并后共有 {len(merged_files)} 个不重复的PSD文件")
    
    # 移动文件
    if not dry_run:
        print(f"开始将文件移动到 {target_folder}...")
        for src_path, file_name in merged_files:
            dst_path = os.path.join(target_folder, file_name)
            try:
                shutil.move(src_path, dst_path)
                print(f"已移动: {src_path} -> {dst_path}")
            except Exception as e:
                print(f"移动失败 {src_path}: {e}")
    else:
        print("干运行模式：不实际移动文件")
        for src_path, file_name in merged_files:
            dst_path = os.path.join(target_folder, file_name)
            print(f"将移动: {src_path} -> {dst_path}")
    
    print("操作完成！")

def main():
    parser = argparse.ArgumentParser(description='合并两个文件夹中的PSD文件，自动去重')
    parser.add_argument('--source1', default="/storage/human_psd/no",help='第一个源文件夹路径')
    parser.add_argument('--source2', default='/storage/human_psd/hzj的殖民地/llz',help='第二个源文件夹路径')
    parser.add_argument('--target', default='/storage/human_psd/psd_tao_llz',help='目标文件夹路径')
    parser.add_argument('--dry-run',action='store_true', help='干运行模式，不实际移动文件')
    
    args = parser.parse_args()
    
    # 检查源文件夹是否存在
    if not os.path.exists(args.source1):
        print(f"错误：源文件夹 {args.source1} 不存在")
        return
    
    if not os.path.exists(args.source2):
        print(f"错误：源文件夹 {args.source2} 不存在")
        return
    
    merge_psd_files(args.source1, args.source2, args.target, args.dry_run)

if __name__ == "__main__":
    main()    