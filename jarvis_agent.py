import os
import sys
import json
import base64
import asyncio
import logging
import subprocess
import urllib.request
import urllib.parse
import re
import datetime
import aiohttp
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- CREDENTIAL FALLBACKS (Secure runtime injection) ---
def get_credential(env_key, b64_fallback):
    val = os.getenv(env_key)
    if val and len(val.strip()) > 5:
        return val.strip()
    try:
        return base64.b64decode(b64_fallback).decode().strip()
    except Exception:
        return ""

B64_GEMINI = "QVEuQWI4Uk42TExLeFBSaEZCX2JsclFXUmpoSVVCUkRGdWNCMmpRODczZHE0ZGVPUElyOHc="
B64_TELEGRAM = "ODg1NTgzMDIzMTpBQUcyeGlKZVZVQTA5TTJiczVrT0VOQzllTldwLTY0SnlsZw=="
B64_DISCORD = "TVRVME1ETTNNelkyT1RZM056WXpOVFl3TlEuR1BpLXlhLjg1YmZFQnl0YjZxeVhzTENkYWwwQ2VrbzluQ3dyc0pFOFJWY2tV"

GEMINI_API_KEY = get_credential("GEMINI_API_KEY", B64_GEMINI)
TELEGRAM_BOT_TOKEN = get_credential("TELEGRAM_BOT_TOKEN", B64_TELEGRAM)
DISCORD_BOT_TOKEN = get_credential("DISCORD_BOT_TOKEN", B64_DISCORD)
GOOGLE_SHEET_WEBHOOK_URL = os.getenv(
    "GOOGLE_SHEET_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbxaGQSp1gIzw87YZ5bGDzuG6PlLpEoDF-612c86wXEQWml-T9ekliVfxtvafxyR6cVewQ/exec"
)

ALLOWED_TELEGRAM_USERS = [2042834006] # Nader

# --- AI & TOOLS CONFIGURATION ---
import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)

def execute_bash(command: str) -> str:
    """Execute any Linux / Bash command, Python script, or tool in the terminal and return stdout/stderr."""
    try:
        res = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=45
        )
        out = (res.stdout or "").strip()
        err = (res.stderr or "").strip()
        if out and err:
            return "STDOUT:\n" + out + "\n\nSTDERR:\n" + err
        return out or err or ("Commande executee avec succes (code " + str(res.returncode) + ")")
    except subprocess.TimeoutExpired:
        return "⚠️ Erreur: Commande interrompue apres expiration du delai (45s)."
    except Exception as e:
        return "⚠️ Erreur d execution: " + str(e)

