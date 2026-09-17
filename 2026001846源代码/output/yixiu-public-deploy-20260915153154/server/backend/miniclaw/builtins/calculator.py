"""内置插件：计算器工具

提供数学计算能力，包括基础运算、单位换算等。
"""
import math
import re
from miniclaw.tools import BaseTool, ToolResult, ToolParameter


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "数学计算工具，支持基础四则运算、幂运算、开方、三角函数等数学计算"
    parameters = [
        ToolParameter(name="expression", type="string", description="数学表达式，例如 '2+3*4', 'sqrt(16)', 'sin(3.14)'"),
    ]

    def execute(self, **kwargs) -> ToolResult:
        expression = kwargs.get("expression", "").strip()
        if not expression:
            return ToolResult(success=False, output="", error="缺少表达式参数")

        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "len": len,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "log10": math.log10,
            "pi": math.pi, "e": math.e, "ceil": math.ceil,
            "floor": math.floor, "factorial": math.factorial,
        }

        dangerous = re.compile(r'(__|import|exec|eval|open|file|compile|globals|locals)')
        if dangerous.search(expression):
            return ToolResult(success=False, output="", error="表达式包含不允许的操作")

        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return ToolResult(success=True, output=str(result), metadata={"expression": expression, "result": result})
        except ZeroDivisionError:
            return ToolResult(success=False, output="", error="除零错误")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"计算错误: {str(e)}")


class UnitConverterTool(BaseTool):
    name = "unit_converter"
    description = "单位换算工具，支持长度、重量、温度等单位之间的换算"
    parameters = [
        ToolParameter(name="value", type="number", description="要换算的数值"),
        ToolParameter(name="from_unit", type="string", description="原始单位，如 'km', 'kg', 'celsius'"),
        ToolParameter(name="to_unit", type="string", description="目标单位，如 'm', 'g', 'fahrenheit'"),
    ]

    LENGTH_MAP = {
        "km": 1000, "m": 1, "cm": 0.01, "mm": 0.001,
        "mile": 1609.344, "yard": 0.9144, "foot": 0.3048, "inch": 0.0254,
    }
    WEIGHT_MAP = {
        "kg": 1000, "g": 1, "mg": 0.001,
        "pound": 453.592, "ounce": 28.3495,
    }

    def execute(self, **kwargs) -> ToolResult:
        try:
            value = float(kwargs.get("value", 0))
            from_unit = kwargs.get("from_unit", "").lower().strip()
            to_unit = kwargs.get("to_unit", "").lower().strip()
        except (ValueError, TypeError):
            return ToolResult(success=False, output="", error="无效的数值")

        if from_unit == to_unit:
            return ToolResult(success=True, output=str(value))

        if from_unit in ("celsius", "fahrenheit", "kelvin") and to_unit in ("celsius", "fahrenheit", "kelvin"):
            result = self._convert_temperature(value, from_unit, to_unit)
            return ToolResult(success=True, output=f"{value} {from_unit} = {result} {to_unit}")

        for unit_map, unit_name in [(self.LENGTH_MAP, "长度"), (self.WEIGHT_MAP, "重量")]:
            if from_unit in unit_map and to_unit in unit_map:
                base = value * unit_map[from_unit]
                result = base / unit_map[to_unit]
                return ToolResult(success=True, output=f"{value} {from_unit} = {result:.6g} {to_unit}")

        return ToolResult(success=False, output="", error=f"不支持从 {from_unit} 到 {to_unit} 的换算")

    def _convert_temperature(self, value, from_unit, to_unit):
        celsius = value
        if from_unit == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "kelvin":
            celsius = value - 273.15

        if to_unit == "celsius":
            return round(celsius, 4)
        elif to_unit == "fahrenheit":
            return round(celsius * 9 / 5 + 32, 4)
        elif to_unit == "kelvin":
            return round(celsius + 273.15, 4)
        return celsius


def register(api):
    api.register_tool(CalculatorTool())
    api.register_tool(UnitConverterTool())
