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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
from functools import lru_cache
import asyncio
import aiofiles
from typing import List, Dict, Tuple, Optional
import warnings
from dataclasses import dataclass
from queue import Queue
import threading
import psutil
import gc

warnings.filterwarnings('ignore')

# 配置参数
MAX_WORKERS = min(multiprocessing.cpu_count(), 16)
THREAD_WORKERS = 8
CHUNK_SIZE = 10  # 每批处理的PSD文件数
MEMORY_LIMIT_MB = 4096  # 内存限制

@dataclass
class LayerInfo:
    """图层信息数据类"""
    layer: object
    type: int
    z: int
    bounds: tuple
    name: str

class MemoryMonitor:
    """内存监控器"""
    @staticmethod
    def get_memory_usage():
        """获取当前内存使用量（MB）"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def check_memory():
        """检查内存使用情况"""
        usage = MemoryMonitor.get_memory_usage()
        if usage > MEMORY_LIMIT_MB:
            gc.collect()
            return False
        return True

class BatchImageSaver:
    """批量图片保存器"""
    def __init__(self, max_queue_size=100):
        self.queue = Queue(maxsize=max_queue_size)
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        self.stop_event = threading.Event()
    
    def _worker(self):
        """后台保存线程"""
        while not self.stop_event.is_set() or not self.queue.empty():
            try:
                if not self.queue.empty():
                    img, filepath = self.queue.get(timeout=1)
                    img.save(filepath, 'PNG', optimize=True, compress_level=6)
                    self.queue.task_done()
            except:
                pass
    
    def save(self, img, filepath):
        """添加到保存队列"""
        self.queue.put((img, filepath))
    
    def wait_completion(self):
        """等待所有保存完成"""
        self.queue.join()
    
    def stop(self):
        """停止保存器"""
        self.stop_event.set()
        self.worker_thread.join()

class UltraOptimizedPSDExtractor:
    def __init__(self, psd_path: str, output_folder: str, saver: BatchImageSaver):
        self.psd_path = psd_path
        self.output_folder = output_folder
        self.file_id = os.path.splitext(os.path.basename(psd_path))[0]
        self.saver = saver
        
        # 延迟加载PSD
        self._psd = None
        self._layers_info = []
        
        # 输出文件夹
        self.file_output_folder = os.path.join(output_folder, self.file_id)
        os.makedirs(self.file_output_folder, exist_ok=True)
    
    @property
    def psd(self):
        """延迟加载PSD"""
        if self._psd is None:
            self._psd = PSDImage.open(self.psd_path)
        return self._psd
    
    def determine_layer_type_ultra_fast(self, layer, bounds=None) -> Optional[int]:
        """超快速图层类型判断"""
        if not layer.is_visible():
            return None
        
        # 类型映射表
        type_map = {
            TypeLayer: 1,
            ShapeLayer: 0,
            AdjustmentLayer: 4
        }
        
        # 直接类型判断
        for layer_class, type_value in type_map.items():
            if isinstance(layer, layer_class):
                # 特殊处理形状图层
                if type_value == 0 and bounds:
                    area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
                    if area > (self.psd.width * self.psd.height * 0.8):
                        return 3
                return type_value
        
        # 快速名称检查
        name_lower = layer.name.lower()
        if any(bg in name_lower for bg in ['background', '背景', 'bg']):
            return 3
        
        if isinstance(layer, PixelLayer):
            if layer.mask or any(mask in name_lower for mask in ['mask', '蒙版']):
                return 4
            
            # 基于面积的快速判断
            if bounds:
                area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
                if area > (self.psd.width * self.psd.height * 0.7):
                    return 3
            
            return 2
        
        return isinstance(layer, Group) and None or 2
    
    def process_layers_batch(self) -> List[LayerInfo]:
        """批量处理图层收集"""
        all_layers = []
        
        def collect_layers(container, z_start=0):
            z = z_start
            for layer in reversed(list(container)):
                if isinstance(layer, Group) and layer.is_visible():
                    z = collect_layers(layer, z)
                elif layer.is_visible() and hasattr(layer, 'bbox'):
                    bounds = layer.bbox
                    if bounds:
                        layer_type = self.determine_layer_type_ultra_fast(layer, bounds)
                        if layer_type is not None:
                            all_layers.append(LayerInfo(
                                layer=layer,
                                type=layer_type,
                                z=z,
                                bounds=bounds,
                                name=layer.name
                            ))
                            z += 1
            return z
        
        collect_layers(self.psd)
        return all_layers
    
    def export_layer_ultra_fast(self, layer_info: LayerInfo) -> Optional[str]:
        """超快速图层导出"""
        try:
            filename = f"{self.file_id}_{layer_info.type}_{layer_info.z}.png"
            filepath = os.path.join(self.file_output_folder, filename)
            
            # 获取图层图像
            img = layer_info.layer.composite()
            if img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 使用批量保存器
                self.saver.save(img, filepath)
                return filename
        except:
            return None
    
    def generate_preview_fast(self) -> Optional[str]:
        """快速预览生成"""
        try:
            preview_filename = f"{self.file_id}_preview.png"
            preview_path = os.path.join(self.file_output_folder, preview_filename)
            
            preview = self.psd.composite()
            if preview:
                if preview.mode != 'RGB':
                    if preview.mode == 'RGBA':
                        bg = Image.new('RGB', preview.size, (255, 255, 255))
                        bg.paste(preview, mask=preview.split()[3])
                        preview = bg
                    else:
                        preview = preview.convert('RGB')
                
                # 降低质量以加快保存速度
                preview.save(preview_path, 'PNG', quality=80, optimize=True)
                return preview_filename
        except:
            return None
    
    def extract_ultra_optimized(self) -> bool:
        """超优化提取流程"""
        try:
            # 1. 快速生成预览
            preview = self.generate_preview_fast()
            
            # 2. 批量收集图层
            layers = self.process_layers_batch()
            
            # 3. 使用线程池处理图层导出
            with ThreadPoolExecutor(max_workers=THREAD_WORKERS) as executor:
                futures = []
                for layer_info in layers:
                    future = executor.submit(self.export_layer_ultra_fast, layer_info)
                    futures.append((future, layer_info))
                
                # 收集结果
                for future, layer_info in futures:
                    filename = future.result()
                    if filename:
                        bounds = layer_info.bounds
                        self._layers_info.append({
                            "z": layer_info.z,
                            "type": layer_info.type,
                            "left": bounds[0],
                            "top": bounds[1],
                            "width": bounds[2] - bounds[0],
                            "height": bounds[3] - bounds[1],
                            "image_path": filename,
                            "layer_name": layer_info.name
                        })
            
            # 4. 保存JSON
            self.save_json_fast()
            
            # 5. 清理内存
            del self._psd
            gc.collect()
            
            return True
        except Exception as e:
            print(f"Error processing {self.psd_path}: {e}")
            return False
    
    def save_json_fast(self):
        """快速JSON保存"""
        self._layers_info.sort(key=lambda x: x['z'])
        
        json_data = {
            "id": self.file_id,
            "canvas_width": self.psd.width,
            "canvas_height": self.psd.height,
            "preview_path": f"{self.file_id}_preview.png",
            "z": [l["z"] for l in self._layers_info],
            "type": [l["type"] for l in self._layers_info],
            "left": [l["left"] for l in self._layers_info],
            "top": [l["top"] for l in self._layers_info],
            "width": [l["width"] for l in self._layers_info],
            "height": [l["height"] for l in self._layers_info],
            "image_path": [l["image_path"] for l in self._layers_info],
            "layer_names": [l["layer_name"] for l in self._layers_info]
        }
        
        json_path = os.path.join(self.file_output_folder, f"{self.file_id}_layers.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, separators=(',', ':'))

def process_psd_chunk(chunk_data: Tuple[List[str], str]) -> List[Tuple[str, bool]]:
    """处理一批PSD文件"""
    psd_files, output_folder = chunk_data
    results = []
    
    # 为每个进程创建独立的保存器
    saver = BatchImageSaver()
    
    try:
        for psd_file in psd_files:
            # 检查内存
            if not MemoryMonitor.check_memory():
                gc.collect()
            
            try:
                extractor = UltraOptimizedPSDExtractor(psd_file, output_folder, saver)
                success = extractor.extract_ultra_optimized()
                results.append((psd_file, success))
            except Exception as e:
                print(f"Error with {psd_file}: {e}")
                results.append((psd_file, False))
        
        # 等待所有图片保存完成
        saver.wait_completion()
        saver.stop()
        
    except Exception as e:
        print(f"Chunk processing error: {e}")
    
    return results

def get_all_psd_files(folder_path: str) -> List[str]:
    """获取所有PSD文件"""
    return [os.path.join(root, file) 
            for root, _, files in os.walk(folder_path) 
            for file in files if file.lower().endswith('.psd')]

def main():
    # 配置
    psd_folder = r"/storage/human_psd/psd_fp_v1"
    output_folder = r"/storage/human_psd/fp_v1_output_v2"
    
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有PSD文件
    psd_files = get_all_psd_files(psd_folder)
    total_files = len(psd_files)
    
    if total_files == 0:
        print(f"No PSD files found in {psd_folder}")
        return
    
    print(f"Found {total_files} PSD files")
    print(f"Memory usage: {MemoryMonitor.get_memory_usage():.1f} MB")
    
    # 分块处理
    chunks = [psd_files[i:i + CHUNK_SIZE] for i in range(0, total_files, CHUNK_SIZE)]
    chunk_tasks = [(chunk, output_folder) for chunk in chunks]
    
    # 动态调整进程数
    num_processes = min(MAX_WORKERS, len(chunks))
    print(f"Using {num_processes} processes with chunk size {CHUNK_SIZE}")
    
    # 进度跟踪
    from tqdm import tqdm
    completed = 0
    
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = {executor.submit(process_psd_chunk, task): task 
                  for task in chunk_tasks}
        
        with tqdm(total=total_files, desc="Processing PSD files") as pbar:
            for future in as_completed(futures):
                try:
                    results = future.result()
                    completed += len(results)
                    pbar.update(len(results))
                    
                    # 显示内存使用
                    mem_usage = MemoryMonitor.get_memory_usage()
                    pbar.set_postfix(memory=f"{mem_usage:.1f}MB")
                    
                except Exception as e:
                    print(f"\nChunk error: {e}")
    
    print(f"\nCompleted! Processed {completed}/{total_files} files")
    print(f"Final memory usage: {MemoryMonitor.get_memory_usage():.1f} MB")

if __name__ == "__main__":
    main()