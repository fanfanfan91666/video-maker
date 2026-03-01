import sys
from pathlib import Path
from moviepy import VideoFileClip

# --- 核心配置区域 ---
SOURCE_FOLDER = Path("videos")  # 存放带水印原视频的文件夹
OUTPUT_FOLDER = Path("cutted_videos")  # 裁剪后视频存放的文件夹
TOP_CUT_HEIGHT = 100  # 顶部裁剪像素高度


def batch_crop_videos():
    # 1. 确保输出目录存在 (parents=True 相当于自动创建多级目录, exist_ok=True 避免已存在时报错)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # 2. 检查源目录状态
    if not SOURCE_FOLDER.exists() or not SOURCE_FOLDER.is_dir():
        print(f"❌ 严重错误: 找不到源文件夹 '{SOURCE_FOLDER}'，请确认路径是否正确。")
        sys.exit(1)

    # 3. 获取所有 MP4 文件（不区分大小写扩展名）
    video_files = list(SOURCE_FOLDER.glob("*.[mM][pP]4"))

    if not video_files:
        print(f"❓ '{SOURCE_FOLDER}' 文件夹为空，或没有找到支持的视频文件。")
        return

    print(f"🔍 扫描完毕，共发现 {len(video_files)} 个视频，准备启动批量裁剪引擎...\n")

    # 4. 遍历处理
    success_count = 0
    for file_path in video_files:
        # output_path 自动拼接为 meme_clips/原文件名
        output_path = OUTPUT_FOLDER / file_path.name
        print(f"🎬 正在处理: {file_path.name} ... ", end="", flush=True)

        clip = None
        try:
            # 加载视频 (将 Path 对象转为字符串供 MoviePy 使用)
            clip = VideoFileClip(str(file_path))

            # --- 裁剪逻辑 (MoviePy 2.0+ 语法) ---
            cropped_clip = clip.cropped(y1=TOP_CUT_HEIGHT)

            # 渲染导出
            cropped_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",  # 极速预设，专为简单裁剪优化
                threads=4,  # 释放多核 CPU 算力
                logger=None  # 屏蔽 MoviePy 内部进度条，保持终端整洁
            )
            print("✅ 成功")
            success_count += 1

        except Exception as e:
            print(f"❌ 失败 (错误信息: {e})")

        finally:
            # 【关键优化】无论成功与否，必定执行清理操作，防止文件占用和内存溢出
            if clip is not None:
                try:
                    clip.close()
                except Exception:
                    pass

    print(f"\n✨ 批量任务结束！成功处理: {success_count}/{len(video_files)} 个视频。")
    print(f"📂 干净的视频已全部存放于: {OUTPUT_FOLDER.absolute()}")


if __name__ == "__main__":
    batch_crop_videos()