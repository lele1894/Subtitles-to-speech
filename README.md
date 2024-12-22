# Subtitles-to-speech
字幕转语音工具

## 功能介绍
- 支持 SRT 和 ASS 字幕文件转换为语音
- 支持多种中文语音选择
- 支持视频配音和背景音乐混合
- 实时预览语音效果
- 自动按时间轴同步音频
- 可调节语速和音量
- 支持原音频音量调节

## 环境要求
- Python 3.7+
- FFmpeg

## 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/yourusername/Subtitles-to-speech.git
cd Subtitles-to-speech
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 安装 FFmpeg
- Windows: 
  - 下载 [FFmpeg](https://www.gyan.dev/ffmpeg/builds/)
  - 添加到系统环境变量
- Linux: `sudo apt-get install ffmpeg`
- Mac: `brew install ffmpeg`

## 使用说明
1. 运行程序
```bash
python subtitle_to_speech.py
```

2. 基本操作
   - 选择视频/音频文件（可选）
   - 选择字幕文件（支持 .srt 和 .ass 格式）
   - 选择语音
   - 调整语音参数（语速、音量）
   - 调整原音频音量（如果有）
   - 点击"开始转换"

3. 高级功能
   - 试听：可以预览选择的语音效果
   - 停止���随时停止语音预览
   - 实时日志：显示处理进度和状态

4. 输出文件
   - 生成的文件保存在原始文件同目录下
   - 视频文件：原文件名_s.mp4
   - 音频文件：原文件名_s.mp3

## 注意事项
- 确保系统已正确安装 FFmpeg
- 需要网络连接以使用 Edge TTS 服务
- 转换大文件可能需要较长时间
- 建议先试听语音效果再进行转换

## 技术栈
- edge-tts: 微软 Edge 文字转语音服务
- pydub: 音频处理
- pysubs2: 字幕文件解析
- pygame: 音频播放
- tkinter: 图形界面

## 开发者
[你的名字/组织]

## License
MIT License

## 更新日志
### v1.0.0 (2024-01-xx)
- 初始版本发布
- 支持基本的字幕转语音功能
- 添加视频配音支持
- 添加语音预览功能

## 下载
从 [Releases](https://github.com/yourusername/Subtitles-to-speech/releases) 页面下载最新版本。