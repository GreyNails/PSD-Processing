import os
import json
import argparse
from tqdm import tqdm

def merge_json_files(input_folder, output_file, encoding='utf-8'):
    """
    递归地从指定文件夹中读取所有JSON文件，并将它们合并到一个新的JSON文件中。
    
    参数:
    input_folder (str): 包含JSON文件的文件夹路径
    output_file (str): 输出的合并后的JSON文件路径
    encoding (str): 文件读取和写入的编码，默认为'utf-8'
    """
    # 存储所有JSON数据的列表
    all_json_data = []
    
    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误: 文件夹 '{input_folder}' 不存在")
        return False
    
    # 遍历文件夹中的所有文件
    json_files = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    if not json_files:
        print(f"错误: 在文件夹 '{input_folder}' 中未找到JSON文件")
        return False
    
    # 使用tqdm显示进度条
    for json_file in tqdm(json_files, desc="读取JSON文件"):
        try:
            with open(json_file, 'r', encoding=encoding) as f:
                # 加载JSON数据
                json_data = json.load(f)
                # 添加到总列表中，同时记录源文件路径
                all_json_data.append(
                    # 'source_file': os.path.relpath(json_file, input_folder),
                    json_data
                )
        except Exception as e:
            print(f"警告: 无法解析文件 '{json_file}': {str(e)}")
    
    # 保存合并后的JSON文件
    try:
        with open(output_file, 'w', encoding=encoding) as f:
            json.dump(all_json_data, f, ensure_ascii=False, indent=2)
        print(f"成功合并 {len(all_json_data)} 个JSON文件到 '{output_file}'")
        return True
    except Exception as e:
        print(f"错误: 无法保存合并后的文件 '{output_file}': {str(e)}")
        return False

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='合并多个JSON文件到一个文件中')
    parser.add_argument('-i', '--input',default='/storage/human_psd/psd_output/fp_v2_output', help='包含JSON文件的文件夹路径')
    parser.add_argument('-o', '--output', default='/storage/human_psd/json/fp_v2.json', help='输出的合并后的JSON文件路径')
    parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码，默认为utf-8')
    
    args = parser.parse_args()
    
    # 确保输出文件夹存在
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 执行合并
    merge_json_files(args.input, args.output, args.encoding)

if __name__ == "__main__":
    main()