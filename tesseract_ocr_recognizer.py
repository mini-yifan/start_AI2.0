import pytesseract 
from PIL import Image 
import cv2 
import os 
import subprocess

# 自动检测Tesseract路径
def find_tesseract_path():
    # 常见的Tesseract安装路径
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    
    # 检查常见路径
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # 尝试通过which命令查找（适用于已添加到PATH的情况）
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True)
        else:  # Unix-like
            result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

# 设置Tesseract路径
tesseract_path = find_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"找到Tesseract OCR: {tesseract_path}")
else:
    print("警告: 未找到Tesseract OCR安装。请先安装Tesseract OCR软件。")
    print("安装指南:")
    print("1. Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装")
    print("2. 安装时记住安装路径，稍后可能需要手动设置")
    print("3. 如需中文识别，请在安装时选择中文语言包") 

def preprocess(img_path): 
    """灰度 → 二值化 → 去噪，提升 OCR 准确率"""
    img = cv2.imread(img_path, cv2.IMREAD_COLOR) 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    # 二值化（阈值可根据实际图片调节） 
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU) 
    # 中值滤波去噪 
    denoise = cv2.medianBlur(binary, 3) 
    return denoise 

def ocr_image(img_path, lang='chi_sim'): 
    """返回图片中的文字字符串"""
    # 检查文件是否存在
    if not os.path.exists(img_path):
        return f"错误: 文件 '{img_path}' 不存在"
    
    # 检查Tesseract是否可用
    if not tesseract_path:
        return "错误: 未找到Tesseract OCR安装。请先安装Tesseract OCR软件。\n"
        "安装步骤: https://github.com/UB-Mannheim/tesseract/wiki"
    
    try:
        # 检查文件扩展名
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        _, ext = os.path.splitext(img_path.lower())
        if ext not in valid_extensions:
            return f"错误: 文件 '{img_path}' 不是支持的图片格式"
            
        processed = preprocess(img_path) 
        # 将 OpenCV 图像转为 Pillow 对象 
        pil_img = Image.fromarray(processed) 
        text = pytesseract.image_to_string(pil_img, lang=lang) 
        return text.strip() 
    except pytesseract.TesseractNotFoundError:
        return "错误: 找不到Tesseract OCR可执行文件。请检查安装或手动设置路径。"
    except Exception as e:
        return f"OCR识别出错: {str(e)}"

if __name__ == '__main__': 
    print("=== Tesseract OCR文字识别工具 ===")
    print()
    
    # 提供手动设置路径的选项
    if not tesseract_path:
        manual_path = input("请输入Tesseract OCR的安装路径（留空跳过）: ")
        if manual_path and os.path.exists(manual_path):
            pytesseract.pytesseract.tesseract_cmd = manual_path
            tesseract_path = manual_path
            print(f"已设置Tesseract路径: {manual_path}")
    
    img_file = r'./imgs/test.png'          # 替换为你的图片路径 
    print(f"正在识别图片: {img_file}")
    result = ocr_image(img_file, lang='chi_sim+eng') 
    print("\n识别结果:")
    print(result)
    
    print("\n=== 使用提示 ===")
    print("1. 确保已安装Tesseract OCR并正确设置路径")
    print("2. 对于中英文混合识别，使用lang='chi_sim+eng'")
    print("3. 仅英文识别使用lang='eng'")
    print("4. 仅中文识别使用lang='chi_sim'")
    print("5. 如需识别其他语言，请安装对应的语言包并修改lang参数")