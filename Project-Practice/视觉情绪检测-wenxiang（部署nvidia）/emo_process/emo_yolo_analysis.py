import tensorrt as trt
from cuda import cuda
import cv2
import numpy as np
from PIL import Image
import time
import ctypes
import os

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

class HostDeviceMem:
    """Host/Device memory holder (使用 ctypes 指针)"""
    def __init__(self, host_ptr, device_mem, nbytes, size):
        self.host = host_ptr
        self.device = device_mem
        self.nbytes = nbytes
        self.size = size

    def __del__(self):
        try:
            if hasattr(self, 'host') and self.host:
                cuda.cuMemFreeHost(self.host)
            if hasattr(self, 'device') and self.device:
                cuda.cuMemFree(self.device)
        except Exception as e:
            logging.debug(f"Cleanup error: {e}")

class TensorRTInference:
    def __init__(self, engine_path, device_id=0):
        self.device_id = device_id
        self.engine_path = engine_path
        
        # 初始化设备上下文
        self._initialize_device_context()
        
        # 加载引擎
        self._load_engine()
        
        # 分配内存
        self.inputs, self.outputs, self.bindings = self._allocate_buffers()
        
        logging.info(f"TensorRT Loaded: {engine_path}")
        logging.info(f"Input shape = {self.input_shape}, dtype={self.input_dtype}")

    def _initialize_device_context(self):
        """初始化CUDA上下文"""
        # 初始化CUDA
        (cuda_err,) = cuda.cuInit(0)
        if cuda_err != cuda.CUresult.CUDA_SUCCESS:
            raise RuntimeError(f"CUDA init failed: {cuda_err}")
        
        # 设置设备
        err, device = cuda.cuDeviceGet(self.device_id)
        if err != cuda.CUresult.CUDA_SUCCESS:
            raise RuntimeError(f"Failed to get device {self.device_id}: {err}")
        
        # 创建上下文
        flags = cuda.CUctx_flags.CU_CTX_SCHED_AUTO
        err, self.cu_ctx = cuda.cuCtxCreate(flags, self.device_id)
        if err != cuda.CUresult.CUDA_SUCCESS:
            raise RuntimeError(f"Failed to create CUDA context: {err}")
        
        # 创建流
        err, self.stream = cuda.cuStreamCreate(0)
        if err != cuda.CUresult.CUDA_SUCCESS:
            raise RuntimeError(f"Failed to create stream: {err}")

    def _load_engine(self):
        """加载TensorRT引擎 - 包含你的YOLO插件加载"""
        try:
            with open(self.engine_path, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
                self.engine = runtime.deserialize_cuda_engine(f.read())
            
            self.context = self.engine.create_execution_context()
            
            # 解析输入输出
            self.input_binding = 0
            self.input_shape = self.engine.get_binding_shape(self.input_binding)
            self.input_dtype = trt.nptype(self.engine.get_binding_dtype(self.input_binding))
            
        except Exception as e:
            logging.error(f"Failed to load engine {self.engine_path}: {e}")
            raise

    def _allocate_buffers(self):
        """分配主机/设备缓冲区"""
        inputs = []
        outputs = []
        bindings = []

        for binding in self.engine:
            idx = self.engine.get_binding_index(binding)
            dims = self.engine.get_binding_shape(idx)
            size = trt.volume(dims)
            dtype = trt.nptype(self.engine.get_binding_dtype(idx))
            nbytes = size * dtype().itemsize

            # 分配主机固定内存
            err, host_ptr = cuda.cuMemHostAlloc(nbytes, cuda.CU_MEMHOSTALLOC_PORTABLE)
            if err != cuda.CUresult.CUDA_SUCCESS:
                raise RuntimeError(f"Failed to allocate host memory: {err}")

            err, device_mem = cuda.cuMemAlloc(nbytes)
            if err != cuda.CUresult.CUDA_SUCCESS:
                cuda.cuMemFreeHost(host_ptr)
                raise RuntimeError(f"Failed to allocate device memory: {err}")

            bindings.append(int(device_mem))

            mem = HostDeviceMem(host_ptr, device_mem, nbytes, size)

            if self.engine.binding_is_input(binding):
                inputs.append(mem)
            else:
                outputs.append(mem)

        return inputs, outputs, bindings

    def infer(self, input_np: np.ndarray):
        """执行推理"""
        # 自动添加batch维度
        if input_np.ndim == 3:
            input_np = np.expand_dims(input_np, axis=0)
        elif input_np.ndim != 4:
            raise ValueError("Input must be (C,H,W) or (N,C,H,W)")

        # 验证输入形状
        if input_np.shape != tuple(self.input_shape):
            # 尝试动态调整（如果引擎支持）
            if self.context.set_binding_shape(0, input_np.shape):
                self.input_shape = input_np.shape
            else:
                raise ValueError(f"Input shape mismatch, expect {self.input_shape}, got {input_np.shape}")

        # 将数据复制到主机内存
        input_mem = self.inputs[0]
        ptr = input_mem.host
        arr = (ctypes.c_float * input_np.size).from_address(ptr)
        np_arr = np.ctypeslib.as_array(arr)
        np_arr[:] = input_np.flatten()

        # 推送CUDA上下文
        prev_ctx = cuda.cuCtxGetCurrent()
        cuda.cuCtxPushCurrent(self.cu_ctx)

        try:
            # 复制输入到GPU
            cuda.cuMemcpyHtoDAsync(input_mem.device, input_mem.host, input_mem.nbytes, self.stream)

            # 执行推理
            if not self.context.execute_v2(self.bindings):
                raise RuntimeError("Inference execution failed")

            # 复制输出到CPU
            trt_out_list = []
            for out_mem in self.outputs:
                cuda.cuMemcpyDtoHAsync(out_mem.host, out_mem.device, out_mem.nbytes, self.stream)
                arr = (ctypes.c_float * out_mem.size).from_address(out_mem.host)
                np_arr = np.ctypeslib.as_array(arr).copy()
                trt_out_list.append(np_arr)

            cuda.cuStreamSynchronize(self.stream)
            
            return trt_out_list

        finally:
            # 恢复之前的上下文
            cuda.cuCtxPopCurrent()
            if prev_ctx[1]:
                cuda.cuCtxPushCurrent(prev_ctx[1])

    def cleanup(self):
        """显式清理资源"""
        try:
            if hasattr(self, 'outputs'):
                del self.outputs
            if hasattr(self, 'inputs'):
                del self.inputs
            if hasattr(self, 'stream') and self.stream:
                cuda.cuStreamDestroy(self.stream)
            if hasattr(self, 'context'):
                del self.context
            if hasattr(self, 'engine'):
                del self.engine
            if hasattr(self, 'cu_ctx') and self.cu_ctx:
                cuda.cuCtxDestroy(self.cu_ctx)
        except Exception as e:
            logging.debug(f"Cleanup warning: {e}")

    def __del__(self):
        self.cleanup()

class PyTorchEmotionAnalyzer:
    def __init__(self, emotion_model_path=None, face_model_path=None, emonet_path=None, device_id=0):
        """
        参数:
            emotion_model_path: 情感识别TensorRT模型路径
            face_model_path: YOLO人脸检测TensorRT模型路径
            emonet_path: EmoNet VA模型路径（可选）
            device_id: GPU设备ID
        """
        self.emotion_labels = ['Neutral', 'Happy', 'Sad', 'Surprise', 'Fear', 'Disgusted', 'Anger', 'Contempt']
        
        # 保存所有模型路径
        self.emotion_model_path = emotion_model_path
        self.face_model_path = face_model_path
        self.emonet_path = None
        
        # logging.info(f"初始化PyTorchEmotionAnalyzer:")
        # logging.info(f"情感模型: {emotion_model_path}")
        # logging.info(f"人脸模型: {face_model_path}")
        # logging.info(f"EmoNet模型: {emonet_path}")
        
        # 加载TensorRT推理器
        self.emotion_trt = TensorRTInference(emotion_model_path, device_id)
        self.face_trt = TensorRTInference(face_model_path, device_id)
        # self.emonet_trt = TensorRTInference(emonet_path, device_id)
        
        # 获取模型输入信息
        self.face_input_shape = self.face_trt.input_shape
        self.emotion_input_shape = self.emotion_trt.input_shape
        
        # 人脸检测参数
        self.face_input_size = (self.face_input_shape[3], self.face_input_shape[2])  # (width, height)
        self.confidence_threshold = 0.5
        
        # logging.info(f"PyTorchEmotionAnalyzer初始化完成")
        # logging.info(f"人脸模型输入尺寸: {self.face_input_shape}")
        # logging.info(f"情感模型输入尺寸: {self.emotion_input_shape}")
        # logging.info(f"EmoNet模型输入尺寸: {self.emonet_trt.input_shape}")
    
    def detect_faces(self, frame):
        """使用YOLO检测人脸"""
        try:
            # 获取原始图像形状用于后处理
            orig_h, orig_w = frame.shape[:2]
            
            # 预处理人脸检测图像
            processed_image = frame.copy()
            
            # 调整大小
            input_img = cv2.resize(processed_image, self.face_input_size)
            
            # 归一化
            input_img = input_img.astype(np.float32) / 255.0
            
            # 转换为NCHW格式供模型使用
            input_img = np.transpose(input_img, (2, 0, 1))  # HWC -> CHW
            input_img = np.expand_dims(input_img, axis=0)   # CHW -> NCHW [1, C, H, W]
            
            # TensorRT推理
            outputs = self.face_trt.infer(input_img)
            
            # 后处理检测结果
            faces_info = self._postprocess_faces(outputs, (orig_h, orig_w))
            
            return faces_info
            
        except Exception as e:
            logging.error(f"人脸检测失败: {e}")
            return []
    
    def _postprocess_faces(self, outputs, orig_shape):
        """后处理人脸检测结果"""
        faces_info = []
        orig_h, orig_w = orig_shape
        
        # 处理展平的输出 [1, 5, 8400] -> (42000,)
        if len(outputs) == 1 and outputs[0].size == 42000:  # 1 * 5 * 8400=42000
            # 重新整形为 [1, 5, 8400]
            predictions_reshaped = outputs[0].reshape(1, 5, 8400)
            # 取第一个batch，转置为 [8400, 5]
            predictions = predictions_reshaped[0].T
        else:
            predictions = outputs[0]
            if predictions.ndim > 1:
                predictions = predictions.reshape(-1, predictions.shape[-1])
        
        # 检查形状
        if predictions.shape[1] != 5:
            logging.error(f"检测输出形状错误: {predictions.shape}")
            return []
        
        # 提取边界框和置信度
        boxes = predictions[:, :4]      # [cx, cy, w, h]
        scores = predictions[:, 4]      # confidence
        
        # 过滤低置信度的检测结果
        conf_mask = scores > self.confidence_threshold
        boxes = boxes[conf_mask]
        scores = scores[conf_mask]
        
        if len(boxes) == 0:
            return []
        
        # 应用非极大值抑制
        indices = self._non_max_suppression(boxes, scores, 0.5)
        
        for idx in indices:
            box = boxes[idx]
            score = scores[idx]
            
            # 计算缩放比例
            scale_x = orig_w / self.face_input_size[0]
            scale_y = orig_h / self.face_input_size[1]
            
            # 转换边界框坐标 [cx, cy, w, h] -> [x1, y1, x2, y2]
            x_center, y_center, width, height = box
            x1 = (x_center - width / 2) * scale_x
            y1 = (y_center - height / 2) * scale_y
            x2 = (x_center + width / 2) * scale_x
            y2 = (y_center + height / 2) * scale_y
            
            # 确保坐标在图像范围内且有效
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(orig_w, int(x2)), min(orig_h, int(y2))
            
            # 检查边界框是否有效
            if x2 <= x1 or y2 <= y1:
                continue
            
            faces_info.append({
                'bbox': (x1, y1, x2, y2),
                'confidence': float(score)
            })
        
        return faces_info
    
    def _non_max_suppression(self, boxes, scores, iou_threshold):
        """非极大值抑制"""
        if len(boxes) == 0:
            return []
        
        x_center, y_center, width, height = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        x1 = x_center - width / 2
        y1 = y_center - height / 2
        x2 = x_center + width / 2
        y2 = y_center + height / 2
        
        boxes_xyxy = np.column_stack([x1, y1, x2, y2])
        
        # 按置信度排序
        order = scores.argsort()[::-1]
        boxes_xyxy = boxes_xyxy[order]
        scores = scores[order]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            # 计算IOU
            xx1 = np.maximum(boxes_xyxy[i, 0], boxes_xyxy[order[1:], 0])
            yy1 = np.maximum(boxes_xyxy[i, 1], boxes_xyxy[order[1:], 1])
            xx2 = np.minimum(boxes_xyxy[i, 2], boxes_xyxy[order[1:], 2])
            yy2 = np.minimum(boxes_xyxy[i, 3], boxes_xyxy[order[1:], 3])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            area_i = (boxes_xyxy[i, 2] - boxes_xyxy[i, 0]) * (boxes_xyxy[i, 3] - boxes_xyxy[i, 1])
            area_others = (boxes_xyxy[order[1:], 2] - boxes_xyxy[order[1:], 0]) * (boxes_xyxy[order[1:], 3] - boxes_xyxy[order[1:], 1])
            
            iou = inter / (area_i + area_others - inter + 1e-7)
            
            # 保留IOU低于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return keep
    
    def detect_emotion(self, face_roi):
        try:
            if face_roi.size == 0 or face_roi.shape[0] < 10 or face_roi.shape[1] < 10:
                return None
            
            # 预处理人脸图像
            transposse_data = self._preprocess_face_image(face_roi)
            input_data = np.expand_dims(transposse_data, axis=0)

            # TensorRT推理
            outputs = self.emotion_trt.infer(input_data)
            
            if outputs and len(outputs) > 0:
                logits = outputs[0].reshape(1, -1)
                probabilities = self._softmax(logits)[0]
                
                emotion_dict = {
                    'neutral': float(probabilities[0]),
                    'happy': float(probabilities[1]),
                    'sad': float(probabilities[2]),
                    'surprised': float(probabilities[3]),
                    'fear': float(probabilities[4]),
                    'disgusted': float(probabilities[5]),
                    'angry': float(probabilities[6]),
                    'contempt': float(probabilities[7])
                }
                return emotion_dict
            
            return None
            
        except Exception as e:
            logging.error(f"情感分析失败: {e}")
            return None
            
    def detect_va(self, face_roi):
        if not hasattr(self, 'emonet_trt') or self.emonet_trt is None:
            return None, 0.0
            
        try:
            if face_roi.size == 0 or face_roi.shape[0] < 10 or face_roi.shape[1] < 10:
                return None, 0.0
                
            img_resized = cv2.resize(face_roi, (256, 256))[:,:,:3]
            transposse_data = np.transpose(img_resized, (2, 0, 1))/ 255.0
            input_data = np.expand_dims(transposse_data, axis=0)
            outputs = self.emonet_trt.infer(input_data) # 这里输出是list类型，长度为4即["heatmap", "expression", "valence", "arousal"]
            
            if outputs and len(outputs) > 0:
                valence_score = np.clip(outputs[2], -1.0, 1.0)
                arousal_score = np.clip(outputs[3], -1.0, 1.0)
            return valence_score, arousal_score
            
        except Exception as e:
            logging.error(f"VA分析失败: {e}")
            return None, 0.0
    
    def _preprocess_face_image(self, face_image):
        # 确保图像是RGB格式
        if len(face_image.shape) == 3 and face_image.shape[2] == 3:
            if face_image.dtype == np.uint8:
                face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # 调整尺寸到模型输入大小
        h, w = 224, 224  # 情感模型输入尺寸
        img_resized = cv2.resize(face_image, (w, h))
        
        # 转换为float32并归一化
        img_normalized = img_resized.astype(np.float32) / 255.0
        
        # 标准化 (ImageNet均值和标准差)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_normalized = (img_normalized - mean) / std
        
        # 调整维度顺序: HWC -> CHW
        img_chw = np.transpose(img_normalized, (2, 0, 1))
        
        return img_chw
    
    def _softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def analyze_frame(self, frame):
        try:
            # 检测人脸
            faces = self.detect_faces(frame)
            # if not faces:
            #     return None
            emotions = []
            
            closest_face = None
            max_area = 0
            
            for i, face_data in enumerate(faces):
                x1, y1, x2, y2 = face_data['bbox']
                face_area = (x2 - x1) * (y2 - y1)

                if face_area > max_area:
                    max_area = face_area
                    closest_face = face_data

            if closest_face is not None:
                x1, y1, x2, y2 = closest_face['bbox']
                detection_conf = closest_face['confidence']

                # 提取人脸区域
                height, width = frame.shape[:2]
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(width, x2), min(height, y2)

                if x2 > x1 and y2 > y1:
                    face_roi = frame[y1:y2, x1:x2]
                    
                    if face_roi.size > 0:
                        # 分析情感
                        emotion_result = self.detect_emotion(face_roi)
                        valence, arousal = self.detect_va(face_roi)
                        
                        if emotion_result:
                            emotions.append({
                                'bbox': (x1, y1, x2, y2),
                                'emotion_result': emotion_result,  # 字典格式
                                'valence': valence,
                                'arousal': arousal,
                                'detection_face_conf': detection_conf,
                                'distance_metric': max_area
                            })
            
            return {
                'emotions': emotions,
                'face_count': len(emotions),
            }
            
        except Exception as e:
            logging.error(f"帧分析失败: {e}")
            return {'emotions': [], 'face_count': 0, 'error': str(e)}
    
    def analyze_video(self, video_path, callback=None):
        """分析视频文件"""
        results = []
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        processed_frames = 0
        ac_frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ac_frame_count += 1
            
            frame_result = self.analyze_frame(frame)
            frame_result['frame_index'] = processed_frames
            results.append(frame_result)
            processed_frames += 1
            
            if callback:
                callback(processed_frames, frame_count)
        
        cap.release()
        
        logging.info(f"视频分析完成，共处理 {processed_frames} 帧")
        logging.info(f"视频信息: 总帧数: {frame_count}, FPS: {fps}, 实际处理帧数: {ac_frame_count}")
        
        return results
    
    def progress_callback(self, current, total):
        """进度回调函数"""
        progress = (current / total) * 100
        print(f"\r处理进度: {current}/{total} ({progress:.1f}%)", end='', flush=True)
    
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'emotion_trt'):
                self.emotion_trt.cleanup()
            if hasattr(self, 'face_trt'):
                self.face_trt.cleanup()
            if hasattr(self, 'emonet_trt'):
                self.emonet_trt.cleanup()
        except Exception as e:
            logging.debug(f"资源清理失败: {e}")

