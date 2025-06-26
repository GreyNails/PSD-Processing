import os
import shutil
import argparse
from tqdm import tqdm

def move_psd_files(source_dir, target_dir, overwrite=False):
    """
    递归移动多层文件夹中的所有PSD文件到目标文件夹
    
    参数:
    source_dir (str): 源文件夹路径
    target_dir (str): 目标文件夹路径
    overwrite (bool): 是否覆盖目标文件夹中已存在的文件，默认为False
    """
    # 确保源文件夹存在
    if not os.path.exists(source_dir):
        print(f"错误：源文件夹 '{source_dir}' 不存在")
        return False
    
    # 确保目标文件夹存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 存储移动的文件数量
    moved_count = 0
    skipped_count = 0
    failed_count = 0
    
    # 递归遍历源文件夹及其子文件夹
    for root, _, files in os.walk(source_dir):
        for file in tqdm(files, desc=f"处理 {os.path.basename(root)}"):
            if file.lower().endswith('.psd'):
                source_path = os.path.join(root, file)
                target_path = os.path.join(target_dir, file)
                
                # 检查目标文件是否存在
                if os.path.exists(target_path):
                    if overwrite:
                        print(f"警告：目标文件 '{target_path}' 已存在，将被覆盖")
                    else:
                        print(f"警告：目标文件 '{target_path}' 已存在，跳过")
                        skipped_count += 1
                        continue
                
                # 移动文件
                try:
                    shutil.move(source_path, target_path)
                    moved_count += 1
                except Exception as e:
                    print(f"错误：无法移动文件 '{source_path}' - {e}")
                    failed_count += 1
    
    # 输出结果
    print(f"\n移动完成！")
    print(f"成功移动: {moved_count}")
    print(f"跳过: {skipped_count}")
    print(f"失败: {failed_count}")
    
    return True

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='递归移动多层文件夹中的所有PSD文件')
    parser.add_argument('-s', '--source', default='/storage/human_psd/orin/freepik_v3', help='源文件夹路径')
    parser.add_argument('-t', '--target', default='/storage/human_psd/psd/psd_fp_v2', help='目标文件夹路径')
    parser.add_argument('--overwrite', action='store_true', help='覆盖已存在的文件')
    
    args = parser.parse_args()
    
    # 执行移动操作
    move_psd_files(args.source, args.target, args.overwrite)

if __name__ == "__main__":
    main()