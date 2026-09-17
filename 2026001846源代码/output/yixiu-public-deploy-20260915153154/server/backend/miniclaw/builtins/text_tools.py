"""内置插件：文本处理工具

提供文本分析、字数统计、文本转换等功能。
"""
import re
import hashlib
import base64
from urllib.parse import quote, unquote
from miniclaw.tools import BaseTool, ToolResult, ToolParameter


class TextAnalysisTool(BaseTool):
    name = "text_analysis"
    description = "文本分析工具，统计字符数、词数、行数，提取关键信息"
    parameters = [
        ToolParameter(name="text", type="string", description="要分析的文本"),
        ToolParameter(name="mode", type="string", description="分析模式: 'stats'(统计), 'extract_numbers'(提取数字), 'extract_urls'(提取链接)", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        mode = kwargs.get("mode", "stats").strip().lower()

        if not text:
            return ToolResult(success=False, output="", error="文本不能为空")

        if mode == "stats":
            chars = len(text)
            chars_no_space = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
            words = len(text.split())
            lines = len(text.splitlines())
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            digits = len(re.findall(r'\d', text))

            stats = {
                "总字符数": chars,
                "字符数(不含空格)": chars_no_space,
                "词数": words,
                "行数": lines,
                "中文字符": chinese_chars,
                "英文字符": english_chars,
                "数字": digits,
            }
            output = "\n".join(f"  {k}: {v}" for k, v in stats.items())
            return ToolResult(success=True, output=f"文本统计:\n{output}", metadata=stats)

        elif mode == "extract_numbers":
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                output = "提取到的数字: " + ", ".join(numbers)
            else:
                output = "未找到数字"
            return ToolResult(success=True, output=output, metadata={"numbers": numbers})

        elif mode == "extract_urls":
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
            if urls:
                output = "提取到的链接:\n" + "\n".join(f"  {u}" for u in urls)
            else:
                output = "未找到链接"
            return ToolResult(success=True, output=output, metadata={"urls": urls})

        return ToolResult(success=False, output="", error=f"不支持的模式: {mode}")

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        mode = kwargs.get("mode", "stats").strip().lower()

        if not text:
            return ToolResult(success=False, output="", error="文本不能为空")

        if mode == "stats":
            chars = len(text)
            chars_no_space = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
            words = len(text.split())
            lines = len(text.splitlines())
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            digits = len(re.findall(r'\d', text))

            stats = {
                "总字符数": chars,
                "字符数(不含空格)": chars_no_space,
                "词数": words,
                "行数": lines,
                "中文字符": chinese_chars,
                "英文字符": english_chars,
                "数字": digits,
            }
            output = "\n".join(f"  {k}: {v}" for k, v in stats.items())
            return ToolResult(success=True, output=f"文本统计:\n{output}", metadata=stats)

        elif mode == "extract_numbers":
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                output = "提取到的数字: " + ", ".join(numbers)
            else:
                output = "未找到数字"
            return ToolResult(success=True, output=output, metadata={"numbers": numbers})

        elif mode == "extract_urls":
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
            if urls:
                output = "提取到的链接:\n" + "\n".join(f"  {u}" for u in urls)
            else:
                output = "未找到链接"
            return ToolResult(success=True, output=output, metadata={"urls": urls})

        return ToolResult(success=False, output="", error=f"不支持的模式: {mode}")


class TextTransformTool(BaseTool):
    name = "text_transform"
    description = "文本转换工具，支持大小写转换、编码解码、哈希计算等"
    parameters = [
        ToolParameter(name="text", type="string", description="要转换的文本"),
        ToolParameter(name="operation", type="string", description="操作: 'upper', 'lower', 'reverse', 'md5', 'sha256', 'base64_encode', 'base64_decode', 'url_encode', 'url_decode'"),
    ]

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        operation = kwargs.get("operation", "").strip().lower()

        if not text:
            return ToolResult(success=False, output="", error="文本不能为空")

        try:
            if operation == "upper":
                result = text.upper()
            elif operation == "lower":
                result = text.lower()
            elif operation == "reverse":
                result = text[::-1]
            elif operation == "md5":
                result = hashlib.md5(text.encode()).hexdigest()
            elif operation == "sha256":
                result = hashlib.sha256(text.encode()).hexdigest()
            elif operation == "base64_encode":
                result = base64.b64encode(text.encode()).decode()
            elif operation == "base64_decode":
                result = base64.b64decode(text.encode()).decode()
            elif operation == "url_encode":
                result = quote(text)
            elif operation == "url_decode":
                result = unquote(text)
            else:
                return ToolResult(success=False, output="", error=f"不支持的操作: {operation}")

            return ToolResult(success=True, output=result, metadata={"operation": operation, "result": result})
        except Exception as e:
            return ToolResult(success=False, output="", error=f"转换失败: {str(e)}")


def register(api):
    api.register_tool(TextAnalysisTool())
    api.register_tool(TextTransformTool())
