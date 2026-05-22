import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

import config.settings as config


class TestRecordLogger:
    FIELDNAMES = [
        "Participant ID",
        "Product Name",
        "Test Time",
        "Emotional Response",
        "Composite Index",
    ]

    LEGACY_FIELD_MAP = {
        "Participant ID": ["Participant ID", "人员ID", "person_id"],
        "Product Name": ["Product Name", "测试产品", "产品名称", "display_name", "product_name"],
        "Test Time": ["Test Time", "测试时间", "test_time"],
        "Emotional Response": ["Emotional Response", "情绪反应", "emotion_reaction"],
        "Composite Index": ["Composite Index", "综合指数", "comprehensive_score"],
    }

    def __init__(self, file_path=None):
        self.file_path = Path(file_path) if file_path else config.SCRIPT_DIR / "test_records.csv"

    def ensure_file(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_rows([])
            return

        with open(self.file_path, "r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            current_fieldnames = reader.fieldnames or []
            rows = list(reader)

        normalized_rows = [self._normalize_row(row) for row in rows]
        needs_rewrite = current_fieldnames != self.FIELDNAMES or normalized_rows != rows
        if needs_rewrite:
            self._write_rows(normalized_rows)

    def _normalize_row(self, row):
        normalized = {}
        for target_field, candidates in self.LEGACY_FIELD_MAP.items():
            normalized[target_field] = ""
            for candidate in candidates:
                value = row.get(candidate, "")
                if value not in ("", None):
                    normalized[target_field] = value
                    break
        normalized["Emotional Response"] = self._normalize_emotion_response(normalized["Emotional Response"])
        return normalized

    def _normalize_emotion_response(self, text):
        if not text:
            return text

        normalized = str(text)
        replacements = {
            "无明显感知": "No obvious emotional response was detected",
            "带来轻微的兴奋感": "A mild sense of excitement was detected",
            "带来明显的兴奋感": "A clear sense of excitement was detected",
            "带来强烈的兴奋感": "A strong sense of excitement was detected",
            "带来轻微的愉悦感": "A mild sense of pleasure was detected",
            "带来明显的愉悦感": "A clear sense of pleasure was detected",
            "带来强烈的愉悦感": "A strong sense of pleasure was detected",
            "带来轻微的舒缓感": "A mild calming effect was detected",
            "带来明显的舒缓感": "A clear calming effect was detected",
            "带来强烈的舒缓感": "A strong calming effect was detected",
            "带来轻微的专注感": "A mild focus response was detected",
            "带来明显的专注感": "A clear focus response was detected",
            "带来强烈的专注感": "A strong focus response was detected",
            "带来轻微的浪漫感": "A mild romantic response was detected",
            "带来明显的浪漫感": "A clear romantic response was detected",
            "带来强烈的浪漫感": "A strong romantic response was detected",
            "带来轻微的自信感": "A mild confidence response was detected",
            "带来明显的自信感": "A clear confidence response was detected",
            "带来强烈的自信感": "A strong confidence response was detected",
            "，伴随": ", accompanied by ",
            "轻微的兴奋感": "a mild sense of excitement",
            "明显的兴奋感": "a clear sense of excitement",
            "强烈的兴奋感": "a strong sense of excitement",
            "轻微的愉悦感": "a mild sense of pleasure",
            "明显的愉悦感": "a clear sense of pleasure",
            "强烈的愉悦感": "a strong sense of pleasure",
            "轻微的舒缓感": "a mild calming effect",
            "明显的舒缓感": "a clear calming effect",
            "强烈的舒缓感": "a strong calming effect",
            "轻微的专注感": "a mild focus response",
            "明显的专注感": "a clear focus response",
            "强烈的专注感": "a strong focus response",
            "轻微的浪漫感": "a mild romantic response",
            "明显的浪漫感": "a clear romantic response",
            "强烈的浪漫感": "a strong romantic response",
            "轻微的自信感": "a mild confidence response",
            "明显的自信感": "a clear confidence response",
            "强烈的自信感": "a strong confidence response",
        }
        for source, target in replacements.items():
            normalized = normalized.replace(source, target)
        return normalized

    def _write_rows(self, rows):
        with open(self.file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    def append_record(
        self,
        person_id,
        product_name,
        emotion_reaction,
        comprehensive_score,
        test_time=None,
    ):
        self.ensure_file()
        try:
            formatted_score = f"{float(comprehensive_score):.1f}"
        except (TypeError, ValueError):
            formatted_score = comprehensive_score
        record = {
            "Participant ID": person_id,
            "Product Name": product_name,
            "Test Time": test_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Emotional Response": emotion_reaction,
            "Composite Index": formatted_score,
        }

        with open(self.file_path, "a", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.FIELDNAMES)
            writer.writerow(record)

    def load_records(self):
        self.ensure_file()
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            try:
                df = pd.read_csv(self.file_path, encoding=encoding).fillna("")
                break
            except UnicodeDecodeError:
                continue
        else:
            df = pd.read_csv(self.file_path).fillna("")

        if list(df.columns) != self.FIELDNAMES:
            df = df.rename(
                columns={
                    candidate: target
                    for target, candidates in self.LEGACY_FIELD_MAP.items()
                    for candidate in candidates
                }
            )
            for field in self.FIELDNAMES:
                if field not in df.columns:
                    df[field] = ""
            df = df[self.FIELDNAMES]

        return df

    def filter_records(self, person_id="", product_name="", test_date=""):
        df = self.load_records()
        if df.empty:
            return df

        filtered_df = df.copy()

        if person_id:
            filtered_df = filtered_df[
                filtered_df["Participant ID"].astype(str).str.contains(person_id, case=False, na=False)
            ]

        if product_name:
            filtered_df = filtered_df[
                filtered_df["Product Name"].astype(str).str.contains(product_name, case=False, na=False)
            ]

        if test_date:
            filtered_df = filtered_df[
                filtered_df["Test Time"].astype(str).str.startswith(test_date)
            ]

        return filtered_df.reset_index(drop=True)

    def export_records(self, df):
        export_root = config.SCRIPT_DIR / "exports" / f"records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_root.mkdir(parents=True, exist_ok=True)
        export_path = export_root / "test_records_filtered.csv"
        df.to_csv(export_path, index=False, encoding="utf-8-sig")
        return export_path
