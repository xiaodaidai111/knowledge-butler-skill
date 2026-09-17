"""
文件解析与切片服务
- 支持 PDF / DOCX / TXT / MD / CSV
- 切片策略：按段落 + 长度兜底（每段约 chunk_size 字符，重叠 overlap 字符）
- 解析失败时优雅降级，返回原文摘要
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 切片参数
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 120


def _split_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> List[str]:
    """按字符长度切片，支持重叠。优先在段落边界切分。"""
    if not text:
        return []
    # 按双换行（段落）切
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= chunk_size:
            buffer = f"{buffer}\n\n{para}".strip()
            continue
        if buffer:
            chunks.append(buffer)
        # 段落本身超长，再按 chunk_size 兜底切
        if len(para) > chunk_size:
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i:i + chunk_size])
        else:
            buffer = para
        # 不强制合并，直接进 buffer 等下一段
        buffer = para if len(para) <= chunk_size else ""
    if buffer:
        chunks.append(buffer)
    # 过滤空块
    return [c.strip() for c in chunks if c.strip()]


def _parse_pdf(path: Path) -> str:
    """解析 PDF 文本。优先使用 pypdf，降级 pdfplumber。"""
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n\n".join(texts).strip()
    except ImportError:
        pass
    try:
        import pdfplumber  # type: ignore
        texts: List[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:
                    continue
        return "\n\n".join(texts).strip()
    except ImportError:
        logger.warning("PDF 解析依赖缺失（pypdf / pdfplumber），无法提取 %s", path.name)
        return ""


def _parse_docx(path: Path) -> str:
    """解析 Word DOCX。"""
    try:
        import docx  # type: ignore  # python-docx
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        # 表格内容也提取
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        return "\n\n".join(paragraphs).strip()
    except ImportError:
        logger.warning("DOCX 解析依赖缺失（python-docx），无法提取 %s", path.name)
        return ""


def _parse_plain(path: Path) -> str:
    """解析 TXT/MD/CSV 等纯文本。"""
    # 尝试常见编码
    for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def parse_file(path, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> List[str]:
    """
    统一文件解析入口：返回切片后的文本块列表。
    支持 PDF / DOCX / TXT / MD / CSV。其他类型返回空列表。
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        logger.warning("文件不存在: %s", path)
        return []

    suffix = path.suffix.lower()
    text = ""
    if suffix == ".pdf":
        text = _parse_pdf(path)
    elif suffix in {".docx", ".doc"}:
        # 老式 .doc 需要其他工具，python-docx 仅支持 docx
        if suffix == ".doc":
            logger.warning("老式 .doc 暂不支持，建议转换为 .docx: %s", path.name)
            return []
        text = _parse_docx(path)
    elif suffix in {".txt", ".md", ".csv", ".json"}:
        text = _parse_plain(path)
    else:
        logger.info("文件类型 %s 不在可解析范围", suffix)
        return []

    if not text:
        logger.info("文件 %s 解析后为空", path.name)
        return []

    chunks = _split_text(text, chunk_size=chunk_size, overlap=overlap)
    logger.info("文件 %s 解析得 %d 字符，切分为 %d 块", path.name, len(text), len(chunks))
    return chunks


def supported_suffixes() -> set:
    return {".pdf", ".docx", ".txt", ".md", ".csv", ".json"}
