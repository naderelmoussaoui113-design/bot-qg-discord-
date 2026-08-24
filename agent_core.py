import os
import json
import time
import datetime
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import google.generativeai as genai
import tempfile
from notebooklm_bridge import query_live_notebooklm, get_notebooklm_knowledge
from product_hunter import generate_daily_winning_products
from creative_spy import generate_daily_creative_spy
from sheets_bridge import parse_product_dossier_to_dict, push_to_google_sheet
from web_fetcher import enrich_prompt_with_urls

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID", "1540374293416771625"))

# Paths for Shared Memory
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_brain")
os.makedirs(SHARED_DIR, exist_ok=True)
MEMORY_FILE = os.path.join(SHARED_DIR, "shared_memory.json")
TASKS_FILE = os.path.join(SHARED_DIR, "mac_tasks.md")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Shared Memory Management
def load_shared_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_updated": datetime.datetime.now().isoformat(),
        "projects": {
            "coussins": {
                "name": "Boutique Coussins Ergonomiques (Shopify)",
                "target": "Sommeil, cervicales, douleurs dorsales, confort de vie",
                "notes": []
            },
            "ebook_handicap": {
                "name": "Projet Ebook Handicap & Démarches",
                "target": "Aidants, familles, personnes en situation de handicap, démarches MDPH",
                "notes": []
            }
        },
        "recent_activities": [],
        "mac_todo_queue": []
    }

def save_shared_memory(data):
    data["last_updated"] = datetime.datetime.now().isoformat()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_project_note(project_key, text, is_voice=False):
    mem = load_shared_memory()
    if project_key not in mem["projects"]:
        mem["projects"][project_key] = {"name": project_key, "notes": []}
    
    note_entry = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "vocal" if is_voice else "texte",
        "content": text
    }
    mem["projects"][project_key]["notes"].append(note_entry)
    mem["projects"][project_key]["notes"] = mem["projects"][project_key]["notes"][-30:]
    save_shared_memory(mem)

