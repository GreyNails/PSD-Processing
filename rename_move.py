import os
import random
import shutil
from pathlib import Path

def generate_unique_random_number(used_numbers, min_val=1000000000, max_val=9999999999):
    """生成唯一的十位随机数"""
    while True:
        random_num = random.randint(min_val, max_val)
        if random_num not in used_numbers:
            used_numbers.add(random_num)
            return random_num

def process_psd_files(source_dir, target_dir):
    """处理PSD文件：重命名并移动"""
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    used_numbers = set()
    file_count = 0
    error_count = 0
    
    # 递归遍历源目录下的所有文件和文件夹
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # 检查是否为PSD文件
            if file.lower().endswith('.psd'):
                file_count += 1
                source_path = os.path.join(root, file)
                file_base, file_ext = os.path.splitext(file)
                
                try:
                    # 生成唯一的十位随机数
                    random_num = generate_unique_random_number(used_numbers)
                    
                    # 构造新文件名
                    new_filename = f"{file_base}_{random_num}{file_ext}"
                    target_path = os.path.join(target_dir, new_filename)
                    
                    # 处理重名情况：如果目标文件已存在，添加额外随机字符
                    counter = 1
                    while os.path.exists(target_path):
                        new_filename = f"{file_base}_{random_num}_{counter}{file_ext}"
                        target_path = os.path.join(target_dir, new_filename)
                        counter += 1
                    
                    # 移动并重命名文件
                    shutil.move(source_path, target_path)
                    print(f"已处理: {source_path} -> {target_path}")
                    
                except Exception as e:
                    error_count += 1
                    print(f"处理文件 {source_path} 时出错: {e}")
    
    print(f"\n处理完成！")
    print(f"总PSD文件数: {file_count}")
    print(f"成功处理: {file_count - error_count}")
    print(f"处理错误: {error_count}")

def main():
    # 设置源目录和目标目录（使用原始字符串避免转义）
    source_directory = r"/storage/human_psd/psd/psd_fp_v2"  # 包含PSD文件的源文件夹
    target_directory = r"/storage/human_psd/psd/psd_fp_v2_1"  # 重命名后文件移动到的目标文件夹
    
    if not os.path.exists(source_directory):
        print(f"错误：源文件夹 {source_directory} 不存在")
        return
    
    print(f"开始处理PSD文件...")
    process_psd_files(source_directory, target_directory)

if __name__ == "__main__":
    main()