if __name__ == "__main__":
    # 初始化分析器
    analyzer = PyTorchEmotionAnalyzer(
        emotion_model_path='/home/nvidia/workspace/wenxiang/weights/mobilenetv3_fp.engine',
        face_model_path='/home/nvidia/workspace/wenxiang/weights/yolov11n-face.engine',
        emonet_path='/home/nvidia/workspace/wenxiang/weights/emonet.engine',  
        device_id=0
    )
    # cap = cv2.VideoCapture(0)
    # 测试单张图片
    # while True:
    #     ret,frame = cap.read()
    #     if ret:
    #         # frame = cv2.imread("/home/nvidia/workspace/wenxiang/happy_1.jpg")



    #         # if frame is not None:
    #         result = analyzer.analyze_frame(frame)
    #         print(f"检测到 {result['face_count']} 个人脸")
    #         for emotion in result['emotions']:
    #             # print(f"位置: {emotion['bbox']}, 人脸检测置信度: {emotion['detection_face_conf']:.2f}")
    #             print(f"情感结果: {emotion['emotion_result']}")  # 现在输出字典格式
    #             # print(f"Valence: {emotion['valence']:.4f}, Arousal: {emotion['arousal']:.4f}")


    from emotion_result_vis import EmotionCSVWriter
    csv_writer = EmotionCSVWriter()     

    video_path = "/home/nvidia/workspace/eval_data/03_365_1.mp4"
    
    results = analyzer.analyze_video(video_path)


    csv_path = csv_writer.save_with_video_path(results, video_path)
    print(f"当前结果 ：{csv_path}")
    # 清理资源
    del analyzer

