import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import matplotlib.font_manager as fm
import os
import random

from utils.i18n import get_language_manager

FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_prop = fm.FontProperties(fname=FONT_PATH)
plt.rcParams['font.sans-serif'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

class SimplifiedEmotionAnalysis:

    def __init__(self, user_id, product_name=None):
        self.language_manager = get_language_manager()
        self.user_id = user_id
        self.product_name = product_name
        self.init_emocol = ['happy', 'surprised', 'sad', 'neutral']
        self.indensity_emocol = ['happy', 'surprised', 'angry', 'disgusted', 'fear', 'contempt']

        self.negative_emotions = ['angry', 'disgusted', 'fear', 'contempt']

        self.base_emotions = ['happy', 'neutral', 'surprised', 'sad', 'negative']
        self.six_emitions = ['Excitement', 'Happiness', 'Relaxation', 'Concentration', 'Romance', 'Confidence']
        self.six_emotion_labels = [
            self.language_manager.get_emotion_dimension_label(label)
            for label in self.six_emitions
        ]
        self.pair_emo = {'Excitement': 'Happiness', 'Happiness': 'Excitement', 'Confidence': 'Excitement', 'Relaxation': 'Happiness', 'Romance': 'Confidence', 'Concentration': 'Relaxation'}
        self.high_global_thresholds = {'happy': 0.05,'sad': 0.2, 'surprised': 0.1,'negative': 0.1, 'indensity':0.2, 'neutral':0.8}
        self.low_global_thresholds = {'happy': 0.01,'sad': 0.05, 'surprised': 0.02,'negative': 0.05, 'indensity':0.1, 'neutral':0.6}

        
        self.fluctuation_threshold = 0.05
        self.needs_adjustment = False
        self.max_score = 98
        self.min_score = 25

    def adjustment_method(self,chlib_path):
        calib_df = pd.read_csv(chlib_path)
        calib_mean = {}
        calib_std = {}

        for emo in self.init_emocol:
            if emo in calib_df.columns:
                emo_data = calib_df[emo].dropna()
                if len(emo_data) > 0:
                    calib_mean[emo] = np.mean(emo_data)
                    calib_std[emo] = np.std(emo_data)
                else:
                    calib_mean[emo] = 0
            else:
                calib_mean[emo] = 0

        if all(col in calib_df.columns for col in self.indensity_emocol):
            indensity_sums = []
            for _, row in calib_df.iterrows():
                if all(pd.notna(row[emo]) for emo in self.indensity_emocol):
                    indensity_sum = sum(row[emo] for emo in self.indensity_emocol)
                    indensity_sums.append(indensity_sum)
            calib_mean['indensity'] = np.mean(indensity_sums) if indensity_sums else 0
            calib_std['indensity'] = np.std(indensity_sums) if indensity_sums else 0

        if all(col in calib_df.columns for col in self.negative_emotions):
            negative_sums = []
            for _, row in calib_df.iterrows():
                if all(pd.notna(row[emo]) for emo in self.negative_emotions):
                    negative_sum = sum(row[emo] for emo in self.negative_emotions)
                    negative_sums.append(negative_sum)
            calib_mean['negative'] = np.mean(negative_sums) if negative_sums else 0
            calib_std['negative'] = np.std(negative_sums) if negative_sums else 0

        adjustment_factors = {}
        
        # 计算调整因子
        for emo, mean_val in calib_mean.items():
            high_threshold = self.high_global_thresholds.get(emo, 0.0)
            low_threshold = self.low_global_thresholds.get(emo, 0.0)

            if mean_val > high_threshold:
                adjustment_factor = mean_val / high_threshold
                adjustment_factors[emo] = max(adjustment_factor, 3.0)
                self.needs_adjustment = True
            elif mean_val < low_threshold:
                adjustment_factor = mean_val / low_threshold 
                adjustment_factors[emo] = adjustment_factor
                self.needs_adjustment = True
            else:
                adjustment_factors[emo] = 1.0
        
        return adjustment_factors
   
    def adjustment_data(self, pro_path, adjustment_factors):
        pro_df = pd.read_csv(pro_path)
        
        happy, sad, surprised, negative, neutral, indensity= [], [], [], [], [], []
        happy_factor = adjustment_factors.get('happy', 1.0)
        sad_factor = adjustment_factors.get('sad', 1.0)
        surprised_factor = adjustment_factors.get('surprised', 1.0)
        negative_factor = adjustment_factors.get('negative', 1.0)
        neutral_factor = adjustment_factors.get('neutral', 1.0)
        indensity_factor = adjustment_factors.get('indensity', 1.0)

        for _, row in pro_df.iterrows():
            emo_happy = row["happy"] if pd.notna(row["happy"]) else None
            emo_sad = row["sad"] if pd.notna(row["sad"]) else None
            emo_surprised = row["surprised"] if pd.notna(row["surprised"]) else None
            emo_angry = row["angry"] if pd.notna(row["angry"]) else None
            emo_disgusted = row["disgusted"] if pd.notna(row["disgusted"]) else None
            emo_fear = row["fear"] if pd.notna(row["fear"]) else None
            emo_contempt = row["contempt"] if pd.notna(row["contempt"]) else Nonem
            emo_neutral = row["neutral"] if pd.notna(row["neutral"]) else None

            emo_negative = None
            if all(x is not None for x in [emo_angry, emo_disgusted, emo_fear, emo_contempt]):
                emo_negative = emo_angry + emo_disgusted + emo_fear + emo_contempt

            emo_indensity = None
            if all(x is not None for x in [emo_happy, emo_surprised, emo_negative]):
                emo_indensity = emo_happy + emo_surprised + emo_negative

            def apply_processing(value, factor):
                return value / factor

            happy.append(apply_processing(emo_happy, happy_factor))
            sad.append(apply_processing(emo_sad, sad_factor))
            surprised.append(apply_processing(emo_surprised, surprised_factor))
            negative.append(apply_processing(emo_negative, negative_factor))
            neutral.append(apply_processing(emo_neutral, neutral_factor))
            indensity.append(apply_processing(emo_indensity, indensity_factor))

        return happy, sad, surprised, negative, neutral, indensity

    def _extract_series_features(self, emo_series, window_size)  :
        if len(emo_series) < window_size:
            return None
        mean_data = np.mean(emo_series)
        std_data = np.std(emo_series)

        local_stds = []
        for i in range(len(emo_series) - window_size + 1):
            window = emo_series[i:i+window_size]
            local_stds.append(np.std(window))

        fluctuation_intensity = np.mean(local_stds) if local_stds else 0

        return {
            "mean_data":mean_data,
            "std_data":std_data,
            "fluct_intensity": fluctuation_intensity
        }

    def calc_combined_score(self, chlib_emo_series, pro_emo_series, window_size=5):
        chlib_features = self._extract_series_features(chlib_emo_series, window_size)
        pro_features = self._extract_series_features(pro_emo_series, window_size)
        # 避免除零
        epsilon = 0.01

        # 计算所有相对特征
        return {
            "mean_ratio": pro_features["mean_data"] / (chlib_features["mean_data"] + epsilon),
            "fluct_intensity": pro_features["fluct_intensity"] / (chlib_features["fluct_intensity"] + epsilon),# 波动特征
            "coefficient_variable":(pro_features["std_data"]/(pro_features["mean_data"] + epsilon)) * 100
        }

    def excite_calm_exclusive(self,six_dim_scores):
        """情绪互斥调整"""
        excite_score = six_dim_scores["Excitement"]
        calm_score = six_dim_scores["Relaxation"]
        score_diff = abs(excite_score - calm_score)

        if score_diff <= 20.0:
            if excite_score > calm_score:
                six_dim_scores["Relaxation"] = np.clip(calm_score * 0.2, self.min_score, self.max_score)
            else:
                six_dim_scores["Excitement"] = np.clip(excite_score * 0.2, self.min_score, self.max_score)

        else:
            six_dim_scores["Excitement"] = np.clip(excite_score, self.min_score, self.max_score)
            six_dim_scores["Relaxation"] = np.clip(calm_score, self.min_score, self.max_score)
        return six_dim_scores
     
    def calculate_dynamic_score(self, feat, emotion_type):
        fluct_intensity = feat.get('fluct_intensity', 0)
        coefficient_variable = feat.get('coefficient_variable', 0)
        
        if fluct_intensity <= 1.0:
            fluct_score = fluct_intensity * (60 / 1.0)
        elif 1.0 < fluct_intensity <= 2.0:
            fluct_score = 60 + (fluct_intensity - 1.0) * (40 / 1.0)
        else:
            fluct_score = 100 
        
        # Excitement、Confidence、Happiness类型
        if emotion_type in ["Excitement", "Confidence", "Happiness", "负面"]:
            if coefficient_variable <= 20:
                var_score = 30  
            elif 20 < coefficient_variable <= 50:
                var_score = 30 + (coefficient_variable - 20) 
            elif 50 < coefficient_variable <= 80:
                var_score = 60 + (coefficient_variable - 50)   
            else:
                var_score = 100
        
        # Romance、Concentration类型 - 反向计算
        elif emotion_type in ["Romance", "Concentration"]:
            if coefficient_variable <= 20:
                var_score = 100
            elif 20 < coefficient_variable <= 50:
                var_score = 100 - coefficient_variable  
            elif 50 < coefficient_variable <= 80:
                var_score = 60 - coefficient_variable 
            else:
                var_score = 30
        else:
            var_score = 60
    
        final_score = fluct_score * 0.6 + var_score * 0.4
        
        return np.clip(final_score, self.min_score, self.max_score)

    def calculate_six_dim_scores(self, happy_feat, sad_feat, surprised_feat, negative_feat, neutral_feat, indensity_feat):
        six_dim_scores = {emo: 0.0 for emo in self.six_emitions}

        if happy_feat['mean_ratio'] <= 0.3:
            happy_score = 20
        elif 0.3 < happy_feat['mean_ratio'] <= 1.0:
            happy_score = 20 + (happy_feat['mean_ratio'] - 0.3) * ((60 - 20)/0.7)
        elif 1.0 < happy_feat['mean_ratio'] <= 3.0:
            happy_score = 40 + (happy_feat['mean_ratio'] - 1.0) * ((90 - 60) / 2.0)
        elif 3.0 < happy_feat['mean_ratio'] <= 5.0:
            happy_score = 60 + (happy_feat['mean_ratio'] - 3.0) * ((90 - 60) / 2.0)
        else:
            happy_score = 95

        if sad_feat['mean_ratio'] <= 0.3:
            sad_score =  30
        elif 0.3 < sad_feat['mean_ratio'] <= 1.0:
            sad_score = 30 + (sad_feat['mean_ratio'] - 0.3) * ((60 - 30)/0.7)
        elif 1.0 < sad_feat['mean_ratio'] <= 2.0:
            sad_score = 60 + (sad_feat['mean_ratio'] - 1.0) * ((90 - 60) / 2.0)
        else:
            sad_score = 95
        
        if surprised_feat['mean_ratio'] <= 0.3:
            surprised_score = 30
        elif 0.3 < surprised_feat['mean_ratio'] <= 1.0:
            surprised_score = 30 + (surprised_feat['mean_ratio'] - 0.3) * (30 / 0.7)
        elif 1.0 < surprised_feat['mean_ratio'] <= 3.0:
            surprised_score = 60 + (surprised_feat['mean_ratio'] - 1.0) * ((95 - 60) / 2.0)
        else:
            surprised_score = 95

        if negative_feat['mean_ratio'] >= 3.0:
            negative_score = 30
        elif 3.0 > negative_feat['mean_ratio'] >= 1.0:
            negative_score = 30 + (negative_feat['mean_ratio'] - 1.0) * (30 / 2.0)
        elif 1.0 > negative_feat['mean_ratio'] > 0.3:
            negative_score = 60 + (1.0 - negative_feat['mean_ratio']) * ((95 - 60) / 0.7)
        else:
            negative_score = 95

        if neutral_feat['mean_ratio'] <= 0.8:
            neutral_score_1 = 95
        elif 0.8 <= neutral_feat['mean_ratio'] <= 1.0:
            neutral_score_1 = 95 - (neutral_feat['mean_ratio'] - 0.8) * (95 / 0.2)
        elif 1.0 <= neutral_feat['mean_ratio'] <= 1.2:
            neutral_score_1 = 60 - (1.2 - neutral_feat['mean_ratio'] ) * (60 / 0.2)
        else:
            neutral_score_1 = 30

        if indensity_feat['mean_ratio'] <= 0.3:
            indensity_score =  30
        elif 0.3 < indensity_feat['mean_ratio'] <= 1.0:
            indensity_score = 30 + (indensity_feat['mean_ratio'] - 0.3) * ((60 - 30)/ 0.7)
        elif 1.0 < indensity_feat['mean_ratio'] <= 3.0:
            indensity_score = 60 + (indensity_feat['mean_ratio'] - 1.0) * ((95 - 60) / 2.0)
        else:
            indensity_score = 95

        # 限制小幅度变化
        if happy_feat['mean_ratio'] > 1.0:
            happy_score_2 = 60 + (happy_feat['mean_ratio'] - 1.0) * (90 - 60)
        else:
            happy_score_2 = 40

        # Excitement：
        excite_static = np.clip(indensity_score, 0, self.max_score) 
        excite_dynamic = self.calculate_dynamic_score(indensity_feat, "Excitement")
        six_dim_scores["Excitement"] = excite_static * 0.3 + excite_dynamic * 0.7

        # Happiness：
        happy_static = np.clip(happy_score, 0, self.max_score)
        happy_dynamic = self.calculate_dynamic_score(happy_feat, "Happiness")
        six_dim_scores["Happiness"] = happy_static * 0.8 + happy_dynamic * 0.2

        # Relaxation： 
        calm_static = np.clip((negative_score * 0.7 + happy_score_2 * 0.3), 0, self.max_score)
        calm_dynamic = self.calculate_dynamic_score(indensity_feat, "Excitement")
        six_dim_scores["Relaxation"] = calm_static * 0.4 + (100.0 - calm_dynamic) * 0.6

        # Concentration：
        Concentration_conditions = [sad_feat['mean_ratio'] > 1.5, negative_feat['mean_ratio'] < 1.5, indensity_feat['mean_ratio'] > 1.5]
        
        # 基础分限制
        Concentration_base = sad_score
        condition_bonus = 0
        for condition in Concentration_conditions:
            if condition:
                condition_bonus += 8.0
        
        Concentration_static = np.clip(Concentration_base - condition_bonus, 0, self.max_score) 
        Concentration_dynamic = self.calculate_dynamic_score(sad_feat, "Concentration")
        six_dim_scores["Concentration"] = Concentration_static * 0.7 + Concentration_dynamic * 0.3

        # Confidence：中等强度 
        conf_static = np.clip(surprised_score, 0, self.max_score) 
        conf_dynamic = self.calculate_dynamic_score(surprised_feat, "Confidence")
        six_dim_scores["Confidence"] = conf_static * 0.6 + conf_dynamic * 0.4

        # Romance：中等强度 
        Romance_static = np.clip((happy_score_2 * 0.4 + neutral_score_1 * 0.6) , 0, self.max_score) 
        Romance_dynamic = self.calculate_dynamic_score(neutral_feat, "Romance")  
        six_dim_scores["Romance"] = Romance_static * 0.6 + Romance_dynamic * 0.4

        six_dim_scores = {
            emo: np.clip(score, self.min_score, self.max_score)
            for emo, score in six_dim_scores.items()
        }

        # 情绪指数
        a = six_dim_scores["Happiness"]
        b = six_dim_scores["Excitement"]
        c = six_dim_scores["Relaxation"]
        d = six_dim_scores["Concentration"]
        e = six_dim_scores["Confidence"]
        f = six_dim_scores["Romance"]
        bc = max(b, c)  
        df = max(d, f)  
        combination_score = a * 0.3 + bc * 0.4 + df * 0.2 + e * 0.1
        print(f'基础情绪指数: {combination_score}')

        # 调整1
        ac = max(a,c)
        if ac - combination_score < 5.0:
            combination_score = combination_score
        else:
            combination_score = combination_score + 5.0
        print(f'调整1最高最终: {combination_score}')

        # 调整2
        scores_dict = {
            "Excitement": six_dim_scores["Excitement"],
            "Concentration": six_dim_scores["Concentration"],
            "Confidence": six_dim_scores["Confidence"],
            "Romance": six_dim_scores["Romance"]
        }
        max_emotion = max(scores_dict, key=scores_dict.get)
        max_score = scores_dict[max_emotion]
        print(f'最高分情绪: {max_emotion}, 分数: {max_score}')

        if max_emotion == "Confidence" or max_emotion == "Concentration":
            combination_score = combination_score * 0.8 + max_score * 0.2
            print(f'{max_emotion}最高最终: {combination_score}')

        elif max_emotion == "Excitement":
            if max_score > 70.0:
                # 高度负面调整逻辑
                negative_ratio_in_excitement = negative_feat['mean_ratio'] / indensity_feat['mean_ratio']
                if negative_ratio_in_excitement > 3.0/4.0:  
                    combination_score = combination_score - 8.0
                elif negative_ratio_in_excitement > 2.0/3.0:  
                    combination_score = combination_score - 6.0
                elif negative_ratio_in_excitement > 1.0/2.0:  
                    combination_score = combination_score - 4.0
                print(f'Excitement>70+负面调整后: {combination_score}')
            else:
                combination_score = combination_score
                print(f'Excitement<=70保持: {combination_score}')

        else:
            combination_score = combination_score
            print(f'{max_emotion}最高保持: {combination_score}')

        print(f'最终情绪指数: {combination_score}')
        return six_dim_scores, combination_score
 
    def generate_radar_chart(self, emotion_dict, csv_file_path):
        if len(emotion_dict) == 0:
            return None
        
        csv_path = Path(csv_file_path)
        output_dir = csv_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        values = [float(emotion_dict.get(emo, 0)) for emo in self.six_emitions]
        angles = np.linspace(0, 2 * np.pi, len(self.six_emitions), endpoint=False).tolist()
        angles_closed = angles + angles[:1]
        values_closed = values + values[:1]
        
        fig, ax = plt.subplots(figsize=(11, 9), dpi=360, subplot_kw=dict(projection='polar'))
        ax.plot(angles_closed, values_closed, 'o-', linewidth=4, color='#FF6B6B')
        ax.fill(angles_closed, values_closed, alpha=0.25, color='#FF6B6B')
        
        ax.set_xticks(angles) 
        ax.set_xticklabels(self.six_emotion_labels, fontsize=20)
        
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 20))
        ax.set_yticklabels([f"{x}" for x in np.arange(0, 101, 20)], fontsize=14)

        if self.product_name:
            output_filename = f"product_{self.product_name}_{self.user_id}_radar.png"
        else:
            output_filename = f"product_{self.user_id}_radar.png"
        output_path = output_dir / output_filename
        
        plt.savefig(output_path, dpi=360, bbox_inches='tight', pad_inches=0.25)
        plt.close()
        
        return str(output_path)
    
    def run_full_analysis(self, calibration_csv_path, product_csv_path):
        try:
            adjustment_factors= self.adjustment_method(calibration_csv_path)
            chlib_happy, chlib_sad, chlib_surprised, chlib_negative, chlib_neutral, chlib_indensity = self.adjustment_data(calibration_csv_path, adjustment_factors)
            pro_happy, pro_sad, pro_surprised, pro_negative, pro_neutral, pro_indensity = self.adjustment_data(product_csv_path, adjustment_factors)

            happy_feat= self.calc_combined_score(chlib_happy, pro_happy)
            sad_feat= self.calc_combined_score(chlib_sad, pro_sad)
            surprised_feat= self.calc_combined_score(chlib_surprised, pro_surprised)
            negative_feat= self.calc_combined_score(chlib_negative, pro_negative)
            neutral_feat= self.calc_combined_score(chlib_neutral, pro_neutral)
            indensity_feat= self.calc_combined_score(chlib_indensity, pro_indensity)

            six_dim_scores, comb_score = self.calculate_six_dim_scores(happy_feat, sad_feat, surprised_feat, negative_feat, neutral_feat,indensity_feat)
            six_dim_scores = self.excite_calm_exclusive(six_dim_scores)
            radar_chart_path = self.generate_radar_chart(six_dim_scores, product_csv_path)
            print(comb_score)

            # from description_template import EmotionSpeechSynthesizer
            from virtual.description_template import EmotionSpeechSynthesizer

            speech_synthesizer = EmotionSpeechSynthesizer(product_name=self.product_name)
            speech = speech_synthesizer.generate_product_specific_speech(six_dim_scores)
            print(speech)
            return comb_score, speech, six_dim_scores, radar_chart_path
        except Exception as e:
            print(f"分析错误: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None

def main():
    user_id, product_name = "110", "茉莉花产品"
    
    calibration_csv_path = r'/home/nvidia/workspace/wenxiang/recordings/lijy1205/calibration_lijy1205.csv'
    product_csv_path = r'/home/nvidia/workspace/wenxiang/recordings/lijy1205/product_T-003_lijy1205.csv'

    
    analyzer = SimplifiedEmotionAnalysis(
        user_id=user_id,
        product_name=product_name
    )
    comb_score, speech, six_dim_scores, radar_chart_path= analyzer.run_full_analysis(calibration_csv_path=calibration_csv_path,product_csv_path=product_csv_path)

if __name__ == "__main__":
    main()
