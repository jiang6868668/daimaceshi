部署到 Render（最简单一键公开访问）

我已在 feature/recipe-video-mvp 分支添加了 render.yaml，使你能够在 Render 平台上快速部署本项目。下面是最简操作指南——只需几次点击。

最小化部署步骤（两步）
1. 在 Render 控制台（https://render.com）登录并用 GitHub 授权，选择仓库 jiang6868668/daimaceshi。
2. 在 Render 控制台点击 New → "Blueprint from Repo"（或 Create Web Service），选择该仓库并选择分支 feature/recipe-video-mvp，Render 会自动读取 render.yaml 并创建两个服务：
   - recipe-video-web（FastAPI，公开 URL，可访问 /static/index.html）
   - recipe-video-worker（后台 worker，处理生成任务）

部署后你还需要在 Render 的 Web Service 和 Worker 的 Environment 设置中添加环境变量（Environment → Environment Variables）：
- REDIS_URL = <渲染时创建的 Redis 实例连接串，例如 redis://...>
- ELEVENLABS_API_KEY = （你的 ElevenLabs API Key，可空回退 gTTS）
- ELEVEN_VOICE_ID = （可选）
- PEXELS_API_KEY = （你的 Pexels API Key，可空）
- OPENAI_API_KEY = （可选）

如何创建 Redis（Render 提供 Managed Redis）
- 在 Render 控制台点击 New → Redis，创建一个 Redis 实例，创建完成后在实例的 Dashboard 找到 Connection String（例如 redis://:password@hostname:6379/0），把它填到 REDIS_URL。

部署成功验证
- Web Service 会产生一个公开的 URL，比如 https://<your-service>.onrender.com
- 打开 https://<your-service>.onrender.com/static/index.html 即可看到 Demo 页面，输入菜名并生成视频。

如果你愿意，我可以继续帮你：
- 在分支上添加一键 ZIP 打包并在页面显示“下载全部”的功能（你点一次就能下载所有步骤） - 回复“加 ZIP”即可；
- 或者如果你允许把 Render 的控制权交给我（不推荐），我可以代为在 Render 控制台完成创建（需要你提供 Render 账户授权）。

我已经把 render.yaml 提交到 feature/recipe-video-mvp 分支，你现在只需在 Render 上将该仓库连接并用该分支创建服务（如上）。如需我一步步在线指导点击，我可以在你操作时实时协助。