import os
import json
import argparse
from tqdm import tqdm
from pathlib import Path

def load_json_file(json_path):
    """加载JSON文件并返回文件名集合"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except FileNotFoundError:
        print(f"错误：JSON文件 '{json_path}' 不存在")
        return set()
    except json.JSONDecodeError as e:
        print(f"错误：解析JSON文件时出错 - {e}")
        return set()
    except Exception as e:
        print(f"错误：加载JSON文件时出错 - {e}")
        return set()

def delete_psd_files_recursive(folder_path, target_files, dry_run=True):
    """
    递归检查多层文件夹，删除JSON中指定的PSD文件
    
    参数:
    folder_path (str): 要检查的根文件夹路径
    target_files (set): JSON中的目标文件名集合
    dry_run (bool): 是否只预览不删除，默认True
    """
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return
    
    # 存储找到的匹配文件
    matched_files = []
    
    # 递归遍历所有子文件夹
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.psd') and file in target_files:
                matched_files.append(os.path.join(root, file))
    
    print(f"在 {folder_path} 及其子文件夹中找到 {len(matched_files)} 个匹配的PSD文件")
    
    if not matched_files:
        print("没有需要删除的文件")
        return
    
    # 预览或删除文件
    if dry_run:
        print("\n预览模式 - 以下文件将被删除:")
        for file in matched_files[:10]:  # 显示前10个文件
            print(f"  - {os.path.relpath(file, folder_path)}")
        if len(matched_files) > 10:
            print(f"  ... 等 {len(matched_files)} 个文件")
        print("\n要实际执行删除，请使用 --execute 参数")
    else:
        print("\n开始删除文件...")
        deleted_count = 0
        failed_files = []
        
        for file_path in tqdm(matched_files, desc="删除文件"):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"警告：无法删除文件 '{file_path}' - {e}")
                failed_files.append(file_path)
        
        print(f"\n操作完成！")
        print(f"成功删除: {deleted_count}")
        print(f"删除失败: {len(failed_files)}")
        
        if failed_files:
            print("\n删除失败的文件:")
            for file in failed_files:
                print(f"  - {os.path.relpath(file, folder_path)}")

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='递归删除多层文件夹中的指定PSD文件')
    parser.add_argument('-j', '--json', default='/home/usr/dell/DataTool-HumanCentric/psd-processing/fp_v1_psd_files.json', help='包含目标文件名的JSON文件路径')
    parser.add_argument('-f', '--folder', default='/storage/human_psd/orin/freepik_v3', help='要检查的根文件夹路径')
    parser.add_argument('--execute', action='store_true', help='实际执行删除操作，默认只预览')
    
    args = parser.parse_args()
    
    # 加载目标文件名集合
    target_files = load_json_file(args.json)
    if not target_files:
        return
    
    # 执行删除操作
    delete_psd_files_recursive(args.folder, target_files, dry_run=not args.execute)

if __name__ == "__main__":
    main()