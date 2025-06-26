
import os
import re
import shutil
from collections import defaultdict
from tqdm import tqdm

def copy_largest_images_by_id(source_dir, target_dir):
    """
    从源目录中找出每个ID对应的最大PNG文件，并复制到目标目录
    
    参数:
    source_dir (str): 源目录路径
    target_dir (str): 目标目录路径
    """
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 用于存储每个ID对应的最大文件信息
    id_files = defaultdict(list)
    
    # 正则表达式模式，用于提取ID部分
    # 匹配格式如: 0618_tao_llz_b0291fd717_2_80.png 中的 0618_tao_llz_b0291fd717
    pattern = r'^(.+?)_\d+_\d+\.png$'
    
    # 遍历源目录中的所有文件
    for filename in tqdm(os.listdir(source_dir), desc="扫描文件"):
        if filename.lower().endswith('.png'):
            # 尝试提取ID
            match = re.match(pattern, filename)
            if match:
                file_id = match.group(1)
                file_path = os.path.join(source_dir, filename)
                
                # 获取文件大小
                try:
                    file_size = os.path.getsize(file_path)
                    id_files[file_id].append((filename, file_size, file_path))
                except OSError as e:
                    print(f"警告: 无法获取文件 {filename} 的大小: {e}")
    
    print(f"找到 {len(id_files)} 个不同的ID")
    
    # 复制每个ID对应的最大文件
    copied_count = 0
    for file_id, files in tqdm(id_files.items(), desc="复制文件"):
        # 按文件大小降序排序
        files.sort(key=lambda x: x[1], reverse=True)
        largest_file = files[0]
        
        # 复制文件到目标目录
        try:
            target_path = os.path.join(target_dir, largest_file[0])
            shutil.copy2(largest_file[2], target_path)
            copied_count += 1
        except Exception as e:
            print(f"错误: 无法复制文件 {largest_file[0]}: {e}")
    
    print(f"\n操作完成！")
    print(f"共处理 {len(id_files)} 个ID")
    print(f"成功复制 {copied_count} 个文件")

if __name__ == "__main__":
    # 指定源目录和目标目录
    source_directory = "/storage/human_psd/img_human_detected/orin/fp_v2"  # 替换为实际的源目录路径
    target_directory = "/storage/human_psd/img_human_detected/filltered/fp_v2"  # 替换为实际的目标目录路径
    
    copy_largest_images_by_id(source_directory, target_directory)