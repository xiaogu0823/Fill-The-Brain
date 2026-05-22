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

class CalibVideoAnalysisWorker(QObject):
    """视频分析工作线程 - 处理情感分析算法"""
    
    # 分析进度和结果信号
    analysis_started = pyqtSignal(str, str)      # 视频路径, 产品名称
    analysis_progress = pyqtSignal(int, int)     # 当前帧, 总帧数  
    analysis_finished = pyqtSignal(str, str, str)  # 视频路径, csv路径, 产品名称
    analysis_finished_calib = pyqtSignal(str, str) 
    analysis_failed = pyqtSignal(str, str, str)  # 视频路径, 错误信息, 产品名称

    def __init__(self):
        super().__init__()
        self.analyzer = None
        self.csv_writer = None
        self.is_analyzing = False
        self.current_video_path = ""
        self.current_product_name = ""
        self.is_initialized = False
        self.face_model = None
        self.emotion_model = None
        self.emont_model = None
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
            logging.info("Analyzer initialized successfully with the global model manager.")
            
        except Exception as e:
            logging.error(f"Failed to initialize the analyzer: {e}")
            self.is_initialized = False

    @pyqtSlot(object)
    def analyze_frame(self, frame):
        if not self.accepting_frames:
            return

        with self.queue_lock:
            self.frame_queue.append(frame)
            
    @pyqtSlot(str, str)
    def analyze_video(self, video_path, product_name=None):
        """分析视频的槽函数 - 由信号触发"""
        self._run_video_analysis(video_path, product_name=product_name, calibration_mode=False)

    @pyqtSlot(str)
    def analyze_calibration_video(self, video_path):
        """Analyze a saved calibration video after recording finishes."""
        self._run_video_analysis(video_path, product_name=None, calibration_mode=True)

    def _run_video_analysis(self, video_path, product_name=None, calibration_mode=False):
        if not self.is_initialized or not self.analyzer:
            error_msg = "The emotion analyzer was not initialized correctly."
            self.analysis_failed.emit(video_path, error_msg, product_name or "Unknown Product")
            return
            
        if not os.path.exists(video_path):
            error_msg = f"Video file does not exist: {video_path}"
            self.analysis_failed.emit(video_path, error_msg, product_name or "Unknown Product")
            return
        
        self.is_analyzing = True
        self.current_video_path = video_path
        self.current_product_name = product_name or "Unknown Product"
        
        try:
            # 发射分析开始信号
            self.analysis_started.emit(video_path, self.current_product_name)
            logging.info(
                f"Starting {'calibration' if calibration_mode else 'product'} video analysis: "
                f"{video_path}, product: {self.current_product_name}"
            )
            
            # 进度回调函数
            def progress_callback(current, total):
                if self.is_analyzing:
                    self.analysis_progress.emit(current, total)
            
            # 执行视频分析
            results = self.analyzer.analyze_video(video_path, callback=progress_callback)
            
            # 保存结果到CSV
            csv_path = self.csv_writer.save_with_video_path(results, video_path)
            
            # 发射分析完成信号
            if calibration_mode:
                self.analysis_finished_calib.emit(video_path, csv_path)
                logging.info(f"Calibration video analysis completed: {video_path}")
            else:
                self.analysis_finished.emit(video_path, csv_path, self.current_product_name)
                logging.info(f"Video analysis completed for product: {self.current_product_name}")
            
        except Exception as e:
            error_msg = f"Video analysis failed: {str(e)}"
            logging.error(error_msg)
            self.analysis_failed.emit(video_path, error_msg, self.current_product_name)
        
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
            frame_index += 1
            
    @pyqtSlot()
    def stop_analysis(self):
        """停止分析"""
        self.is_analyzing = False
        logging.info("Video analysis stopped.")
        
    def start_realtime_analysis(self):
        self.accepting_frames = False
        if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        with self.queue_lock:
            self.frame_queue.clear()
        self.realtime_results = []
        self.accepting_frames = True

        self.worker_thread = threading.Thread(
            target=self._consume_frames,
            daemon=True
        )
        self.worker_thread.start()

    def stop_realtime_analysis_and_finalize(self, video_path, product_name=None):
        """
        录制结束后调用
        """
        self.accepting_frames = False
        if hasattr(self, 'worker_thread') and self.worker_thread:
            self.worker_thread.join()  # 等所有帧处理完
            self.worker_thread = None
        
        self.current_video_path = video_path
        self.current_product_name = product_name or "Unknown Product"
        
        csv_path = self.csv_writer.save_with_video_path(
            self.realtime_results,
            video_path
        )
        print(f"stop_realtime_analysis_and_finalize received product_name={product_name}")
        
        if product_name is not None:
            self.analysis_finished.emit(video_path, csv_path, product_name)
        else:
            self.analysis_finished_calib.emit(video_path, csv_path)

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
        self._worker = CalibVideoAnalysisWorker()
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
