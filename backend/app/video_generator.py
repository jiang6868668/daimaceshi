"""
Core job logic:
- generate recipe (simple fallback or use OpenAI if OPENAI_API_KEY provided)
- for each step: try to find a Pexels video; if not found, generate a slide (Pillow)
- generate TTS with ElevenLabs (if key present) or fallback to gTTS
- compose clips with MoviePy and save per-step mp4 files to output/

Changes in this file (compared to MVP):
- Default output target is vertical 1080x1920
- Export each step as an individual short clip: {dish}_step_{i+1}.mp4
- Ensure clips are letterboxed/padded to exact 1080x1920 using a black background
"""

import os
import json
import time
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any
from . import config
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    ColorClip,
)
from gtts import gTTS

# optional: OpenAI for recipe generative prompts
try:
    import openai
    openai.api_key = config.OPENAI_API_KEY
    _HAS_OPENAI = bool(config.OPENAI_API_KEY)
except Exception:
    _HAS_OPENAI = False

OUTPUT_DIR = Path(config.OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Target vertical output size for Jianying (剪映)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def generate_video_job(dish: str):
    """
    Entrypoint for RQ job.
    Returns dict with video_paths on success.
    """
    try:
        recipe = generate_recipe(dish)
        step_clips = []
        audio_files = []
        for i, step in enumerate(recipe['steps']):
            text = step.get('text') or f"步骤 {i+1}"
            est = max(3, int(step.get('est_seconds', 5)))
            # try Pexels
            clip_path = try_get_pexels_clip(text, est)
            if clip_path:
                step_clips.append({"path": clip_path, "est_seconds": est, "type": "video"})
            else:
                img_path = create_slide_image(f"{i+1}. {text}")
                step_clips.append({"path": img_path, "est_seconds": est, "type": "image"})
            audio_path = tts_text_to_file(text, i)
            audio_files.append(audio_path)

        # produce per-step clips
        produced = []
        for i, sc in enumerate(step_clips):
            audio_path = audio_files[i]
            step_fn = f"{dish.replace(' ', '_')}_step_{i+1}.mp4"
            out_path = OUTPUT_DIR / step_fn
            compose_single_clip(sc, audio_path, str(out_path))
            produced.append(f"/videos/{step_fn}")

        return {"video_paths": produced}
    except Exception as e:
        traceback.print_exc()
        raise


def generate_recipe(dish: str) -> Dict[str, Any]:
    """
    Generate a simple recipe structure.
    If OpenAI is configured, attempt to use it to create JSON structure (title, steps).
    Otherwise return a fallback basic recipe (demo).
    """
    if _HAS_OPENAI:
        prompt = f"""为菜名'{dish}'生成简短菜谱 JSON，包含：
title, ingredients(list of strings), steps(list of {{text, est_seconds}})
只输出纯 JSON"""
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini" if hasattr(openai, 'ChatCompletion') else "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception:
            # fallthrough to simple
            pass

    steps = [
        {"text": "准备食材，洗净并切好。", "est_seconds": 5},
        {"text": "热锅热油，炒香佐料。", "est_seconds": 6},
        {"text": f"加入主要食材，翻炒至熟。", "est_seconds": 8},
        {"text": "调味并装盘，完成上桌。", "est_seconds": 5},
    ]
    return {
        "title": dish,
        "ingredients": ["若干主料", "适量调料"],
        "steps": steps
    }


def try_get_pexels_clip(query: str, duration: int) -> str:
    """
    Search Pexels videos for the query and download a short clip.
    Returns local file path or empty string on failure.
    """
    if not config.PEXELS_API_KEY:
        return ""
    try:
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": config.PEXELS_API_KEY}
        params = {"query": query, "per_page": 3}
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        videos = data.get("videos", [])
        if not videos:
            return ""
        video = videos[0]
        files = video.get("video_files", [])
        if not files:
            return ""
        files_sorted = sorted(files, key=lambda f: f.get("width", 0))
        chosen = files_sorted[min(1, len(files_sorted)-1)]
        download_url = chosen.get("link")
        if not download_url:
            return ""
        tmp = Path(tempfile.mkdtemp()) / f"clip_{int(time.time())}.mp4"
        with requests.get(download_url, stream=True, timeout=60) as r2:
            r2.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r2.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return str(tmp)
    except Exception:
        return ""


def create_slide_image(text: str, size=(TARGET_WIDTH, TARGET_HEIGHT), bg=(250, 245, 240)) -> str:
    """
    Create a simple slide image with centered text.
    Returns filepath.
    """
    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except Exception:
        font = ImageFont.load_default()
    margin = 60
    # simple wrap
    lines = []
    words = text.split(' ')
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.getsize(test)[0] <= size[0] - 2 * margin:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # vertical centering
    total_h = sum([font.getsize(line)[1] + 8 for line in lines])
    y = (size[1] - total_h) // 2
    for line in lines:
        w, h = font.getsize(line)
        x = (size[0] - w) // 2
        draw.text((x, y), line, fill=(30, 30, 30), font=font)
        y += h + 8
    tmp = Path(tempfile.mkdtemp()) / f"slide_{int(time.time())}.png"
    img.save(tmp)
    return str(tmp)


def tts_text_to_file(text: str, index: int) -> str:
    """
    Generate TTS audio file for given text.
    Tries ElevenLabs if API key present, otherwise fallback to gTTS.
    Returns path to mp3 file.
    """
    if config.ELEVENLABS_API_KEY and config.ELEVEN_VOICE_ID:
        try:
            return elevenlabs_tts(text, index)
        except Exception:
            pass
    tmp = Path(tempfile.mkdtemp()) / f"tts_{index}.mp3"
    tts = gTTS(text, lang='zh-cn')
    tts.save(str(tmp))
    return str(tmp)


def elevenlabs_tts(text: str, index: int) -> str:
    """
    Call ElevenLabs TTS endpoint and write to mp3.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.75}
    }
    resp = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
    resp.raise_for_status()
    tmp = Path(tempfile.mkdtemp()) / f"tts_{index}.mp3"
    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return str(tmp)


def compose_single_clip(sc: Dict[str, Any], audio_path: str, output_path: str):
    """
    Compose a single step clip (video or image) with provided audio and export to output_path.
    Ensures final resolution is TARGET_WIDTH x TARGET_HEIGHT (1080x1920) with letterboxing on black background.
    """
    est = sc.get('est_seconds', 5)
    # prefer audio duration so voice fits
    try:
        audio = AudioFileClip(audio_path)
        dur = max(est, audio.duration)
    except Exception:
        audio = None
        dur = est

    clip = None
    if sc['type'] == 'video':
        try:
            clip = VideoFileClip(sc['path'])
            # if source longer than needed, trim
            if clip.duration > dur:
                clip = clip.subclip(0, dur)
        except Exception:
            clip = None
    if sc['type'] == 'image' or clip is None:
        # image fallback
        clip = ImageClip(sc['path']).set_duration(dur)

    # scale down/up keeping aspect ratio so it fits within target box
    scale_factor = min(TARGET_WIDTH / clip.w, TARGET_HEIGHT / clip.h)
    clip = clip.resize(scale_factor)

    # create black background and center the clip
    bg = ColorClip(size=(TARGET_WIDTH, TARGET_HEIGHT), color=(0, 0, 0)).set_duration(dur)
    final = CompositeVideoClip([bg, clip.set_pos('center')]).set_duration(dur)

    # attach audio if available
    if audio is not None:
        try:
            final = final.set_audio(audio.set_duration(dur))
        except Exception:
            pass

    # write file with reasonable bitrate and settings for mobile editing
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", bitrate="5000k")
    final.close()


# legacy compose_clips kept for reference but not used for per-step export
def compose_clips(step_clips: List[Dict[str, Any]], audio_files: List[str], output_path: str):
    """
    Deprecated in this branch: kept for backward compatibility if needed.
    """
    clips = []
    for i, sc in enumerate(step_clips):
        dur = sc.get("est_seconds", 5)
        if sc["type"] == "video":
            clip = VideoFileClip(sc["path"])
            if clip.duration > dur:
                clip = clip.subclip(0, dur)
            try:
                audio = AudioFileClip(audio_files[i])
                clip = clip.set_audio(audio)
            except Exception:
                pass
            scale_factor = min(TARGET_WIDTH / clip.w, TARGET_HEIGHT / clip.h)
            clip = clip.resize(scale_factor)
            bg = ColorClip(size=(TARGET_WIDTH, TARGET_HEIGHT), color=(0, 0, 0)).set_duration(dur)
            clip = CompositeVideoClip([bg, clip.set_pos('center')]).set_duration(dur)
            clips.append(clip)
        else:
            img_clip = ImageClip(sc["path"]).set_duration(dur)
            scale_factor = min(TARGET_WIDTH / img_clip.w, TARGET_HEIGHT / img_clip.h)
            img_clip = img_clip.resize(scale_factor)
            bg = ColorClip(size=(TARGET_WIDTH, TARGET_HEIGHT), color=(0, 0, 0)).set_duration(dur)
            img_clip = CompositeVideoClip([bg, img_clip.set_pos('center')]).set_duration(dur)
            try:
                audio = AudioFileClip(audio_files[i])
                img_clip = img_clip.set_audio(audio)
            except Exception:
                pass
            clips.append(img_clip)

    if not clips:
        raise RuntimeError("no clips to compose")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", bitrate="5000k")
    final.close()
