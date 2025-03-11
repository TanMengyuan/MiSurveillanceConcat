import os
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from commons import load_config, get_date_from_dir


def collect_video_files(root_dir, aggregator):
    """遍历根目录，按日期收集所有 mp4 文件路径"""
    date_videos = defaultdict(list)

    for subdir, _, files in os.walk(root_dir):
        current_dir = os.path.basename(subdir)
        if len(current_dir) < 8:
            continue
        date = get_date_from_dir(current_dir, aggregator)
        for file in files:
            if file.lower().endswith('.mp4'):
                full_path = os.path.join(subdir, file)
                date_videos[date].append(full_path)

    # 按文件名排序
    for date in date_videos:
        date_videos[date].sort()

    return date_videos


def create_concat_list(video_files, list_file_path):
    """为 FFmpeg 创建 concat_list.txt 文件"""
    with open(list_file_path, 'w', encoding='utf-8') as f:
        for video in video_files:
            video = video.replace('\\', '/')  # 兼容 Windows 和 Linux
            f.write(f"file '{video}'\n")


def concatenate_videos(date, video_files, output_dir):
    """使用 FFmpeg 拼接视频，支持并行处理"""
    os.makedirs(output_dir, exist_ok=True)

    list_file = os.path.join(output_dir, f"{date}_concat_list.txt")
    create_concat_list(video_files, list_file)

    output_file = os.path.join(output_dir, f"{date}.mp4")

    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file,
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
        '-threads', '4',  # ✅ 允许 FFmpeg 并行处理
        '-preset', 'ultrafast',  # ✅ 提高编码速度
        output_file
    ]

    print(f"正在拼接 {date}，输出文件：{output_file}")

    try:
        subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace'
        )
        print(f"✅ {date} 拼接完成。\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ 拼接 {date} 失败：\n{e.stderr}\n")
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)


def main():
    # load configs
    cfg = load_config('config.ini')
    root_dir = cfg['root_dir']
    output_dir = cfg['output_dir']
    aggregator = cfg['aggregator']
    cpu_cores = cfg['cpu_cores']

    # 检查 FFmpeg 是否可用
    try:
        subprocess.run(
            ['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace'
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg 未安装或未添加到系统环境变量，请检查后重试。")
        sys.exit(1)

    # 收集视频文件
    date_videos = collect_video_files(root_dir, aggregator)

    if not date_videos:
        print("未找到 MP4 视频文件，请检查目录路径和文件格式。")
        sys.exit(1)

    # 计算最大 CPU 线程数
    max_workers = min(cpu_cores, os.cpu_count() or 1)  # 最多 4 个进程，避免过载

    # 使用多进程并行处理多个日期
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for date, video_files in date_videos.items():
            if video_files:
                futures.append(executor.submit(concatenate_videos, date, video_files, output_dir))

        # 等待所有任务完成
        for future in futures:
            future.result()

    print("🎉 所有视频拼接完成！")


if __name__ == "__main__":
    main()
