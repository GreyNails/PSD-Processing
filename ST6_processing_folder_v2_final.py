import os
import json
from PIL import Image
import numpy as np
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, ShapeLayer, TypeLayer, AdjustmentLayer
try:
    from psd_tools.api.layers import Group
except ImportError:
    from psd_tools.api.layers import GroupLayer as Group
import io
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

class OptimizedPSDLayerExtractor:
    def __init__(self, psd_path, output_folder):
        self.psd_path = psd_path
        self.output_folder = output_folder
        self.psd = PSDImage.open(psd_path)
        self.file_id = os.path.splitext(os.path.basename(psd_path))[0]
        self.layers_info = []
        
        # 创建输出文件夹
        file_output_folder = os.path.join(output_folder, self.file_id)
        os.makedirs(file_output_folder, exist_ok=True)
        self.file_output_folder = file_output_folder
        
        # 缓存composite结果
        self._composite_cache = {}
        
    def determine_layer_type_fast(self, layer):
        """快速判断图层类型（优化版）"""
        # 跳过不可见图层
        if not layer.is_visible():
            return None
            
        # 文本图层
        if isinstance(layer, TypeLayer):
            return 1
        
        # 基于名称的快速判断
        layer_name_lower = layer.name.lower()
        if layer_name_lower in ['background', '背景', 'bg']:
            return 3
            
        # 形状图层
        if isinstance(layer, ShapeLayer):
            # 简化的背景检查（不需要精确计算面积）
            if hasattr(layer, 'bbox') and layer.bbox:
                bounds = layer.bbox
                layer_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
                if layer_area > (self.psd.width * self.psd.height * 0.8):
                    return 3
            return 0
            
        # 调整图层
        if isinstance(layer, AdjustmentLayer):
            return 4
            
        # 像素图层
        if isinstance(layer, PixelLayer):
            # 快速蒙版检查
            if layer.mask or 'mask' in layer_name_lower or '蒙版' in layer_name_lower:
                return 4
            
            # 大图层快速背景检查（基于面积，避免像素分析）
            if hasattr(layer, 'bbox') and layer.bbox:
                bounds = layer.bbox
                layer_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
                canvas_area = self.psd.width * self.psd.height
                
                # 如果图层覆盖超过70%的画布，直接判定为背景
                if layer_area > canvas_area * 0.7:
                    return 3
            
            return 2  # imageElement
                
        # 组图层不处理
        if isinstance(layer, Group):
            return None
            
        return 2
    
    def _get_layer_composite(self, layer):
        """获取图层composite（带缓存）"""
        layer_id = id(layer)
        if layer_id not in self._composite_cache:
            self._composite_cache[layer_id] = layer.composite()
        return self._composite_cache[layer_id]
    
    def export_layer_async(self, layer_data):
        """异步导出单个图层"""
        layer, layer_type, z_index = layer_data
        try:
            filename = f"{self.file_id}_{layer_type}_{z_index}.png"
            filepath = os.path.join(self.file_output_folder, filename)
            
            img = self._get_layer_composite(layer)
            if img:
                # 确保是RGBA模式
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img.save(filepath, 'PNG', optimize=True)
                return filename
        except Exception as e:
            print(f"导出图层 {layer.name} 时出错: {e}")
            return None
    
    def collect_all_layers(self):
        """收集所有需要处理的图层信息"""
        layers_to_export = []
        
        def collect_recursive(layers, z_start=0):
            z_index = z_start
            for layer in reversed(list(layers)):
                if not layer.is_visible():
                    continue
                    
                if isinstance(layer, Group):
                    z_index = collect_recursive(layer, z_index)
                    continue
                
                layer_type = self.determine_layer_type_fast(layer)
                if layer_type is None:
                    continue
                    
                bounds = layer.bbox
                if not bounds:
                    continue
                
                layers_to_export.append({
                    'layer': layer,
                    'type': layer_type,
                    'z': z_index,
                    'bounds': bounds,
                    'name': layer.name
                })
                z_index += 1
            return z_index
        
        collect_recursive(self.psd)
        return layers_to_export
    
    def export_preview_optimized(self):
        """优化的预览图导出"""
        try:
            preview_filename = f"{self.file_id}_preview.png"
            preview_path = os.path.join(self.file_output_folder, preview_filename)
            
            # 直接使用PSD的composite方法
            preview = self.psd.composite()
            
            if preview:
                # 转换为RGB
                if preview.mode == 'RGBA':
                    background = Image.new('RGB', preview.size, (255, 255, 255))
                    background.paste(preview, mask=preview.split()[3])
                    preview = background
                elif preview.mode != 'RGB':
                    preview = preview.convert('RGB')
                
                preview.save(preview_path, 'PNG', quality=85, optimize=True)
                return preview_filename
        except:
            return None
    
    def extract_optimized(self):
        """优化的提取流程"""
        try:
            # 1. 导出预览图
            self.export_preview_optimized()
            
            # 2. 收集所有图层信息
            layers_to_export = self.collect_all_layers()
            
            # 3. 使用线程池并行导出图层
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 准备导出任务
                export_tasks = []
                for layer_info in layers_to_export:
                    task = (layer_info['layer'], layer_info['type'], layer_info['z'])
                    export_tasks.append(task)
                
                # 并行导出
                futures = {executor.submit(self.export_layer_async, task): task 
                          for task in export_tasks}
                
                # 收集结果
                for future in as_completed(futures):
                    task = futures[future]
                    layer_info = next(l for l in layers_to_export 
                                    if l['layer'] == task[0])
                    
                    image_filename = future.result()
                    if image_filename:
                        bounds = layer_info['bounds']
                        self.layers_info.append({
                            "z": layer_info['z'],
                            "type": layer_info['type'],
                            "left": bounds[0],
                            "top": bounds[1],
                            "width": bounds[2] - bounds[0],
                            "height": bounds[3] - bounds[1],
                            "image_path": image_filename,
                            "layer_name": layer_info['name']
                        })
            
            # 4. 保存JSON
            self.save_json_optimized()
            
            # 清理缓存
            self._composite_cache.clear()
            
            return True
        except Exception as e:
            print(f"处理文件 {self.psd_path} 时出错: {e}")
            return False
    
    def save_json_optimized(self):
        """优化的JSON保存"""
        json_filename = f"{self.file_id}_layers.json"
        json_path = os.path.join(self.file_output_folder, json_filename)
        
        # 按z值排序
        self.layers_info.sort(key=lambda x: x['z'])
        
        # 构建列表格式
        list_format = {
            "id": self.file_id,
            "canvas_width": self.psd.width,
            "canvas_height": self.psd.height,
            "preview_path": f"{self.file_id}_preview.png",
            "z": [l["z"] for l in self.layers_info],
            "type": [l["type"] for l in self.layers_info],
            "left": [l["left"] for l in self.layers_info],
            "top": [l["top"] for l in self.layers_info],
            "width": [l["width"] for l in self.layers_info],
            "height": [l["height"] for l in self.layers_info],
            "image_path": [l["image_path"] for l in self.layers_info],
            "layer_names": [l["layer_name"] for l in self.layers_info]
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(list_format, f, ensure_ascii=False, indent=2)


def process_single_psd(args):
    """处理单个PSD文件（用于多进程）"""
    psd_file, output_folder = args
    try:
        extractor = OptimizedPSDLayerExtractor(psd_file, output_folder)
        success = extractor.extract_optimized()
        return psd_file, success
    except Exception as e:
        print(f"处理 {psd_file} 时出错: {e}")
        return psd_file, False


def get_all_psd_files(folder_path):
    """获取文件夹中所有PSD文件"""
    psd_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.psd'):
                psd_files.append(os.path.join(root, file))
    return psd_files


def main():
    # 配置
    psd_folder = r"/storage/human_psd/psd/psd_fp_v2"
    output_folder = r"/storage/human_psd/psd_output/fp_v2_output"
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有PSD文件
    psd_files = get_all_psd_files(psd_folder)
    total_files = len(psd_files)
    
    if total_files == 0:
        print(f"错误：在 {psd_folder} 中未找到PSD文件")
        return
        
    print(f"找到 {total_files} 个PSD文件，开始批量处理...")
    
    # 确定进程数（CPU核心数的一半，但不超过8）
    num_processes = min(multiprocessing.cpu_count() // 2, 8, total_files)
    print(f"使用 {num_processes} 个进程并行处理...")
    
    # 准备任务参数
    tasks = [(psd_file, output_folder) for psd_file in psd_files]
    
    # 使用进程池并行处理
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # 提交所有任务
        futures = {executor.submit(process_single_psd, task): task[0] 
                  for task in tasks}
        
        # 使用tqdm显示进度
        with tqdm(total=total_files, desc="处理PSD文件") as pbar:
            for future in as_completed(futures):
                psd_file = futures[future]
                try:
                    _, success = future.result()
                    if success:
                        pbar.set_postfix_str(f"完成: {os.path.basename(psd_file)}")
                except Exception as e:
                    print(f"\n错误处理 {psd_file}: {e}")
                pbar.update(1)
    
    print("\n批量处理完成！")


if __name__ == "__main__":
    main()