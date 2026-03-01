import sys
from pathlib import Path
from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector

# --- 文件夹配置 ---
INPUT_FOLDER = Path("cutted_videos")  # 存放待分段视频的文件夹
OUTPUT_FOLDER = Path("meme_clips")  # 分段后片段存放的文件夹


def split_meme_video(video_path, output_dir, threshold=55.0, min_scene_len=45):
    """
    智能拆分单个梗图视频
    """
    print(f"\n🎬 正在分析视频: {video_path.name} ...")

    # 1. 加载视频
    # 注意：open_video 需要字符串格式的路径
    video = open_video(str(video_path))

    # 2. 初始化场景管理器
    scene_manager = SceneManager()

    # 3. 添加检测器
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len))

    # 4. 开始检测
    scene_manager.detect_scenes(video, show_progress=True)

    # 5. 获取场景列表
    scene_list = scene_manager.get_scene_list()

    if not scene_list:
        print(f"⚠️ 未能在 {video_path.name} 中检测到明显的场景切换，跳过切割。")
        return

    print(f"✂️ 检测到 {len(scene_list)} 个片段，准备开始切割...")

    # 6. 调用 FFmpeg 进行无损切割
    # 默认输出文件名格式为：原视频名-Scene-001.mp4，不会发生覆盖冲突
    split_video_ffmpeg(str(video_path), scene_list, output_dir=str(output_dir), show_progress=True)
    print(f"✅ {video_path.name} 切割完成！")


def batch_split_videos():
    """
    批量扫描并处理文件夹中的所有视频
    """
    # 1. 确保输出文件夹存在
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # 2. 检查输入文件夹是否存在
    if not INPUT_FOLDER.exists() or not INPUT_FOLDER.is_dir():
        print(f"❌ 严重错误: 找不到输入文件夹 '{INPUT_FOLDER}'，请先创建并放入视频。")
        sys.exit(1)

    # 3. 获取所有 mp4 文件（兼容大小写后缀）
    video_files = list(INPUT_FOLDER.glob("*.[mM][pP]4"))

    if not video_files:
        print(f"❓ '{INPUT_FOLDER}' 文件夹为空，没有找到支持的视频文件。")
        return

    print(f"🔍 扫描完毕，共发现 {len(video_files)} 个视频，准备批量智能分段...\n")

    # 4. 循环处理每个视频
    success_count = 0
    for video_file in video_files:
        try:
            # 调用切割函数
            split_meme_video(video_file, OUTPUT_FOLDER)
            success_count += 1
        except Exception as e:
            print(f"❌ 处理 {video_file.name} 时发生错误: {e}")
            print("如果报错 ffmpeg not found，请确保电脑安装了 FFmpeg 并配好了环境变量。")
            continue  # 出错则跳过当前视频，继续处理下一个

    print(f"\n✨ 批量分段任务结束！成功处理: {success_count}/{len(video_files)} 个视频。")
    print(f"📂 所有生成的片段已存放在: {OUTPUT_FOLDER.absolute()}")


if __name__ == "__main__":
    batch_split_videos()