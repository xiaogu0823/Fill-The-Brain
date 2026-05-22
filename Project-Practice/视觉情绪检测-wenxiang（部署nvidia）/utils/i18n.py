from __future__ import annotations

import re

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox


LANGUAGE_EN = "en"
LANGUAGE_ZH = "zh"


TRANSLATIONS = {
    "ok": {"en": "OK", "zh": "确定"},
    "yes": {"en": "Yes", "zh": "是"},
    "no": {"en": "No", "zh": "否"},
    "cancel": {"en": "Cancel", "zh": "取消"},
    "close": {"en": "Close", "zh": "关闭"},
    "error_title": {"en": "Error", "zh": "错误"},
    "notice_title": {"en": "Notice", "zh": "提示"},
    "warning_title": {"en": "Warning", "zh": "警告"},
    "file_error_title": {"en": "File Error", "zh": "文件错误"},
    "query_failed_title": {"en": "Query Failed", "zh": "查询失败"},
    "export_failed_title": {"en": "Export Failed", "zh": "导出失败"},
    "export_complete_title": {"en": "Export Complete", "zh": "导出完成"},
    "selection_conflict_title": {"en": "Selection Conflict", "zh": "选择冲突"},
    "input_error_title": {"en": "Input Error", "zh": "输入错误"},
    "duplicate_id_title": {"en": "Duplicate ID", "zh": "重复 ID"},
    "save_error_title": {"en": "Save Error", "zh": "保存失败"},
    "workflow_complete_title": {"en": "Workflow Complete", "zh": "流程完成"},
    "analysis_complete_title": {"en": "Analysis Complete", "zh": "分析完成"},
    "analysis_failed_title": {"en": "Analysis Failed", "zh": "分析失败"},
    "calibration_complete_title": {"en": "Calibration Complete", "zh": "校准完成"},
    "calibration_failed_title": {"en": "Calibration Failed", "zh": "校准失败"},
    "camera_error_title": {"en": "Camera Error", "zh": "摄像头错误"},
    "action_failed_title": {"en": "Action Failed", "zh": "操作失败"},
    "confirm_action_title": {"en": "Confirm Action", "zh": "确认操作"},
    "confirm_product_switch_title": {"en": "Confirm Product Switch", "zh": "确认切换产品"},
    "product_switched_title": {"en": "Product Switched", "zh": "产品已切换"},
    "data_not_found_title": {"en": "Data Not Found", "zh": "未找到数据"},
    "finish_title": {"en": "Finish", "zh": "结束"},
    "open_folder_failed_title": {"en": "Open Folder Failed", "zh": "打开文件夹失败"},
    "file_not_found_title": {"en": "File Not Found", "zh": "文件不存在"},
    "overwrite_existing_result_title": {"en": "Overwrite Existing Result", "zh": "覆盖已有结果"},
    "existing_product_title": {"en": "Existing Product", "zh": "已有产品记录"},
    "records_center_title": {"en": "Test Records Center", "zh": "测试记录中心"},
    "select_next_product_title": {"en": "Select the Next Product", "zh": "选择下一个产品"},
    "login_window_title": {"en": "Participant Registration", "zh": "人员信息登记"},
    "login_main_title": {"en": "Participant Information Entry", "zh": "人员信息录入"},
    "login_id_label": {"en": "Participant ID:", "zh": "人员 ID："},
    "login_id_placeholder": {"en": "Enter participant ID", "zh": "请输入人员 ID"},
    "login_name_label": {"en": "Product Name:", "zh": "产品名称："},
    "login_name_placeholder": {"en": "Enter product name", "zh": "请输入产品名称"},
    "login_optional_products": {"en": "Optional Products:", "zh": "可选产品："},
    "login_button": {"en": "Login", "zh": "进入系统"},
    "enter_or_choose_product_name": {
        "en": "Please enter or choose a product name.",
        "zh": "请输入产品名称，或从列表中选择一个产品。",
    },
    "enter_participant_id": {
        "en": "Please enter a participant ID.",
        "zh": "请输入人员 ID。",
    },
    "login_selection_conflict_text": {
        "en": "Please use only one product input method: either type a product name or choose one from the list.",
        "zh": "请输入一种产品输入方式：要么手动输入产品名称，要么从列表中选择。",
    },
    "duplicate_id_confirm": {
        "en": (
            "Participant ID '{person_id}' already exists.\n\n"
            "If you continue, the historical records will be kept and "
            "the new test results will be appended instead of overwritten.\n\n"
            "Do you want to continue with this ID?"
        ),
        "zh": (
            "人员 ID “{person_id}” 已存在。\n\n"
            "如果继续，系统会保留历史记录，并将新的测试结果追加写入，而不是覆盖旧结果。\n\n"
            "仍要继续使用这个 ID 吗？"
        ),
    },
    "duplicate_id_notice": {
        "en": (
            "Participant ID '{person_id}' already exists.\n\n"
            "If you continue logging in, the system will keep the historical "
            "records and append the new test result to the record table."
        ),
        "zh": (
            "人员 ID “{person_id}” 已存在。\n\n"
            "如果继续登录，系统会保留历史记录，并把新的测试结果追加到记录表中。"
        ),
    },
    "save_record_failed": {
        "en": "Failed to save the record: {error}",
        "zh": "保存记录失败：{error}",
    },
    "cannot_find_file": {
        "en": "Cannot find file: '{file_path}'.",
        "zh": "找不到文件：'{file_path}'。",
    },
    "read_file_failed": {
        "en": "Failed to read the file: {error}",
        "zh": "读取文件失败：{error}",
    },
    "workflow_complete_message": {
        "en": (
            "The full test workflow for person '{person_id}' "
            "and product '{product_name}' has finished."
        ),
        "zh": "人员“{person_id}”针对产品“{product_name}”的完整测试流程已结束。",
    },
    "failed_launch_test_window": {
        "en": "Failed to launch the test window.",
        "zh": "启动测试窗口失败。",
    },
    "test_window_title": {
        "en": "Calibration and Test - Participant ID: {person_id} | Product: {product}",
        "zh": "校准与测试 - 人员 ID：{person_id} | 产品：{product}",
    },
    "camera_preview_not_running": {
        "en": "Camera preview is not running.",
        "zh": "摄像头预览未启动。",
    },
    "calibration_preview_title": {"en": "Calibration Preview", "zh": "校准预览"},
    "calibration_preview_capturing": {
        "en": "Calibration Preview | Capturing baseline",
        "zh": "校准预览 | 正在采集基线",
    },
    "calibration_preview_hint": {
        "en": "Keep a natural expression and click Start Calibration.",
        "zh": "请保持自然表情，然后点击“开始校准”。",
    },
    "test_preview_title": {
        "en": "Test Preview | Current Product: {product}",
        "zh": "测试预览 | 当前产品：{product}",
    },
    "remaining_time": {"en": "Remaining Time: {seconds}s", "zh": "剩余时间：{seconds}秒"},
    "start_calibration_button": {"en": "Start Calibration (3s)", "zh": "开始校准（3秒）"},
    "calibrating_button": {"en": "Calibrating...", "zh": "校准中..."},
    "calibration_complete_button": {"en": "Calibration Complete", "zh": "校准完成"},
    "analyzing_calibration_button": {"en": "Analyzing Calibration...", "zh": "校准分析中..."},
    "start_recording_button": {
        "en": "Start Recording (10s)",
        "zh": "开始录制（10秒）",
    },
    "recording_button": {"en": "Recording...", "zh": "录制中..."},
    "recording_complete_button": {"en": "Recording Complete", "zh": "录制完成"},
    "next_product_button": {"en": "Next Product", "zh": "下一产品"},
    "current_product_analysis_button": {
        "en": "Current Product Analysis",
        "zh": "当前产品分析",
    },
    "overall_results_button": {"en": "Overall Results", "zh": "综合结果"},
    "finish_test_button": {"en": "Finish Test", "zh": "结束测试"},
    "recordings_button": {"en": "Files", "zh": "文件"},
    "recordings_button_tooltip": {
        "en": "Open the recordings directory",
        "zh": "打开录制目录",
    },
    "test_records_button": {"en": "Logs", "zh": "记录"},
    "test_records_button_tooltip": {
        "en": "Open test_records.csv",
        "zh": "打开 test_records.csv",
    },
    "language_button_tooltip_to_zh": {"en": "Switch to Chinese", "zh": "切换到中文"},
    "language_button_tooltip_to_en": {"en": "Switch to English", "zh": "切换到英文"},
    "status_complete_calibration_first": {
        "en": "Status: Complete calibration first. The window will switch to testing automatically after analysis.",
        "zh": "状态：请先完成校准，分析结束后界面会自动切换到测试阶段。",
    },
    "status_calibration_complete_start_testing": {
        "en": "Status: Calibration complete. Start testing product {product}.",
        "zh": "状态：校准完成，请开始测试产品 {product}。",
    },
    "status_ready_product": {
        "en": "Status: Ready - Product: {product}",
        "zh": "状态：就绪 - 产品：{product}",
    },
    "status_camera_initialized": {
        "en": "Status: Camera initialized successfully.",
        "zh": "状态：摄像头初始化成功。",
    },
    "status_camera_init_failed": {
        "en": "Status: Camera initialization failed.",
        "zh": "状态：摄像头初始化失败。",
    },
    "camera_connection_check": {
        "en": "Unable to open the camera. Please check the connection.",
        "zh": "无法打开摄像头，请检查连接。",
    },
    "status_calibration_recording_finished": {
        "en": "Status: Calibration recording finished. Analyzing the saved calibration video.",
        "zh": "状态：校准录制已完成，正在分析保存的校准视频。",
    },
    "status_recording_complete_start_analysis": {
        "en": "Status: Recording complete. Starting video analysis for {product}.",
        "zh": "状态：录制完成，正在开始分析产品 {product} 的视频。",
    },
    "status_analyzing_recorded_video": {
        "en": "Status: Analyzing the recorded video.",
        "zh": "状态：正在分析录制视频。",
    },
    "status_video_file_missing": {
        "en": "Status: Video file not found. Analysis failed.",
        "zh": "状态：未找到视频文件，分析失败。",
    },
    "status_analyzing_calibration_video": {
        "en": "Status: Analyzing the calibration video...",
        "zh": "状态：正在分析校准视频...",
    },
    "status_analyzing_video_for_product": {
        "en": "Status: Analyzing video for {product}...",
        "zh": "状态：正在分析产品 {product} 的视频...",
    },
    "status_calibration_analysis_progress": {
        "en": "Status: Calibration analysis progress {progress}% ({current_frame}/{total_frames} frames)",
        "zh": "状态：校准分析进度 {progress}%（{current_frame}/{total_frames} 帧）",
    },
    "status_analysis_progress": {
        "en": "Status: Analysis progress {progress}% ({current_frame}/{total_frames} frames)",
        "zh": "状态：分析进度 {progress}%（{current_frame}/{total_frames} 帧）",
    },
    "status_video_analysis_complete": {
        "en": "Status: Video analysis complete. Results saved to: {csv_path}",
        "zh": "状态：视频分析完成，结果已保存到：{csv_path}",
    },
    "analysis_complete_message": {
        "en": "The analysis for product {product} is complete.",
        "zh": "产品 {product} 的分析已完成。",
    },
    "status_analysis_complete_for_product": {
        "en": "Status: Analysis for {product} is complete.",
        "zh": "状态：产品 {product} 的分析已完成。",
    },
    "analysis_complete_with_score_error": {
        "en": "Analysis for product {product} finished, but score calculation failed: {error}",
        "zh": "产品 {product} 的分析已结束，但分数计算失败：{error}",
    },
    "status_analysis_complete_with_score_error": {
        "en": "Status: Analysis finished, but score calculation failed - {error}",
        "zh": "状态：分析已完成，但分数计算失败 - {error}",
    },
    "calibration_complete_message": {
        "en": "Calibration recording and analysis are complete. Switching to the testing stage.",
        "zh": "校准录制和分析已完成，正在切换到测试阶段。",
    },
    "calibration_result_load_failed": {
        "en": "Failed to load the calibration result: {error}",
        "zh": "加载校准结果失败：{error}",
    },
    "status_calibration_analysis_failed": {
        "en": "Status: Calibration analysis failed - {error}",
        "zh": "状态：校准分析失败 - {error}",
    },
    "calibration_analysis_failed": {
        "en": "Calibration analysis failed: {error}",
        "zh": "校准分析失败：{error}",
    },
    "status_analysis_failed": {
        "en": "Status: Analysis failed - {error}",
        "zh": "状态：分析失败 - {error}",
    },
    "analysis_failed_for_product": {
        "en": "Analysis failed for product {product}: {error}",
        "zh": "产品 {product} 的分析失败：{error}",
    },
    "complete_calibration_first_notice": {
        "en": "Complete calibration before starting the test recording.",
        "zh": "请先完成校准，再开始测试录制。",
    },
    "recording_already_completed_notice": {
        "en": "The current test has already been recorded and cannot be recorded again.",
        "zh": "当前测试已经录制完成，不能重复录制。",
    },
    "camera_not_ready_for_recording": {
        "en": "The camera was not initialized correctly, so recording cannot start.",
        "zh": "摄像头未正确初始化，无法开始录制。",
    },
    "camera_not_ready_for_calibration": {
        "en": "The camera was not initialized correctly, so calibration cannot start.",
        "zh": "摄像头未正确初始化，无法开始校准。",
    },
    "status_recording_in_progress": {
        "en": "Status: Recording for {seconds} seconds... Product: {product}",
        "zh": "状态：正在录制 {seconds} 秒... 产品：{product}",
    },
    "status_calibration_in_progress": {
        "en": "Status: Calibration in progress. Please keep a natural expression.",
        "zh": "状态：校准进行中，请保持自然表情。",
    },
    "complete_test_before_analysis": {
        "en": "Complete the test recording before opening the analysis.",
        "zh": "请先完成测试录制，再打开分析结果。",
    },
    "finish_current_recording_first": {
        "en": "Finish the current recording first.",
        "zh": "请先完成当前录制。",
    },
    "confirm_product_switch_message": {
        "en": (
            "Start the test for product '{new_product}'?\n\n"
            "The test data for the current product "
            "'{current_product}' will be saved."
        ),
        "zh": (
            "要开始测试产品“{new_product}”吗？\n\n"
            "当前产品“{current_product}”的测试数据会先被保存。"
        ),
    },
    "product_selection_error": {
        "en": "An error occurred while selecting a product: {error}",
        "zh": "选择产品时发生错误：{error}",
    },
    "overwrite_existing_result_message": {
        "en": "This product already has a test record. Continuing will replace the old result. Do you want to continue?",
        "zh": "该产品已经有测试记录，继续操作会覆盖旧结果。仍要继续吗？",
    },
    "product_switched_message": {
        "en": "Switched to product '{product}'.\nClick 'Start Recording' to begin the test.",
        "zh": "已切换到产品“{product}”。\n点击“开始录制”即可开始测试。",
    },
    "status_viewing_analysis_result": {
        "en": "Status: Viewing the analysis result for {product}.",
        "zh": "状态：正在查看产品 {product} 的分析结果。",
    },
    "product_details_not_found": {
        "en": "No detailed analysis data was found for product '{product}'.",
        "zh": "未找到产品“{product}”的详细分析数据。",
    },
    "failed_to_open_product_details": {
        "en": "Failed to open product details: {error}",
        "zh": "打开产品详情失败：{error}",
    },
    "finish_test_message": {
        "en": "Do you want to finish the test? The test data will be saved.",
        "zh": "要结束本次测试吗？测试数据会先被保存。",
    },
    "overall_analysis_requires_completion": {
        "en": "Overall analysis requires completed test data. Do you want to finish the current product test flow?",
        "zh": "查看综合分析需要先完成当前产品测试。要结束当前产品的测试流程吗？",
    },
    "status_overall_analysis_mode": {
        "en": "Status: Overall analysis mode - showing the product ranking.",
        "zh": "状态：综合分析模式 - 正在显示产品排名。",
    },
    "status_calibration_data_loaded": {
        "en": "Status: Calibration data loaded - {file_name}",
        "zh": "状态：已加载校准数据 - {file_name}",
    },
    "status_calibration_data_missing": {
        "en": "Status: Warning - calibration data file does not exist.",
        "zh": "状态：警告 - 校准数据文件不存在。",
    },
    "status_calibration_data_error": {
        "en": "Status: Error - failed to load calibration data: {error}",
        "zh": "状态：错误 - 加载校准数据失败：{error}",
    },
    "open_folder_failed_message": {
        "en": "Unable to open:\n{path}",
        "zh": "无法打开：\n{path}",
    },
    "open_recordings_directory_failed": {
        "en": "Unable to open the recordings directory:\n{error}",
        "zh": "无法打开录制目录：\n{error}",
    },
    "test_record_file_missing": {
        "en": "Could not find the test record file:\n{file_path}",
        "zh": "找不到测试记录文件：\n{file_path}",
    },
    "open_test_records_failed": {
        "en": "Failed to open test_records.csv:\n{error}",
        "zh": "打开 test_records.csv 失败：\n{error}",
    },
    "product_summary_table": {"en": "Product Summary Table", "zh": "产品汇总表"},
    "score_table_title": {"en": "Product Emotional Score", "zh": "产品情绪评分"},
    "score_table_header_order": {"en": "Order", "zh": "序号"},
    "score_table_header_product": {"en": "Product Name", "zh": "产品名称"},
    "score_table_header_index": {"en": "Emotional Index", "zh": "情绪指数"},
    "score_table_header_summary": {"en": "Emotion Summary", "zh": "情绪摘要"},
    "score_table_tooltip": {
        "en": "Click a product name to open the detailed analysis.",
        "zh": "点击产品名称可查看详细分析。",
    },
    "score_table_no_data": {"en": "No product data", "zh": "暂无产品数据"},
    "score_table_count": {"en": "{count} products", "zh": "{count} 个产品"},
    "filters_group": {"en": "Filters", "zh": "筛选条件"},
    "participant_id": {"en": "Participant ID", "zh": "人员 ID"},
    "product_name": {"en": "Product Name", "zh": "产品名称"},
    "filter_by_test_date": {"en": "Filter by Test Date", "zh": "按测试日期筛选"},
    "search_button": {"en": "Search", "zh": "查询"},
    "reset_button": {"en": "Reset", "zh": "重置"},
    "export_results_button": {"en": "Export Results", "zh": "导出结果"},
    "record_file_info": {"en": "Record file: {file_path}", "zh": "记录文件：{file_path}"},
    "current_result_count": {"en": "Current result count: {count}", "zh": "当前结果数：{count}"},
    "query_failed_message": {
        "en": "Failed to query the test records:\n{error}",
        "zh": "查询测试记录失败：\n{error}",
    },
    "no_records_to_export": {
        "en": "There are no records to export.",
        "zh": "当前没有可导出的记录。",
    },
    "export_complete_message": {
        "en": "The results were exported to:\n{path}",
        "zh": "结果已导出到：\n{path}",
    },
    "export_failed_message": {
        "en": "Failed to export the filtered records:\n{error}",
        "zh": "导出筛选记录失败：\n{error}",
    },
    "select_next_product_label": {
        "en": "Choose the next product to test:",
        "zh": "请选择下一个要测试的产品：",
    },
    "selection_mode_group": {"en": "Selection Mode", "zh": "选择方式"},
    "enter_new_product_label": {
        "en": "Enter a new product name:",
        "zh": "输入新的产品名称：",
    },
    "type_product_name_placeholder": {
        "en": "Type the product name...",
        "zh": "请输入产品名称...",
    },
    "choose_existing_products_label": {
        "en": "Choose from the existing products:",
        "zh": "从已有产品中选择：",
    },
    "no_products_available": {"en": "No products available", "zh": "暂无可选产品"},
    "confirm_button": {"en": "Confirm", "zh": "确认"},
    "cancel_button": {"en": "Cancel", "zh": "取消"},
    "valid_product_name_required": {
        "en": "Please enter a valid product name.",
        "zh": "请输入有效的产品名称。",
    },
    "existing_product_message": {
        "en": (
            "Product '{product_name}' already has a test record.\n\n"
            "Continue only if you want to replace the previous result."
        ),
        "zh": (
            "产品“{product_name}”已经有测试记录。\n\n"
            "只有在你希望替换之前结果时才继续。"
        ),
    },
    "chart_time_seconds": {"en": "Time (s)", "zh": "时间（秒）"},
    "chart_emotion_intensity": {"en": "Emotion Intensity", "zh": "情绪强度"},
    "chart_emotion_distribution": {"en": "Emotion Distribution", "zh": "情绪分布"},
    "chart_score_label": {"en": "Score", "zh": "分数"},
    "chart_level_label": {"en": "Level", "zh": "等级"},
    "chart_emotion_label": {"en": "Emotion", "zh": "情绪"},
    "chart_emotional_index": {"en": "{product} Emotional Index: {score}", "zh": "{product} 情绪指数：{score}"},
    "chart_no_dominant_summary": {
        "en": "No dominant emotion summary available.",
        "zh": "暂无主要情绪摘要。",
    },
    "level_minimal": {"en": "Minimal", "zh": "轻微"},
    "level_mild": {"en": "Mild", "zh": "较弱"},
    "level_moderate": {"en": "Moderate", "zh": "中等"},
    "level_strong": {"en": "Strong", "zh": "强烈"},
}


