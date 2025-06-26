import os
import shutil
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def remove_top_layer(input_path, output_path):
    """
    删除PSD文件中最上面的图层（Photoshop中显示在最顶部的图层）
    
    参数:
    input_path: 输入PSD文件路径
    output_path: 输出PSD文件路径
    
    返回:
    (success, message) - 成功标志和消息
    """
    try:
        # 打开PSD文件
        psd = PSDImage.open(input_path)
        
        # 获取所有图层
        layers = list(psd)
        
        if not layers:
            return False, "PSD文件中没有图层"
        
        # 在psd-tools中，图层顺序是反的
        # 最后一个图层（索引-1）是Photoshop中最上面的图层
        top_layer_index = len(layers) - 1
        top_layer = layers[top_layer_index]
        top_layer_name = top_layer.name
        
        # 将最上面的图层设置为不可见
        psd[top_layer_index].visible = False
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存修改后的PSD文件
        psd.save(output_path)
        
        return True, f"成功隐藏顶层图层: {top_layer_name}"
        
    except Exception as e:
        return False, f"处理失败: {str(e)}"


def process_single_file(args):
    """处理单个文件（用于多进程）"""
    input_path, output_path = args
    filename = os.path.basename(input_path)
    
    try:
        success, message = remove_top_layer(input_path, output_path)
        return {
            'filename': filename,
            'success': success,
            'message': message,
            'input_path': input_path,
            'output_path': output_path
        }
    except Exception as e:
        return {
            'filename': filename,
            'success': False,
            'message': f"处理异常: {str(e)}",
            'input_path': input_path,
            'output_path': output_path
        }


def batch_remove_top_layer(input_folder, output_folder, use_multiprocess=True):
    """
    批量处理文件夹中的所有PSD文件
    
    参数:
    input_folder: 输入文件夹路径
    output_folder: 输出文件夹路径
    use_multiprocess: 是否使用多进程（默认True）
    """
    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误：输入文件夹不存在: {input_folder}")
        return
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有PSD文件
    psd_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.psd'):
                # 保持相对路径结构
                rel_path = os.path.relpath(root, input_folder)
                input_path = os.path.join(root, file)
                
                if rel_path == '.':
                    output_path = os.path.join(output_folder, file)
                else:
                    output_dir = os.path.join(output_folder, rel_path)
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, file)
                
                psd_files.append((input_path, output_path))
    
    if not psd_files:
        print(f"在 {input_folder} 中没有找到PSD文件")
        return
    
    print(f"找到 {len(psd_files)} 个PSD文件")
    print(f"输入文件夹: {input_folder}")
    print(f"输出文件夹: {output_folder}")
    print("-" * 60)
    
    # 统计结果
    success_count = 0
    failed_files = []
    
    if use_multiprocess and len(psd_files) > 1:
        # 多进程处理
        num_processes = min(multiprocessing.cpu_count() - 1, len(psd_files))
        num_processes = max(1, num_processes)
        
        print(f"使用 {num_processes} 个进程并行处理...")
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # 提交所有任务
            future_to_file = {executor.submit(process_single_file, task): task 
                            for task in psd_files}
            
            # 使用进度条显示处理进度
            with tqdm(total=len(psd_files), desc="处理进度") as pbar:
                for future in as_completed(future_to_file):
                    result = future.result()
                    
                    if result['success']:
                        success_count += 1
                        tqdm.write(f"✓ {result['filename']}: {result['message']}")
                    else:
                        failed_files.append(result)
                        tqdm.write(f"✗ {result['filename']}: {result['message']}")
                    
                    pbar.update(1)
    else:
        # 单进程处理
        print("使用单进程处理...")
        
        for input_path, output_path in tqdm(psd_files, desc="处理进度"):
            filename = os.path.basename(input_path)
            
            success, message = remove_top_layer(input_path, output_path)
            
            if success:
                success_count += 1
                print(f"✓ {filename}: {message}")
            else:
                failed_files.append({
                    'filename': filename,
                    'message': message,
                    'input_path': input_path
                })
                print(f"✗ {filename}: {message}")
    
    # 打印汇总信息
    print("\n" + "=" * 60)
    print(f"处理完成！")
    print(f"成功: {success_count}/{len(psd_files)} 个文件")
    
    if failed_files:
        print(f"\n失败的文件 ({len(failed_files)} 个):")
        for failed in failed_files:
            print(f"  - {failed['filename']}: {failed['message']}")


def batch_remove_top_layer_simple(input_folder, output_folder):
    """
    简化版批量处理（顺序处理，适合调试）
    """
    # 检查输入文件夹
    if not os.path.exists(input_folder):
        print(f"错误：输入文件夹不存在: {input_folder}")
        return
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 统计
    success_count = 0
    total_count = 0
    
    # 遍历所有PSD文件
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.psd'):
            total_count += 1
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            print(f"\n处理文件 {total_count}: {filename}")
            
            success, message = remove_top_layer(input_path, output_path)
            
            if success:
                success_count += 1
                print(f"  ✓ {message}")
            else:
                print(f"  ✗ {message}")
    
    print(f"\n处理完成！成功: {success_count}/{total_count}")


def preview_files(input_folder):
    """预览将要处理的文件"""
    psd_files = []
    
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.psd'):
                psd_files.append(os.path.join(root, file))
    
    if not psd_files:
        print("没有找到PSD文件")
        return
    
    print(f"找到 {len(psd_files)} 个PSD文件:")
    for i, file in enumerate(psd_files[:10], 1):
        print(f"  {i}. {os.path.relpath(file, input_folder)}")
    
    if len(psd_files) > 10:
        print(f"  ... 还有 {len(psd_files) - 10} 个文件")


if __name__ == "__main__":
    # 设置输入输出文件夹路径
    input_folder = r"/storage/human_psd/psd_tao_llz"  # 替换为你的输入文件夹路径
    output_folder = r"/storage/human_psd/pas_tal_llz_notop"  # 替换为你的输出文件夹路径
    
    # 示例用法
    # input_folder = r"D:\PSD_Files\Original"
    # output_folder = r"D:\PSD_Files\Modified"
    
    # 方法1: 使用多进程批量处理（推荐，处理大量文件时更快）
    batch_remove_top_layer(input_folder, output_folder, use_multiprocess=True)
    
    # 方法2: 使用单进程批量处理（简单稳定，适合少量文件或调试）
    # batch_remove_top_layer(input_folder, output_folder, use_multiprocess=False)
    
    # 方法3: 使用简化版处理（最简单）
    # batch_remove_top_layer_simple(input_folder, output_folder)
    
    # 预览功能：先查看有哪些文件
    # preview_files(input_folder)