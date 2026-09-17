"""MiniClaw CLI 入口

模仿 OpenClaw 的 cli/ 模块，提供命令行界面。
支持: miniclaw serve (启动网关), miniclaw chat (终端对话), miniclaw tools (查看工具), miniclaw plugins (查看插件)
"""
import sys
import os
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


def cmd_serve(args):
    from .config import MiniClawConfig
    from .gateway import MiniClawGateway

    config = MiniClawConfig.load(args.config)
    gateway = MiniClawGateway(config=config)
    gateway.start(host=args.host, port=args.port)


def cmd_chat(args):
    from .config import MiniClawConfig
    from .agent import MiniClawAgent
    from .plugins import PluginLoader
    from .tools import global_tool_registry, global_hook_runner

    config = MiniClawConfig.load(args.config)
    loader = PluginLoader(tool_registry=global_tool_registry, hook_runner=global_hook_runner)
    loader.load_builtins("miniclaw.builtins")

    agent = MiniClawAgent(config=config)

    print("\n" + "=" * 50)
    print("  MiniClaw AI 助手 v0.1.0")
    print(f"  工具: {', '.join(global_tool_registry.list_tools()) or '无'}")
    print("  输入 'q' 退出, 'tools' 查看工具, 'plugins' 查看插件")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("你: ").strip()
            if user_input.lower() in ("q", "quit", "exit"):
                print("再见!")
                break
            if not user_input:
                continue
            if user_input == "tools":
                print(f"\n可用工具: {', '.join(global_tool_registry.list_tools())}\n")
                continue
            if user_input == "plugins":
                for p in loader.list_plugins():
                    status = "✅" if p["loaded"] else "❌"
                    print(f"  {status} {p['name']} v{p['version']}")
                print()
                continue

            print("思考中...", end="\r")
            result = agent.process(user_input)
            print("              ", end="\r")
            print(f"AI: {result.reply}")
            if result.steps:
                for step in result.steps:
                    if step.step_type == "tool_call":
                        status = "✅" if step.tool_result and step.tool_result.success else "❌"
                        print(f"  {status} 工具: {step.tool_name}")
        except KeyboardInterrupt:
            print("\n再见!")
            break


def cmd_tools(args):
    from .plugins import PluginLoader
    from .tools import global_tool_registry, global_hook_runner

    loader = PluginLoader(tool_registry=global_tool_registry, hook_runner=global_hook_runner)
    loader.load_builtins("miniclaw.builtins")

    tools = global_tool_registry.get_all_tools()
    if not tools:
        print("没有可用工具")
        return

    print(f"\nMiniClaw 工具列表 ({len(tools)} 个):\n")
    for tool in tools:
        print(f"  🔧 {tool.name}")
        print(f"     描述: {tool.description}")
        if tool.parameters:
            for p in tool.parameters:
                req = "必填" if p.required else "可选"
                print(f"     - {p.name} ({p.type}, {req}): {p.description}")
        print()


def cmd_plugins(args):
    from .plugins import PluginLoader
    from .tools import global_tool_registry, global_hook_runner

    loader = PluginLoader(tool_registry=global_tool_registry, hook_runner=global_hook_runner)
    loader.load_builtins("miniclaw.builtins")

    plugins = loader.list_plugins()
    if not plugins:
        print("没有已加载的插件")
        return

    print(f"\nMiniClaw 插件列表 ({len(plugins)} 个):\n")
    for p in plugins:
        status = "✅ 已加载" if p["loaded"] else f"❌ 错误: {p['error']}"
        print(f"  {status} {p['name']} v{p['version']}")
        if p.get("description"):
            print(f"     {p['description']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="miniclaw",
        description="MiniClaw - 微型插件驱动 AI 网关",
    )
    parser.add_argument("--config", "-c", help="配置文件路径", default=None)
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    serve_parser = subparsers.add_parser("serve", help="启动网关服务器")
    serve_parser.add_argument("--host", "-H", default=None, help="监听地址")
    serve_parser.add_argument("--port", "-p", type=int, default=None, help="监听端口")

    subparsers.add_parser("chat", help="终端对话模式")
    subparsers.add_parser("tools", help="查看可用工具")
    subparsers.add_parser("plugins", help="查看已加载插件")

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "tools":
        cmd_tools(args)
    elif args.command == "plugins":
        cmd_plugins(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
