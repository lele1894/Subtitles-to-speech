import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pysubs2
import os
import asyncio
import edge_tts
from pydub import AudioSegment
import tempfile
import time
import sys
import subprocess
from pygame import mixer
import threading
from datetime import datetime
from queue import Queue
import gc

class SubtitleToSpeech:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("字幕转语音工具")
        self.window.withdraw()  # 先隐藏窗口
        
        # 设置图标
        try:
            self.window.iconbitmap("app.ico")
        except:
            print("无法加载图标文件")
        
        # 设置窗口大小和位置
        self.window.geometry("850x850")
        self.window.minsize(850, 850)
        self.center_window(850, 850)
        
        # 获取可用的语音列表
        self.voices = self.get_voice_list()
        
        # 初始化音频播放器
        mixer.init()
        self.is_playing = False
        
        # 创建界面元素
        self.create_widgets()
        
        # 显示窗口
        self.window.deiconify()
        
        # 添加日志队列和更新标志
        self.log_queue = Queue()
        self.is_updating_log = False
        
        # 启动日志更新循环
        self.window.after(100, self._process_log_queue)
    
    def get_voice_list(self):
        # 运行异步函数获取声音列表
        return asyncio.run(edge_tts.list_voices())
    
    def create_widgets(self):
        # 设置主题色和样式
        bg_color = "#f0f0f0"
        frame_bg = "#ffffff"
        self.window.configure(bg=bg_color)
        
        # 主器
        main_container = tk.Frame(self.window, bg=bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 顶部标题
        title_frame = tk.Frame(main_container, bg=bg_color)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        title_label = tk.Label(
            title_frame,
            text="字幕转语音工具",
            font=("Microsoft YaHei UI", 16, "bold"),
            bg=bg_color
        )
        title_label.pack()
        
        # 左右面板容器
        panels_frame = tk.Frame(main_container, bg=bg_color)
        panels_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 包含所有控制组件
        left_frame = tk.Frame(panels_frame, bg=bg_color, width=400)  # 在Frame创建时设置宽度
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_frame.pack_propagate(False)  # 防止子控件影响Frame大小
        
        # 文件选择区域
        file_frame = tk.LabelFrame(
            left_frame,
            text=" 文件选择 ",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=frame_bg,
            relief=tk.GROOVE
        )
        file_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # 视频/音频选择
        media_frame = tk.Frame(file_frame, bg=frame_bg)
        media_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.select_media_btn = tk.Button(
            media_frame,
            text="选择视频/音频",
            command=self.select_media,
            width=15,
            relief=tk.GROOVE,
            cursor="hand2"
        )
        self.select_media_btn.pack(side=tk.LEFT)
        
        self.media_label = tk.Label(
            media_frame,
            text="未选择文件",
            anchor='w',
            bg=frame_bg
        )
        self.media_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 字幕文件选择
        subtitle_frame = tk.Frame(file_frame, bg=frame_bg)
        subtitle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.select_btn = tk.Button(
            subtitle_frame,
            text="选择字幕文件",
            command=self.select_file,
            width=15,
            relief=tk.GROOVE,
            cursor="hand2"
        )
        self.select_btn.pack(side=tk.LEFT)
        
        self.file_label = tk.Label(
            subtitle_frame,
            text="未选择文件",
            anchor='w',
            bg=frame_bg
        )
        self.file_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 语音设置区域 - 增加高度
        voice_frame = tk.LabelFrame(
            left_frame,  # 改为left_frame
            text=" 语音设置 ",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=frame_bg,
            relief=tk.GROOVE
        )
        voice_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # 语音选择列表 - 增加高度
        voice_list_frame = tk.Frame(voice_frame, bg=frame_bg)
        voice_list_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.voice_list = tk.Listbox(
            voice_list_frame,
            height=12,  # 增加高度
            selectmode=tk.SINGLE,
            font=("Microsoft YaHei UI", 9)
        )
        self.voice_list.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 添加
        scrollbar = tk.Scrollbar(voice_list_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.voice_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.voice_list.yview)
        
        # 添加语音选项
        voice_choices = self._get_voice_choices()
        for voice in voice_choices:
            self.voice_list.insert(tk.END, voice)
        self.voice_list.selection_set(0)  # 默认选择第一个
        
        # 试听按钮区域
        preview_frame = tk.Frame(voice_frame, bg=frame_bg)
        preview_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.preview_btn = tk.Button(
            preview_frame,
            text="试听语音",
            command=self.preview_voice,
            relief=tk.GROOVE,
            cursor="hand2",
            width=10
        )
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加停止按钮
        self.stop_btn = tk.Button(
            preview_frame,
            text="停止",
            command=self.stop_preview,
            relief=tk.GROOVE,
            cursor="hand2",
            width=10,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 语音参数设置
        params_frame = tk.LabelFrame(
            left_frame,
            text=" 语音参数 ",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=frame_bg,
            relief=tk.GROOVE
        )
        params_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # 语速设置
        rate_frame = tk.Frame(params_frame, bg=frame_bg)
        rate_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(rate_frame, text="语速:", bg=frame_bg).pack(side=tk.LEFT)
        
        self.rate_var = tk.StringVar(value="+0%")
        self.rate_menu = ttk.Combobox(
            rate_frame,
            textvariable=self.rate_var,
            values=["-50%", "-25%", "+0%", "+25%", "+50%"],
            width=10,
            state="readonly"
        )
        self.rate_menu.pack(side=tk.LEFT, padx=5)
        
        # 音量设置
        volume_frame = tk.Frame(params_frame, bg=frame_bg)
        volume_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(volume_frame, text="音量:", bg=frame_bg).pack(side=tk.LEFT)
        
        self.volume_var = tk.StringVar(value="+0%")
        self.volume_menu = ttk.Combobox(
            volume_frame,
            textvariable=self.volume_var,
            values=["-50%", "-25%", "+0%", "+25%", "+50%"],
            width=10,
            state="readonly"
        )
        self.volume_menu.pack(side=tk.LEFT, padx=5)
        
        # 音量控制区域
        volume_frame = tk.LabelFrame(
            left_frame,  # 改为left_frame
            text=" 音频设置 ",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=frame_bg,
            relief=tk.GROOVE
        )
        volume_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # 背景音量
        self.bg_volume_scale = tk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            label="原始音频音量(%)",
            bg=frame_bg,
            highlightthickness=0
        )
        self.bg_volume_scale.set(30)
        self.bg_volume_scale.pack(fill=tk.X, padx=10, pady=5)
        
        # 开始转换按钮
        self.convert_btn = tk.Button(
            left_frame,  # 改为left_frame
            text="开始转换",
            command=self.start_conversion,
            width=20,
            height=2,
            relief=tk.GROOVE,
            cursor="hand2",
            bg="#4CAF50",
            fg="white",
            font=("Microsoft YaHei UI", 9, "bold")
        )
        self.convert_btn.pack(pady=10)
        
        # 转换按钮下方添加进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            left_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))
        
        # 右侧面板 - 只包含日志显示
        right_frame = tk.Frame(panels_frame, bg=bg_color)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  # expand=True 使其占用剩余空间
        
        # 日志显示区域
        log_frame = tk.LabelFrame(
            right_frame,
            text=" 处理日志 ",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=frame_bg,
            relief=tk.GROOVE
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            bg=frame_bg,
            relief=tk.FLAT,
            font=("Microsoft YaHei UI", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 日志滚动条
        log_scrollbar = tk.Scrollbar(log_frame, orient="vertical")
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.config(command=self.log_text.yview)
    
    def _get_voice_choices(self):
        """获取语音选项"""
        voice_choices = []
        for v in self.voices:
            try:
                if 'zh' in v['Locale'].lower():
                    name = v.get('FriendlyName', v.get('Name', ''))
                    short_name = v.get('ShortName', '')
                    voice_choices.append(f"{short_name} ({name})")
            except Exception as e:
                print(f"处理语音信息时出错: {str(e)}")
                continue
        
        return voice_choices if voice_choices else ["未找到中文语音"]
    
    async def convert_text_to_speech(self, text, output_file, voice, rate, volume):
        max_retries = 3  # 最大重试次数
        retry_delay = 1  # 重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(
                    text, 
                    voice,
                    rate=rate,
                    volume=volume
                )
                await communicate.save(output_file)
                return  # 成功则直接返回
                
            except Exception as e:
                if attempt < max_retries - 1:  # 如果还有重试机会
                    print(f"语音生成失败{retry_delay}秒后重试: {str(e)}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 增加重试延迟
                else:  # 最后一次尝试失败
                    raise  # 重新抛出异常
    
    def _start_conversion_thread(self):
        """在新线程中启动转换过程"""
        self.convert_btn.config(state='disabled')
        
        # 创建并启动转换线程
        convert_thread = threading.Thread(
            target=lambda: asyncio.run(self.convert_subtitle()),
            daemon=True
        )
        convert_thread.start()
        
        # 定期检查线程状态并恢复按钮
        def check_thread():
            if convert_thread.is_alive():
                self.window.after(100, check_thread)
            else:
                self.convert_btn.config(state='normal')
        
        self.window.after(100, check_thread)
    
    def start_conversion(self):
        """启动转换过程"""
        self._start_conversion_thread()
    
    async def convert_subtitle(self):
        total_start_time = datetime.now()
        
        subtitle_path = self.file_label.cget("text")
        media_path = self.media_label.cget("text")
        
        if subtitle_path == "未选择文件":
            self.show_message("错误", "请先选择字幕文件!")
            return
        
        # 检查是否选择了视频文件
        is_video = media_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))
        
        # 创建一个主临时目录
        with tempfile.TemporaryDirectory() as main_temp_dir:
            try:
                # 加载字幕文件
                try:
                    subs = pysubs2.load(subtitle_path)
                except Exception as e:
                    self.show_message("错误", f"读取字幕文件失败: {str(e)}")
                    return
                
                # 果选择了视频，提取音频
                if is_video:
                    extract_start = datetime.now()
                    self.update_log("正在提取视频音频...")
                    
                    # 在主临时目录中创建音频文件
                    temp_audio = os.path.join(main_temp_dir, "extracted_audio.mp3")
                    
                    # 使用ffmpeg提取音频
                    command = [
                        'ffmpeg',
                        '-i', media_path,
                        '-vn',  # 不处理视频
                        '-acodec', 'libmp3lame',
                        '-q:a', '0',  # 最高质量
                        '-y',  # 覆盖已存在的文件
                        temp_audio
                    ]
                    
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        # 提取成功，更新音频路径
                        audio_path = temp_audio
                    else:
                        raise Exception(f"提取音频失败: {stderr.decode()}")
                    
                    self.update_log(f"✓ 音频提取完成 (耗时: {format_time_delta(extract_start)})")
                else:
                    audio_path = media_path
                
                # 获选择的语音
                voice_full = self.voice_list.get(self.voice_list.curselection())
                voice = voice_full.split()[0] if voice_full else None
                if not voice:
                    self.show_message("错误", "请选择语音!")
                    return
                
                rate = self.rate_var.get()
                volume = self.volume_var.get()
                
                # 创建语音片段的临时目录
                speech_temp_dir = os.path.join(main_temp_dir, "speech_segments")
                os.makedirs(speech_temp_dir, exist_ok=True)
                
                # 转换字幕
                convert_start = datetime.now()
                total = len(subs)
                self.update_log(f"开始转换 {total} 条字幕...")
                
                audio_segments = []
                
                # 重置进度条
                self.progress_var.set(0)
                
                for i, line in enumerate(subs):
                    text = line.text.strip()
                    if not text:
                        continue
                        
                    try:
                        # 生成语音文件
                        temp_file = os.path.join(speech_temp_dir, f"speech_{i+1}.mp3")
                        try:
                            await self.convert_text_to_speech(text, temp_file, voice, rate, volume)
                        except Exception as e:
                            self.update_log(f"警告: 转换失败，正在重试...")
                            continue
                        
                        # 等待文件生成完成
                        while not os.path.exists(temp_file):
                            await asyncio.sleep(0.1)
                        
                        # 读取音频片段
                        audio_segment = AudioSegment.from_mp3(temp_file)
                        
                        # 调整音频长度以匹配字幕持续时间
                        subtitle_duration = line.end - line.start
                        
                        if len(audio_segment) > subtitle_duration:
                            speed_factor = len(audio_segment) / subtitle_duration
                            audio_segment = audio_segment.speedup(playback_speed=speed_factor)
                        elif len(audio_segment) < subtitle_duration:
                            silence_duration = subtitle_duration - len(audio_segment)
                            audio_segment = audio_segment + AudioSegment.silent(duration=silence_duration)
                        
                        audio_segment = audio_segment[0:subtitle_duration]
                        
                        audio_segments.append({
                            'start': line.start,
                            'audio': audio_segment,
                            'text': text
                        })
                        
                    except Exception as e:
                        self.update_log(f"⚠️ 转换失败: {str(e)}")
                        continue
                    
                    # 只更新进度条，不显示进度信息
                    self.progress_var.set((i + 1) / total * 100)
                
                self.update_log(f"✓ 字幕转换完成 (耗时: {format_time_delta(convert_start)})")
                
                try:
                    if not audio_segments:
                        raise Exception("没有成功转换任何音频片段")
                    
                    # 创建完整的配音音频
                    final_duration = max(segment['start'] + len(segment['audio']) 
                                      for segment in audio_segments) + 1000
                    dubbed_audio = AudioSegment.silent(duration=final_duration)
                    
                    # 合并所有配音片段
                    for segment in audio_segments:
                        dubbed_audio = dubbed_audio.overlay(
                            segment['audio'], 
                            position=segment['start'],
                            gain_during_overlay=-1  # 轻微降低重叠部分的音量
                        )
                    
                    # 创建输出目录
                    output_dir = os.path.join(os.path.dirname(subtitle_path), "speech_output")
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    # 如果有背景音频，行混音
                    if audio_path and audio_path != "未选择文件":
                        mix_start = datetime.now()
                        self.update_log("正在混合音频...")
                        
                        # 读取背景音频
                        background_audio = AudioSegment.from_file(
                            audio_path,
                            format="mp3",
                            parameters=["-bufsize", "10M"]
                        )
                        
                        # 调整背景音量
                        bg_volume = self.bg_volume_scale.get() / 100.0
                        background_audio = background_audio - (20 * (1 - bg_volume))
                        
                        # 确保背景音频足够长
                        if len(background_audio) < len(dubbed_audio):
                            times_to_repeat = (len(dubbed_audio) // len(background_audio)) + 1
                            background_audio = background_audio * times_to_repeat
                        
                        # 裁剪到需要的长度
                        background_audio = background_audio[:len(dubbed_audio)]
                        
                        # 合并音频
                        final_audio = background_audio.overlay(dubbed_audio)
                    else:
                        final_audio = dubbed_audio
                    
                    # 生成输出件名（原始文件所在目录）
                    input_name = os.path.splitext(media_path)[0]  # 获取带扩展名的原始文件名
                    
                    # 保存音频文件
                    audio_output = f"{input_name}_s.mp3"
                    final_audio.export(
                        audio_output,
                        format="mp3",
                        parameters=["-q:a", "0", "-ar", "44100", "-b:a", "192k"]
                    )
                    
                    # 如果是视频文件，创建新的视频
                    if is_video:
                        video_start = datetime.now()
                        self.update_log("正在生成最终视频...")
                        
                        # 使用原始文件名加上_s后缀
                        output_video = f"{input_name}_s.mp4"
                        
                        command = [
                            'ffmpeg',
                            '-i', media_path,  # 原视频
                            '-i', audio_output,  # 混合后的音频
                            '-c:v', 'copy',  # 复制视频流
                            '-c:a', 'aac',  # 音频编码
                            '-strict', 'experimental',
                            '-map', '0:v:0',  # 使用第一个输入的视频流
                            '-map', '1:a:0',  # 使用第二个输入的音频流
                            '-y',  # 覆盖已存在的文件
                            output_video
                        ]
                        
                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        stdout, stderr = process.communicate()
                        
                        if process.returncode != 0:
                            raise Exception(f"生成视频失败: {stderr.decode()}")
                    
                    self.update_log(f"✓ 视频生成完成 (耗时: {format_time_delta(video_start)})")
                    
                    # 显示总耗时
                    self.update_log(f"\n✨ 全部处理完成！总耗时: {format_time_delta(total_start_time)}")
                    
                    if is_video:
                        self.show_message("完成", f"视频转换完成!\n保存为: {output_video}\n总耗时: {format_time_delta(total_start_time)}")
                    else:
                        self.show_message("完成", f"音频转换完成!\n保存为: {audio_output}\n总耗时: {format_time_delta(total_start_time)}")
                    
                except Exception as e:
                    self.show_message("错误", f"处理失败: {str(e)}")
                    return
                
            except Exception as e:
                self.show_message("错误", f"转换失败: {str(e)}")
                return
        
        # 完成后清理临时文件
        self.cleanup_temp_files()
        
        # 在处理大量音频片段后主动进行垃圾回收
        gc.collect()
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("字幕文件", "*.srt;*.ass"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.file_label.config(text=file_path)
    
    def select_media(self):
        """选择视频或音频文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("媒体文件", "*.mp4;*.mkv;*.avi;*.mov;*.mp3;*.wav;*.m4a;*.aac"),
                ("视频文件", "*.mp4;*.mkv;*.avi;*.mov"),
                ("音频文件", "*.mp3;*.wav;*.m4a;*.aac"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.media_label.config(text=file_path)
    
    def stop_preview(self):
        """停止试听"""
        if self.is_playing:
            mixer.music.stop()
            self.is_playing = False
            self.preview_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def play_preview(self, preview_file):
        """在新线程中播放预览音频"""
        try:
            mixer.music.load(preview_file)
            mixer.music.play()
            self.is_playing = True
            
            # 等待播放完成
            while mixer.music.get_busy():
                time.sleep(0.1)
            
            # 播放完成后恢复按钮状态
            self.is_playing = False
            self.preview_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            
        except Exception as e:
            print(f"播放音频失败: {str(e)}")
            self.preview_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def preview_voice(self):
        """试听当前选择的语音"""
        selection = self.voice_list.curselection()
        if not selection:
            self.show_message("错误", "请先选择语音!")
            return
        
        voice_full = self.voice_list.get(selection[0])
        voice = voice_full.split()[0]
        
        # 禁试听按钮，启用停止按钮
        self.preview_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.preview_btn.config(text="生成中...")
        self.window.update()
        
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                preview_file = os.path.join(temp_dir, "preview.mp3")
                
                # 获取当前设置
                rate = self.rate_var.get()
                volume = self.volume_var.get()
                
                # 生成语音
                asyncio.run(self.convert_text_to_speech(
                    "你好，我是你的语音模特。", 
                    preview_file,
                    voice,
                    rate,
                    volume
                ))
                
                # 等待文件生成并确认文件存在
                max_wait = 50
                while not os.path.exists(preview_file) and max_wait > 0:
                    time.sleep(0.1)
                    max_wait -= 1
                
                if os.path.exists(preview_file) and os.path.getsize(preview_file) > 0:
                    # 复制到临时文件
                    temp_preview = os.path.join(tempfile.gettempdir(), "voice_preview.mp3")
                    import shutil
                    shutil.copy2(preview_file, temp_preview)
                    
                    # 在新线程中播放音频
                    self.preview_btn.config(text="播放中...")
                    threading.Thread(
                        target=self.play_preview,
                        args=(temp_preview,),
                        daemon=True
                    ).start()
                else:
                    raise Exception("生成预览音频失败")
        except Exception as e:
            self.show_message("错误", f"试听失败: {str(e)}")
            self.preview_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.preview_btn.config(text="试听语音")
    
    def update_log(self, message):
        """将日志消息添加到队列"""
        self.log_queue.put(message)
    
    def run(self):
        try:
            self.window.mainloop()
        finally:
            # 清理资源
            self.cleanup_temp_files()
            # 确保所有线程都已终止
            for thread in threading.enumerate():
                if thread != threading.current_thread():
                    thread.join(timeout=1.0)
            
            # 关闭事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.stop()
                if not loop.is_closed():
                    loop.close()
            except Exception:
                pass
    
    def cleanup_temp_files(self):
        """清理临时文件和文件夹"""
        try:
            temp_dir = os.path.join(os.path.dirname(self.file_label.cget("text")), "speech_output")
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")
    
    def center_window(self, width, height):
        """使窗口在屏幕中居中"""
        # 获取屏幕宽度和高度
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 计算窗口位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 设置窗口位置
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_message(self, title, message):
        """显示消息到日志"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        if title == "错误":
            self.update_log(f"[{timestamp}] ❌ {message}")
        elif title == "完成":
            self.update_log(f"[{timestamp}] ✅ {message}")
        else:
            self.update_log(f"[{timestamp}] ℹ️ {message}")
        self.window.update()
    
    def _process_log_queue(self):
        """处理日志队列"""
        if not self.is_updating_log:
            self.is_updating_log = True
            while not self.log_queue.empty():
                message = self.log_queue.get()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
            self.is_updating_log = False
        
        # 继续循环
        self.window.after(100, self._process_log_queue)

def format_time_delta(start_time):
    """计算并格式化耗时"""
    delta = datetime.now() - start_time
    seconds = delta.total_seconds()
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"

if __name__ == "__main__":
    app = SubtitleToSpeech()
    app.run() 