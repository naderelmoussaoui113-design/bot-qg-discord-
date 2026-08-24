import urllib.request
import urllib.parse
import re
import asyncio
import json
import subprocess
import shutil

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def extract_urls(text: str) -> list:
    """Trouve toutes les URLs HTTP/HTTPS dans un texte."""
    if not text:
        return []
    url_pattern = r'https?://[^\s<>"\')]+'
    return re.findall(url_pattern, text)

def _fetch_jina_reader(url: str) -> str:
    """Utilise l'API universelle Jina Reader (r.jina.ai) pour extraire le markdown propre d'une page."""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        req = urllib.request.Request(
            jina_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/plain",
            }
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read().decode("utf-8", errors="ignore")[:4000]
    except Exception:
        return ""

def _fetch_youtube_data(url: str) -> dict:
    """Extrait les métadonnées et la transcription YouTube via yt-dlp."""
    try:
        # Vérifier si yt-dlp est disponible
        yt_dlp_cmd = shutil.which("yt-dlp") or "yt-dlp"
        
        # Dump JSON metadata
        res = subprocess.run(
            [yt_dlp_cmd, "--dump-json", "--no-warnings", "--skip-download", url],
            capture_output=True,
            text=True,
            timeout=15
        )
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            title = data.get("title", "")
            channel = data.get("uploader", "")
            duration = data.get("duration_string", "")
            description = data.get("description", "")
            views = data.get("view_count", 0)
            
            sample_text = f"Titre : {title}\nChaîne : {channel} | Durée : {duration} | Vues : {views:,}\n\nDescription :\n{description[:2500]}"
            
            return {
                "url": url,
                "platform": "YouTube Video (agent-reach)",
                "title": title,
                "description": f"Chaîne : {channel} - {views} vues",
                "image_url": data.get("thumbnail", ""),
                "text_sample": sample_text
            }
    except Exception:
        pass
    return {}

