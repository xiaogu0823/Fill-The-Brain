import csv
import logging
import os
from typing import List, Dict, Any
from pathlib import Path

class EmotionCSVWriter:
    """
    情感分析结果CSV写入器 - CSV文件保存路径与视频路径一致
    """
    def __init__(self, output_encoding='utf-8-sig'):
        """
        初始化CSV写入器
        
        参数:
            output_encoding: 输出文件编码格式
        """
        self.output_encoding = output_encoding
        self.logger = logging.getLogger(__name__)
    
    def _get_video_info(self, video_path: str) -> tuple:
        """
        从视频路径中提取目录、文件名等信息
        参数:
            video_path: 视频文件路径
        返回:
            tuple: (视频目录, 视频名称, 纯净文件名)
        """
        try:
            video_file = Path(video_path)
            video_dir = video_file.parent  
            video_name = video_file.stem   
            
            # 清理文件名
            safe_chars = " -_.()[]{}"
            clean_name = "".join(c for c in video_name if c.isalnum() or c in safe_chars).strip()
            
            if not clean_name:
                clean_name = "video_analysis"
                
            return video_dir, video_name, clean_name
            
        except Exception as e:
            self.logger.warning(f"提取视频信息失败: {e}")
            return Path.cwd(), "video_analysis", "video_analysis"
    
    def save_with_video_path(self, results: List[Dict], video_path: str, 
                           output_dir: str = None) -> str:
        """
        将CSV文件保存到与视频相同的目录或指定目录
        
        参数:
            results: 情感分析结果列表
            video_path: 视频文件路径
            output_dir: 指定输出目录（None表示使用视频所在目录）
            
        返回:
            str: 生成的CSV文件路径
        """
        try:
            # 获取视频信息
            video_dir, video_name, clean_name = self._get_video_info(video_path)
            
            # 确定输出目录
            if output_dir is None:
                # 使用视频所在目录
                output_directory = video_dir
            else:
                # 使用指定目录
                output_directory = Path(output_dir)
            
            # 确保输出目录存在
            os.makedirs(output_directory, exist_ok=True)
            
            # 生成CSV文件名：视频名称.csv
            filename = f"{clean_name}.csv"
            output_path = os.path.join(output_directory, filename)
            
            # 如果文件已存在，添加序号避免覆盖
            counter = 1
            original_output_path = output_path
            while os.path.exists(output_path):
                name_part = f"{clean_name}_{counter}"
                filename = f"{name_part}.csv"
                output_path = os.path.join(output_directory, filename)
                counter += 1

            success = self._save_with_csv(results, output_path)
            
            if success:
                if output_path != original_output_path:
                    self.logger.info(f"文件已存在，使用新名称: {output_path}")
                
                self.logger.info(f"情感分析结果已保存到: {output_path}")
                return output_path
            else:
                return ""
                
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")
            return ""
    
    
    def _save_with_csv(self, results: List[Dict], output_path: str) -> bool:
        try:
            with open(output_path, 'w', newline='', encoding=self.output_encoding) as csvfile:
                fieldnames = [
                    'frame_index', 'valence', 'arousal',
                    'neutral', 'happy', 'sad', 'surprised', 
                    'fear', 'disgusted', 'angry', 'contempt'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for frame_result in results:
                    frame_idx = frame_result.get('frame_index', 0)
                    
                    for emotion_data in frame_result['emotions']:
                        emo_data = emotion_data['emotion_result']
                        row_data = {
                            'frame_index': frame_idx,
                            'valence': emotion_data.get('valence', 0),
                            'arousal': emotion_data.get('arousal', 0),
                            'neutral': emo_data.get('neutral', 0),
                            'happy': emo_data.get('happy', 0),
                            'sad': emo_data.get('sad', 0),
                            'surprised': emo_data.get('surprised', 1),
                            'fear': emo_data.get('fear', 0),
                            'disgusted': emo_data.get('disgusted', 0),
                            'angry': emo_data.get('angry', 1),
                            'contempt': emo_data.get('contempt', 0)
                        }
                        writer.writerow(row_data)
            return True
            
        except Exception as e:
            self.logger.error(f"使用csv模块保存失败: {e}")
            return False
    
    def batch_process_videos(self, video_results_dict: Dict[str, List[Dict]], 
                           output_dir: str = None) -> Dict[str, str]:
        """
        批量处理多个视频的情感分析结果，每个CSV与对应视频在同一目录
        
        参数:
            video_results_dict: 字典，键为视频路径，值为情感分析结果列表
            output_dir: 统一输出目录（None表示各CSV与视频同目录）            
        返回:
            Dict[str, str]: 视频路径到CSV文件路径的映射
        """
        processed_files = {}
        
        for video_path, results in video_results_dict.items():
            try:
                file_path = self.save_with_video_path(results, video_path, output_dir)
                
                if file_path:
                    processed_files[video_path] = file_path
                    self.logger.info(f"成功处理视频: {Path(video_path).name} -> {file_path}")
                else:
                    self.logger.error(f"处理视频失败: {video_path}")
                    
            except Exception as e:
                self.logger.error(f"处理视频 '{video_path}' 时发生错误: {e}")
                continue
        
        return processed_files
    
    def create_output_directory(self, directory_path: str) -> bool:
        """
        创建输出目录
        
        参数:
            directory_path: 目录路径
            
        返回:
            bool: 创建是否成功
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            self.logger.info(f"目录创建成功: {directory_path}")
            return True
        except Exception as e:
            self.logger.error(f"目录创建失败: {e}")
            return False


