"""内置插件：时间日期工具

提供当前时间查询、日期计算、倒计时等功能。
"""
import datetime
from miniclaw.tools import BaseTool, ToolResult, ToolParameter


class CurrentTimeTool(BaseTool):
    name = "current_time"
    description = "获取当前日期和时间信息，支持指定时区"
    parameters = [
        ToolParameter(name="timezone", type="string", description="时区，如 'Asia/Shanghai'，默认为本地时间", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        timezone = kwargs.get("timezone", "").strip()
        now = datetime.datetime.now()
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

        info = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": weekday_names[now.weekday()],
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "timestamp": int(now.timestamp()),
        }

        if timezone:
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(timezone)
                tz_now = datetime.datetime.now(tz)
                info["timezone"] = timezone
                info["timezone_time"] = tz_now.strftime("%Y-%m-%d %H:%M:%S %Z")
            except ImportError:
                info["timezone_error"] = "Python 3.9+ 才支持 zoneinfo"
            except Exception as e:
                info["timezone_error"] = f"时区错误: {e}"

        output = (
            f"当前时间: {info['datetime']}\n"
            f"星期: {info['weekday']}\n"
            f"时间戳: {info['timestamp']}"
        )
        if "timezone_time" in info:
            output += f"\n{info['timezone']}: {info['timezone_time']}"

        return ToolResult(success=True, output=output, metadata=info)


class DateCalcTool(BaseTool):
    name = "date_calc"
    description = "日期计算工具，计算两个日期之间的间隔或在某个日期上加减天数"
    parameters = [
        ToolParameter(name="operation", type="string", description="操作类型: 'diff'(计算间隔) 或 'add'(加减天数)"),
        ToolParameter(name="date1", type="string", description="日期1，格式 YYYY-MM-DD"),
        ToolParameter(name="date2", type="string", description="日期2（diff模式需要），格式 YYYY-MM-DD", required=False),
        ToolParameter(name="days", type="integer", description="要加减的天数（add模式需要），负数表示减", required=False),
    ]

    def execute(self, **kwargs) -> ToolResult:
        operation = kwargs.get("operation", "").strip().lower()
        date1_str = kwargs.get("date1", "").strip()

        try:
            date1 = datetime.datetime.strptime(date1_str, "%Y-%m-%d").date()
        except ValueError:
            return ToolResult(success=False, output="", error="日期格式错误，请使用 YYYY-MM-DD")

        if operation == "diff":
            date2_str = kwargs.get("date2", "").strip()
            if not date2_str:
                return ToolResult(success=False, output="", error="diff 操作需要 date2 参数")
            try:
                date2 = datetime.datetime.strptime(date2_str, "%Y-%m-%d").date()
            except ValueError:
                return ToolResult(success=False, output="", error="date2 格式错误")
            delta = abs((date2 - date1).days)
            return ToolResult(
                success=True,
                output=f"{date1} 和 {date2} 之间相隔 {delta} 天",
                metadata={"days": delta, "date1": str(date1), "date2": str(date2)},
            )

        elif operation == "add":
            days = kwargs.get("days")
            if days is None:
                return ToolResult(success=False, output="", error="add 操作需要 days 参数")
            try:
                days = int(days)
            except (ValueError, TypeError):
                return ToolResult(success=False, output="", error="days 必须是整数")
            result_date = date1 + datetime.timedelta(days=days)
            return ToolResult(
                success=True,
                output=f"{date1} {'加上' if days >= 0 else '减去'} {abs(days)} 天后是 {result_date}",
                metadata={"result": str(result_date), "days": days},
            )

        return ToolResult(success=False, output="", error="不支持的操作类型，请使用 'diff' 或 'add'")


def register(api):
    api.register_tool(CurrentTimeTool())
    api.register_tool(DateCalcTool())