RECORD_HEADER_TRANSLATIONS = {
    "Participant ID": "人员 ID",
    "Product Name": "产品名称",
    "Test Time": "测试时间",
    "Emotional Response": "情绪反应",
    "Composite Index": "综合指数",
}


EMOTION_DIMENSION_TRANSLATIONS = {
    "Excitement": {"en": "Excitement", "zh": "兴奋"},
    "Happiness": {"en": "Happiness", "zh": "愉悦"},
    "Relaxation": {"en": "Relaxation", "zh": "舒缓"},
    "Concentration": {"en": "Concentration", "zh": "专注"},
    "Romance": {"en": "Romance", "zh": "浪漫"},
    "Confidence": {"en": "Confidence", "zh": "自信"},
}


CURVE_LEGEND_TRANSLATIONS = {
    LANGUAGE_EN: ["Happy", "Immerse", "Surprise", "Negative"],
    LANGUAGE_ZH: ["愉悦", "沉浸", "惊喜", "负向"],
}


EMOTION_TEXT_REPLACEMENTS = [
    ("No significant emotional fluctuation", "无明显情绪波动"),
    ("No dominant emotion summary available", "暂无主要情绪摘要"),
    ("A strong and energizing sense of excitement was detected", "检测到强烈且充满活力的兴奋感"),
    ("A strong sense of excitement was detected", "检测到强烈兴奋感"),
    ("A clear sense of excitement was detected", "检测到明显兴奋感"),
    ("A mild sense of excitement was detected", "检测到轻微兴奋感"),
    ("No obvious excitement was detected", "未检测到明显兴奋感"),
    ("A strong sense of pleasure was detected", "检测到强烈愉悦感"),
    ("A clear sense of pleasure was detected", "检测到明显愉悦感"),
    ("A mild sense of pleasure was detected", "检测到轻微愉悦感"),
    ("No obvious pleasure was detected", "未检测到明显愉悦感"),
    ("A strong calming effect was detected", "检测到强烈舒缓感"),
    ("A clear calming effect was detected", "检测到明显舒缓感"),
    ("A mild calming effect was detected", "检测到轻微舒缓感"),
    ("No obvious calming effect was detected", "未检测到明显舒缓感"),
    ("A strong focus response was detected", "检测到强烈专注感"),
    ("A clear focus response was detected", "检测到明显专注感"),
    ("A mild focus response was detected", "检测到轻微专注感"),
    ("No obvious focus response was detected", "未检测到明显专注感"),
    ("A strong romantic response was detected", "检测到强烈浪漫感"),
    ("A clear romantic response was detected", "检测到明显浪漫感"),
    ("A mild romantic response was detected", "检测到轻微浪漫感"),
    ("No obvious romantic response was detected", "未检测到明显浪漫感"),
    ("A strong confidence response was detected", "检测到强烈自信感"),
    ("A clear confidence response was detected", "检测到明显自信感"),
    ("A mild confidence response was detected", "检测到轻微自信感"),
    ("No obvious confidence response was detected", "未检测到明显自信感"),
    (" brings a strong and energizing sense of excitement", " 带来强烈且充满活力的兴奋感"),
    (" brings a moderate level of excitement", " 带来中等程度的兴奋感"),
    (" brings a mild sense of excitement", " 带来轻微兴奋感"),
    (" brings a strong and deeply enjoyable feeling", " 带来强烈且愉悦的感受"),
    (" brings a moderate level of Happiness", " 带来中等程度的愉悦感"),
    (" brings a mild sense of Happiness", " 带来轻微愉悦感"),
    (" brings a strong and deeply Relaxation effect", " 带来强烈舒缓效果"),
    (" brings a moderate level of relaxation", " 带来中等程度的舒缓感"),
    (" brings a mild sense of relaxation", " 带来轻微舒缓感"),
    (" brings a strong and highly focused state", " 带来强烈且高度专注的状态"),
    (" brings a moderate level of focus", " 带来中等程度的专注感"),
    (" brings a mild increase in focus", " 带来轻微专注提升"),
    (" brings a strong and immersive romantic mood", " 带来强烈且沉浸式的浪漫氛围"),
    (" brings a moderate romantic atmosphere", " 带来中等程度的浪漫氛围"),
    (" brings a mild sense of Romance", " 带来轻微浪漫感"),
    (" brings a strong and empowering sense of Confidence", " 带来强烈且充满力量的自信感"),
    (" brings a moderate level of Confidence", " 带来中等程度的自信感"),
    (" brings a mild sense of Confidence", " 带来轻微自信感"),
    ("a strong and energizing sense of excitement", "强烈且充满活力的兴奋感"),
    ("a strong sense of excitement", "强烈兴奋感"),
    ("a moderate level of excitement", "中等程度的兴奋感"),
    ("a clear sense of excitement", "明显兴奋感"),
    ("a mild sense of excitement", "轻微兴奋感"),
    ("a strong sense of pleasure", "强烈愉悦感"),
    ("a moderate level of Happiness", "中等程度的愉悦感"),
    ("a clear sense of pleasure", "明显愉悦感"),
    ("a mild sense of pleasure", "轻微愉悦感"),
    ("a strong calming effect", "强烈舒缓感"),
    ("a moderate level of relaxation", "中等程度的舒缓感"),
    ("a clear calming effect", "明显舒缓感"),
    ("a mild calming effect", "轻微舒缓感"),
    ("a strong sense of focus", "强烈专注感"),
    ("a strong and highly focused state", "强烈且高度专注的状态"),
    ("a moderate level of focus", "中等程度的专注感"),
    ("a clear focus response", "明显专注感"),
    ("a mild increase in focus", "轻微专注提升"),
    ("a mild focus response", "轻微专注感"),
    ("a strong romantic mood", "强烈浪漫感"),
    ("a moderate romantic atmosphere", "中等程度的浪漫氛围"),
    ("a clear romantic response", "明显浪漫感"),
    ("a mild sense of Romance", "轻微浪漫感"),
    ("a mild romantic response", "轻微浪漫感"),
    ("a strong sense of Confidence", "强烈自信感"),
    ("a moderate level of Confidence", "中等程度的自信感"),
    ("a clear confidence response", "明显自信感"),
    ("a mild sense of Confidence", "轻微自信感"),
    ("a mild confidence response", "轻微自信感"),
    ("No obvious emotional response was detected", "未检测到明显情绪反应"),
    ("Pending", "待分析"),
]


