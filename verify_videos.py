import os
import subprocess
import json
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict


def get_video_info(video_path):
    """
    获取视频的时长、分辨率、音频编码等信息
    """
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path
    ]

    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace', check=True
        )
        video_info = json.loads(result.stdout)
    except subprocess.CalledProcessError:
        print(f"❌ 获取视频信息失败: {video_path}")
        return None
    
    return video_info

def analyze_videos(video_list):
    """
    分析所有原始视频，计算总时长，并记录分辨率和音频信息
    """
    total_duration = 0
    resolutions = set()
    audio_codecs = set()

    for video in video_list:
        info = get_video_info(video)
        if info:
            try:
                duration = float(info["format"]["duration"])
                total_duration += duration

                for stream in info["streams"]:
                    if stream["codec_type"] == "video":
                        width = stream.get("width", 0)
                        height = stream.get("height", 0)
                        resolutions.add(f"{width}x{height}")

                    if stream["codec_type"] == "audio":
                        audio_codec = stream.get("codec_name", "unknown")
                        audio_codecs.add(audio_codec)
            except KeyError:
                print(f"⚠️ 解析 {video} 失败，可能文件损坏！")

    return total_duration, resolutions, audio_codecs

def verify_video_integrity(date, original_videos, merged_video):
    """
    验证拼接前后的视频是否一致
    """
    print(f"\n🔍 正在验证 {date} 的视频拼接完整性...")

    original_duration, original_res, original_audio = analyze_videos(original_videos)
    merged_info = get_video_info(merged_video)

    if not merged_info:
        print(f"❌ 无法获取拼接后 {date} 的视频信息，可能拼接失败。")
        return False

    merged_duration = float(merged_info["format"]["duration"])
    merged_res = set()
    merged_audio = set()

    for stream in merged_info["streams"]:
        if stream["codec_type"] == "video":
            width = stream.get("width", 0)
            height = stream.get("height", 0)
            merged_res.add(f"{width}x{height}")

        if stream["codec_type"] == "audio":
            merged_audio.add(stream.get("codec_name", "unknown"))

    # 允许最多 1 秒误差（避免 FFmpeg 可能带来的微小时长误差）
    duration_diff = abs(original_duration - merged_duration)

    print("\n====== 🎯 拼接完整性检查结果 ======")
    print(f"📌 原始视频总时长: {original_duration:.2f} 秒")
    print(f"📌 拼接后视频时长: {merged_duration:.2f} 秒")
    print(f"📌 原始视频分辨率: {original_res}")
    print(f"📌 拼接后视频分辨率: {merged_res}")
    print(f"📌 原始音频编码: {original_audio}")
    print(f"📌 拼接后音频编码: {merged_audio}")

    if duration_diff > 1:
        print("❌ ⚠️ 拼接后时长与原始视频不匹配，可能有丢失！")
        return False

    if original_res != merged_res:
        print("❌ ⚠️ 拼接后的视频分辨率不匹配！")
        return False

    if original_audio != merged_audio:
        print("⚠️ 拼接后音频编码可能变化，但可能仍可播放。")

    print(f"✅ {date} 拼接完整性检查通过！\n")
    return True

def main():
    root_dir = r"G:\监控视频"
    output_dir = r"G:\拼接后视频"

    # 收集所有日期的视频
    date_videos = defaultdict(list)

    for subdir, _, files in os.walk(root_dir):
        current_dir = os.path.basename(subdir)
        if len(current_dir) < 8:
            continue
        date = current_dir[:8]
        for file in files:
            if file.lower().endswith('.mp4'):
                full_path = os.path.join(subdir, file)
                date_videos[date].append(full_path)

    if not date_videos:
        print("❌ 未找到 MP4 视频文件，无法验证！")
        return

    max_workers = min(4, os.cpu_count() or 1)  # 限制最多 4 个进程，防止 CPU 过载

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for date, video_files in date_videos.items():
            merged_video = os.path.join(output_dir, f"{date}.mp4")
            if os.path.exists(merged_video):
                futures.append(executor.submit(verify_video_integrity, date, video_files, merged_video))
            else:
                print(f"⚠️ 未找到拼接后的视频 {merged_video}，跳过验证。")

        # 等待所有任务完成
        for future in futures:
            future.result()

    print("🎉 所有视频验证完成！")

if __name__ == "__main__":
    main()