def append_mac_task(task_text, category="Général"):
    mem = load_shared_memory()
    entry = {
        "id": int(time.time()),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": category,
        "task": task_text,
        "status": "pending"
    }
    mem["mac_todo_queue".append(entry) if "mac_todo_queue" in mem else None]
    save_shared_memory(mem)
    
    with open(TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"- [ ] **[{entry['date']} - {category}]** {task_text}
")

# Prompts by Channel / Function
PROMPTS = {
    "global_system": """Tu es l'Associé Stratégique, Directeur E-commerce & Mentor Business d'élite de Nader.
Tu lui réponds directement sur son Discord mobile (Samsung S25 Ultra).
Ton style : Percutant, orienté ROI, structuré, sans blabla inutile. Tu penses comme un fondateur e-commerce à 7 chiffres (Alex Hormozi, direct-response copywriting, psychologie de persuasion).

ACCÈS AU CERVEAU CENTRAL NOTEBOOKLM & CONTEXTE DES PROJETS :
- Tu as accès en continu aux 100 sources d'élite e-commerce de Nader (Focus Business, Meta Ads, TikTok Ads, scaling 10k€/mois, fiscalité LLC, Shopify, Claude Design).
- Tu as une vision transversale de tous ses projets : Boutique Coussins ergonomiques Shopify, Projet Ebook Handicap, Chasse de produits TrendTrack.
- Quand Nader te pose une question ou te demande de développer un produit, réponds de façon ultra détaillée, concrète et immédiatement actionnable !
""",

    "notebook-lm-direct": """Rôle : Moteur d'Interrogation NotebookLM en Direct.
Objectif : Interroger les 100 sources d'élite de Nader sur Google NotebookLM.
Directives :
- Donner des réponses extrêmement précises, directes et détaillées basées sur les documents du carnet.
- Citer les méthodes, chiffres, filtres et sources exactes.
""",

    "chasse-produits-winners": """Rôle : Chasseur de Produits Winners & Développeur d'Offres M d'Élite.
DIRECTIVES STRICTES :
1. Si Nader te demande de chasser/chercher des produits : sors une sélection de pépites selon les 5 critères de la Méthode Focus & Zezinho (Marge > 70%, Effet Wow 3s, Logistique < 1kg, 0 batterie).
2. SI NADER TE DEMANDE DE DÉVELOPPER UN PRODUIT PRÉCIS OU UN DES PRODUITS DE LA LISTE :
   DÉVELOPPE CE PRODUIT SPÉCIFIQUE EN PROFONDEUR SANS PROPOSER 5 AUTRES PRODUITS !
   Structure le dossier complet :
   - 🎯 Offre Irrésistible M (Pack Solo vs Pack Duo à forte marge)
   - 💰 Pricing & Calcul de rentabilité chirurgical (Prix, COGS, Marge brute, Marge nette)
   - 🎬 3 Angles de Créatives TikTok & Meta Ads avec Hooks d'arrêt de scroll
   - 🛍️ Angles Copywriting & Structure de page produit
   - 📊 Prêt pour injection Google Sheet 36 colonnes
""",

    "espionnage-pubs-tiktok-meta": """Rôle : Analyste Publicitaire & Espionnage TikTok / Meta Ads.
Objectif : Décortiquer les meilleures publicités e-commerce scalées en France et à l'international.
"""
}

async def send_smart_chunks(destination, text, max_len=1900):
    if not text:
        return
    lines = text.split("
")
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_len:
            if current_chunk.strip():
                if hasattr(destination, "reply"):
                    try:
                        await destination.reply(current_chunk)
                    except Exception:
                        await destination.channel.send(current_chunk)
                else:
                    target = destination.channel if hasattr(destination, "channel") else destination
                    await target.send(current_chunk)
                await asyncio.sleep(0.6)
            current_chunk = line + "
"
        else:
            current_chunk += line + "
"
            
    if current_chunk.strip():
        if hasattr(destination, "reply"):
            try:
                await destination.reply(current_chunk)
            except Exception:
                await destination.channel.send(current_chunk)
        else:
            target = destination.channel if hasattr(destination, "channel") else destination
            await target.send(current_chunk)

async def ask_gemini(prompt, media_parts=None, channel_name="general", category_name=""):
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    mem = load_shared_memory()
    projects_context = f"

--- MÉMOIRE ACTIVE DES PROJETS DE NADER ---
"
    for p_k, p_v in mem.get("projects", {}).items():
        notes_str = "
".join([f"- [{n.get('date')}] {n.get('content')}" for n in p_v.get("notes", [])[-5:]])
        projects_context += f"• Projet {p_v.get('name')} (Cible: {p_v.get('target')}):
{notes_str or 'Aucune note récente.'}
"
    
    system_instructions = PROMPTS.get("global_system", "") + projects_context
    
    matched_prompt = ""
    for key, p in PROMPTS.items():
        if key in channel_name:
            matched_prompt = p
            break
    
    if matched_prompt:
        system_instructions += "

--- RÔLE SPÉCIFIQUE DU SALON #" + channel_name + " ---
" + matched_prompt

    notebook_knowledge = get_notebooklm_knowledge()
    if notebook_knowledge and ("PILOTAGE" in category_name.upper() or "QG" in category_name.upper() or "notebook" in channel_name or "chasse" in channel_name):
        system_instructions += f"

--- EXTRAIT DU CARNET NOTEBOOKLM (100 SOURCES E-COMMERCE) ---
{notebook_knowledge[:35000]}
--- FIN NOTEBOOKLM ---"
            
    contents = []
    if media_parts:
        contents.extend(media_parts)
    if prompt:
        contents.append(prompt)
    elif not contents:
        contents.append("Bonjour !")
        
    last_err = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instructions,
                generation_config={"temperature": 0.7, "max_output_tokens": 8192}
            )
            response = await asyncio.to_thread(model.generate_content, contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            continue
            
    return f"⚠️ Erreur d'analyse IA : {str(last_err)}"

LAST_DAILY_HUNT_FILE = os.path.join(SHARED_DIR, "last_daily_hunt.txt")

@tasks.loop(minutes=30)
async def daily_product_hunt():
    try:
        await bot.wait_until_ready()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_paris = now_utc + datetime.timedelta(hours=2)
        today_str = now_paris.strftime("%Y-%m-%d")
        
        if now_paris.hour != 6:
            return
            
        if os.path.exists(LAST_DAILY_HUNT_FILE):
            with open(LAST_DAILY_HUNT_FILE, "r") as f:
                last_sent = f.read().strip()
                if last_sent == today_str:
                    return
                    
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return
        
        chasse_channel = discord.utils.get(guild.text_channels, name="🎯-chasse-produits-winners")
        rapport_channel = discord.utils.get(guild.text_channels, name="🌅-rapport-du-matin")
        spy_channel = discord.utils.get(guild.text_channels, name="🕵️-espionnage-pubs-tiktok-meta")
        
        winners_dossier = await generate_daily_winning_products(count=5)
        header = f"🌅 **RADAR DU MATIN ({now_paris.strftime('%d/%m/%Y')} - 06:00) : 5 WINNERS VALIDÉS** 🎯

"
        full_msg = header + winners_dossier
        
        if chasse_channel:
            await send_smart_chunks(chasse_channel, full_msg)
            
        if spy_channel:
            spy_dossier = await generate_daily_creative_spy()
            spy_header = f"🕵️ **RADAR CRÉATIVES ADS DU MATIN ({now_paris.strftime('%d/%m/%Y')} - 06:00) : TOP 3 PUBS SCALÉES** 🎬

"
            await send_smart_chunks(spy_channel, spy_header + spy_dossier)
                    
        if rapport_channel:
            await rapport_channel.send(f"📊 **RADAR DU MATIN :**
• Tes 5 produits gagnants du jour sont prêts dans {chasse_channel.mention if chasse_channel else '#🎯-chasse-produits-winners'} !
• Tes 3 créatives/hooks à copier sont dans {spy_channel.mention if spy_channel else '#🕵️-espionnage-pubs-tiktok-meta'} !")
            
        with open(LAST_DAILY_HUNT_FILE, "w") as f:
            f.write(today_str)
    except Exception as e:
        print(f"Error in daily_product_hunt: {e}")

@bot.event
async def on_ready():
    print(f"👑 Mon Associé IA is ONLINE & CONNECTED as {bot.user} (ID: {bot.user.id})")
    if not daily_product_hunt.is_running():
        daily_product_hunt.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_text = message.content or ""
    media_parts = []
    is_voice = False
    temp_files_to_cleanup = []
    gemini_files_to_cleanup = []
    
    try:
        if message.attachments:
            for att in message.attachments:
                file_bytes = await att.read()
                content_type = att.content_type or ""
                
                if "audio" in content_type or att.filename.endswith((".ogg", ".mp3", ".wav", ".m4a", ".aac")):
                    is_voice = True
                    mime = content_type if content_type else "audio/ogg"
                    media_parts.append({"mime_type": mime, "data": file_bytes})
                    if not user_text:
                        user_text = "Écoute cet enregistrement vocal de Nader. Retranscris l'essentiel, synthétise les points clés et dégage les tâches précises à exécuter."
                
                elif "image" in content_type or att.filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    mime = content_type if content_type else "image/jpeg"
                    media_parts.append({"mime_type": mime, "data": file_bytes})
                    if not user_text:
                        user_text = "Analyse attentivement cette image / capture d'écran selon le rôle de ce salon."
                
                elif "video" in content_type or att.filename.endswith((".mp4", ".mov", ".webm", ".avi", ".mkv")):
                    mime = content_type if content_type else "video/mp4"
                    suffix = os.path.splitext(att.filename)[1] or ".mp4"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(file_bytes)
                        tmp_path = tmp_file.name
                    temp_files_to_cleanup.append(tmp_path)
                    
                    uploaded_video = await asyncio.to_thread(genai.upload_file, tmp_path, mime_type=mime)
                    while uploaded_video.state.name == "PROCESSING":
                        await asyncio.sleep(2)
                        uploaded_video = await asyncio.to_thread(genai.get_file, uploaded_video.name)
                        
                    gemini_files_to_cleanup.append(uploaded_video)
                    media_parts.append(uploaded_video)
                    
                    if not user_text:
                        user_text = "Analyse cette vidéo publicitaire : décortique le Hook visuel (0-3s), le Hook verbal, la démonstration produit, le CTA et réécris 3 versions françaises ultra-performantes adaptées à notre marque."

        if user_text:
            user_text, _ = await enrich_prompt_with_urls(user_text)

        if not user_text and not media_parts:
            return

        channel_name = message.channel.name
        category_name = message.channel.category.name if message.channel.category else ""
        
        # Récupération de l'historique récent du salon
        history_context = ""
        try:
            history_msgs = []
            async for hist in message.channel.history(limit=6):
                if hist.id != message.id and hist.content:
                    sender = "Nader" if not hist.author.bot else "Associé IA"
                    history_msgs.append(f"[{sender}]: {hist.content[:400]}")
            if history_msgs:
                history_msgs.reverse()
                history_context = "
--- HISTORIQUE RÉCENT DU SALON (#" + channel_name + ") ---
" + "
".join(history_msgs) + "
------------------------------------------------
"
        except Exception:
            pass

        u_lower = user_text.lower()
        response_text = ""

        # 1. Project Specific Notes Recording
        if "vocaux-et-notes" in channel_name:
            async with message.channel.typing():
                enhanced_prompt = f"{history_context}

Message de Nader : {user_text}" if history_context else user_text
                response_text = await ask_gemini(enhanced_prompt, media_parts=media_parts, channel_name=channel_name, category_name=category_name)
                
                project_key = "coussins" if "COUSSINS" in category_name.upper() else "ebook_handicap" if "EBOOK" in category_name.upper() else "general"
                append_project_note(project_key, user_text if not is_voice else response_text[:200], is_voice=is_voice)

        # 2. Direct NotebookLM Channel
        elif "notebook" in channel_name:
            async with message.channel.typing():
                response_text = await query_live_notebooklm(user_text)
                if not response_text or len(response_text) < 20:
                    enhanced_prompt = f"{history_context}

Question de Nader : {user_text}" if history_context else user_text
                    response_text = await ask_gemini(enhanced_prompt, media_parts=media_parts, channel_name=channel_name, category_name=category_name)
                response_text = f"🧠 **NOTEBOOKLM (100 SOURCES E-COMMERCE) :**

{response_text}"

        # 3. Product Hunter Channel (Smart Intent Routing)
        elif "chasse-produits" in channel_name:
            async with message.channel.typing():
                is_explicit_hunt = any(k in u_lower for k in ["cherche 5", "trouve 5", "nouveaux produits", "chasse des produits", "5 winners", "top 5 winners", "radar du jour", "propose 5"]) and not any(k in u_lower for k in ["développe", "analyse", "détaille", "ce produit", "produit #", "sheet", "tableau", "transfère", "créas", "offre", "prix"])
                
                if is_explicit_hunt:
                    winners_dossier = await generate_daily_winning_products(count=5, specific_niche=user_text)
                    response_text = f"🎯 **RADAR WINNERS VALIDÉS (MÉTHODE FOCUS & ZEZINHO / FRANCE) :**

{winners_dossier}"
                else:
                    # Nader demande de développer un produit spécifique ou d'analyser !
                    enhanced_prompt = f"""Tu es dans le salon #chasse-produits-winners.
{history_context}

DEMANDE SPÉCIFIQUE DE NADER :
{user_text}

DIRECTIVES STRICTES :
- Ne génère SURTOUT PAS une nouvelle liste de 5 produits !
- Concentre-toi à 100% sur le produit dont parle Nader (ou le produit cité dans l'historique ci-dessus).
- Développe ce produit de manière chirurgicale :
  1. 🎯 Structure de l'Offre M (Pack Solo vs Pack Duo avec pricing rentable et markup > x3.5)
  2. 🎬 3 Angles de Créatives TikTok / Meta Ads avec Hooks percutants
  3. 🛍️ Copywriting de la Fiche Produit (Bénéfices viscéraux, caractéristiques, réassurance)
  4. 📊 Synthèse financière pour Google Sheet
"""
                    response_text = await ask_gemini(enhanced_prompt, media_parts=media_parts, channel_name=channel_name, category_name=category_name)

        # 4. Creative Spy Channel
        elif "espionnage" in channel_name or "tiktok-meta" in channel_name:
            async with message.channel.typing():
                if media_parts or "http" in user_text or any(k in u_lower for k in ["analyse", "détaille", "réécris", "hook", "script", "développe"]):
                    enhanced_prompt = f"{history_context}

Demande de Nader : {user_text}" if history_context else user_text
                    response_text = await ask_gemini(enhanced_prompt, media_parts=media_parts, channel_name=channel_name, category_name=category_name)
                else:
                    spy_dossier = await generate_daily_creative_spy(specific_niche=user_text)
                    response_text = f"🕵️ **DOSSIER ESPIONNAGE CRÉATIVES ADS (TIKTOK & META FRANCE) :**

{spy_dossier}"

        # 5. All other QG and General channels
        else:
            async with message.channel.typing():
                enhanced_prompt = f"{history_context}

Demande de Nader : {user_text}" if history_context else user_text
                response_text = await ask_gemini(enhanced_prompt, media_parts=media_parts, channel_name=channel_name, category_name=category_name)

        # PONT GOOGLE SHEETS GLOBAL (Fonctionne dans TOUS les salons)
        if any(k in u_lower for k in ["sheet", "tableau", "transfèr", "export", "enregistr", "injecte dans le sheet", "ajoute au sheet"]):
            context_for_sheet = (response_text + "

" + history_context + "

" + user_text)
            product_dict = parse_product_dossier_to_dict(context_for_sheet)
            push_res = push_to_google_sheet(product_dict)
            if push_res.get("success"):
                response_text += f"

📊 **GOOGLE SHEETS :** {push_res.get('message')}"
            else:
                response_text += f"

📊 **GOOGLE SHEETS :** {push_res.get('message')}"

        # Tâche Mac globale
        if "tâche mac" in u_lower or "à faire sur le mac" in u_lower or "a-faire-sur-le-mac" in channel_name:
            task_summary = response_text.split("
")[0][:120] if response_text else user_text[:120]
            append_mac_task(task_summary, category=channel_name)
            guild = message.guild
            mac_channel = discord.utils.get(guild.text_channels, name="📋-a-faire-sur-le-mac")
            if mac_channel and mac_channel.id != message.channel.id:
                task_embed = discord.Embed(
                    title="📌 NOUVELLE ACTION SYNCHRONISÉE POUR LE MAC",
                    description=f"**Source :** Salon 
**Action :** {task_summary}",
                    color=discord.Color.green()
                )
                await mac_channel.send(embed=task_embed)
        
        # Log recent activity
        mem = load_shared_memory()
        mem.setdefault("recent_activities", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "category": category_name,
            "channel": channel_name,
            "user_prompt": user_text[:150],
            "bot_summary": response_text[:200]
        })
        mem["recent_activities"] = mem["recent_activities"][-50:]
        save_shared_memory(mem)
        
        # Reply
        await send_smart_chunks(message, response_text)

    finally:
        for tmp in temp_files_to_cleanup:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
        for g_file in gemini_files_to_cleanup:
            try:
                await asyncio.to_thread(g_file.delete)
            except Exception:
                pass

async def run_web_server():
    from aiohttp import web
    async def handle_ping(request):
        return web.Response(text="Bot is running 24/7 on Cloud!")

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌍 Health-check Web Server listening on port {port}")

async def main():
    await run_web_server()
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
