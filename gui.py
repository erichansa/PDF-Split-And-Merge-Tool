"""
GUI 界面实现模块
基于 PySide6 (Qt6) 实现现代、美观、易用的 PDF 拆分、合并与单文件瘦身桌面应用。
"""

import os
import sys
import json
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QFileDialog, QRadioButton,
    QButtonGroup, QListWidget, QListWidgetItem, QMessageBox,
    QGroupBox, QProgressBar, QAbstractItemView, QFrame, QCheckBox
)

from pdf_processor import (
    get_pdf_page_count,
    parse_page_ranges,
    split_pdf_each_page,
    split_pdf_by_ranges,
    merge_pdfs,
    compress_single_pdf
)


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "app_name": "PDF 工具箱 - 拆分·合并·瘦身",
        "window_width": 840,
        "window_height": 720,
        "default_split_folder_suffix": "_拆分结果",
        "default_merged_filename": "合并文档.pdf",
        "default_compress_suffix": "_已瘦身.pdf"
    }


def format_size(bytes_num: int) -> str:
    """人性化格式化文件字节大小"""
    if bytes_num >= 1024 * 1024:
        return f"{bytes_num / (1024 * 1024):.2f} MB"
    elif bytes_num >= 1024:
        return f"{bytes_num / 1024:.1f} KB"
    else:
        return f"{bytes_num} Bytes"


# 现代化 QSS 样式表
MODERN_STYLE = """
QMainWindow {
    background-color: #f7f9fc;
}

QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #edf2f7;
    border: 1px solid #cbd5e0;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 500;
    color: #4a5568;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background: #ffffff;
    border-color: #e2e8f0;
    border-bottom-color: #ffffff;
    color: #2b6cb0;
    font-weight: bold;
}

QGroupBox {
    font-size: 13px;
    font-weight: bold;
    color: #2d3748;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 16px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: transparent;
    color: #3182ce;
}

QLineEdit {
    padding: 8px 12px;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    background: #ffffff;
    font-size: 13px;
    color: #2d3748;
}

QLineEdit:focus {
    border: 1.5px solid #3182ce;
}

QPushButton {
    background-color: #edf2f7;
    color: #2d3748;
    border: 1px solid #cbd5e0;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e2e8f0;
    border-color: #a0aec0;
}

QPushButton:pressed {
    background-color: #cbd5e0;
}

QPushButton#primaryBtn {
    background-color: #3182ce;
    color: #ffffff;
    border: none;
    padding: 11px 24px;
    font-size: 14px;
    font-weight: bold;
    border-radius: 6px;
}

QPushButton#primaryBtn:hover {
    background-color: #2b6cb0;
}

QPushButton#primaryBtn:pressed {
    background-color: #2c5282;
}

QListWidget {
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    background-color: #ffffff;
    font-size: 13px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f0f4f8;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #ebf8ff;
    color: #2b6cb0;
}

QRadioButton, QCheckBox {
    font-size: 13px;
    color: #2d3748;
    spacing: 8px;
}
"""


