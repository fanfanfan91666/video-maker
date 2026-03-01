import streamlit as st
import os
import shutil
import random
from pathlib import Path
from send2trash import send2trash

# 导入所有需要的 moviepy 组件
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector

# --- 页面基础配置 ---
st.set_page_config(page_title="自动化视频剪辑工作台", layout="wide")
st.title("🎬 自动化视频处理与合成工作台")

# --- 初始化目录结构 (包含所有新文件夹) ---
ASSETS_DIR = Path("assets")
DIRS = {
    "videos": ASSETS_DIR / "videos",
    "cutted": ASSETS_DIR / "cutted_videos",
    "meme": ASSETS_DIR / "meme_clips",
    "merger": ASSETS_DIR / "merger_clips",
    "start": ASSETS_DIR / "meme_start",  # 新增：片头
    "end": ASSETS_DIR / "meme_end",  # 新增：片尾
    "pictures": ASSETS_DIR / "meme_pictures",  # 新增：背景图
    "final": ASSETS_DIR / "final_videos",  # 新增：最终输出
}

# 自动创建不存在的文件夹
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

# ================= 1. 上传与裁剪 =================
st.header("1. 上传原始视频 (带水印)")
uploaded_file = st.file_uploader("请选择需要处理的 MP4 文件", type=["mp4"])

if uploaded_file:
    raw_video_path = DIRS["videos"] / uploaded_file.name
    with open(raw_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    col1, col2 = st.columns(2)
    with col1:
        st.video(str(raw_video_path))

    with col2:
        st.subheader("2. 裁剪顶部去水印")
        crop_height = st.slider("调整裁剪高度 (像素)", min_value=0, max_value=300, value=100, step=10)
        cropped_video_path = DIRS["cutted"] / uploaded_file.name

        if st.button("✂️ 开始裁剪", use_container_width=True):
            with st.spinner("正在疯狂裁剪中，请稍候..."):
                try:
                    clip = VideoFileClip(str(raw_video_path))
                    cropped_clip = clip.cropped(y1=crop_height)
                    cropped_clip.write_videofile(
                        str(cropped_video_path),
                        codec="libx264", audio_codec="aac", preset="ultrafast", logger=None
                    )
                    clip.close()
                    st.success("✅ 裁剪成功！")
                except Exception as e:
                    st.error(f"裁剪报错: {e}")

    st.divider()

    # ================= 3. 智能分段 =================
    if cropped_video_path.exists():
        st.header("3. 智能视频分段")
        threshold = st.slider("场景切换敏感度 (数值越小越容易切碎)", min_value=10.0, max_value=100.0, value=55.0,
                              step=5.0)

        if st.button("🔪 开始智能分段"):
            with st.spinner("正在逐帧分析画面..."):
                try:
                    video = open_video(str(cropped_video_path))
                    scene_manager = SceneManager()
                    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=45))
                    scene_manager.detect_scenes(video)
                    scene_list = scene_manager.get_scene_list()

                    if scene_list:
                        split_video_ffmpeg(str(cropped_video_path), scene_list, output_dir=str(DIRS["meme"]),
                                           show_progress=False)
                        st.success(f"✅ 成功切割为 {len(scene_list)} 个独立片段！")
                    else:
                        st.warning("⚠️ 视频画面变化不明显，未能切出多个片段。")
                except Exception as e:
                    st.error(f"分段报错: {e}")

    st.divider()