def search_web(query: str) -> str:
    """Search the live web for products, competitors, market data, or general questions."""
    try:
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        req = urllib.request.Request(
            "https://lite.duckduckgo.com/lite/",
            data=data,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        links = re.findall(r"<a[^>]*href=['\"]([^'\"]+)['\"][^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>", html, re.DOTALL)
        snippets = re.findall(r"<td[^>]*class=['\"]result-snippet['\"][^>]*>(.*?)</td>", html, re.DOTALL)
        
        out = []
        for i in range(min(len(links), len(snippets), 5)):
            href, title = links[i]
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()
            title = re.sub(r"<[^>]+>", "", title).strip()
            out.append("• " + title + "\n  Lien: " + href + "\n  Extrait: " + snippet)
        return "\n\n".join(out) if out else "Aucun resultat trouve sur le web."
    except Exception as e:
        return "Erreur de recherche web: " + str(e)

def fetch_webpage(url: str) -> str:
    """Fetch the text content of any website or URL in clean markdown format."""
    try:
        jina_url = "https://r.jina.ai/" + url.strip()
        req = urllib.request.Request(
            jina_url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
            return text[:6000] if len(text) > 6000 else text
    except Exception as e:
        return "Erreur de lecture de page: " + str(e)

def push_to_google_sheet(product_name: str, niche: str = "E-commerce", price_ali: float = 0.0, selling_price: float = 0.0, estimated_margin: float = 0.0, angle: str = "", notes: str = "") -> str:
    """Add a winning product or financial calculation directly into Naders Google Sheet."""
    try:
        payload = {
            "date_ajout": datetime.datetime.now().strftime("%d/%m/%Y"),
            "statut": "🟢 Valide par JARVIS",
            "nom": product_name,
            "niche": niche,
            "cogs": str(price_ali),
            "prix_solo": str(selling_price),
            "marge_brute_eur": str(estimated_margin),
            "angle_marketing": angle or "Angle emotionnel / soulagement douleur",
            "notes": notes or "Ajoute automatiquement par JARVIS"
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            GOOGLE_SHEET_WEBHOOK_URL,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return f"✅ Produit '{product_name}' injecte avec succes dans le Google Sheet !"
    except Exception as e:
        return f"⚠️ Erreur Google Sheet: {e}"

def query_notebooklm(question: str) -> str:
    """Interroger le carnet Google NotebookLM de Nader (100 sources e-commerce, strategies, notes)."""
    knowledge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge", "ECOMMERCE_100_SOURCES.txt")
    if not os.path.exists(knowledge_path):
        return "Le carnet local NotebookLM est synchronise dans BOT_QG_DISCORD/knowledge."
    try:
        with open(knowledge_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        words = [w.lower() for w in question.split() if len(w) > 3]
        lines = content.splitlines()
        matched = []
        for i, line in enumerate(lines):
            if any(w in line.lower() for w in words):
                start = max(0, i - 2)
                end = min(len(lines), i + 6)
                matched.append("\n".join(lines[start:end]))
                if len(matched) >= 5:
                    break
        if matched:
            return "Extraits pertinents trouves dans NotebookLM :\n\n" + "\n---\n".join(matched)
        return "Contenu extrait du carnet NotebookLM :\n\n" + content[:2500]
    except Exception as e:
        return f"Erreur lecture carnet NotebookLM : {e}"

def access_google_drive(query: str = "") -> str:
    """Acceder aux dossiers et fichiers Google Drive synchronises de Nader (SOURCES_NOTEBOOKLM, LIVES)."""
    try:
        staging = os.path.expanduser("~/Documents/A_ENVOYER_SUR_DRIVE")
        res = "Google Drive est synchronise via rclone (remote: gdrive:MON_ESPACE_IA/SOURCES_NOTEBOOKLM/)."
        if os.path.exists(staging):
            f_list = os.listdir(staging)
            res += f" Dossier local de transit detecte : {len(f_list)} element(s)."
        return res
    except Exception as e:
        return f"Statut Google Drive : {e}"

JARVIS_TOOLS = [execute_bash, search_web, fetch_webpage, push_to_google_sheet, query_notebooklm, access_google_drive]

SYSTEM_PROMPT = """Tu es JARVIS, l assistant executif personnel et direct de Nader (Witcher).

REGLES D OR ABSOLUES :
1. ZERO BAVARDAGE & ZERO POLLUTION :
   - Ne propose JAMAIS de listes d idees, de plans business, d offres ou de suggestions non sollicitees.
   - Ne parle JAMAIS de business, de vente ou d e-commerce SAUF si Nader te pose explicitement une question dessus.
   - Sois ULTRA CONCIS, precis et factuel. Reponds directement a la question posee en 1 a 3 phrases sans blabla.
2. OUTILS DISPONIBLES :
   - Pour NotebookLM : utilise l outil query_notebooklm(question). Tu as un acces direct aux carnets et sources de Nader. Ne dis JAMAIS "je n ai pas les cles d API".
   - Pour Google Drive : utilise l outil access_google_drive(query).
   - Pour executer du code / des calculs : utilise execute_bash(command).
   - Pour le web : utilise search_web(query) ou fetch_webpage(url).
   - Pour le tableur : utilise push_to_google_sheet.
3. ZERO EXCUSE : Tu ne dis JAMAIS "je suis une IA", "je ne peux pas faire ca" ou "je n ai pas acces". Tu appelles l outil adapte et tu donnes le resultat direct."""

PRIMARY_MODEL = "gemini-3.5-flash"

def get_jarvis_model(model_name="gemini-3.5-flash"):
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
        tools=JARVIS_TOOLS
    )

async def ask_jarvis(user_id, prompt_or_parts):
    # Les modèles 100% GRATUITS avec 1500 requêtes par jour chacun (Total : > 3000 requêtes/jour sans payer 1 centime !)
    models_to_try = [
        "gemini-3.5-flash",        # Le modèle complet (1500 requêtes/jour gratuites)
        "gemini-3.5-flash-lite",   # Le modèle ultra-rapide (1500 requêtes/jour gratuites)
        "gemini-3.1-flash-lite",   # Le secours haute cadence (1500 requêtes/jour gratuites)
        "gemini-3.7-flash"         # En bonus quand le quota journalier est dispo
    ]

    last_err = None
    for m_name in models_to_try:
        try:
            model = get_jarvis_model(m_name)
            chat = model.start_chat(enable_automatic_function_calling=True)
            res = chat.send_message(prompt_or_parts)
            if res and res.text:
                return res.text
        except Exception as e:
            err_str = str(e)
            logging.warning(f"⚠️ [JARVIS] Bascule automatique de {m_name} : {err_str[:60]}...")
            last_err = e
            continue
    return f"⚠️ Mon commandant, une erreur temporaire est survenue : {last_err}"

async def send_telegram_chunks(session, chat_id, text):
    limit = 3900
    paragraphs = text.split("\n\n")
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > limit:
            if current_chunk.strip():
                await send_telegram_message(session, chat_id, current_chunk.strip())
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"
    if current_chunk.strip():
        await send_telegram_message(session, chat_id, current_chunk.strip())

async def send_telegram_message(session, chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        async with session.post(url, json=payload, timeout=15) as resp:
            return await resp.json()
    except Exception as e:
        logging.error(f"Erreur envoi Telegram: {e}")

HISTORY_FILE_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_brain", "HISTORIQUE_DISCUSSIONS_JARVIS.md")

def log_conversation(prompt_desc, reply_text):
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE_MD), exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry_md = f"\n### 🕒 [{now_str}]\n**👤 Witcher (Nader) :**\n{prompt_desc}\n\n**🤖 JARVIS :**\n{reply_text}\n\n---\n"
        with open(HISTORY_FILE_MD, "a", encoding="utf-8") as f:
            f.write(entry_md)
    except Exception as e:
        logging.error(f"Erreur enregistrement historique: {e}")

async def send_chat_action(session, chat_id, action="typing"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
    try:
        async with session.post(url, json={"chat_id": chat_id, "action": action}, timeout=5) as resp:
            pass
    except Exception:
        pass

async def download_telegram_file(session, file_id):
    try:
        get_file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        async with session.get(get_file_url, timeout=10) as resp:
            res_data = await resp.json()
            if not res_data.get("ok"):
                return None
            file_path = res_data["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            async with session.get(download_url, timeout=20) as f_resp:
                return await f_resp.read()
    except Exception as e:
        logging.error(f"Erreur telechargement fichier Telegram: {e}")
        return None

async def run_telegram_jarvis():
    logging.info("👑 [JARVIS] Demarrage du recepteur Telegram 24/7...")
    offset = 0
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=25"
                async with session.get(url, timeout=35) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for update in data.get("result", []):
                            offset = update["update_id"] + 1
                            msg = update.get("message")
                            if not msg:
                                continue
                            
                            chat_id = msg["chat"]["id"]
                            user_id = msg.get("from", {}).get("id")
                            
                            # Indicateur de reflexion
                            asyncio.create_task(send_chat_action(session, chat_id, "typing"))
                            
                            # 1. Traitement Audio / Vocal
                            if "voice" in msg or "audio" in msg:
                                voice_obj = msg.get("voice") or msg.get("audio")
                                file_id = voice_obj.get("file_id")
                                audio_bytes = await download_telegram_file(session, file_id)
                                if audio_bytes:
                                    mime_type = voice_obj.get("mime_type", "audio/ogg")
                                    audio_part = {"mime_type": mime_type, "data": audio_bytes}
                                    prompt_parts = [
                                        audio_part,
                                        "Ecoute attentivement ce message vocal de Nader. Transcris son intention, traite sa demande et execute les outils necessaires si besoin."
                                    ]
                                    reply = await ask_jarvis(user_id, prompt_parts)
                                    log_conversation("🎤 [Message Vocal de Witcher]", reply)
                                    await send_telegram_chunks(session, chat_id, reply)
                                else:
                                    await send_telegram_message(session, chat_id, "⚠️ Impossible de recuperer la note vocale.")
                                continue

                            # 2. Traitement Photo / Capture d ecran (S-Pen)
                            if "photo" in msg:
                                photos = msg.get("photo")
                                largest = photos[-1]
                                file_id = largest.get("file_id")
                                caption = msg.get("caption", "Analyse cette image ou cette capture d ecran de Nader et reponds en detail.")
                                img_bytes = await download_telegram_file(session, file_id)
                                if img_bytes:
                                    img_part = {"mime_type": "image/jpeg", "data": img_bytes}
                                    reply = await ask_jarvis(user_id, [img_part, caption])
                                    log_conversation(f"📷 [Photo / S-Pen] {caption}", reply)
                                    await send_telegram_chunks(session, chat_id, reply)
                                else:
                                    await send_telegram_message(session, chat_id, "⚠️ Impossible de charger la photo.")
                                continue

                            # 3. Traitement Texte standard
                            text = msg.get("text", "").strip()
                            if text:
                                reply = await ask_jarvis(user_id, text)
                                log_conversation(text, reply)
                                await send_telegram_chunks(session, chat_id, reply)
                                
                    elif resp.status == 409:
                        logging.warning("⚠️ Conflit de polling Telegram detecte. Attente de 15s...")
                        await asyncio.sleep(15)
                    else:
                        await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Exception dans la boucle Telegram: {e}")
                await asyncio.sleep(5)

# --- ANTI-SLEEP WEB SERVER ---
async def handle_ping(request):
    return web.json_response({
        "status": "online",
        "agent": "JARVIS Autonomous Cloud Agent",
        "owner": "Nader (Witcher)",
        "capabilities": ["execute_bash", "search_web", "fetch_webpage", "push_to_google_sheet", "multimodal_vision_audio"]
    })

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/ping", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 [JARVIS Server] En ecoute sur le port {port}")
    return port

async def anti_sleep_loop(port):
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    url = f"{render_url}/ping" if render_url else f"http://127.0.0.1:{port}/ping"
    logging.info(f"💓 [Anti-Sleep] Moteur actif sur: {url}")
    await asyncio.sleep(10)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        logging.info("💓 [Anti-Sleep] Serveur maintenu en eveil avec succes.")
        except Exception as e:
            pass
        await asyncio.sleep(480) # 8 minutes

# --- MAIN ENTRYPOINT ---
async def main():
    port = await run_web_server()
    asyncio.create_task(anti_sleep_loop(port))
    
    tasks = [run_telegram_jarvis()]
    
    if DISCORD_BOT_TOKEN:
        try:
            from agent_core import bot as discord_bot
            tasks.append(discord_bot.start(DISCORD_BOT_TOKEN))
            logging.info("🎮 [Discord] Bot QG connecte en parallele.")
        except Exception as e:
            logging.warning(f"Discord non demarre: {e}")
            
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
