import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams
from scipy import signal
import os
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d
import matplotlib.font_manager as fm
from scipy.signal import butter, filtfilt

from utils.i18n import get_language_manager

FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_prop = fm.FontProperties(fname=FONT_PATH)
plt.rcParams['font.sans-serif'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False


class EmotionLineChat:
    def __init__(self, calib_csv_file, pro_csv_file, person_id, product_name, frame_interval, video_duration):
        np.random.seed(42)
        self.language_manager = get_language_manager()
        self.calib_csv_file = calib_csv_file
        self.pro_csv_file = pro_csv_file
        self.person_id = person_id 
        self.product_name = product_name  
        self.video_duration = video_duration
        self.frame_interval = frame_interval

    def calib_df(self):
        calib_df = pd.read_csv(self.calib_csv_file)

        # 情绪上限
        UPPER_THRESHOLDS = {
            'happy': 0.1,
            'sad': 0.2, 
            'surprised': 0.1,
            'negative': 0.2
        }

        emotion_cols = ["happy", "sad", "surprised"]
        calib_mean = {}
        for emo in emotion_cols:
            if emo in calib_df.columns:
                emo_data = calib_df[emo].dropna()
                if len(emo_data) > 0:
                    calib_mean[emo] = np.mean(emo_data)
                else:
                    calib_mean[emo] = 0
            else:
                calib_mean[emo] = 0
        
        negative_cols = ["fear", "disgusted", "angry", "contempt"]
        if all(col in calib_df.columns for col in negative_cols):
            negative_sums = []
            for _, row in calib_df.iterrows():
                if all(pd.notna(row[emo]) for emo in negative_cols):
                    negative_sum = sum(row[emo] for emo in negative_cols)
                    negative_sums.append(negative_sum)
            
            if negative_sums:
                calib_mean['negative'] = np.mean(negative_sums)
            else:
                calib_mean['negative'] = 0
        else:
            calib_mean['negative'] = 0
        
        adjustment_factors = {}
        needs_adjustment = False
        
        for emo, median_val in calib_mean.items():
            threshold = UPPER_THRESHOLDS.get(emo, 0)
            
            if median_val > threshold:
                adjustment_factor = median_val / threshold
                adjustment_factors[emo] = adjustment_factor
                needs_adjustment = True
            else:
                adjustment_factors[emo] = 1.0
        
        return calib_mean, adjustment_factors, needs_adjustment

    def clean_and_clip(self, lst, emotion_type='happy'):
        THRESHOLD_MAP = [
            (0.5, 0.6, 0.85), 
            (0.6, 0.7, 0.80),
            (0.7, 0.8, 0.75),
            (0.8, float('inf'), 0.70)
        ]
        lst = [0 if np.isnan(x) else x for x in lst]
        
        result = []
        for x in lst:
            processed_value = x
            for min_val, max_val, weight in THRESHOLD_MAP:
                if min_val <= x < max_val:
                    processed_value = x * weight
                    break
            if emotion_type == 'happy' and processed_value < 0.05:
                original_value = processed_value
                processed_value = processed_value * 4.0
                processed_value = min(processed_value, 0.3)
            result.append(processed_value)
        
        return result

    def butter_lowpass_filtfilt(self, data, cutoff=1.5, fs=15, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return filtfilt(b, a, data, padlen=3)

    def smooth_list(self, plot_list):
        indices = [index for index, value in enumerate(plot_list) if value is None]
        plot_data_without_none = np.array(plot_list)[np.array(plot_list) != None].tolist()
        
        if len(plot_data_without_none) > 5:
            smooth_plot_list = self.butter_lowpass_filtfilt(plot_data_without_none).tolist()
            for i in indices:
                smooth_plot_list.insert(i, None)
            return smooth_plot_list
        else:
            return plot_list

    def create_output_filename(self, suffix='emolinechat', extension='png'):
        return f"{self.product_name}_{self.person_id}_{suffix}.{extension}"

    def create_emotion_curve(self):
        calib_mean, adjustment_factors, needs_adjustment = self.calib_df()
        df = pd.read_csv(self.pro_csv_file)
        required_cols = ["happy", "sad", "surprised", "fear", "disgusted", "angry", "contempt"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Warning: missing columns in {self.pro_csv_file}: {missing_cols}")
        
        positive, soak, surprise, negative, angry, disgusted, fearful, contempt = [], [], [], [], [], [], [], []
        
        happy_factor = adjustment_factors.get('happy', 1.0)
        sad_factor = adjustment_factors.get('sad', 1.0)
        surprised_factor = adjustment_factors.get('surprised', 1.0)
        negative_factor = adjustment_factors.get('negative', 1.0)

        for _, row in df.iterrows():
            emo_happy = row["happy"] if pd.notna(row["happy"]) else None
            emo_sad = row["sad"] if pd.notna(row["sad"]) else None
            emo_surprised = row["surprised"] if pd.notna(row["surprised"]) else None
            emo_angry = row["angry"] if pd.notna(row["angry"]) else None
            emo_disgusted = row["disgusted"] if pd.notna(row["disgusted"]) else None
            emo_fear = row["fear"] if pd.notna(row["fear"]) else None
            emo_contempt = row["contempt"] if pd.notna(row["contempt"]) else None
            emo_negative = None
            if all(x is not None for x in [emo_angry, emo_disgusted, emo_fear, emo_contempt]):
                emo_negative = emo_angry + emo_disgusted + emo_fear + emo_contempt

            def apply_processing(value, factor):
                return value / factor

            positive.append(apply_processing(emo_happy, happy_factor))
            soak.append(apply_processing(emo_sad, sad_factor))
            surprise.append(apply_processing(emo_surprised, surprised_factor))
            negative.append(apply_processing(emo_negative, negative_factor))


        # 绘图
        csv_dir = os.path.dirname(self.pro_csv_file)
        csv_basename = os.path.splitext(os.path.basename(self.pro_csv_file))[0]
        
        if needs_adjustment:
            output_filename = f"{csv_basename}_adjusted_curve.png"
        else:
            output_filename = f"{csv_basename}_normal_curve.png"
            
        output_path = os.path.join(csv_dir, output_filename)
        

        positive = self.clean_and_clip(positive, emotion_type='happy')
        soak = self.clean_and_clip(soak, emotion_type='sad')
        surprise = self.clean_and_clip(surprise, emotion_type='surprised')
        negative = self.clean_and_clip(negative, emotion_type='negative')
        plot_data = [self.smooth_list(positive), self.smooth_list(soak), self.smooth_list(surprise), self.smooth_list(negative)]

        plt.figure(figsize=(16, 10), dpi=360)
        plt.xlabel(self.language_manager.tr("chart_time_seconds"), fontsize=20, labelpad=14)
        plt.ylabel(self.language_manager.tr("chart_emotion_intensity"), fontsize=20, labelpad=14)

        colors = ["#FF6B9D", "#FFD166", "#118AB2", "#06D6A0"]
        legends = self.language_manager.get_curve_legend_labels()

        if 'frame_index' in df.columns:
            frame_indices = df['frame_index'].values
        else:
            frame_indices = np.arange(len(df))
        
        time_in_seconds = frame_indices / 15

        # 有效数据点用于自动确定y轴范围
        all_valid_values = []
        
        for idx, curve in enumerate(plot_data):
            valid_indices = [i for i, x in enumerate(curve) if x is not None and x > 0]
            if valid_indices:
                valid_times = [time_in_seconds[i] for i in valid_indices]
                valid_values = [curve[i] for i in valid_indices]
                all_valid_values.extend(valid_values)  
                plt.plot(valid_times, valid_values, color=colors[idx], label=legends[idx], 
                        linewidth=4, antialiased=True, alpha=0.9, linestyle='-')

        plt.xlim(0, self.video_duration)
        x_ticks = list(range(0, int(self.video_duration) + 1))
        plt.xticks(x_ticks, fontsize=16)

        # 动态设置y轴范围
        if all_valid_values:
            y_min = min(all_valid_values)
            y_max = max(all_valid_values)
            
            if y_max < 0.4:
                plt.ylim(0.00, 0.40)
                y_ticks = [0.00, 0.05, 0.10, 0.20, 0.30, 0.40]
                y_tick_labels = ["0.00","0.05", "0.10", "0.20","0.30", "0.40"]
                plt.yticks(y_ticks, y_tick_labels, fontsize=16)                
            else:
                y_axis_min = max(0, y_min)
                y_axis_max = 1.0
                
                if y_axis_max - y_axis_min < 0.1:
                    center = (y_axis_max + y_axis_min) / 2
                    y_axis_min = max(0, center - 0.05)
                    y_axis_max = center + 0.05
                
                plt.ylim(y_axis_min, y_axis_max)
                num_ticks = 6
                y_ticks = np.linspace(y_axis_min, y_axis_max, num_ticks)
                y_tick_labels = [f"{tick:.1f}" for tick in y_ticks]
                plt.yticks(y_ticks, y_tick_labels, fontsize=16)                
        else:
            plt.ylim(0, 1.0) # 数据无效使用默认数值
            y_ticks = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            y_tick_labels = ["0.0", "0.2", "0.4", "0.6", "0.8", "1.0"]
            plt.yticks(y_ticks, y_tick_labels, fontsize=16)

        y_axis_bottom = plt.ylim()[0]
        plt.axhline(y=y_axis_bottom, color="#64748b", linewidth=1.6, alpha=0.65)
        plt.legend(loc='upper right', fontsize=16, frameon=True)
        plt.grid(alpha=0.18, linewidth=0.8)
        
        plt.savefig(output_path, dpi=360, bbox_inches='tight', pad_inches=0.25)
        plt.close()
        
        return output_path

    