# ================= 4. 片段审阅与筛选 =================
meme_files = list(DIRS["meme"].glob("*.mp4"))
if meme_files:
    st.header(f"4. 挑选可用片段 (当前共 {len(meme_files)} 个)")

    selected_files = []
    NUM_COLS = 5  # 你可以在这里自由设置每行显示几个视频

    # 核心改动：按行（Row）来生成列，强制每行平齐
    for i in range(0, len(meme_files), NUM_COLS):
        # 每次循环创建全新的一行
        cols = st.columns(NUM_COLS)
        # 往这一行的每一列里塞入视频
        for j in range(NUM_COLS):
            if i + j < len(meme_files):
                m_file = meme_files[i + j]
                with cols[j]:
                    st.video(str(m_file))
                    if st.checkbox(f"选用此片段", key=m_file.name):
                        selected_files.append(m_file)

    st.write("")  # 留点空隙

    # ================= 下方是你之前加好的操作按钮 =================


    # === 核心改动：将底部的操作区分为3列 ===
    # 比例设为 [2, 2, 2, 3]，给三个按钮同等宽度，右边留白
    action_col1, action_col2, action_col3, _ = st.columns([2, 2, 2, 3])

    # 按钮1：移入待拼接区
    with action_col1:
        if st.button("➡️ 确认选中！移入待拼接区", type="primary", use_container_width=True):
            if selected_files:
                for sf in selected_files:
                    target_path = DIRS["merger"] / sf.name
                    shutil.move(str(sf), str(target_path))
                st.success(f"🎉 成功转移 {len(selected_files)} 个视频！")
                st.rerun()
            else:
                st.warning("⚠️ 请至少勾选一个视频！")

    # 按钮2：移入回收站
    with action_col2:
        if st.button("🗑️ 垃圾片段！直接丢进回收站", type="secondary", use_container_width=True):
            if selected_files:
                trashed_count = 0
                for sf in selected_files:
                    if sf.exists():
                        try:
                            send2trash(str(sf))
                            trashed_count += 1
                        except Exception as e:
                            st.error(f"清理 {sf.name} 失败: {e}")
                st.success(f"🗑️ 成功清理，已将 {trashed_count} 个片段扔进回收站！")
                st.rerun()
            else:
                st.warning("⚠️ 请至少勾选一个视频！")

    # 按钮3：顺序拼接 (新增功能)
    with action_col3:
        if st.button("🔗 误切修复！顺序拼接选中片段", type="secondary", use_container_width=True):
            if len(selected_files) >= 2:
                with st.spinner("⚙️ 正在无缝拼接选中的片段，请稍候..."):
                    # 1. 按文件名升序排序，确保拼接顺序 (Scene-002 一定在 Scene-003 前面)
                    selected_files.sort(key=lambda x: x.name)

                    clips_to_merge = []
                    merged_clip = None
                    try:
                        # 2. 读取所有选中的视频
                        clips_to_merge = [VideoFileClip(str(sf)) for sf in selected_files]

                        # 3. 拼接它们
                        merged_clip = concatenate_videoclips(clips_to_merge, method="compose")

                        # 4. 导出为新文件 (存放在当前 meme_clips 文件夹中)
                        merged_name = f"Merged_Fixed_{random.randint(1000, 9999)}.mp4"
                        merged_path = DIRS["meme"] / merged_name

                        merged_clip.write_videofile(
                            str(merged_path),
                            codec="libx264",
                            audio_codec="aac",
                            preset="fast",
                            logger=None
                        )

                    except Exception as e:
                        st.error(f"拼接出错啦: {e}")
                    finally:
                        # 5. 【极其重要】关闭内存占用，否则 Windows 无法删除原文件
                        if merged_clip is not None:
                            try:
                                merged_clip.close()
                            except:
                                pass
                        for c in clips_to_merge:
                            try:
                                c.close()
                            except:
                                pass

                    # 6. 删除原有的碎片视频
                    if merged_path.exists():
                        trashed_count = 0
                        for sf in selected_files:
                            try:
                                send2trash(str(sf))
                                trashed_count += 1
                            except Exception as e:
                                st.warning(f"原文件 {sf.name} 删除失败 (可能被占用): {e}")

                        st.success(f"🔗 完美缝合！已生成 {merged_name} 并清理了 {trashed_count} 个原碎片。")
                        st.rerun()  # 刷新页面，显示新生成的视频

            elif len(selected_files) == 1:
                st.warning("⚠️ 拼接至少需要勾选 2 个片段哦！只选 1 个没法拼~")
            else:
                st.warning("⚠️ 请勾选需要拼接的视频片段！")

st.divider()

# ================= 5. 终极合成 =================
st.header("5. 终极合成：生成最终短视频")

# 扫描文件夹中的素材
start_files = [f.name for f in DIRS["start"].glob("*.mp4")]
end_files = [f.name for f in DIRS["end"].glob("*.mp4")]
pic_files = [f.name for f in DIRS["pictures"].iterdir() if f.suffix.lower() in ['.jpg', '.png', '.jpeg']]
merger_files = [f.name for f in DIRS["merger"].glob("*.mp4")]

# UI 选择器：左右两列布局
colA, colB = st.columns(2)

with colA:
    # 1. 片头选择与预览
    sel_start = st.selectbox("🎬 选择片头 (来自 meme_start)", start_files) if start_files else None
    if sel_start:
        # 嵌套列：按 1:1 比例分，只把视频放在左边，这样视频就只有一半大小了
        preview_col1, _ = st.columns([1, 1])
        with preview_col1:
            st.video(str(DIRS["start"] / sel_start))

    st.write("---")  # 加个细分割线区分一下

    # 2. 片尾选择与预览
    sel_end = st.selectbox("🔚 选择片尾 (来自 meme_end)", end_files) if end_files else None
    if sel_end:
        preview_col2, _ = st.columns([1, 1])
        with preview_col2:
            st.video(str(DIRS["end"] / sel_end))

    st.write("---")

    # 3. 背景图选择与预览
    sel_pic = st.selectbox("🖼️ 选择背景图 (来自 meme_pictures)", pic_files) if pic_files else None
    if sel_pic:
        preview_col3, _ = st.columns([1, 1])
        with preview_col3:
            # use_container_width 会让图片自适应我们限制好的列宽
            st.image(str(DIRS["pictures"] / sel_pic), use_container_width=True)

