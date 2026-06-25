# Recipe Video Generator (MVP)

已更新：默认输出为竖屏（1080x1920），并对每一步导出为单独短片，方便直接导入剪映（Jianying）进行逐段编辑。

主要变更
- 输出分辨率：1080x1920（竖屏）
- 每个步骤输出单文件：{dish}_step_{i+1}.mp4，保存在 output/ 目录
- 文件名通过 /videos/{filename} 提供下载链接

快速使用
1. 检出 feature/recipe-video-mvp 分支：
   git fetch origin
   git checkout -b feature/recipe-video-mvp origin/feature/recipe-video-mvp

2. 填写 .env（复制 .env.template）并填写：
   ELEVENLABS_API_KEY、PEXELS_API_KEY（可选 OPENAI_API_KEY）

3. 启动（Docker 推荐）：
   docker-compose up --build

4. 在浏览器打开 demo：
   http://localhost:8000/static/index.html
   提交菜名后，任务完成会返回每个步骤的下载链接（示例：/videos/番茄炒蛋_step_1.mp4）

5. 下载到本地或手机：
   - 直接在浏览器下载到电脑
   - 或上传到云盘/使用微信文件传输/USB 传到手机

导入剪映（推荐流程）
- 每个步骤为独立短片，可以在剪映中逐段导入并进行剪切、加速、转场和字幕等精细编辑
- 已确保编码为 H.264 + AAC，码率和分辨率适合手机编辑

注意
- ElevenLabs 与 Pexels 需要 API Key。若未配置 ElevenLabs，系统会回退到 gTTS（音质较低）
- 若 Pexels 未能找到合适视频片段，会使用生成的竖屏幻灯片图片作为片段

下一步
- 若需要，我可以：
  - 在前端展示所有导出文件的打包 ZIP 下载按钮；
  - 自动把导出文件上传到 S3 / Google Drive 并返回下载链接；
  - 根据你指定的 voice_id 调整语音风格；
  - 增加每步视频中自动字幕文件（SRT）以便在剪映中快速打开字幕轨道。
