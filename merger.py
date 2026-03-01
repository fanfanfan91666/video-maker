import os
import random
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips

# --- 配置区域 ---
SOURCE_FOLDER = r"merger_clips"
PIC_FOLDER = r"meme_pictures"
OUTPUT_FOLDER = "final_videos"
START_VIDEO = "meme_start.mp4"  # 固定片头
END_VIDEO = "meme_end.mp4"  # 固定片尾
OUTPUT_FILE = "final_meme_compilation.mp4"

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def process_and_merge_videos(folder_path, pic_folder, output_folder):
    output_path = os.path.join(output_folder, OUTPUT_FILE)

    # 1. 随机选取背景图
    pic_files = [f for f in os.listdir(pic_folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    if not pic_files:
        print("❌ 错误：meme_pictures 文件夹内没找到图片")
        return
    bg_pic_path = os.path.join(pic_folder, random.choice(pic_files))
    print(f"🖼️ 选用背景图: {bg_pic_path}")

    # 2. 视频筛选与排序
    all_files = [f for f in os.listdir(folder_path) if f.endswith(".mp4")]

    # 排除掉固定首尾的视频，剩下的用来随机乱序
    middle_videos = [f for f in all_files if f not in [START_VIDEO, END_VIDEO]]
    random.shuffle(middle_videos)

    # 重新组合：[片头] + [乱序视频] + [片尾]
    final_order = []
    if START_VIDEO in all_files:
        final_order.append(START_VIDEO)

    final_order.extend(middle_videos)

    if END_VIDEO in all_files:
        final_order.append(END_VIDEO)
    else:
        print(f"⚠️ 警告：未找到片尾视频 {END_VIDEO}")

    temp_clips = []
    total_duration = 0

    try:
        print(f"🎬 开始处理共 {len(final_order)} 个片段...")
        for filename in final_order:
            file_path = os.path.join(folder_path, filename)
            clip = VideoFileClip(file_path)

            # 强制偶数尺寸（解决画面撕裂/位移的核心）
            ratio = min(TARGET_WIDTH / clip.w, TARGET_HEIGHT / clip.h)
            new_w = int(clip.w * ratio) // 2 * 2
            new_h = int(clip.h * ratio) // 2 * 2
            clip_resized = clip.resized((new_w, new_h))

            # 背景图层
            bg = (ImageClip(bg_pic_path)
                  .resized((TARGET_WIDTH, TARGET_HEIGHT))
                  .with_duration(clip.duration))

            # 明确层级合成
            combined = CompositeVideoClip(
                [bg.with_position((0, 0)),
                 clip_resized.with_position("center")],
                size=(TARGET_WIDTH, TARGET_HEIGHT)
            ).with_audio(clip.audio)

            temp_clips.append(combined)
            total_duration += clip.duration
            print(f" - 已合成: {filename}")

        # --- 插入 0.5s 背景图 (基于总时长中点) ---
        print(f"⏳ 总时长约 {total_duration:.2f}s，插入 0.5s 中插图片...")
        acc_time = 0
        insert_idx = len(temp_clips) // 2  # 默认中间索引

        # 寻找更精确的时间中点索引
        temp_acc = 0
        for i, clip in enumerate(temp_clips):
            temp_acc += clip.duration
            if temp_acc >= (total_duration / 2):
                insert_idx = i + 1
                break

        intermission = (ImageClip(bg_pic_path)
                        .resized((TARGET_WIDTH, TARGET_HEIGHT))
                        .with_duration(0.5))

        temp_clips.insert(insert_idx, intermission)

        # 3. 导出
        print(f"🚀 正在导出到: {output_path}")
        final_video = concatenate_videoclips(temp_clips, method="chain")

        final_video.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            ffmpeg_params=["-pix_fmt", "yuv420p"]
        )
        print(f"\n✅ 处理完成！片头：{START_VIDEO}，片尾：{END_VIDEO}")

    except Exception as e:
        print(f"\n❌ 出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        for c in temp_clips:
            try:
                c.close()
            except:
                pass


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    process_and_merge_videos(SOURCE_FOLDER, PIC_FOLDER, OUTPUT_FOLDER)