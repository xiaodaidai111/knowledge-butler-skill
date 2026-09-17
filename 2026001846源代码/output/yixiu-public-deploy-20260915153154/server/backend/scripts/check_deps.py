import cv2
import ultralytics
import dashscope

print("=== 依赖检查 ===")
print(f"cv2: {cv2.__version__ if hasattr(cv2, '__version__') else 'installed'}")
print(f"ultralytics: {ultralytics.__version__ if hasattr(ultralytics, '__version__') else 'installed'}")
print(f"dashscope: {dashscope.__version__ if hasattr(dashscope, '__version__') else 'installed'}")
print("\n所有依赖检查完成！")
