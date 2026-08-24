import os
import sys
import json
import time
import urllib.parse
import urllib.request
import asyncio
import subprocess
import shutil
import tempfile
import argparse
import re
import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

VOICES = {
    "femme_dynamique": "fr-FR-VivienneMultilingualNeural",
    "femme_naturelle": "fr-FR-DeniseNeural",
    "homme_dynamique": "fr-FR-HenriNeural",
    "homme_jeune": "fr-FR-AlainNeural"
}

OUTPUT_DIR = Path("/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/CREATIVES_UGC")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def generate_voiceover(text: str, output_path: str, voice: str = "fr-FR-VivienneMultilingualNeural") -> bool:
    """Génère un fichier audio MP3 de voix off française ultra-réaliste 100% gratuitement via Edge-TTS."""
    try:
        cmd = [
            sys.executable, "-m", "edge_tts",
            "--voice", voice,
            "--text", text,
            "--write-media", output_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"❌ Erreur Edge-TTS : {e}")
        return False

def download_flux_image(prompt: str, output_path: str, retries: int = 3) -> bool:
    """Télécharge une image 9:16 ultra-réaliste 100% gratuitement via Flux / Pollinations."""
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&model=flux&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
                if len(data) > 5000:
                    with open(output_path, "wb") as f:
                        f.write(data)
                    return True
        except Exception as e:
            print(f"⚠️ Essai {attempt+1}/{retries} échoué : {e}")
            time.sleep(3)
            
    # Fallback image de sécurité si le réseau bloque
    try:
        img = Image.new("RGB", (720, 1280), color=(20, 24, 33))
        draw = ImageDraw.Draw(img)
        draw.text((100, 600), "PRODUIT GAGNANT 2026", fill=(255, 255, 255))
        img.save(output_path)
        return True
    except Exception:
        return False

def add_tiktok_caption(image_path: str, caption_text: str, output_path: str):
    """Ajoute des sous-titres stylisés type TikTok (Jaune Fluo / Boîte Noire épaisse) directement sur l'image."""
    try:
        im = Image.open(image_path).convert("RGB").resize((720, 1280))
        draw = ImageDraw.Draw(im)
        font = ImageFont.load_default(size=42)
        
        # Découpage du texte s'il est trop long
        words = caption_text.split()
        lines = []
        current_line = []
        for w in words:
            current_line.append(w)
            if len(" ".join(current_line)) > 18:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))
            
        y_start = 1280 - 360 - (len(lines) * 60)
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (720 - tw) // 2
            ty = y_start + (i * 70)
            
            # Fond noir contrasté arrondi
            draw.rectangle([tx - 25, ty - 12, tx + tw + 25, ty + th + 14], fill=(0, 0, 0))
            # Texte Jaune Fluo TikTok
            draw.text((tx, ty), line, fill=(255, 230, 0), font=font)
            
        im.save(output_path)
    except Exception as e:
        print(f"⚠️ Erreur caption : {e}")
        shutil.copy(image_path, output_path)

