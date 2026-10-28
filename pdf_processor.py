"""
PDF 处理核心逻辑模块
负责纯粹的 PDF 拆分、合并、单文件瘦身与信息读取，无 GUI 依赖。
"""

import os
import shutil
from typing import List, Tuple, Dict, Any, Optional
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
import pymupdf

# 标准 A4 纸张尺寸点数 (72 points / inch)
A4_WIDTH = 595.28
A4_HEIGHT = 841.89


def get_pdf_page_count(pdf_path: str) -> int:
    """获取 PDF 的总页数"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    reader = PdfReader(pdf_path)
    return len(reader.pages)


def parse_page_ranges(range_str: str, max_pages: int) -> List[Tuple[int, int]]:
    """
    解析用户输入的页码范围字符串。
    支持格式如: "1-3, 5, 7-10; 12"
    返回 1-based 的元组列表: [(1, 3), (5, 5), (7, 10), (12, 12)]
    """
    if not range_str or not range_str.strip():
        raise ValueError("页码范围不能为空")

    normalized = range_str.replace("；", ";").replace("，", ",").replace(" ", "")
    parts = [p for p in normalized.replace(";", ",").split(",") if p]

    result_ranges = []
    for part in parts:
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError(f"无效的页码区间: '{part}'")
            start, end = int(start_str), int(end_str)
            if start > end:
                raise ValueError(f"起始页不能大于结束页: '{part}'")
            if start < 1:
                raise ValueError(f"页码必须从 1 开始: '{part}'")
            if end > max_pages:
                raise ValueError(f"页码 '{end}' 超出文档最大总页数 ({max_pages})")
            result_ranges.append((start, end))
        else:
            if not part.isdigit():
                raise ValueError(f"无效的单页页码: '{part}'")
            page_num = int(part)
            if page_num < 1:
                raise ValueError(f"页码必须从 1 开始: '{part}'")
            if page_num > max_pages:
                raise ValueError(f"页码 '{page_num}' 超出文档最大总页数 ({max_pages})")
            result_ranges.append((page_num, page_num))

    if not result_ranges:
        raise ValueError("未检测到有效的页码设置")

    return result_ranges


def split_pdf_each_page(src_pdf: str, output_dir: str, prefix: str = "") -> List[str]:
    """
    将 PDF 拆分为单个页面，每页生成一个独立的 PDF 文件。
    返回生成的文件路径列表。
    """
    if not os.path.exists(src_pdf):
        raise FileNotFoundError(f"原文件不存在: {src_pdf}")

    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(src_pdf)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(os.path.basename(src_pdf))[0]
    file_prefix = prefix.strip() if prefix.strip() else base_name

    pad_len = max(len(str(total_pages)), 3)
    created_files = []

    for idx, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        page_str = str(idx + 1).zfill(pad_len)
        out_filename = f"{file_prefix}_p{page_str}.pdf"
        out_filepath = os.path.join(output_dir, out_filename)

        with open(out_filepath, "wb") as f:
            writer.write(f)
        created_files.append(out_filepath)

    return created_files


def split_pdf_by_ranges(src_pdf: str, output_dir: str, ranges: List[Tuple[int, int]], prefix: str = "") -> List[str]:
    """
    按照给定的页码区间列表拆分 PDF。
    ranges: [(1, 3), (5, 5), (7, 10)] 等 1-based 页码
    返回生成的文件路径列表。
    """
    if not os.path.exists(src_pdf):
        raise FileNotFoundError(f"原文件不存在: {src_pdf}")

    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(src_pdf)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(os.path.basename(src_pdf))[0]
    file_prefix = prefix.strip() if prefix.strip() else base_name

    created_files = []

    for start_p, end_p in ranges:
        writer = PdfWriter()
        # 将 1-based 转为 0-based
        for p_idx in range(start_p - 1, min(end_p, total_pages)):
            writer.add_page(reader.pages[p_idx])

        if start_p == end_p:
            out_filename = f"{file_prefix}_p{start_p}.pdf"
        else:
            out_filename = f"{file_prefix}_p{start_p}-{end_p}.pdf"

        out_filepath = os.path.join(output_dir, out_filename)
        with open(out_filepath, "wb") as f:
            writer.write(f)
        created_files.append(out_filepath)

    return created_files


def scale_and_center_page(page: PageObject, target_w: float, target_h: float) -> PageObject:
    """
    将输入 page 按比例等比缩放并居中放置在大小为 (target_w, target_h) 的新画板上。
    保持原始方向自适应（若原页面为横向且目标是竖向，则自动匹配横向目标画板）。
    """
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)

    # 自适应方向：如果原页面是横向，目标画板也自适应调整为横向
    is_src_landscape = w > h
    is_target_landscape = target_w > target_h
    if is_src_landscape != is_target_landscape:
        target_w, target_h = target_h, target_w

    # 如果尺寸已经与目标极度接近（误差 < 1 pt），直接返回原页面
    if abs(w - target_w) < 1.0 and abs(h - target_h) < 1.0:
        return page

    # 计算等比缩放比
    scale = min(target_w / w, target_h / h)
    # 计算平移量（包含原页面非零起点偏移）
    tx = (target_w - w * scale) / 2.0 - float(page.mediabox.left) * scale
    ty = (target_h - h * scale) / 2.0 - float(page.mediabox.bottom) * scale

    target_page = PageObject.create_blank_page(width=target_w, height=target_h)
    op = Transformation().scale(scale, scale).translate(tx, ty)
    target_page.merge_transformed_page(page, op)
    return target_page


def optimize_pdf_file(pdf_path: str, quality_mode: str = "balanced") -> int:
    """
    对生成的 PDF 文件进行智能压缩瘦身：
    - 去除冗余元数据与未引用对象 (garbage=4)
    - 内容流数据深度 Deflate 压缩 (deflate=True)
    - 对超大高分辨率位图进行重采样优化 (balanced 对应 150 DPI，extreme 对应 100 DPI)
    返回优化后的文件字节大小。
    """
    if quality_mode == "none":
        return os.path.getsize(pdf_path)

    temp_path = pdf_path + ".tmp_opt.pdf"

    doc = pymupdf.open(pdf_path)
    try:
        if quality_mode == "balanced":
            doc.rewrite_images(dpi_threshold=145, dpi_target=140, quality=78)
        elif quality_mode == "extreme":
            doc.rewrite_images(dpi_threshold=105, dpi_target=100, quality=65)
    except Exception:
        pass

    doc.save(temp_path, garbage=4, deflate=True, clean=True)
    doc.close()

    # 替换原文件
    if os.path.exists(temp_path):
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        os.rename(temp_path, pdf_path)

    return os.path.getsize(pdf_path)


def compress_single_pdf(
    src_pdf: str,
    output_path: str,
    quality_mode: str = "balanced",
    unify_a4: bool = False
) -> Tuple[int, int]:
    """
    专门对单个 PDF 文件进行智能瘦身压缩，可选同步规范化页面尺寸为标准 A4。
    返回 (原始字节数, 压缩后字节数)。
    """
    if not os.path.exists(src_pdf):
        raise FileNotFoundError(f"文件不存在: {src_pdf}")

    orig_size = os.path.getsize(src_pdf)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # 如果需要统一为标准 A4 页面大小
    if unify_a4:
        reader = PdfReader(src_pdf)
        writer = PdfWriter()
        for page in reader.pages:
            scaled_p = scale_and_center_page(page, A4_WIDTH, A4_HEIGHT)
            writer.add_page(scaled_p)
        with open(output_path, "wb") as f:
            writer.write(f)
    else:
        # 如果不需要调整尺寸，先复制为目标基础文件
        if os.path.abspath(src_pdf) != os.path.abspath(output_path):
            shutil.copy2(src_pdf, output_path)

    # 深度瘦身压缩
    optimize_pdf_file(output_path, quality_mode=quality_mode)
    new_size = os.path.getsize(output_path)
    return orig_size, new_size


def merge_pdfs(
    pdf_paths: List[str],
    output_path: str,
    size_mode: str = "a4",
    compress_mode: str = "balanced"
) -> str:
    """
    将多个 PDF 文件按顺序合并为一个新的 PDF 文件。
    size_mode 可选:
      - "a4": 统一为标准 A4 页面大小（自动等比缩放并居中，防止页面忽大忽小）
      - "first_page": 统一为首个文件第 1 页的页面大小
      - "original": 保持各自页面的原始大小（不调整）
    compress_mode 可选:
      - "balanced": 智能高清瘦身（大图压缩为 150 DPI，视觉无损，极大减少几兆膨胀）
      - "extreme": 极限瘦身（大图压缩为 100 DPI，适合邮件/限额上传）
      - "none": 不压缩
    返回最终输出文件路径。
    """
    if not pdf_paths:
        raise ValueError("请至少提供一个需要合并的 PDF 文件")

    for path in pdf_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")

    # 确定目标基准尺寸
    target_dim: Optional[Tuple[float, float]] = None
    if size_mode == "a4":
        target_dim = (A4_WIDTH, A4_HEIGHT)
    elif size_mode == "first_page":
        first_reader = PdfReader(pdf_paths[0])
        if len(first_reader.pages) > 0:
            first_p = first_reader.pages[0]
            target_dim = (float(first_p.mediabox.width), float(first_p.mediabox.height))
        else:
            target_dim = (A4_WIDTH, A4_HEIGHT)

    writer = PdfWriter()
    for path in pdf_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            if size_mode in ("a4", "first_page") and target_dim is not None:
                scaled_p = scale_and_center_page(page, target_dim[0], target_dim[1])
                writer.add_page(scaled_p)
            else:
                writer.add_page(page)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "wb") as f:
        writer.write(f)

    # 执行智能瘦身优化
    if compress_mode and compress_mode != "none":
        try:
            optimize_pdf_file(output_path, quality_mode=compress_mode)
        except Exception:
            pass

    return output_path