with colB:
    # 默认选中所有 merger_clips 里的视频
    sel_mids = st.multiselect("🔄 挑选要拼接的中间片段 (自动乱序)", merger_files,
                              default=merger_files) if merger_files else []
    st.info("💡 中间片段已在上方挑选完毕，此处无需预览。程序会自动将它们乱序拼接到片头和片尾之间。")

# 开始合成按钮
if st.button("🚀 开始渲染最终大片", type="primary", use_container_width=True):
    # 校验是否缺素材
    if not all([sel_start, sel_end, sel_pic, sel_mids]):
        st.warning("⚠️ 缺素材啦！请确保片头、片尾、背景图和中间片段都有文件可供选择。")
    else:
        with st.spinner("⚙️ 正在重新编码像素、对齐画面并生成特效，请去喝杯咖啡耐心等待..."):
            generation_success = False  # 标记是否成功生成
            output_name = f"Final_Meme_{random.randint(1000, 9999)}.mp4"
            output_path = DIRS["final"] / output_name
            temp_clips = []

            try:
                TARGET_WIDTH, TARGET_HEIGHT = 1080, 1920

                # 乱序中间片段
                random.shuffle(sel_mids)

                # 构建绝对路径列表
                final_order = [DIRS["start"] / sel_start] + [DIRS["merger"] / m for m in sel_mids] + [
                    DIRS["end"] / sel_end]
                bg_pic_path = str(DIRS["pictures"] / sel_pic)

                total_duration = 0

                # 处理每个视频片段
                for file_path in final_order:
                    clip = VideoFileClip(str(file_path))

                    # 防撕裂偶数缩放
                    ratio = min(TARGET_WIDTH / clip.w, TARGET_HEIGHT / clip.h)
                    new_w, new_h = int(clip.w * ratio) // 2 * 2, int(clip.h * ratio) // 2 * 2
                    clip_resized = clip.resized((new_w, new_h))

                    # 背景层
                    bg = (ImageClip(bg_pic_path)
                          .resized((TARGET_WIDTH, TARGET_HEIGHT))
                          .with_duration(clip.duration))

                    # 合成
                    combined = CompositeVideoClip(
                        [bg.with_position((0, 0)), clip_resized.with_position("center")],
                        size=(TARGET_WIDTH, TARGET_HEIGHT)
                    ).with_audio(clip.audio)

                    temp_clips.append(combined)
                    total_duration += clip.duration

                # 插入 0.5s 背景图中插
                insert_idx = len(temp_clips) // 2
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

                # 最终拼接与渲染
                final_video = concatenate_videoclips(temp_clips, method="chain")
                final_video.write_videofile(
                    str(output_path),
                    fps=30, codec="libx264", audio_codec="aac",
                    preset="fast", threads=4, logger=None,
                    ffmpeg_params=["-pix_fmt", "yuv420p"]
                )

                # 如果代码能顺利跑到这里，说明渲染成功
                generation_success = True

            except Exception as e:
                st.error(f"合成过程中出错: {e}")
            finally:
                # 【关键】必须先彻底关闭所有 clip 释放文件占用，才能对其进行删除/移动操作
                for c in temp_clips:
                    try:
                        c.close()
                    except:
                        pass

            # --- 渲染成功后的清理与UI展示逻辑 ---
            if generation_success:
                trashed_count = 0
                # 遍历刚才用到的所有中间片段
                for m in sel_mids:
                    file_to_trash = DIRS["merger"] / m
                    if file_to_trash.exists():
                        try:
                            # 移入系统回收站
                            send2trash(str(file_to_trash))
                            trashed_count += 1
                        except Exception as e:
                            st.warning(f"无法清理文件 {m}，它可能被其他程序占用了。")

                st.success(f"🎉 视频合成完毕！已保存为: {output_name}")
                if trashed_count > 0:
                    st.info(f"🗑️ 空间已清理：已自动将 {trashed_count} 个用过的中间片段移入电脑回收站。")

                st.balloons()  # 放个庆祝气球特效

                # 限制最终视频的播放器大小
                _, final_col, _ = st.columns([1, 2, 1])
                with final_col:
                    st.video(str(output_path))

#streamlit run web_ui.py