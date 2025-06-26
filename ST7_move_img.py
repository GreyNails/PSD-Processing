import os
import shutil
import fnmatch
from pathlib import Path
from tqdm import tqdm

def copy_matching_png_files(source_folder, destination_folder):
    """
    递归查找源文件夹中所有名称格式为 *_2_*.png 的文件，并复制到目标文件夹
    
    Args:
        source_folder (str): 源文件夹路径
        destination_folder (str): 目标文件夹路径
    """
    
    # 确保目标文件夹存在
    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    
    # 统计变量
    found_files = []
    copied_files = 0
    skipped_files = 0
    
    print(f"开始搜索文件夹: {source_folder}")
    print(f"目标文件夹: {destination_folder}")
    print("搜索模式: *_2_*.png")
    print("-" * 50)
    
    # 递归遍历源文件夹
    for root, dirs, files in tqdm(os.walk(source_folder)):
        # 在当前目录中查找匹配的PNG文件
        for filename in files:
            if fnmatch.fnmatch(filename, "*_2_*.png"):
                source_file_path = os.path.join(root, filename)
                destination_file_path = os.path.join(destination_folder, filename)
                
                found_files.append(source_file_path)
                
                try:
                    # 检查目标文件是否已存在
                    if os.path.exists(destination_file_path):
                        # 生成新的文件名避免冲突
                        base_name, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(destination_file_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            destination_file_path = os.path.join(destination_folder, new_filename)
                            counter += 1
                        
                        # print(f"文件重名，重命名为: {os.path.basename(destination_file_path)}")
                    
                    # 复制文件
                    shutil.copy2(source_file_path, destination_file_path)
                    # print(f"✓ 已复制: {filename}")
                    # print(f"  源路径: {source_file_path}")
                    # print(f"  目标路径: {destination_file_path}")
                    copied_files += 1
                    
                except Exception as e:
                    # print(f"✗ 复制失败: {filename}")
                    # print(f"  错误信息: {str(e)}")
                    skipped_files += 1
                
                # print("-" * 30)
    
    # 显示总结
    print("\n" + "=" * 50)
    print("操作完成！")
    print(f"找到的文件数量: {len(found_files)}")
    print(f"成功复制: {copied_files}")
    print(f"复制失败: {skipped_files}")
    
    if found_files:
        print("\n找到的所有文件:")
        for i, file_path in enumerate(found_files, 1):
            print(f"{i}. {file_path}")
    else:
        print("\n未找到符合条件的文件。")

def main():
    """主函数 - 设置源文件夹和目标文件夹路径"""
    
    # 在这里修改你的路径
    source_folder = "/storage/human_psd/psd_output/fp_v2_output"
    destination_folder = "/storage/human_psd/img/fp_v2"
    # os.mkdir(destination_folder,exit_ok=True)
    os.makedirs(destination_folder, exist_ok=True)
    
    # 验证源文件夹是否存在
    if not os.path.exists(source_folder):
        print(f"错误: 源文件夹不存在 - {source_folder}")
        return
    
    if not os.path.isdir(source_folder):
        print(f"错误: 指定的源路径不是文件夹 - {source_folder}")
        return
    
    # 确认操作
    print(f"\n将要执行的操作:")
    print(f"源文件夹: {source_folder}")
    print(f"目标文件夹: {destination_folder}")
    print(f"搜索模式: *_2_*.png")
    
    confirm = input("\n确认执行此操作? (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        copy_matching_png_files(source_folder, destination_folder)
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()