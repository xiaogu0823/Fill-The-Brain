import tensorrt as trt
import torch
import logging
import atexit
from typing import Dict, Optional
from timm.models.pvt_v2 import pvt_v2_b2 
from emonet.models import EmoNet
from ultralytics import YOLO

class GlobalModelManager:
    """
    全局模型管理器 - 修复state_dict加载问题
    适配PyTorchEmotionAnalyzer的需求
    """
    _instance = None
    _models: Dict[str, torch.nn.Module] = {}
    
    # 模型类型映射：根据模型key确定要创建的模型类
    _model_classes = {
        "emotion_model": pvt_v2_b2,  
        "face_detector": YOLO,  
        "va_model": EmoNet 
    }
    
    # 模型初始化参数 
    _model_init_params = {
        "emotion_model": {"pretrained": False, "num_classes": 8},  # PVT模型参数
        "va_model": {"n_expression": 8}  # EmoNet模型参数
    }
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalModelManager, cls).__new__(cls)
            atexit.register(cls._instance.cleanup)
        return cls._instance
    
    def load_model(self, model_key: str, model_path: str, **kwargs) -> torch.nn.Module:
        if model_key in self._models:
            logging.info(f"模型 '{model_key}' 已加载，返回现有实例")
            return self._models[model_key]
        
        try:
            logging.info(f"正在加载模型: {model_key}，路径: {model_path}")
            device = kwargs.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
            
            # 特殊处理YOLO模型
            if model_key == "face_detector":
                return self._load_yolo_model(model_path, **kwargs)
            
            # 加载PyTorch模型
            return self._load_pytorch_model(model_key, model_path, device, **kwargs)
            
        except Exception as e:
            logging.error(f"模型 '{model_key}' 加载失败: {e}")
            raise
    
    def _load_pytorch_model(self, model_key: str, model_path: str, device: str, **kwargs):
        """加载PyTorch模型（处理state_dict）"""
        # 1. 先创建模型实例
        if model_key not in self._model_classes:
            raise ValueError(f"未知的模型类型: {model_key}")
        
        model_class = self._model_classes[model_key]
        init_params = self._model_init_params.get(model_key, {}).copy()
        
        # 允许通过kwargs覆盖默认参数
        init_params.update(kwargs)
        
        # 创建模型实例
        model = model_class(**init_params)
        model = model.to(device)
        
        # 2. 如果提供了模型路径，则加载权重
        if model_path:
            checkpoint = torch.load(model_path, map_location=device, weights_only=False)
            logging.info(f"加载的模型文件类型: {type(checkpoint)}")
            
            # 3. 智能处理不同类型的模型文件
            if isinstance(checkpoint, dict):
                state_dict = self._extract_state_dict(checkpoint, model_key)
                # 处理可能的module.前缀（多GPU训练）
                state_dict = self._fix_state_dict_keys(state_dict)
                
                # 加载状态字典到模型
                try:
                    model.load_state_dict(state_dict)
                    logging.info(f"模型 '{model_key}' 状态字典加载成功")
                except Exception as e:
                    logging.warning(f"严格模式加载失败: {e}，尝试非严格模式")
                    model.load_state_dict(state_dict, strict=False)
                    logging.info(f"模型 '{model_key}' 非严格模式加载成功")
            else:
                # 如果是完整模型对象
                model = checkpoint.to(device)
                logging.info("加载了完整模型对象")
        else:
            logging.info(f"模型 '{model_key}' 未提供权重路径，使用初始化模型")
        
        # 4. 设置评估模式
        model.eval()
        
        # 存储到模型字典
        self._models[model_key] = model
        logging.info(f"模型 '{model_key}' 加载成功，设备: {device}")
        
        return model
    
    def _extract_state_dict(self, checkpoint: dict, model_key: str):
        """从检查点中提取state_dict（适配不同模型格式）"""
        if model_key == "emotion_model":
            # 适配PVT模型的检查点格式
            if 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
                logging.info("检测到包含'state_dict'的PVT模型检查点")
            else:
                state_dict = checkpoint
                logging.info("使用直接的状态字典作为PVT模型权重")
        elif model_key == "va_model":
            # 适配EmoNet模型的检查点格式
            state_dict = checkpoint
            logging.info("使用直接的状态字典作为VA模型权重")
        else:
            # 默认处理方式
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
                logging.info("检测到包含'model_state_dict'的检查点")
            elif 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
                logging.info("检测到包含'state_dict'的检查点")
            else:
                state_dict = checkpoint
                logging.info("检测到直接的状态字典")
        
        return state_dict
    
    def _load_yolo_model(self, model_path: str, **kwargs):
        """加载YOLO模型（特殊处理）"""
        try:
            model = YOLO(model_path)
            # 设置YOLO参数
            model.conf = kwargs.get('conf', 0.7)  
            model.iou = kwargs.get('iou', 0.5)
            
            # 存储YOLO模型
            self._models["face_detector"] = model
            logging.info(f"YOLO模型加载成功: {model_path}")
            return model
            
        except Exception as e:
            logging.error(f"YOLO模型加载失败: {e}")
            raise
    
    def _fix_state_dict_keys(self, state_dict):
        """修复state_dict键名（处理多GPU训练的前缀）"""
        try:
            if not isinstance(state_dict, dict):
                return state_dict
                
            # 检查是否所有键都有module.前缀
            keys = list(state_dict.keys())
            if not keys:
                return state_dict
                
            has_module_prefix = all(key.startswith('module.') for key in keys)
            
            if has_module_prefix:
                logging.info("检测到多GPU训练模型，移除module.前缀")
                from collections import OrderedDict
                new_state_dict = OrderedDict()
                for k, v in state_dict.items():
                    name = k[7:] if k.startswith('module.') else k  # 移除module.前缀
                    new_state_dict[name] = v
                return new_state_dict
            else:
                # 检查是否有混合前缀的情况
                from collections import OrderedDict
                new_state_dict = OrderedDict()
                for k, v in state_dict.items():
                    name = k[7:] if k.startswith('module.') else k
                    new_state_dict[name] = v
                return new_state_dict
                
        except Exception as e:
            logging.warning(f"修复state_dict键名时出错: {e}，使用原始state_dict")
            return state_dict
    
    def get_model(self, model_key: str) -> Optional[torch.nn.Module]:
        """获取已加载的模型实例"""
        return self._models.get(model_key)
    
    def unload_model(self, model_key: str) -> bool:
        """卸载指定模型并释放资源"""
        if model_key in self._models:
            model = self._models[model_key]
            
            # 特殊处理YOLO模型
            if model_key == "face_detector":
                # YOLO模型可能有特殊的清理需求
                try:
                    if hasattr(model, 'model'):
                        del model.model
                except:
                    pass
            
            del self._models[model_key]
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logging.info(f"模型 '{model_key}' 已卸载")
            return True
        return False
    
    def cleanup(self):
        """程序退出时统一释放所有模型资源"""
        if not self._models:
            return
        
        logging.info("开始清理所有模型资源...")
        model_keys = list(self._models.keys())
        for model_key in model_keys:
            self.unload_model(model_key)
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logging.info("所有模型资源已释放")


