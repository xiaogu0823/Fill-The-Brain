from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QImage, QPixmap
import cv2
import time
from pathlib import Path
import config.settings as config
from pathlib import Path
from utils.logger import get_logger
import os
from pathlib import Path
import numpy as np
from queue import Queue, Full
from threading import Thread, Event

class CameraManager(QObject):
    """统一的摄像头管理类，供校准和测试窗口共用"""
    # 信号定义
    frame_updated = pyqtSignal(object)  # 传递帧数据
    recording_progress = pyqtSignal(int, float)  # 进度百分比, 已录制时间
    recording_finished = pyqtSignal(str, int)  # 文件名, 总帧数
    frame_for_analysis = pyqtSignal(object)  
    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self._initialized = True
        self.logger = get_logger(__name__) 
        self.camera_index = camera_index
        self.cap = None
        self.preview_timer = QTimer()
            
        self._is_initialized = True
        # 摄像头参数
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 15.0
        # UI更新频率（帧每秒）
        self.ui_update_fps = 15
        # 录制参数
        self.is_recording = False
        self.is_previewing = False
        self.video_writer = None
        self.recorded_frames = []
        self.recording_duration = 0
        self.elapsed_time = 0
        self.video_filename = ""
        self.person_id = ""  # 存储人员ID
        self.video_type = ""  # 视频类型：calibration 或 test
        self.product_name = "" # 产品名称，仅用于测试视频
        # 生产者-消费者模式相关
        self.frame_queue = Queue(maxsize=15)  
        self.producer_thread = None
        self.consumer_active = False
        self.producer_stop_event = Event()  # 用于安全停止生产者线程
        
        # 连接定时器
        self.preview_timer.timeout.connect(self._update_preview)
        self.logger.info(f"Camera manager initialized, camera index: {camera_index}")
        self.analysis_worker = None

        self.calibration_img = None  # 校准图片
        self.calibration_pos = (10, 10)  # 图片在预览画面上的左上角坐标 (x, y)
        self.calibration_size = (400, 400) # 图片在预览画面上的显示大小 (width, height)

    def set_person_id(self, person_id):
        """设置人员ID，用于创建对应的文件夹"""
        self.person_id = person_id
    
    def init_camera(self):
        """初始化摄像头"""
        self.logger.info("Starting camera initialization.")
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.logger.error("Failed to open the camera.")
                return False, "Camera initialization failed."
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            touxiang_img_path = "camera/touxiang.png"

            self.calibration_img = cv2.imread(str(touxiang_img_path), cv2.IMREAD_UNCHANGED)
            # self.logger.info("touxiang初始化成功",self.calibration_img)
            if self.calibration_img is None:
                self.logger.error("Warning: calibration image not found.")
            else:
                # 可选：调整图片大小以适应摄像头画面
                self.calibration_img = cv2.resize(self.calibration_img, self.calibration_size)
                self.logger.info(f"Calibration image '{touxiang_img_path}' loaded and resized to {self.calibration_size}.")
            
            self.logger.info("Camera initialized successfully.")
            return True, "Camera initialized successfully."
            
        except Exception as e:
            self.logger.error(f"Camera initialization error: {str(e)}", exc_info=True)
            return False, f"Camera initialization error: {str(e)}"
    
    def start_preview(self):
        """开始摄像头预览"""
        if self.cap and self.cap.isOpened():
            # 启动生产者-消费者模式
            self._start_producer_consumer()
            
            # 定时器用于控制UI更新频率（比如20fps）
            self.preview_timer.start(1000 // self.ui_update_fps)
            self.is_previewing = True
            self.logger.info(f"Camera preview started, UI refresh rate: {self.ui_update_fps} fps")
            return True
        return False
    
    def _start_producer_consumer(self):
        """启动生产者-消费者线程"""
        if self.producer_thread and self.producer_thread.is_alive():
            self.logger.warning("生产者线程已在运行")
            return
            
        # 重置停止事件
        self.producer_stop_event.clear()
        self.consumer_active = True
        
        # 启动生产者线程
        self.producer_thread = Thread(
            target=self._producer_loop, 
            daemon=True,
            name="CameraProducer"
        )
        self.producer_thread.start()
        self.logger.info("摄像头帧生产者线程已启动")
    
    def _producer_loop(self):
        """生产者线程：专门负责从摄像头读取帧"""
        self.logger.info("生产者线程开始运行")
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        while not self.producer_stop_event.is_set() and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    consecutive_failures = 0  # 重置失败计数
                    
                    # 非阻塞方式放入队列，如果队列满了就丢弃最旧的帧
                    try:
                        # 如果队列已满，先取出一帧腾出空间（丢弃旧帧）
                        if self.frame_queue.full():
                            try:
                                self.frame_queue.get_nowait()
                                self.logger.debug("队列已满，丢弃最旧帧")
                            except:
                                pass
                        
                        # 放入新帧（使用copy避免后续修改影响队列中的帧）
                        self.frame_queue.put(frame.copy(), block=False)
                        
                    except Full:
                        # 理论上不会发生，因为我们已经检查了full()
                        self.logger.warning("帧队列仍然已满，丢弃当前帧")
                        pass
                        
                else:
                    consecutive_failures += 1
                    self.logger.warning(f"读取摄像头帧失败 ({consecutive_failures}/{max_consecutive_failures})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error("连续读取帧失败次数过多，停止生产者线程")
                        break
                    
                    time.sleep(0.01)  # 短暂暂停后重试
                    
            except Exception as e:
                self.logger.error(f"生产者线程异常: {str(e)}", exc_info=True)
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    break
                time.sleep(0.01)
        
        self.logger.info("生产者线程结束运行")
    
    def stop_preview(self):
        """停止摄像头预览"""
        self.is_previewing = False
        
        # 停止生产者-消费者模式
        self._stop_producer_consumer()
        
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        
        self.logger.info("摄像头预览已停止")
        
    def _stop_producer_consumer(self):
        """停止生产者-消费者线程"""
        self.consumer_active = False
        self.producer_stop_event.set()  # 通知生产者线程停止
        
        # 清空队列中剩余的帧
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except:
                break
        
        # 等待生产者线程结束
        if self.producer_thread and self.producer_thread.is_alive():
            self.producer_thread.join(timeout=2.0)  # 最多等待2秒
            if self.producer_thread.is_alive():
                self.logger.warning("Producer thread did not stop within the expected time.")
        
        self.producer_thread = None
        self.logger.info("Producer-consumer mode stopped.")
    
    def start_calibration_recording(self, duration=3):
        """开始校准视频录制"""
        if not self.person_id:
            return False, "Please set the participant ID first."
        
        self.video_type = "calibration"
        return self._start_recording(duration)
    
    def start_test_recording(self, product_name, duration=8):
        """开始测试视频录制"""
        if not self.person_id:
            return False, "Please set the participant ID first."
        
        self.video_type = "test"
        self.product_name = product_name
        return self._start_recording(duration)
    
    def _start_recording(self, duration=8):
        """内部方法：开始录制视频"""
        try:
            # 确保生产者-消费者模式正在运行
            if not self.producer_thread or not self.producer_thread.is_alive():
                self._start_producer_consumer()
            
            # 创建以人员ID命名的输出目录
            output_dir = config.SCRIPT_DIR / "recordings" / self.person_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 根据视频类型生成文件名
            if self.video_type == "calibration":
                self.video_filename = str(output_dir / f"calibration_{self.person_id}.avi")
            else:  # test
                self.video_filename = str(output_dir / f"product_{self.product_name}_{self.person_id}.avi")
            

             # 获取摄像头实际FPS
            actual_fps = self.fps
            print(f"Camera FPS: {actual_fps}")

            if actual_fps <= 0:
                actual_fps = 30.0
            self.fps = actual_fps

            self.recording_duration = duration
            self.elapsed_time = 0
            
            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(
                self.video_filename, fourcc, actual_fps,  # 录制帧率
                (self.frame_width, self.frame_height)
            )
            
            if not self.video_writer.isOpened():
                return False, "Unable to create the video file."
            
            self.recorded_frames = []
            self.is_recording = True  

            # 确保预览是开启的
            if not self.is_previewing:
                self.start_preview()          
            return True, f"{self.video_type} recording started successfully."
            
        except Exception as e:
            return False, f"Failed to start recording: {str(e)}"
    
    def stop_recording(self):
        """停止录制"""
        if self.is_recording:
            self.is_recording = False
            
            if self.video_writer and self.video_writer.isOpened():
                self.video_writer.release()
            
            # 获取总帧数
            if hasattr(self, '_recorded_frame_count'):
                total_frames = self._recorded_frame_count
                # 清理计数器
                delattr(self, '_recorded_frame_count')
            else:
                total_frames = 0
            
            # 清理其他录制相关属性
            for attr in ['_recording_start_time', '_last_progress_emit_time']:
                if hasattr(self, attr):
                    delattr(self, attr)
            
            # 发射录制完成信号
            self.recording_finished.emit(self.video_filename, total_frames)
            
            return self.video_filename, total_frames
        return None, 0

    # def _overlay_calibration_image(self, frame):
    #     """
    #     在给定的帧上叠加校准图片。
    #     :param frame: 原始的OpenCV帧 (BGR格式)。
    #     :return: 叠加了图片的新帧。
    #     """
    #     # 检查图片是否存在
    #     if self.calibration_img is None:
    #         return frame

    #     # 获取原始帧和校准图片的尺寸
    #     frame_h, frame_w = frame.shape[:2]
    #     img_h, img_w = self.calibration_img.shape[:2]

    #     # 计算图片在帧上的位置 (x1, y1) 到 (x2, y2)
    #     x1 = (frame_w - img_w) // 2
    #     y1 = (frame_h - img_h) // 2 + 20
    #     x2, y2 = x1 + img_w, y1 + img_h

    #     # 确保图片不会超出帧的边界
    #     if x1 < 0 or y1 < 0 or x2 > frame_w or y2 > frame_h:
    #         self.logger.warning(f"校准图片尺寸过大，超出帧边界：frame({frame_w}x{frame_h}), img({img_w}x{img_h})")
    #         return frame

    #     # 获取帧中与图片重叠的区域
    #     roi = frame[y1:y2, x1:x2]

    #     # 处理带有Alpha通道的图片（如PNG）
    #     if self.calibration_img.shape[-1] == 4:
    #         # 分离RGB和Alpha通道
    #         b, g, r, a = cv2.split(self.calibration_img)
    #         overlay_rgb = cv2.merge((b, g, r))

    #         # 将Alpha通道归一化到0-1范围，作为掩码
    #         # 关键：确保mask的数据类型是float，以便进行乘法运算
    #         mask = a / 255.0

    #         # 关键修复：使用像素级运算进行混合
    #         # 为了进行广播，需要将mask从(100, 100)扩展到(100, 100, 1)
    #         mask = mask[:, :, np.newaxis]

    #         # 执行混合操作
    #         blended = roi * (1 - mask) + overlay_rgb * mask

    #         # 将结果转换回uint8类型（OpenCV图像的标准类型）
    #         blended = blended.astype(np.uint8)

    #         # 将混合后的区域放回原帧
    #         frame[y1:y2, x1:x2] = blended
    #     else:
    #         # 如果图片没有Alpha通道，则直接替换ROI
    #         frame[y1:y2, x1:x2] = self.calibration_img

    #     return frame
    def _overlay_calibration_image(self, frame):
        """减少内存拷贝"""
        if self.calibration_img is None:
            return frame
        
        frame_h, frame_w = frame.shape[:2]
        img_h, img_w = self.calibration_img.shape[:2]
        
        x1 = (frame_w - img_w) // 2
        y1 = (frame_h - img_h) // 2 + 20
        x2, y2 = x1 + img_w, y1 + img_h
        
        if x1 < 0 or y1 < 0 or x2 > frame_w or y2 > frame_h:
            return frame
        
        # 获取ROI（视图，非拷贝）
        roi = frame[y1:y2, x1:x2]
        
        if self.calibration_img.shape[-1] == 4:
            # 预计算校准图片的RGB和Alpha
            if not hasattr(self, '_cached_overlay_data'):
                b, g, r, a = cv2.split(self.calibration_img)
                self._cached_overlay_rgb = cv2.merge((b, g, r))
                self._cached_overlay_mask = a / 255.0
                self._cached_overlay_mask = self._cached_overlay_mask[:, :, np.newaxis]
            
            # 原地操作，减少拷贝
            roi[:, :] = (roi * (1 - self._cached_overlay_mask) + 
                        self._cached_overlay_rgb * self._cached_overlay_mask).astype(np.uint8)
        else:
            roi[:, :] = self.calibration_img
        
        return frame

    def _update_preview(self):
        """消费者逻辑：按定时器节奏从队列取帧更新UI"""
        if not self.consumer_active:
            return
        
        # 尝试从队列获取最新的一帧（丢弃中间帧，只显示最新的）
        latest_frame = None
        frames_discarded = 0
        
        # 快速清空队列，只保留最新的帧
        while not self.frame_queue.empty():
            try:
                frame = self.frame_queue.get_nowait()
                latest_frame = frame
                frames_discarded += 1
            except:
                break
        
        if frames_discarded > 0:
            if frames_discarded > 1:  
                self.logger.debug(f"丢弃了 {frames_discarded} 帧，显示最新帧")
        
        if latest_frame is not None:
            # 录制逻辑 - 录制原始帧（不带校准图片）
            if self.is_recording:
                self._record_frame(latest_frame)  
                if hasattr(self, 'analysis_worker') and self.analysis_worker.accepting_frames:
                    self.frame_for_analysis.emit(frame)
            # 预览逻辑 - 预览时显示带校准图片
            if self.is_previewing:
                preview_frame = self._overlay_calibration_image(latest_frame.copy())  
                preview_frame = cv2.flip(preview_frame, 1)
                self.frame_updated.emit(preview_frame)
            else:
                # 不预览时也发射原始帧（保持信号活跃）
                self.frame_updated.emit(latest_frame)
        
    def _record_frame(self, frame):
        """录制单帧画面"""
        if self.video_writer and self.video_writer.isOpened():
            # 1. 写入视频文件
            self.video_writer.write(frame)
            
            # 2. 使用帧计数器替代缓存
            if not hasattr(self, '_recorded_frame_count'):
                self._recorded_frame_count = 0
                self._expected_total_frames = int(self.recording_duration * self.fps)  # 记录帧数代替时间  
                self._recording_start_time = time.time()
                print(f"开始录制，预期帧数: {self._expected_total_frames}, 期望时长: {self.recording_duration}秒")
                
            self._recorded_frame_count += 1
            
            # 调试：每隔100帧记录一次当前帧率
            if self._recorded_frame_count % 100 == 0:
                elapsed_time = time.time() - self._recording_start_time
                current_fps = self._recorded_frame_count / elapsed_time

            # # 3. 使用实际时间计算进度
            # current_time = time.time()
            # elapsed = current_time - self._recording_start_time
            # progress = min(100, int((elapsed / self.recording_duration) * 100))
            # 3. 基于帧数计算进度
            progress = min(100, int((self._recorded_frame_count / self._expected_total_frames) * 100))
            elapsed = self._recorded_frame_count / self.fps # 基于帧数和FPS计算已录制时间

            # 4. 控制进度信号发射频率
            if not hasattr(self, '_last_progress_emit_time'):
                self._last_progress_emit_time = 0
            current_time = time.time()
            # 每100ms发射一次进度信号
            if current_time - self._last_progress_emit_time > 0.1:
                self.recording_progress.emit(progress, elapsed)
                self._last_progress_emit_time = current_time
            
            # # 5. 基于真实时间检查录制是否完成
            # if elapsed >= self.recording_duration:
            #     self.stop_recording()
            # 5. 基于帧数检查录制是否完成
            if self._recorded_frame_count >= self._expected_total_frames:
                self.stop_recording()
        
    def get_frame_qimage(self, frame):
        """将OpenCV帧转换为QImage"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        return QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
    
    def get_frame_qpixmap(self, frame, label_size=None):
        """将OpenCV帧转换为QPixmap（可选缩放）"""
        q_img = self.get_frame_qimage(frame)
        pixmap = QPixmap.fromImage(q_img)
        
        if label_size:
            pixmap = pixmap.scaled(
                label_size.width(), label_size.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        return pixmap
    
    def get_recordings_dir(self):
        """获取当前人员的录制目录路径"""
        if not self.person_id:
            return None
        return config.SCRIPT_DIR / "recordings" / self.person_id
    
    def list_recordings(self):
        """列出当前人员的所有录制文件"""
        recordings_dir = self.get_recordings_dir()
        if not recordings_dir or not recordings_dir.exists():
            return []
        
        video_files = list(recordings_dir.glob("*.avi"))
        return sorted(video_files)
    
    def release(self):
        """释放所有资源"""
        self.stop_preview()
        self.stop_recording()
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        