class DropAreaWidget(QWidget):
    """支持拖放文件的通用容器部件"""
    def __init__(self, file_dropped_callback, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.file_dropped_callback = file_dropped_callback

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths and self.file_dropped_callback:
            self.file_dropped_callback(paths)
        event.acceptProposedAction()


class PDFToolboxWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setWindowTitle(self.config.get("app_name", "PDF 工具箱"))
        self.resize(
            self.config.get("window_width", 840),
            self.config.get("window_height", 720)
        )
        self.setStyleSheet(MODERN_STYLE)

        self.current_split_pdf = ""
        self.current_split_total_pages = 0

        self.current_comp_pdf = ""
        self.current_comp_total_pages = 0

        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # 选项卡
        self.tab_widget = QTabWidget()
        self.tab_split = self._build_split_tab()
        self.tab_merge = self._build_merge_tab()
        self.tab_compress = self._build_compress_tab()

        self.tab_widget.addTab(self.tab_split, "✂️ 拆分 PDF")
        self.tab_widget.addTab(self.tab_merge, "📑 合并 PDF")
        self.tab_widget.addTab(self.tab_compress, "🗜️ 单文件瘦身")

        main_layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

    # ==========================
    # 1. 拆分功能界面
    # ==========================
    def _build_split_tab(self) -> QWidget:
        container = DropAreaWidget(self._on_split_file_dropped)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. 选择原文件
        file_box = QGroupBox("1. 选择待拆分的 PDF 文件 (支持直接将文件拖拽至此处)")
        file_layout = QVBoxLayout(file_box)

        select_row = QHBoxLayout()
        self.split_file_input = QLineEdit()
        self.split_file_input.setPlaceholderText("请选择或拖入 PDF 文件...")
        self.split_file_input.setReadOnly(True)

        browse_btn = QPushButton("📂 浏览文件")
        browse_btn.clicked.connect(self._browse_split_file)

        select_row.addWidget(self.split_file_input)
        select_row.addWidget(browse_btn)
        file_layout.addLayout(select_row)

        self.split_info_label = QLabel("未选择文件")
        self.split_info_label.setStyleSheet("color: #718096; font-size: 12px;")
        file_layout.addWidget(self.split_info_label)

        layout.addWidget(file_box)

        # 2. 拆分模式选择
        mode_box = QGroupBox("2. 选择拆分方式")
        mode_layout = QVBoxLayout(mode_box)
        mode_layout.setSpacing(10)

        self.btn_group_split = QButtonGroup(self)

        self.radio_split_each = QRadioButton("单页拆分：将每一页拆分成一个独立的 PDF 文件")
        self.radio_split_each.setChecked(True)
        self.radio_split_each.toggled.connect(self._toggle_split_mode)
        self.btn_group_split.addButton(self.radio_split_each)
        mode_layout.addWidget(self.radio_split_each)

        self.radio_split_ranges = QRadioButton("自定义页码区间拆分：按指定的页码或区间导出")
        self.radio_split_ranges.toggled.connect(self._toggle_split_mode)
        self.btn_group_split.addButton(self.radio_split_ranges)
        mode_layout.addWidget(self.radio_split_ranges)

        range_sub_layout = QHBoxLayout()
        range_sub_layout.setContentsMargins(28, 0, 0, 0)
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("例如: 1-3, 5, 7-10 (支持英文逗号、中文逗号或分号分隔)")
        self.range_input.setEnabled(False)
        range_sub_layout.addWidget(self.range_input)
        mode_layout.addLayout(range_sub_layout)

        layout.addWidget(mode_box)

        # 3. 输出设置
        output_box = QGroupBox("3. 输出设置")
        output_layout = QVBoxLayout(output_box)

        out_dir_row = QHBoxLayout()
        self.split_outdir_input = QLineEdit()
        self.split_outdir_input.setPlaceholderText("拆分结果保存文件夹...")
        out_browse_btn = QPushButton("📁 选择文件夹")
        out_browse_btn.clicked.connect(self._browse_split_outdir)
        out_dir_row.addWidget(self.split_outdir_input)
        out_dir_row.addWidget(out_browse_btn)
        output_layout.addLayout(out_dir_row)

        prefix_row = QHBoxLayout()
        prefix_lbl = QLabel("文件名前缀 (可选):")
        prefix_lbl.setStyleSheet("color: #4a5568;")
        self.split_prefix_input = QLineEdit()
        self.split_prefix_input.setPlaceholderText("默认使用原文件名")
        prefix_row.addWidget(prefix_lbl)
        prefix_row.addWidget(self.split_prefix_input)
        output_layout.addLayout(prefix_row)

        layout.addWidget(output_box)

        # 执行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_start_split = QPushButton("🚀 开始拆分")
        self.btn_start_split.setObjectName("primaryBtn")
        self.btn_start_split.setMinimumWidth(180)
        self.btn_start_split.clicked.connect(self._execute_split)
        btn_layout.addWidget(self.btn_start_split)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return container

    def _toggle_split_mode(self):
        is_range_mode = self.radio_split_ranges.isChecked()
        self.range_input.setEnabled(is_range_mode)
        if is_range_mode:
            self.range_input.setFocus()

    def _on_split_file_dropped(self, paths):
        for p in paths:
            if p.lower().endswith(".pdf"):
                self._load_split_pdf(p)
                break

    def _browse_split_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择待拆分的 PDF", "", "PDF 文件 (*.pdf)"
        )
        if path:
            self._load_split_pdf(path)

    def _load_split_pdf(self, path: str):
        try:
            pages = get_pdf_page_count(path)
            self.current_split_pdf = path
            self.current_split_total_pages = pages
            self.split_file_input.setText(path)

            size_str = format_size(os.path.getsize(path))
            self.split_info_label.setText(
                f"📄 文件名: {os.path.basename(path)}   |   共 {pages} 页   |   大小: {size_str}"
            )
            self.split_info_label.setStyleSheet("color: #2b6cb0; font-size: 12px; font-weight: bold;")

            dir_name = os.path.dirname(path)
            base_name = os.path.splitext(os.path.basename(path))[0]
            default_out = os.path.join(dir_name, f"{base_name}{self.config.get('default_split_folder_suffix', '_拆分结果')}")
            self.split_outdir_input.setText(default_out)

        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"无法打开 PDF 文件:\n{str(e)}")

    def _browse_split_outdir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择拆分结果存放文件夹")
        if dir_path:
            self.split_outdir_input.setText(dir_path)

    def _execute_split(self):
        if not self.current_split_pdf or not os.path.exists(self.current_split_pdf):
            QMessageBox.warning(self, "提示", "请先选择需要拆分的 PDF 文件！")
            return

        out_dir = self.split_outdir_input.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "提示", "请指定拆分结果的保存文件夹！")
            return

        prefix = self.split_prefix_input.text().strip()

        try:
            if self.radio_split_each.isChecked():
                files = split_pdf_each_page(self.current_split_pdf, out_dir, prefix)
                count = len(files)
                msg = f"拆分完成！成功生成 {count} 个单页 PDF 文件。\n保存路径: {out_dir}"
            else:
                range_str = self.range_input.text().strip()
                if not range_str:
                    QMessageBox.warning(self, "提示", "请输入自定义页码区间，例如: 1-3, 5, 7-10")
                    return
                ranges = parse_page_ranges(range_str, self.current_split_total_pages)
                files = split_pdf_by_ranges(self.current_split_pdf, out_dir, ranges, prefix)
                count = len(files)
                msg = f"拆分完成！成功生成 {count} 个区间 PDF 文件。\n保存路径: {out_dir}"

            reply = QMessageBox.information(
                self,
                "处理成功",
                f"{msg}\n\n是否立即打开保存目录？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                os.startfile(out_dir)

        except Exception as e:
            QMessageBox.critical(self, "拆分失败", f"拆分过程中出现错误:\n{str(e)}")

    # ==========================
    # 2. 合并功能界面
    # ==========================
    def _build_merge_tab(self) -> QWidget:
        container = DropAreaWidget(self._on_merge_files_dropped)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. 文件列表与排序管理
        list_box = QGroupBox("1. 待合并的 PDF 文件列表 (支持批量拖入，支持在列表中直接拖拽上下调整顺序)")
        list_layout = QVBoxLayout(list_box)

        h_content = QHBoxLayout()
        self.merge_list = QListWidget()
        self.merge_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.merge_list.setDragDropMode(QAbstractItemView.InternalMove)
        h_content.addWidget(self.merge_list, stretch=4)

        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(8)

        add_btn = QPushButton("➕ 添加文件")
        add_btn.clicked.connect(self._browse_merge_files)

        up_btn = QPushButton("⬆️ 上移")
        up_btn.clicked.connect(self._move_item_up)

        down_btn = QPushButton("⬇️ 下移")
        down_btn.clicked.connect(self._move_item_down)

        remove_btn = QPushButton("🗑️ 移除选中")
        remove_btn.clicked.connect(self._remove_selected_item)

        clear_btn = QPushButton("🧹 清空列表")
        clear_btn.clicked.connect(self._clear_merge_list)

        btn_vbox.addWidget(add_btn)
        btn_vbox.addWidget(up_btn)
        btn_vbox.addWidget(down_btn)
        btn_vbox.addWidget(remove_btn)
        btn_vbox.addWidget(clear_btn)
        btn_vbox.addStretch()

        h_content.addLayout(btn_vbox, stretch=1)
        list_layout.addLayout(h_content)

        self.merge_summary_label = QLabel("列表为空，请添加 PDF 文件")
        self.merge_summary_label.setStyleSheet("color: #718096; font-size: 12px;")
        list_layout.addWidget(self.merge_summary_label)

        layout.addWidget(list_box)

        # 2. 页面尺寸统一设置
        size_box = QGroupBox("2. 页面尺寸统一选项 (解决多来源 PDF 页面大小不一致)")
        size_layout = QVBoxLayout(size_box)
        size_layout.setSpacing(6)

        self.btn_group_size = QButtonGroup(self)
        self.radio_size_a4 = QRadioButton("统一为标准 A4 (推荐：自动等比缩放并居中，彻底消除页面忽大忽小)")
        self.radio_size_a4.setChecked(True)
        self.btn_group_size.addButton(self.radio_size_a4)
        size_layout.addWidget(self.radio_size_a4)

        self.radio_size_first = QRadioButton("统一以第 1 个文件的第 1 页大小为基准")
        self.btn_group_size.addButton(self.radio_size_first)
        size_layout.addWidget(self.radio_size_first)

        self.radio_size_original = QRadioButton("保持各自原始大小 (不进行缩放)")
        self.btn_group_size.addButton(self.radio_size_original)
        size_layout.addWidget(self.radio_size_original)

        layout.addWidget(size_box)

        # 3. 文件体积优化与智能瘦身
        compress_box = QGroupBox("3. 文件体积优化与智能瘦身 (解决大图/编辑扫描件导致合并后文件暴涨)")
        compress_layout = QVBoxLayout(compress_box)
        compress_layout.setSpacing(6)

        self.btn_group_compress = QButtonGroup(self)
        self.radio_comp_balanced = QRadioButton("智能高清瘦身 (推荐：大图重采样至 150 DPI 优质 JPEG，兼顾清晰度与极小体积)")
        self.radio_comp_balanced.setChecked(True)
        self.btn_group_compress.addButton(self.radio_comp_balanced)
        compress_layout.addWidget(self.radio_comp_balanced)

        self.radio_comp_extreme = QRadioButton("极限压缩瘦身 (大图优化至 100 DPI，适合邮件发送与限制体积的网站上传)")
        self.btn_group_compress.addButton(self.radio_comp_extreme)
        compress_layout.addWidget(self.radio_comp_extreme)

        self.radio_comp_none = QRadioButton("不压缩 (保留原始大图，可能导致文件体积较大)")
        self.btn_group_compress.addButton(self.radio_comp_none)
        compress_layout.addWidget(self.radio_comp_none)

        layout.addWidget(compress_box)

        # 4. 合并输出设置
        out_box = QGroupBox("4. 合并后文件保存位置")
        out_layout = QHBoxLayout(out_box)

        self.merge_outfile_input = QLineEdit()
        self.merge_outfile_input.setPlaceholderText("请指定合并后的 PDF 保存完整路径...")

        save_as_btn = QPushButton("💾 另存为...")
        save_as_btn.clicked.connect(self._browse_merge_outfile)

        out_layout.addWidget(self.merge_outfile_input)
        out_layout.addWidget(save_as_btn)

        layout.addWidget(out_box)

        # 执行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_start_merge = QPushButton("🚀 开始合并")
        self.btn_start_merge.setObjectName("primaryBtn")
        self.btn_start_merge.setMinimumWidth(180)
        self.btn_start_merge.clicked.connect(self._execute_merge)
        btn_layout.addWidget(self.btn_start_merge)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return container

    def _on_merge_files_dropped(self, paths):
        added_any = False
        for p in paths:
            if p.lower().endswith(".pdf"):
                self._add_merge_file(p)
                added_any = True
        if added_any:
            self._update_merge_summary()

    def _browse_merge_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择需要合并的 PDF 文件 (可多选)", "", "PDF 文件 (*.pdf)"
        )
        if paths:
            for p in paths:
                self._add_merge_file(p)
            self._update_merge_summary()

    def _add_merge_file(self, path: str):
        try:
            pages = get_pdf_page_count(path)
            fname = os.path.basename(path)
            size_str = format_size(os.path.getsize(path))
            item_text = f"{fname}   [{pages} 页 | {size_str}]   ({path})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, path)
            self.merge_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "跳过无法读取的文件", f"文件 {os.path.basename(path)} 无法解析:\n{str(e)}")

    def _move_item_up(self):
        row = self.merge_list.currentRow()
        if row > 0:
            item = self.merge_list.takeItem(row)
            self.merge_list.insertItem(row - 1, item)
            self.merge_list.setCurrentRow(row - 1)

    def _move_item_down(self):
        row = self.merge_list.currentRow()
        if 0 <= row < self.merge_list.count() - 1:
            item = self.merge_list.takeItem(row)
            self.merge_list.insertItem(row + 1, item)
            self.merge_list.setCurrentRow(row + 1)

    def _remove_selected_item(self):
        row = self.merge_list.currentRow()
        if row >= 0:
            self.merge_list.takeItem(row)
            self._update_merge_summary()

    def _clear_merge_list(self):
        self.merge_list.clear()
        self._update_merge_summary()

    def _update_merge_summary(self):
        count = self.merge_list.count()
        if count == 0:
            self.merge_summary_label.setText("列表为空，请添加 PDF 文件")
            self.merge_summary_label.setStyleSheet("color: #718096; font-size: 12px;")
            return

        total_pages = 0
        total_bytes = 0
        first_dir = ""
        for i in range(count):
            item = self.merge_list.item(i)
            path = item.data(Qt.UserRole)
            if not first_dir and path:
                first_dir = os.path.dirname(path)
            try:
                total_pages += get_pdf_page_count(path)
                total_bytes += os.path.getsize(path)
            except Exception:
                pass

        self.merge_summary_label.setText(
            f"已添加 {count} 个文件   |   共计约 {total_pages} 页   |   原始总大小: {format_size(total_bytes)}"
        )
        self.merge_summary_label.setStyleSheet("color: #2b6cb0; font-size: 12px; font-weight: bold;")

        if not self.merge_outfile_input.text().strip() and first_dir:
            default_out = os.path.join(first_dir, self.config.get("default_merged_filename", "合并文档.pdf"))
            self.merge_outfile_input.setText(default_out)

    def _browse_merge_outfile(self):
        current_text = self.merge_outfile_input.text().strip()
        start_dir = os.path.dirname(current_text) if current_text else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "选择合并后的 PDF 保存路径", start_dir, "PDF 文件 (*.pdf)"
        )
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            self.merge_outfile_input.setText(path)

    def _execute_merge(self):
        count = self.merge_list.count()
        if count < 1:
            QMessageBox.warning(self, "提示", "请至少添加 1 个待处理的 PDF 文件！")
            return

        out_path = self.merge_outfile_input.text().strip()
        if not out_path:
            QMessageBox.warning(self, "提示", "请指定合并后 PDF 的保存路径！")
            return

        pdf_paths = [self.merge_list.item(i).data(Qt.UserRole) for i in range(count)]

        if self.radio_size_a4.isChecked():
            size_mode = "a4"
        elif self.radio_size_first.isChecked():
            size_mode = "first_page"
        else:
            size_mode = "original"

        if self.radio_comp_balanced.isChecked():
            compress_mode = "balanced"
        elif self.radio_comp_extreme.isChecked():
            compress_mode = "extreme"
        else:
            compress_mode = "none"

        try:
            merge_pdfs(pdf_paths, out_path, size_mode=size_mode, compress_mode=compress_mode)
            total_pages = get_pdf_page_count(out_path)
            final_size_str = format_size(os.path.getsize(out_path))

            reply = QMessageBox.information(
                self,
                "合并成功",
                f"已成功将 {count} 个文件处理并合并为一个 PDF 文档！\n总页数: {total_pages} 页\n最终文件大小: {final_size_str}\n保存路径:\n{out_path}\n\n是否立即打开该文件？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                os.startfile(out_path)

        except Exception as e:
            QMessageBox.critical(self, "合并失败", f"合并过程中出现错误:\n{str(e)}")

    # ==========================
    # 3. 单文件瘦身功能界面
    # ==========================
    def _build_compress_tab(self) -> QWidget:
        container = DropAreaWidget(self._on_comp_file_dropped)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. 选择待瘦身的文件
        file_box = QGroupBox("1. 选择待瘦身的 PDF 文件 (支持直接将文件拖拽至此处)")
        file_layout = QVBoxLayout(file_box)

        select_row = QHBoxLayout()
        self.comp_file_input = QLineEdit()
        self.comp_file_input.setPlaceholderText("请选择或拖入需要瘦身的单个 PDF 文件...")
        self.comp_file_input.setReadOnly(True)

        browse_btn = QPushButton("📂 浏览文件")
        browse_btn.clicked.connect(self._browse_comp_file)

        select_row.addWidget(self.comp_file_input)
        select_row.addWidget(browse_btn)
        file_layout.addLayout(select_row)

        self.comp_info_label = QLabel("未选择文件")
        self.comp_info_label.setStyleSheet("color: #718096; font-size: 12px;")
        file_layout.addWidget(self.comp_info_label)

        layout.addWidget(file_box)

        # 2. 瘦身压缩强度设置
        strength_box = QGroupBox("2. 瘦身压缩强度设置")
        strength_layout = QVBoxLayout(strength_box)
        strength_layout.setSpacing(8)

        self.btn_group_single_comp = QButtonGroup(self)

        self.radio_single_balanced = QRadioButton("🌟 智能高清瘦身 (强烈推荐：大图重采样至 150 DPI 优质 JPEG，兼顾清晰度与极小体积)")
        self.radio_single_balanced.setChecked(True)
        self.btn_group_single_comp.addButton(self.radio_single_balanced)
        strength_layout.addWidget(self.radio_single_balanced)

        self.radio_single_extreme = QRadioButton("🚀 极限压缩瘦身 (大图优化至 100 DPI，适合作为邮件附件或严格限制文件大小的网站上传)")
        self.btn_group_single_comp.addButton(self.radio_single_extreme)
        strength_layout.addWidget(self.radio_single_extreme)

        self.radio_single_lossless = QRadioButton("轻度无损精简 (仅清理无用对象、重复字典与数据流压缩，不改变图片分辨率)")
        self.btn_group_single_comp.addButton(self.radio_single_lossless)
        strength_layout.addWidget(self.radio_single_lossless)

        layout.addWidget(strength_box)

        # 3. 页面尺寸辅助规范化
        aux_box = QGroupBox("3. 页面排版辅助规范")
        aux_layout = QVBoxLayout(aux_box)

        self.check_single_unify_a4 = QCheckBox("顺便将所有页面统一为标准 A4 尺寸 (等比缩放居中，彻底消除扫描大图偏大问题)")
        self.check_single_unify_a4.setChecked(True)
        aux_layout.addWidget(self.check_single_unify_a4)

        layout.addWidget(aux_box)

        # 4. 保存位置
        out_box = QGroupBox("4. 瘦身后文件保存位置")
        out_layout = QHBoxLayout(out_box)

        self.comp_outfile_input = QLineEdit()
        self.comp_outfile_input.setPlaceholderText("请指定瘦身后的 PDF 保存完整路径...")

        save_as_btn = QPushButton("💾 另存为...")
        save_as_btn.clicked.connect(self._browse_comp_outfile)

        out_layout.addWidget(self.comp_outfile_input)
        out_layout.addWidget(save_as_btn)

        layout.addWidget(out_box)

        # 执行按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_start_comp = QPushButton("🚀 开始瘦身")
        self.btn_start_comp.setObjectName("primaryBtn")
        self.btn_start_comp.setMinimumWidth(180)
        self.btn_start_comp.clicked.connect(self._execute_single_compress)
        btn_layout.addWidget(self.btn_start_comp)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return container

    def _on_comp_file_dropped(self, paths):
        for p in paths:
            if p.lower().endswith(".pdf"):
                self._load_comp_pdf(p)
                break

    def _browse_comp_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择待瘦身的 PDF", "", "PDF 文件 (*.pdf)"
        )
        if path:
            self._load_comp_pdf(path)

    def _load_comp_pdf(self, path: str):
        try:
            pages = get_pdf_page_count(path)
            orig_size = os.path.getsize(path)
            self.current_comp_pdf = path
            self.current_comp_total_pages = pages
            self.comp_file_input.setText(path)

            size_str = format_size(orig_size)
            self.comp_info_label.setText(
                f"📄 文件名: {os.path.basename(path)}   |   共 {pages} 页   |   当前大小: {size_str}"
            )
            self.comp_info_label.setStyleSheet("color: #2b6cb0; font-size: 12px; font-weight: bold;")

            dir_name = os.path.dirname(path)
            base_name = os.path.splitext(os.path.basename(path))[0]
            suffix = self.config.get("default_compress_suffix", "_已瘦身.pdf")
            default_out = os.path.join(dir_name, f"{base_name}{suffix}")
            self.comp_outfile_input.setText(default_out)

        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"无法打开 PDF 文件:\n{str(e)}")

    def _browse_comp_outfile(self):
        current_text = self.comp_outfile_input.text().strip()
        start_dir = os.path.dirname(current_text) if current_text else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "选择瘦身后的 PDF 保存路径", start_dir, "PDF 文件 (*.pdf)"
        )
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            self.comp_outfile_input.setText(path)

    def _execute_single_compress(self):
        if not self.current_comp_pdf or not os.path.exists(self.current_comp_pdf):
            QMessageBox.warning(self, "提示", "请先选择需要瘦身的 PDF 文件！")
            return

        out_path = self.comp_outfile_input.text().strip()
        if not out_path:
            QMessageBox.warning(self, "提示", "请指定瘦身结果的保存路径！")
            return

        if self.radio_single_balanced.isChecked():
            quality_mode = "balanced"
        elif self.radio_single_extreme.isChecked():
            quality_mode = "extreme"
        else:
            quality_mode = "none"

        unify_a4 = self.check_single_unify_a4.isChecked()

        try:
            orig_bytes, new_bytes = compress_single_pdf(
                self.current_comp_pdf,
                out_path,
                quality_mode=quality_mode,
                unify_a4=unify_a4
            )

            orig_str = format_size(orig_bytes)
            new_str = format_size(new_bytes)
            saved_percent = max(0.0, (orig_bytes - new_bytes) / orig_bytes * 100) if orig_bytes > 0 else 0.0

            result_msg = (
                f"🎉 PDF 瘦身成功！\n\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"• 原始体积: {orig_str}\n"
                f"• 瘦身体积: {new_str}\n"
                f"• 体积减小: {saved_percent:.1f}%\n"
                f"• 页面总数: {self.current_comp_total_pages} 页\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"保存路径:\n{out_path}\n\n"
                f"是否立即打开瘦身后的 PDF 文件？"
            )

            reply = QMessageBox.information(
                self,
                "瘦身成功",
                result_msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                os.startfile(out_path)

        except Exception as e:
            QMessageBox.critical(self, "瘦身失败", f"处理过程中出现错误:\n{str(e)}")
