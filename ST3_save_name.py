import os
import json
import argparse

def find_psd_files(folder_path):
    """递归查找指定文件夹中的所有PSD文件并返回文件名列表"""
    psd_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.psd'):
                psd_files.append(file)  # 只保存文件名而非完整路径
    return psd_files

def save_to_json(files, output_path):
    """将文件列表保存到JSON文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(files, f, ensure_ascii=False, indent=2)
    print(f"已将 {len(files)} 个PSD文件名保存到 {output_path}")

def main():
    parser = argparse.ArgumentParser(description='递归搜索文件夹中的PSD文件并保存文件名到JSON')
    parser.add_argument('--source_folder', default='/storage/human_psd/orin/freepik_v3', help='源文件夹路径')
    parser.add_argument('-o', '--output', default='fp_v2_psd_files.json', help='输出JSON文件路径')
    args = parser.parse_args()

    # 检查源文件夹是否存在
    if not os.path.exists(args.source_folder):
        print(f"错误：源文件夹 {args.source_folder} 不存在")
        return

    # 查找PSD文件
    psd_files = find_psd_files(args.source_folder)
    
    # 保存到JSON
    save_to_json(psd_files, args.output)

if __name__ == "__main__":
    main()