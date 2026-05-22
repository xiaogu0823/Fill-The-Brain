import sys
import os
import time
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import QMessageBox
from collections import deque
import threading
from emo_process.emo_yolo_analysis import PyTorchEmotionAnalyzer
from emo_process.emotion_result_vis import EmotionCSVWriter
from emo_process.model_manager import GlobalModelManager
global_model_manager = GlobalModelManager()

class VideoAnalysisWorker(QObject):
    """视频分析工作线程 - 处理情感分析算法"""
    
    # 分析进度和结果信号
    analysis_started = pyqtSignal(str, int)      # 视频路径, 产品索引
    analysis_progress = pyqtSignal(int, int)     # 当前帧, 总帧数  
    analysis_finished = pyqtSignal(str, str, int) # 视频路径, csv路径, 产品索引
    analysis_failed = pyqtSignal(str, str, int)  # 视频路径, 错误信息, 产品索引
    
    def __init__(self):
        super().__init__()
        self.analyzer = None
        self.csv_writer = None
        self.is_analyzing = False
        self.current_video_path = ""
        self.current_product_index = 0
        self.is_initialized = False
        self.frame_queue = deque()     
        self.queue_lock = threading.Lock()
        self.accepting_frames = False       # 是否接收新帧
        self.realtime_results = []  
    def init_analyzer(self, emotion_model_path, face_model_path, emonet_path):
        """使用全局模型管理器初始化分析器"""
        try:
            self.analyzer = PyTorchEmotionAnalyzer(
                emotion_model_path=emotion_model_path,  
                face_model_path=face_model_path,
                emonet_path=emonet_path
            )
            
            self.csv_writer = EmotionCSVWriter()  

            self.is_initialized = True
            logging.info(" 分析器初始化成功（使用全局模型管理器）")
            
        except Exception as e:
            logging.error(f" 分析器初始化失败: {e}")
            self.is_initialized = False
    @pyqtSlot(object)
    def analyze_frame(self, frame):
        if not self.accepting_frames:
            return

        with self.queue_lock:
            self.frame_queue.append(frame)
    @pyqtSlot(str, int)
    def analyze_video(self, video_path, product_index=0):
        """分析视频的槽函数 - 由信号触发"""
        if not self.is_initialized or not self.analyzer:
            error_msg = "情感分析器未正确初始化"
            self.analysis_failed.emit(video_path, error_msg, product_index)
            return
            
        if not os.path.exists(video_path):
            error_msg = f"视频文件不存在: {video_path}"
            self.analysis_failed.emit(video_path, error_msg, product_index)
            return
        
        self.is_analyzing = True
        self.current_video_path = video_path
        self.current_product_index = product_index
        
        try:
            # 发射分析开始信号
            self.analysis_started.emit(video_path, product_index)
            logging.info(f"开始分析视频: {video_path}, 产品索引: {product_index}")
            
            # 进度回调函数
            def progress_callback(current, total):
                if self.is_analyzing:
                    self.analysis_progress.emit(current, total)
            
            # 执行视频分析
            results = self.analyzer.analyze_video(video_path, callback=progress_callback)
            
            # 保存结果到CSV
            csv_path = self.csv_writer.save_with_video_path(results, video_path)
            
            # 发射分析完成信号
            self.analysis_finished.emit(video_path, csv_path, product_index)
            logging.info(f"视频分析完成: {csv_path}")
            
        except Exception as e:
            error_msg = f"视频分析失败: {str(e)}"
            logging.error(error_msg)
            self.analysis_failed.emit(video_path, error_msg, product_index)
        
        finally:
            self.is_analyzing = False
            
    def _consume_frames(self):
        frame_index = 0

        while self.accepting_frames or self.frame_queue:
            with self.queue_lock:
                if not self.frame_queue:
                    continue
                frame = self.frame_queue.popleft()
            result = self.analyzer.analyze_frame(frame)
            result['frame_index'] = frame_index
            self.realtime_results.append(result)
            print(f'当前帧数为{frame_index}')
            frame_index += 1

    @pyqtSlot()
    def stop_analysis(self):
        """停止分析"""
        self.is_analyzing = False
        logging.info("视频分析已停止")
    def start_realtime_analysis(self):
        print('已经接收到')
        self.realtime_results = []
        self.accepting_frames = True

        self.worker_thread = threading.Thread(
            target=self._consume_frames,
            daemon=True
        )
        self.worker_thread.start()

    def stop_realtime_analysis_and_finalize(self, video_path, product_index):
        """
        录制结束后调用
        """
        self.accepting_frames = False
        self.worker_thread.join()  #  等所有帧处理完

        csv_path = self.csv_writer.save_with_video_path(
            self.realtime_results,
            video_path
        )

        self.analysis_finished.emit(video_path, csv_path, product_index)

class GlobalAnalysisManager:
    """全局分析管理器 - 单例模式"""
    _instance = None
    _worker = None
    _thread = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalAnalysisManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance
    
    def _init_manager(self):
        """初始化管理器"""
        self._worker = VideoAnalysisWorker()
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.start()
    
    def init_analyzer(self, emotion_model_path, face_model_path, emonet_path):
        """初始化分析器"""
        self._worker.init_analyzer(emotion_model_path, face_model_path, emonet_path)
    
    def get_worker(self):
        """获取工作线程对象"""
        return self._worker
    
    def cleanup(self):
        """清理资源"""
        if self._thread and self._thread.isRunning():
            self._worker.stop_analysis()
            self._thread.quit()
            self._thread.wait(3000)  # 等待3秒
            if self._thread.isRunning():
                self._thread.terminate()