def get_audio_duration(audio_path: str) -> float:
    """Récupère la durée de l'audio via ffprobe."""
    try:
        ffprobe_cmd = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        res = subprocess.run(
            [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True,
            text=True
        )
        return float(res.stdout.strip())
    except Exception:
        return 12.0

def build_ugc_video(image_paths: list, audio_path: str, output_video_path: str) -> bool:
    """Compile les scènes animées avec effet de zoom et la voix off en MP4."""
    try:
        ffmpeg_cmd = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        total_duration = get_audio_duration(audio_path)
        img_duration = total_duration / max(len(image_paths), 1)
        
        inputs = []
        filter_complex = ""
        
        for i, img_p in enumerate(image_paths):
            inputs.extend(["-loop", "1", "-t", f"{img_duration:.2f}", "-i", img_p])
            filter_complex += f"[{i}:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,zoompan=z='min(zoom+0.0015,1.12)':d={int(img_duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280[v{i}];"
            
        concat_v = "".join([f"[v{i}]" for i in range(len(image_paths))])
        filter_complex += f"{concat_v}concat=n={len(image_paths)}:v=1:a=0[vout]"
        
        cmd = [
            ffmpeg_cmd, "-y",
            *inputs,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{len(image_paths)}:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_video_path
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 10000
    except Exception as e:
        print(f"❌ Erreur FFmpeg : {e}")
        return False

async def generate_complete_ugc_ad(product_name: str, pain_point: str = "Douleur et inconfort", voice_type: str = "femme_dynamique") -> str:
    """
    Pipeline 100% GRATUIT & LOCAL de Création de Vidéos UGC TikTok/Meta Ads :
    - Voix Off Française Ultra-Réaliste (Edge-TTS 0€)
    - Photos Photoréalistes d'Acteur/Actrice avec le produit (Flux 0€)
    - Sous-titres TikTok Jaunes contrastés (Pillow 0€)
    - Montage, Zooms et Rendu 9:16 (FFmpeg 0€)
    """
    print(f"\n🎬 ─────────────────────────────────────────────────────────────")
    print(f"🚀 GÉNÉRATION VIDÉO UGC 100% GRATUITE DANS LE TERMINAL")
    print(f"📦 Produit : {product_name}")
    print(f"🎯 Angle : {pain_point}")
    print(f"🎙️ Voix : {voice_type}")
    print(f"─────────────────────────────────────────────────────────────\n")
    
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', product_name.lower())[:20]
    final_video = OUTPUT_DIR / f"ugc_{clean_name}_{int(datetime.datetime.now().timestamp())}.mp4"
    voice_name = VOICES.get(voice_type, VOICES["femme_dynamique"])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Scénario Direct-Response en 3 Actes
        scene_captions = [
            f"ARRÊTE DE SOUFFRIR DE ÇA ! 🚨",
            f"J'AI TESTÉ LE {product_name.upper()} ✨",
            f"LIEN ET PROMO EN BIO ! 🛒"
        ]
        
        script_full = (
            f"Si tu as souvent {pain_point.lower()}, écoute bien ça ! "
            f"J'ai testé le tout nouveau {product_name}, et la différence est juste bluffante dès le premier jour. "
            f"Regarde comment ça soulage instantanément la pression. "
            f"Clique vite sur le lien pour profiter de l'offre spéciale avant la rupture de stock !"
        )
        
        # 1. Génération Audio Voix Off
        audio_file = tmp_path / "voiceover.mp3"
        print("🎙️ 1/4 - Génération de la voix off française réaliste (Edge-TTS 0€)...")
        await generate_voiceover(script_full, str(audio_file), voice_name)
        
        # 2. Prompts Images Photoréalistes
        prompts = [
            f"Raw authentic iPhone selfie video shot of a stressed 26-year-old French person with severe back discomfort, natural lighting, TikTok UGC style, 9:16 vertical",
            f"Close up hands holding and presenting innovative {product_name}, modern ergonomic design, bright living room, authentic TikTok product review, 9:16 vertical",
            f"Happy smiling French person relieved and relaxed holding {product_name}, smiling at camera, authentic UGC creator, 9:16 vertical"
        ]
        
        processed_images = []
        print("📸 2/4 - Génération des visuels photoréalistes Flux (0€)...")
        for idx, p in enumerate(prompts):
            raw_img = tmp_path / f"raw_scene_{idx}.jpg"
            captioned_img = tmp_path / f"scene_{idx}_captioned.jpg"
            
            print(f"  • Scène #{idx+1} en cours...")
            download_flux_image(p, str(raw_img))
            add_tiktok_caption(str(raw_img), scene_captions[idx], str(captioned_img))
            processed_images.append(str(captioned_img))
            
        print("🎬 3/4 - Compilation de la vidéo 9:16 avec zooms dynamiques (FFmpeg 0€)...")
        ok = build_ugc_video(processed_images, str(audio_file), str(final_video))
        
        if ok and os.path.exists(final_video):
            size_mb = os.path.getsize(final_video) / (1024 * 1024)
            print(f"\n🎉 4/4 - TERMINÉ ! Ta vidéo UGC est prête à être balancée sur TikTok/Meta :")
            print(f"📁 Fichier : {final_video}")
            print(f"📊 Taille : {size_mb:.2f} MB | Format : 9:16 Vertical HD\n")
            return str(final_video)
        else:
            raise RuntimeError("Échec de la compilation vidéo.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Créateur de Vidéos UGC TikTok/Meta 100% Gratuit dans le Terminal")
    parser.add_argument("--product", type=str, default="Coussin Gel Alvéolé", help="Nom du produit")
    parser.add_argument("--pain", type=str, default="Mal de dos et sciatique en voiture", help="Problème viscéral")
    parser.add_argument("--voice", type=str, default="femme_dynamique", choices=list(VOICES.keys()), help="Voix off")
    
    args = parser.parse_args()
    asyncio.run(generate_complete_ugc_ad(args.product, args.pain, args.voice))
