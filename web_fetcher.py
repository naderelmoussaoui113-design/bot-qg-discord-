import urllib.request
import urllib.parse
import re
import asyncio
import json

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def extract_urls(text: str) -> list:
    """Trouve toutes les URLs HTTP/HTTPS dans un texte."""
    if not text:
        return []
    url_pattern = r'https?://[^\s<>"\')]+'
    return re.findall(url_pattern, text)

async def fetch_url_data(url: str) -> dict:
    """Télécharge et extrait le contenu pertinent d'une page Web de manière asynchrone."""
    def _fetch():
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
                
                # Si c'est directement une image ou vidéo
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
                
                # Détection spécifique Facebook Ads / TikTok / Shopify
                platform = "Web"
                if "facebook.com/ads/library" in url:
                    platform = "Meta Ad Library (Facebook / Instagram Ads)"
                elif "tiktok.com" in url:
                    platform = "TikTok"
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
        except Exception as e:
            return {"url": url, "error": str(e)}

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
            summary = f"🔗 [DONNÉES EN DIRECT DE LA PAGE / PUBLICITÉ] ({data.get('platform', 'Web')})\n"
            summary += f"• URL : {u}\n"
            if data.get("title"):
                summary += f"• Titre : {data.get('title')}\n"
            if data.get("description"):
                summary += f"• Description / Accroche : {data.get('description')}\n"
            if data.get("text_sample"):
                summary += f"• Contenu extrait de la page / Script détecté :\n{data.get('text_sample')}\n"
            extracted_summaries.append(summary)
            
            if data.get("image_url"):
                media_urls.append(data.get("image_url"))
    
    enriched_prompt = prompt + "\n\n" + "═══════════════════════════════════════════\n"
    enriched_prompt += "📥 ANALYSE DU CONTENU DES LIENS TRANSMIS PAR NADER :\n"
    enriched_prompt += "═══════════════════════════════════════════\n"
    enriched_prompt += "\n\n".join(extracted_summaries)
    enriched_prompt += "\n═══════════════════════════════════════════\n"
    enriched_prompt += "Considère ces informations comme le contenu réel de la pub, de la boutique ou du produit à analyser."
    
    return enriched_prompt, media_urls