NO_PRODUCT_EMOTION_PATTERN = re.compile(
    r"^No obvious emotional response was detected for (?P<product>.+)\.$"
)


class LanguageManager(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._language = LANGUAGE_EN

    def get_language(self) -> str:
        return self._language

    def is_chinese(self) -> bool:
        return self._language == LANGUAGE_ZH

    def set_language(self, language: str):
        normalized = LANGUAGE_ZH if language == LANGUAGE_ZH else LANGUAGE_EN
        if normalized == self._language:
            return
        self._language = normalized
        self.language_changed.emit(self._language)

    def toggle_language(self):
        self.set_language(LANGUAGE_ZH if self._language == LANGUAGE_EN else LANGUAGE_EN)

    def tr(self, key: str, **kwargs) -> str:
        entry = TRANSLATIONS.get(key)
        if not entry:
            text = key
        else:
            text = entry.get(self._language) or entry.get(LANGUAGE_EN) or key
        return text.format(**kwargs)

    def get_language_button_text(self) -> str:
        return "中文" if self._language == LANGUAGE_EN else "EN"

    def get_language_button_tooltip(self) -> str:
        if self._language == LANGUAGE_EN:
            return self.tr("language_button_tooltip_to_zh")
        return self.tr("language_button_tooltip_to_en")

    def get_emotion_dimension_label(self, label: str) -> str:
        entry = EMOTION_DIMENSION_TRANSLATIONS.get(label)
        if not entry:
            return label
        return entry.get(self._language, label)

    def get_curve_legend_labels(self):
        return CURVE_LEGEND_TRANSLATIONS.get(self._language, CURVE_LEGEND_TRANSLATIONS[LANGUAGE_EN])

    def get_record_headers(self, headers):
        if not self.is_chinese():
            return list(headers)
        return [RECORD_HEADER_TRANSLATIONS.get(header, header) for header in headers]

    def translate_emotion_text(self, text):
        if text is None:
            return text
        if not self.is_chinese():
            return text

        result = str(text).strip()
        if not result:
            return result

        match = NO_PRODUCT_EMOTION_PATTERN.match(result)
        if match:
            product = match.group("product")
            return f"未检测到产品 {product} 的明显情绪反应。"

        result = result.replace("., accompanied by", ", accompanied by")
        for source, target in EMOTION_TEXT_REPLACEMENTS:
            result = result.replace(source, target)

        result = result.replace(", accompanied by ", "，伴有")
        result = result.replace(" accompanied by ", "，伴有")
        result = result.replace(". ", "。")
        if result.endswith("."):
            result = result[:-1] + "。"
        return result

    def localize_message_box_buttons(self, msg_box: QMessageBox):
        button_key_map = {
            QMessageBox.Ok: "ok",
            QMessageBox.Yes: "yes",
            QMessageBox.No: "no",
            QMessageBox.Cancel: "cancel",
            QMessageBox.Close: "close",
        }
        for standard_button, key in button_key_map.items():
            button = msg_box.button(standard_button)
            if button:
                button.setText(self.tr(key))


_LANGUAGE_MANAGER = LanguageManager()


def get_language_manager() -> LanguageManager:
    return _LANGUAGE_MANAGER
