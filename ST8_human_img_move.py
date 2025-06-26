import json
import os
import shutil
from tqdm import tqdm

def copy_images_from_json(json_path, target_folder):
    """
    从JSON文件读取图片路径列表，并复制到目标文件夹
    
    参数:
    json_path (str): JSON文件路径
    target_folder (str): 目标文件夹路径
    """
    # 确保目标文件夹存在
    os.makedirs(target_folder, exist_ok=True)
    
    try:
        # 读取JSON文件
        with open(json_path, 'r', encoding='utf-8') as f:
            image_paths = json.load(f)
        
        # 检查是否成功读取列表
        if not isinstance(image_paths, list):
            print(f"错误: JSON文件内容不是一个列表: {json_path}")
            return False
        
        print(f"找到 {len(image_paths)} 个图片路径")
        
        # 使用tqdm显示进度条
        success_count = 0
        failed_count = 0
        failed_files = []
        
        for path in tqdm(image_paths, desc="复制图片"):
            try:
                # 确保路径有效
                if not os.path.exists(path):
                    print(f"警告: 文件不存在: {path}")
                    failed_count += 1
                    failed_files.append(path)
                    continue
                
                # 获取文件名
                filename = os.path.basename(path)
                # 构造目标路径
                target_path = os.path.join(target_folder, filename)
                
                # 复制文件
                shutil.copy2(path, target_path)
                success_count += 1
            except Exception as e:
                print(f"错误: 无法复制 {path}: {str(e)}")
                failed_count += 1
                failed_files.append(path)
        
        # 输出结果
        print(f"\n复制完成！")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        
        if failed_count > 0:
            print("\n失败的文件列表:")
            for file in failed_files:
                print(f"- {file}")
        
        return True
        
    except Exception as e:
        print(f"错误: 处理JSON文件时出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 指定JSON文件路径和目标文件夹路径
    json_file = "/storage/human_psd/img_with_human/fp_v2.json"  # 替换为实际的JSON文件路径
    target_folder = "/storage/human_psd/img_human_detected/orin/fp_v2"  # 替换为实际的目标文件夹路径
    
    copy_images_from_json(json_file, target_folder)