def _fetch_reddit_data(url: str) -> dict:
    """Extrait le post Reddit et les top commentaires via l'API JSON Reddit."""
    try:
        clean_url = url.split("?")[0].rstrip("/") + ".json"
        req = urllib.request.Request(
            clean_url,
            headers={"User-Agent": "agent-reach/1.0 (Macintosh)"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            post_data = data[0]["data"]["children"][0]["data"]
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            subreddit = post_data.get("subreddit_name_prefixed", "")
            
            comments = []
            if len(data) > 1 and "data" in data[1]:
                for c in data[1]["data"]["children"][:5]:
                    c_body = c.get("data", {}).get("body")
                    if c_body:
                        comments.append(f"- {c_body}")
            
            sample = f"Subreddit : {subreddit}\nTitre : {title}\nContenu du post :\n{selftext}\n\nTop Avis / Commentaires :\n" + "\n".join(comments)
            
            return {
                "url": url,
                "platform": "Reddit Discussion (agent-reach)",
                "title": f"[{subreddit}] {title}",
                "description": selftext[:300],
                "image_url": "",
                "text_sample": sample[:3500]
            }
    except Exception:
        pass
    return {}

async def fetch_url_data(url: str) -> dict:
    """Télécharge et extrait le contenu pertinent d'une page Web de manière asynchrone (agent-reach engine)."""
    def _fetch():
        # 1. Cas YouTube
        if "youtube.com" in url or "youtu.be" in url:
            yt_res = _fetch_youtube_data(url)
            if yt_res:
                return yt_res

        # 2. Cas Reddit
        if "reddit.com" in url:
            rd_res = _fetch_reddit_data(url)
            if rd_res:
                return rd_res

        # 3. Requête Web classique
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                }
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                content_type = response.headers.get("Content-Type", "")
                
                # Si c'est directement une image
                if "image" in content_type:
                    return {
                        "url": url,
                        "type": "image",
                        "content_type": content_type,
                        "title": "Image directe",
                        "description": f"Image hébergée à l'URL : {url}"
                    }
                
                html = response.read().decode("utf-8", errors="ignore")
                
                # Extraction Titre
                title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else ""
                
                # Extraction OpenGraph & Meta Description
                og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE | re.DOTALL)
                og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE | re.DOTALL)
                meta_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE | re.DOTALL)
                og_image = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', html, re.IGNORECASE | re.DOTALL)
                
                desc = og_desc.group(1).strip() if og_desc else (meta_desc.group(1).strip() if meta_desc else "")
                page_title = og_title.group(1).strip() if og_title else title
                image_url = og_image.group(1).strip() if og_image else ""
                
                # Nettoyage du corps de texte
                clean_body = re.sub(r'<(script|style|svg|noscript)[^>]*>.*?</\1>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
                clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
                clean_body = re.sub(r'\s+', ' ', clean_body).strip()
                
                # Fallback Jina Reader si le texte extrait est trop pauvre (sites protégés/SPA)
                if len(clean_body) < 150:
                    jina_text = _fetch_jina_reader(url)
                    if jina_text:
                        clean_body = jina_text
                
                # Détection de la plateforme
                platform = "Web"
                if "facebook.com/ads/library" in url or "facebook.com" in url:
                    platform = "Meta Ads / Facebook"
                elif "tiktok.com" in url:
                    platform = "TikTok"
                elif "douyin.com" in url:
                    platform = "Douyin (TikTok Chinois)"
                elif "xiaohongshu.com" in url or "xhslink.com" in url:
                    platform = "XiaoHongShu (RED Sourcing)"
                elif "aliexpress.com" in url:
                    platform = "AliExpress Sourcing"
                elif "amazon." in url:
                    platform = "Amazon"
                
                return {
                    "url": url,
                    "platform": platform,
                    "title": page_title,
                    "description": desc,
                    "image_url": image_url,
                    "text_sample": clean_body[:3500]
                }
        except Exception:
            # En cas d'erreur de requête directe, basculer sur Jina Reader
            jina_text = _fetch_jina_reader(url)
            if jina_text:
                return {
                    "url": url,
                    "platform": "Web (Jina Reader)",
                    "title": "Page Web",
                    "description": "Contenu extrait via Jina AI Universal Reader",
                    "image_url": "",
                    "text_sample": jina_text[:3500]
                }
            return {"url": url, "error": "Impossible d'accéder au lien"}

    return await asyncio.to_thread(_fetch)

async def enrich_prompt_with_urls(prompt: str) -> tuple[str, list]:
    """
    Analyse le prompt, télécharge le contenu des liens détectés et enrichit le contexte pour Gemini.
    Retourne (nouveau_prompt_enrichi, liste_media_extraits).
    """
    urls = extract_urls(prompt)
    if not urls:
        return prompt, []
    
    extracted_summaries = []
    media_urls = []
    
    for u in urls[:4]:  # Max 4 URLs par message pour la rapidité
        data = await fetch_url_data(u)
        if data.get("error"):
            extracted_summaries.append(f"🔗 LIEN : {u}\n⚠️ Erreur de lecture automatique : {data.get('error')}")
        else:
            summary = f"🔗 [DONNÉES EN DIRECT - {data.get('platform', 'Web')}]\n"
            summary += f"• URL : {u}\n"
            if data.get("title"):
                summary += f"• Titre : {data.get('title')}\n"
            if data.get("description"):
                summary += f"• Description / Accroche : {data.get('description')}\n"
            if data.get("text_sample"):
                summary += f"• Contenu extrait / Script détecté :\n{data.get('text_sample')}\n"
            extracted_summaries.append(summary)
            
            if data.get("image_url"):
                media_urls.append(data.get("image_url"))
    
    enriched_prompt = prompt + "\n\n" + "═══════════════════════════════════════════\n"
    enriched_prompt += "📥 ANALYSE DU CONTENU DES LIENS (AGENT-REACH ENGINE) :\n"
    enriched_prompt += "═══════════════════════════════════════════\n"
    enriched_prompt += "\n\n".join(extracted_summaries)
    enriched_prompt += "\n═══════════════════════════════════════════\n"
    enriched_prompt += "Considère ces informations comme le contenu réel de la pub, de la boutique, du post Reddit ou de la vidéo YouTube à analyser."
    
    return enriched_prompt, media_urls
