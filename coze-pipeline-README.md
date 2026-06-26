# Instructions for code.coze.cn one-click pipeline

What I committed
- .coze/pipeline.yml on branch feature/recipe-video-mvp — this pipeline builds the Docker image using the Dockerfile and starts the services via docker-compose.

What you need to do now (3 quick steps)
1) Authorize code.coze.cn to access the GitHub repo
   - Log in to https://code.coze.cn and connect your GitHub account (Authorize the app) and add the repository jiang6868668/daimaceshi.

2) Create a new pipeline from repository
   - In code.coze.cn, choose "Create Pipeline" → Select repository jiang6868668/daimaceshi → choose branch feature/recipe-video-mvp.
   - The platform will detect .coze/pipeline.yml automatically; if needed, paste the pipeline content in the UI.

3) Set environment variables (Pipeline settings / Secrets)
   - REDIS_URL = <redis connection string, required>
   - ELEVENLABS_API_KEY = <optional>
   - ELEVEN_VOICE_ID = <optional>
   - PEXELS_API_KEY = <optional>
   - OPENAI_API_KEY = <optional>
   - PORT = 8000

4) Run the pipeline
   - Click Run / Start. Wait for the build to finish and ensure logs show "web ready". The pipeline will keep running and serve the app via the platform's assigned URL.

5) Verify service
   - Open the assigned service URL and go to /static/index.html. Example:
     https://<your-pipeline-host>/static/index.html
   - Input a dish name and click Generate. Wait for worker to process and short videos to appear.

If you want, I can now:
- Attempt to trigger the pipeline (if code.coze.cn provides an API token and you paste it securely into the repo secrets) — I cannot accept tokens directly in chat, so you must add any platform tokens as secrets on the platform or GitHub.
- Or I can guide you through the code.coze.cn UI step-by-step while you click — reply "在线陪我配置".

If you run into any errors, paste the pipeline logs here and I'll debug them immediately.
