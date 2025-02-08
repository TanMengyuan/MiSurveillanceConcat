# MiSurveillanceConcat
🚀 **MiSurveillanceConcat** 是一个用于 **批量拼接小米摄像头监控视频** 的 Python 工具，基于 `FFmpeg` 进行高效合并，并支持多进程加速，极大提升拼接速度。

## ✨ 功能特点
- **自动扫描小米摄像头视频目录**，按日期归类  
- **批量合并同一天的视频**，生成单个 MP4 文件  
- **多进程并行处理**，大幅提高处理速度  
- **零损失合并**（不重新编码视频，仅转换音频）  

## 🔧 安装要求
1. **Python 3.8+**  
2. **FFmpeg**（需添加到系统环境变量）  

### 📦 安装依赖
```bash
pip install -r requirements.txt

