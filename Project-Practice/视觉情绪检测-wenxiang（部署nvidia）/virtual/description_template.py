# -*- coding: utf-8 -*-

from utils.i18n import get_language_manager


class EmotionSpeechSynthesizer:
    def __init__(self, product_name="product"):
        self.product_name = product_name
        self.language_manager = get_language_manager()

    def get_intensity_level(self, score):
        if score <= 40:
            return "D"
        if score <= 60:
            return "C"
        if score <= 80:
            return "B"
        return "A"

    def get_primary_and_secondary(self, emotion_stats):
        sorted_emotions = sorted(emotion_stats.items(), key=lambda x: x[1], reverse=True)
        if not sorted_emotions:
            return None, None, None, None

        primary_emotion, primary_score = sorted_emotions[0]
        if len(sorted_emotions) < 2:
            return primary_emotion, int(primary_score), None, None

        secondary_emotion, secondary_score = sorted_emotions[1]
        if abs(primary_score - secondary_score) > 20:
            return primary_emotion, int(primary_score), None, None

        return primary_emotion, int(primary_score), secondary_emotion, int(secondary_score)

    def generate_product_specific_speech(self, emotion_stats):
        primary_emotion, primary_score, secondary_emotion, secondary_score = self.get_primary_and_secondary(emotion_stats)
        if primary_emotion is None:
            return f"No obvious emotional response was detected for {self.product_name}."

        # 主情绪：完整句
        primary_templates = {
            "Excitement": {
                "D": f"No obvious emotional response was detected for {self.product_name}.",
                "C": f"{self.product_name} brings a mild sense of excitement.",
                "B": f"{self.product_name} brings a moderate level of excitement.",
                "A": f"{self.product_name} brings a strong and energizing sense of excitement.",
            },
            "Happiness": {
                "D": f"No obvious emotional response was detected for {self.product_name}.",
                "C": f"{self.product_name} brings a mild sense of Happiness.",
                "B": f"{self.product_name} brings a moderate level of Happiness.",
                "A": f"{self.product_name} brings a strong and deeply enjoyable feeling.",
            },
            "Relaxation": {
                "D": f"No obvious emotional response was detected for {self.product_name}.",
                "C": f"{self.product_name} brings a mild sense of relaxation.",
                "B": f"{self.product_name} brings a moderate level of relaxation.",
                "A": f"{self.product_name} brings a strong and deeply Relaxation effect.",
            },
            "Concentration": {
                "D": f"No obvious emotional response was detected for {self.product_name}.",
                "C": f"{self.product_name} brings a mild increase in focus.",
                "B": f"{self.product_name} brings a moderate level of focus.",
                "A": f"{self.product_name} brings a strong and highly focused state.",
            },
            "Romance": {
                "D": f"No obvious emotional response was detected for {self.product_name}.",
                "C": f"{self.product_name} brings a mild sense of Romance.",
                "B": f"{self.product_name} brings a moderate romantic atmosphere.",
                "A": f"{self.product_name} brings a strong and immersive romantic mood.",
            },
            "Confidence": {
                "D": f"No obvious emotional response was detected for {self.product_name}.",
                "C": f"{self.product_name} brings a mild sense of Confidence.",
                "B": f"{self.product_name} brings a moderate level of Confidence.",
                "A": f"{self.product_name} brings a strong and empowering sense of Confidence.",
            }
        }

        # 次情绪：短语，专门给 accompanied by / with 使用
        secondary_templates = {
            "Excitement": {
                "D": "a minimal sense of excitement",
                "C": "a mild sense of excitement",
                "B": "a moderate level of excitement",
                "A": "a strong sense of excitement",
            },
            "Happiness": {
                "D": "a minimal sense of Happiness",
                "C": "a mild sense of Happiness",
                "B": "a moderate level of Happiness",
                "A": "a strong sense of Happiness",
            },
            "Relaxation": {
                "D": "a minimal sense of relaxation",
                "C": "a mild sense of relaxation",
                "B": "a moderate level of relaxation",
                "A": "a strong Relaxation effect",
            },
            "Concentration": {
                "D": "a minimal level of focus",
                "C": "a mild increase in focus",
                "B": "a moderate level of focus",
                "A": "a strong sense of focus",
            },
            "Romance": {
                "D": "a minimal sense of Romance",
                "C": "a mild sense of Romance",
                "B": "a moderate romantic atmosphere",
                "A": "a strong romantic mood",
            },
            "Confidence": {
                "D": "a minimal sense of Confidence",
                "C": "a mild sense of Confidence",
                "B": "a moderate level of Confidence",
                "A": "a strong sense of Confidence",
            }
        }

        if primary_emotion not in primary_templates:
            return f"No obvious emotional response was detected for {self.product_name}."

        primary_level = self.get_intensity_level(primary_score)
        primary_speech = primary_templates[primary_emotion][primary_level]

        if secondary_emotion is None or secondary_emotion not in secondary_templates:
            return primary_speech

        secondary_level = self.get_intensity_level(secondary_score)
        secondary_phrase = secondary_templates[secondary_emotion][secondary_level]

        result = f"{primary_speech}, accompanied by {secondary_phrase}."
        return self.language_manager.translate_emotion_text(result)
