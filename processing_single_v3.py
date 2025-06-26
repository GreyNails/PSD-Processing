import os
import json
from PIL import Image
import numpy as np
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, ShapeLayer, TypeLayer, AdjustmentLayer
try:
    from psd_tools.api.layers import Group
except ImportError:
    # 兼容旧版本
    from psd_tools.api.layers import GroupLayer as Group
import io

class PSDLayerExtractor:
    def __init__(self, psd_path, output_folder):
        self.psd_path = psd_path
        self.output_folder = output_folder
        self.psd = PSDImage.open(psd_path)
        self.file_id = os.path.splitext(os.path.basename(psd_path))[0]
        self.layers_info = []
        
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
    def determine_layer_type(self, layer):
        """科学判断图层类型"""
        # 跳过不可见图层
        if not layer.is_visible():
            return None
            
        # 文本图层
        if isinstance(layer, TypeLayer):
            return 1  # textElement
        
        if layer.name.lower() in ['background', '背景', 'bg']:
            return 3  # coloredBackground
            
        # 形状图层（矢量）
        if isinstance(layer, ShapeLayer):
            # 检查是否为纯色背景
            if hasattr(layer, 'vector_mask') and layer.vector_mask:
                bounds = layer.bbox
                if bounds and (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) > (self.psd.width * self.psd.height * 0.8):
                    return 3  # coloredBackground
            return 0  # svgElement
            
        # 调整图层（可能是蒙版）
        if isinstance(layer, AdjustmentLayer):
            return 4  # maskElement
            
        # 像素图层
        if isinstance(layer, PixelLayer):
            # 检查是否为背景
            if layer.name.lower() in ['background', '背景', 'bg']:
                return 3  # coloredBackground
                
            # 检查是否为蒙版
            if layer.mask or 'mask' in layer.name.lower() or '蒙版' in layer.name.lower():
                return 4  # maskElement
                
            # 检查图层内容
            try:
                img = layer.composite()
                if img:
                    # 分析图像内容
                    img_array = np.array(img)
                    
                    # 如果是大面积纯色，可能是背景
                    if len(img_array.shape) >= 3 and img_array.shape[2] >= 3:  # 有RGB通道
                        # 计算图层面积
                        bounds = layer.bbox
                        if bounds:
                            layer_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
                            canvas_area = self.psd.width * self.psd.height
                            
                            # 如果图层覆盖超过70%的画布
                            if layer_area > canvas_area * 0.7:
                                # 分析颜色多样性
                                flat_array = img_array.reshape(-1, img_array.shape[2])
                                unique_colors = np.unique(flat_array, axis=0)
                                
                                # 如果颜色数少于10，认为是背景
                                if len(unique_colors) < 10:
                                    return 3  # coloredBackground
                    
                    return 2  # imageElement
            except Exception as e:
                print(f"分析图层 {layer.name} 时出错: {e}")
                return 2  # 默认为图像元素
                
        # 组图层不处理
        if isinstance(layer, Group):
            return None
            
        # 默认为图像元素
        return 2
        
    def export_layer_as_image(self, layer, layer_type, z_index):
        """导出图层为图片或SVG"""
        try:
            # 生成文件名
            type_str = str(layer_type)
            
            if layer_type == 0:  # svgElement
                # 尝试导出为SVG（目前先导出为PNG）
                filename = f"{self.file_id}_{type_str}_{z_index}.png"
                filepath = os.path.join(self.output_folder, filename)
                
                img = layer.composite()
                if img:
                    # 确保是RGBA模式
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(filepath, 'PNG')
                    return filename
            else:
                # 导出为PNG
                filename = f"{self.file_id}_{type_str}_{z_index}.png"
                filepath = os.path.join(self.output_folder, filename)
                
                img = layer.composite()
                if img:
                    # 确保是RGBA模式以保留透明度
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(filepath, 'PNG')
                    return filename
                    
        except Exception as e:
            print(f"导出图层 {layer.name} 时出错: {e}")
            return None
            
    def process_layers(self, layers=None, z_start=0):
        """递归处理所有图层"""
        if layers is None:
            layers = self.psd
            
        z_index = z_start
        
        # 反转列表以获得正确的z顺序（底层在前）
        for layer in reversed(list(layers)):
            # 跳过不可见图层
            if not layer.is_visible():
                continue
                
            # 处理组
            if isinstance(layer, Group):
                # 递归处理组内的图层
                z_index = self.process_layers(layer, z_index)
                continue
                
            # 判断图层类型
            layer_type = self.determine_layer_type(layer)
            if layer_type is None:
                continue
                
            # 获取图层边界
            bounds = layer.bbox
            if not bounds:
                continue
                
            left, top, right, bottom = bounds
            width = right - left
            height = bottom - top
            
            # 导出图层图片
            image_filename = self.export_layer_as_image(layer, layer_type, z_index)
            
            # 构建图层信息
            layer_info = {
                "z": z_index,
                "type": layer_type,
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "image_path": image_filename if image_filename else "",
                "layer_name": layer.name  # 额外信息，帮助调试
            }
            
            self.layers_info.append(layer_info)
            print(f"处理图层: {layer.name} (类型: {layer_type}, z: {z_index})")
            z_index += 1
            
        return z_index
        
    def export_preview(self):
        """导出PSD预览图（只包含可见图层）"""
        try:
            preview_filename = f"{self.file_id}_preview.png"
            preview_path = os.path.join(self.output_folder, preview_filename)
            
            # 方法1：直接使用PSD的composite方法（最可靠）
            print("正在生成预览图...")
            
            # 使用PSD自带的合成功能，它会自动只渲染可见图层
            preview = self.psd.composite()
            
            if preview:
                # 如果是RGBA模式，添加白色背景
                if preview.mode == 'RGBA':
                    background = Image.new('RGB', preview.size, (255, 255, 255))
                    background.paste(preview, mask=preview.split()[3])
                    preview = background
                elif preview.mode != 'RGB':
                    preview = preview.convert('RGB')
                
                preview.save(preview_path, 'PNG', quality=10)
                print(f"预览图已保存: {preview_filename} (尺寸: {preview.size})")
                return preview_filename
            else:
                print("警告：无法生成预览图")
                
                # 方法2：手动合成（备用方案）
                print("尝试手动合成预览图...")
                return self._manual_composite_preview()
                
        except Exception as e:
            print(f"导出预览图时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 尝试备用方案
            try:
                return self._manual_composite_preview()
            except:
                return None
    
    def _manual_composite_preview(self):
        """手动合成预览图（备用方案）"""
        preview_filename = f"{self.file_id}_preview.png"
        preview_path = os.path.join(self.output_folder, preview_filename)
        
        # 创建画布
        canvas = Image.new('RGBA', (self.psd.width, self.psd.height), (255, 255, 255, 0))
        
        # 获取所有图层并反转（底层在前）
        all_layers = []
        self._get_all_layers(self.psd, all_layers)
        
        visible_count = 0
        for layer in all_layers:
            if not layer.is_visible():
                continue
                
            if isinstance(layer, Group):
                continue
                
            try:
                # 获取图层图像
                layer_image = layer.composite()
                if layer_image:
                    visible_count += 1
                    bounds = layer.bbox
                    if bounds:
                        left, top = int(bounds[0]), int(bounds[1])
                        
                        # 确保图像是RGBA模式
                        if layer_image.mode != 'RGBA':
                            layer_image = layer_image.convert('RGBA')
                        
                        # 创建临时画布并粘贴图层
                        temp = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
                        temp.paste(layer_image, (left, top))
                        
                        # 合成到主画布
                        canvas = Image.alpha_composite(canvas, temp)
                        print(f"  已合成图层: {layer.name}")
                        
            except Exception as e:
                print(f"  合成图层 {layer.name} 失败: {e}")
        
        print(f"共合成了 {visible_count} 个可见图层")
        
        # 转换为RGB
        final = Image.new('RGB', canvas.size, (255, 255, 255))
        final.paste(canvas, mask=canvas.split()[3])
        
        final.save(preview_path, 'PNG', quality=10)
        print(f"手动合成预览图已保存: {preview_filename}")
        return preview_filename
    
    def _get_all_layers(self, layer_container, result):
        """递归获取所有图层（保持原始顺序）"""
        for layer in reversed(list(layer_container)):
            result.append(layer)
            if isinstance(layer, Group) and layer.is_visible():
                self._get_all_layers(layer, result)
    
    def _collect_visible_layers(self, layers, result, z_start=0):
        """递归收集所有可见图层"""
        z_index = z_start
        # 注意：这里使用reversed来保持正确的图层顺序（底层在前）
        for layer in reversed(list(layers)):
            if not layer.is_visible():
                continue
                
            if isinstance(layer, Group):
                # 递归处理组内的图层
                z_index = self._collect_visible_layers(layer, result, z_index)
            else:
                # 跳过没有内容的图层
                if hasattr(layer, 'bbox') and layer.bbox:
                    result.append((layer, z_index))
                    z_index += 1
        return z_index
        
    def save_json(self):
        """保存JSON文件（列表格式）"""
        json_filename = f"{self.file_id}_layers.json"
        json_path = os.path.join(self.output_folder, json_filename)
        
        # 按z值排序
        self.layers_info.sort(key=lambda x: x['z'])
        
        # 转换为列表格式
        list_format = {
            "id": self.file_id,
            "canvas_width": self.psd.width,
            "canvas_height": self.psd.height,
            "preview_path": f"{self.file_id}_preview.png",
            "z": [],
            "type": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
            "image_path": [],
            "layer_names": []  # 额外信息，帮助调试
        }
        
        # 填充列表
        for layer_info in self.layers_info:
            list_format["z"].append(layer_info["z"])
            list_format["type"].append(layer_info["type"])
            list_format["left"].append(layer_info["left"])
            list_format["top"].append(layer_info["top"])
            list_format["width"].append(layer_info["width"])
            list_format["height"].append(layer_info["height"])
            list_format["image_path"].append(layer_info["image_path"])
            list_format["layer_names"].append(layer_info["layer_name"])
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(list_format, f, ensure_ascii=False, indent=2)
            
        print(f"JSON文件已保存至: {json_path}")
        
    def extract(self):
        """执行提取流程"""
        print(f"开始处理PSD文件: {self.psd_path}")
        print(f"PSD尺寸: {self.psd.width} x {self.psd.height}")
        print(f"输出文件夹: {self.output_folder}")
        print("-" * 50)
        
        # 导出预览图（只包含可见图层）
        print("正在生成预览图（仅可见图层）...")
        self.export_preview()
        
        # 处理所有图层
        print("\n正在处理图层...")
        self.process_layers()
        
        # 保存JSON
        print("\n正在保存JSON...")
        self.save_json()
        
        print(f"\n处理完成！共提取 {len(self.layers_info)} 个可见图层")
        print(f"所有文件已保存到: {self.output_folder}")
        

def main():
    # 使用示例 - 使用原始字符串避免转义问题
    psd_file = r"output_jiewu_v2.psd"  # 您的PSD文件路径
    output_folder = r"output"  # 输出文件夹
    
    # 确保PSD文件存在
    if not os.path.exists(psd_file):
        print(f"错误：找不到PSD文件 {psd_file}")
        return
        
    try:
        # 创建提取器并执行
        extractor = PSDLayerExtractor(psd_file, output_folder)
        extractor.extract()
    except Exception as e:
        print(f"处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
from tqdm import tqdm
if __name__ == "__main__":
    import time
    start_time = time.perf_counter()  # 更精确的计时器

    main()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"程序运行时间: {elapsed_time * 1000:.6f} 毫秒")  # 转换为毫秒