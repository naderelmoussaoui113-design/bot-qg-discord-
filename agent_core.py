import os
import json
import time
import datetime
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import google.generativeai as genai
from notebooklm_bridge import query_live_notebooklm, get_notebooklm_knowledge
from product_hunter import generate_daily_winning_products
from sheets_bridge import parse_product_dossier_to_dict, push_to_google_sheet

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
    mem["projects"][project_key]["notes"] = mem["projects"][project_key]["notes"][-30:] # keep last 30
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
    mem["mac_todo_queue"].append(entry)
    save_shared_memory(mem)
    
    with open(TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"- [ ] **[{entry['date']} - {category}]** {task_text}\n")

# Prompts by Channel / Function (Integrating NotebookLM Knowledge + Transversality)
PROMPTS = {
    "global_system": """Tu es l'Associé Stratégique, Directeur E-commerce & Mentor Business d'élite de Nader.
Tu lui réponds directement sur son Discord mobile (Samsung S25 Ultra).
Ton style : Percutant, orienté ROI, structuré, sans blabla inutile. Tu penses comme un fondateur e-commerce à 7 chiffres (Alex Hormozi, direct-response copywriting, psychologie de persuasion).

ACCÈS AU CERVEAU CENTRAL NOTEBOOKLM & CONTEXTE DES PROJETS :
- Tu as accès en continu aux 100 sources d'élite e-commerce de Nader (Focus Business, Meta Ads, TikTok Ads, scaling 10k€/mois, fiscalité LLC, Shopify, Claude Design).
- Tu as une vision transversale de tous ses projets : Boutique Coussins ergonomiques Shopify, Projet Ebook Handicap, Chasse de produits TrendTrack.
- Quand Nader te pose une question dans un salon du QG, tu adaptes immédiatement ta réponse avec ses données et méthodes réelles !
""",

    "notebook-lm-direct": """Rôle : Moteur d'Interrogation NotebookLM en Direct.
Objectif : Interroger les 100 sources d'élite de Nader sur Google NotebookLM.
Directives :
- Donner des réponses extrêmement précises, directes et détaillées basées sur les documents du carnet.
- Citer les méthodes, chiffres, filtres et sources exactes.
""",

    "chasse-produits-winners": """Rôle : Chasseur de Produits Winners & Analyste TrendTrack d'Élite.
DIRECTIVE STRICTE NOTEBOOKLM : Tu dois appliquer les critères stricts des 5 piliers de recherche de NotebookLM :
1. Résolution d'un vrai problème douloureux ou passion intense.
2. Effet Wow / Démontrable en moins de 3 secondes en vidéo (Hook visuel immédiat).
3. Marge brute > 70% (Prix de vente minimum 3x à 4x le coût d'achat livré).
4. Logistique fluide (produit léger, incassable, sans électronique défaillante).
5. Preuve de marché (Boutiques scalées, pubs actives > 14 jours sur TrendTrack / TikTok / Meta).

FORMAT DE RÉPONSE OBLIGATOIRE :
Lorsque Nader te demande de chasser des produits, sors systématiquement une liste de 10 PROPOSITIONS VIABLES ET DÉTAILLÉES avec :
- Nom du produit & Niche
- La douleur résolue / L'effet Wow
- Estimation COGS vs Prix de vente conseillé (Marge brute estimée)
- Angle d'attaque publicitaire (Le Hook visuel)
- Verdict : 🟢 GO (Fort potentiel), 🟡 À TESTER AVEC PRÉCAUTION, ou 🔴 NO-GO.
""",

    "calculateur-cogs-marges": """Rôle : Directeur Financier & Calculateur de Rentabilité E-commerce.
DIRECTIVE STRICTE NOTEBOOKLM : Tu appliques les formules financières exactes de NotebookLM :
- COGS (Coût Produit + Frais de port fournisseur type YunExpress / CJ / AliExpress)
- Prix de vente TTC conseillé & Panier Moyen (AOV)
- Marge brute unitaire en € et en %
- Breakeven ROAS (Seuil de rentabilité pub = Prix de Vente / Marge Brute)
- Marge nette estimée après frais de passerelle Stripe/Shopify (2-3%) et budget pub
- Simulation de bénéfice net en poche pour 50, 100 et 300 commandes/mois.
Sois précis au centime près et présente les résultats sous forme de tableau clair.
""",

    "copywriting-pubs-acquisition": """Rôle : Maître Copywriter Direct-Response & Responsable Acquisition (Meta Ads, TikTok Ads, Recrutement UGC).
Fusionne la puissance créative :
1. Publicités : Toujours fournir 3 variations de HOOKS visuels et verbaux (les 3 premières secondes) + Script complet (Hook ➜ Agitation de la douleur ➜ Démonstration produit ➜ Offre irrésistible ➜ Call To Action d'urgence).
2. Recrutement UGC : Rédiger des scripts d'approche DM/Email personnalisés pour engager des créateurs TikTok/Insta (taux de réponse visé : 80%).
3. Adapte le ton selon le projet (Shop Coussins, Ebook ou nouveau winner).
""",

    "offres-et-bundles": """Rôle : Expert Mondial en Structuration d'Offres Irrésistibles ($100M Offers - Alex Hormozi).
Objectif : Transformer le produit en un pack irrésistible pour maximiser le panier moyen (AOV).
Directives NotebookLM :
- Toujours structurer en 3 niveaux : Offre Solo (entrée), Pack Duo Couple (Best-seller recommandé avec 20% de remise), Pack Famille / Confort Ultime (Panier Max).
- Empiler des bonus perçus à haute valeur et coût nul (guides numériques, garanties 30 nuits d'essai, livraison express VIP).
- Rédiger la garantie « Inversion du risque » (Zéro risque pour le client).
""",

    "emails-et-sms": """Rôle : Stratège E-mail & SMS Marketing (Klaviyo / SMSBump).
Directives :
- SMS : Moins de 160 caractères, ultra percutant, lien court, sentiment d'urgence.
- E-mails : Objet à fort taux d'ouverture (> 45%), accroche narrative, bénéfice émotionnel, bouton CTA bien mis en évidence.
- Séquences : Abandon de panier (H+1, H+24, H+48), Bienvenue, Relance post-achat / Upsell.
""",

    "strategie-marketing": """Rôle : Directeur Stratégique & Architecte Scaling 10k€ - 50k€/mois.
Directives NotebookLM :
- Analyse omnicanale (Meta + TikTok + Google SEO/PMax + Email).
- Stratégie d'expansion de catalogue et rétention client.
- Optimisation du taux de conversion (CRO) de la boutique Shopify.
""",

    "mine-avis-amazon": """Rôle : Espion Industriel & Exploiteur de Faiblesses Concurrentes.
Directives :
- Analyse des avis 1 et 2 étoiles des leaders/concurrents pour identifier les frustrations majeures des clients.
- Transformation de ces défauts en arguments marketing majeurs pour nos produits.
""",

    "espionnage-pubs-tiktok-meta": """Rôle : Rétro-Ingénieur de Publicités Virales.
Directives :
- Analyse de la vidéo/image concurrente.
- Décomposition du Hook et de la structure persuasive.
- Réécriture de 3 déclinaisons originales pour nos boutiques.
""",

    "demineur-sav-objections": """Rôle : Négociateur d'Élite & Démineur d'Objections Clients.
Directives :
- Traitement bienveillant, commercial et ultra convaincant des doutes clients (délais de livraison, efficacité, retours, garantie).
- Transformer les hésitations en commandes fermes.
""",

    "demarchage-b2b-gros": """Rôle : Responsable Grands Comptes & Ventes en Gros.
Directives :
- Rédiger des propositions de vente groupée (kinés, ostéopathes, entreprises, comités) pour écouler des volumes de 20 à 100 pièces par commande sans publicité.
""",

    "rapport-du-matin": """Rôle : Tableau de Bord Exécutif Quotidien.
Directives :
- Synthèse des priorités de la journée, état des chantiers en cours, opportunités de la semaine et plan d'action immédiat.
""",

    "brainstorming-general": """Rôle : Sparring-Partner Stratégique & Générateur d'Idées Business.
Directives :
- Réflexion libre, challenge des idées, exploration de nouveaux marchés et opportunités de croissance rapide.
""",

    "vocaux-et-notes": """Rôle : Secrétaire Général & Enregistreur de Contexte Projet.
Directives :
- Écouter attentivement le vocal ou la note de Nader.
- Retranscrire l'idée clé.
- Enregistrer cette note dans la mémoire dédiée au projet (Coussins ou Ebook).
- Si une action concrète pour l'ordinateur est mentionnée, l'envoyer directement dans 📋-a-faire-sur-le-mac !
"""
}

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def ask_gemini(prompt, media_parts=None, channel_name="general", category_name=""):
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    
    # Load shared memory context
    mem = load_shared_memory()
    projects_context = f"\n\n--- MÉMOIRE ACTIVE DES PROJETS DE NADER ---\n"
    for p_k, p_v in mem.get("projects", {}).items():
        notes_str = "\n".join([f"- [{n.get('date')}] {n.get('content')}" for n in p_v.get("notes", [])[-5:]])
        projects_context += f"• Projet {p_v.get('name')} (Cible: {p_v.get('target')}):\n{notes_str or 'Aucune note récente.'}\n"
    
    # Base instructions
    system_instructions = PROMPTS["global_system"] + projects_context
    
    # Inject channel-specific prompt
    matched_prompt = ""
    for key, p in PROMPTS.items():
        if key in channel_name:
            matched_prompt = p
            break
    
    if matched_prompt:
        system_instructions += "\n\n--- RÔLE SPÉCIFIQUE DU SALON #" + channel_name + " ---\n" + matched_prompt

    # For QG channels, inject relevant NotebookLM 100 sources knowledge
    notebook_knowledge = get_notebooklm_knowledge()
    if notebook_knowledge and ("PILOTAGE" in category_name.upper() or "QG" in category_name.upper() or "notebook" in channel_name):
        system_instructions += f"\n\n--- EXTRAIT DU CARNET NOTEBOOKLM (100 SOURCES E-COMMERCE) ---\n{notebook_knowledge[:35000]}\n--- FIN NOTEBOOKLM ---"
            
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
                generation_config={"temperature": 0.7, "max_output_tokens": 4096}
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
        # Check Paris time (UTC+2 in summer)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_paris = now_utc + datetime.timedelta(hours=2) # Paris summer time
        today_str = now_paris.strftime("%Y-%m-%d")
        
        # Only run at 06:00 AM Paris time (between 06:00 and 06:59)
        if now_paris.hour != 6:
            return
            
        # Check if already sent today
        if os.path.exists(LAST_DAILY_HUNT_FILE):
            with open(LAST_DAILY_HUNT_FILE, "r") as f:
                last_sent = f.read().strip()
                if last_sent == today_str:
                    return # Already sent today!
                    
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return
        
        chasse_channel = discord.utils.get(guild.text_channels, name="🎯-chasse-produits-winners")
        rapport_channel = discord.utils.get(guild.text_channels, name="🌅-rapport-du-matin")
        
        winners_dossier = await generate_daily_winning_products(count=5)
        header = f"🌅 **RADAR DU MATIN ({now_paris.strftime('%d/%m/%Y')} - 06:00) : 5 WINNERS VALIDÉS** 🎯\n\n"
        full_msg = header + winners_dossier
        
        if chasse_channel:
            if len(full_msg) <= 2000:
                await chasse_channel.send(full_msg)
            else:
                chunks = [full_msg[i:i+1950] for i in range(0, len(full_msg), 1950)]
                for chunk in chunks:
                    await chasse_channel.send(chunk)
                    
        if rapport_channel:
            await rapport_channel.send(f"📊 **RADAR DU MATIN :** Tes 5 produits gagnants du jour sont prêts dans {chasse_channel.mention if chasse_channel else '#🎯-chasse-produits-winners'} !")
            
        with open(LAST_DAILY_HUNT_FILE, "w") as f:
            f.write(today_str)
            
        print(f"✅ Daily winning products generated & sent to Discord for {today_str}!")
    except Exception as e:
        print(f"Error in daily_product_hunt: {e}")

@tasks.loop(minutes=8)
async def keep_alive_ping():
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://bot-qg-discord.onrender.com/health", timeout=15) as resp:
                print(f"🔄 Self Keep-Alive Ping: HTTP {resp.status}")
    except Exception as e:
        print(f"Self ping error (normal during boot): {e}")

@bot.event
async def on_ready():
    print(f"👑 Mon Associé IA is ONLINE & CONNECTED as {bot.user} (ID: {bot.user.id})")
    if not daily_product_hunt.is_running():
        daily_product_hunt.start()
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_text = message.content or ""
    media_parts = []
    is_voice = False
    
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
            
            elif "video" in content_type or att.filename.endswith((".mp4", ".mov", ".webm")):
                mime = content_type if content_type else "video/mp4"
                media_parts.append({"mime_type": mime, "data": file_bytes})
                if not user_text:
                    user_text = "Analyse cette vidéo publicitaire : décortique le Hook visuel et verbal, la structure et réécris 3 versions adaptées à nos produits."

    if not user_text and not media_parts:
        return

    channel_name = message.channel.name
    category_name = message.channel.category.name if message.channel.category else ""
    
    # 1. Project Specific Notes Recording
    if "vocaux-et-notes" in channel_name:
        async with message.channel.typing():
            response_text = await ask_gemini(user_text, media_parts=media_parts, channel_name=channel_name, category_name=category_name)
            
            # Save into the corresponding project memory
            project_key = "coussins" if "COUSSINS" in category_name.upper() else "ebook_handicap" if "EBOOK" in category_name.upper() else "general"
            append_project_note(project_key, user_text if not is_voice else response_text[:200], is_voice=is_voice)
            
            # If task for Mac mentioned
            if "mac" in user_text.lower() or "à faire" in user_text.lower():
                task_summary = response_text.split("\n")[0][:120] if response_text else user_text[:120]
                append_mac_task(task_summary, category=f"{category_name} - {channel_name}")
                guild = message.guild
                mac_channel = discord.utils.get(guild.text_channels, name="📋-a-faire-sur-le-mac")
                if mac_channel:
                    task_embed = discord.Embed(
                        title="📌 NOUVELLE ACTION SYNCHRONISÉE POUR LE MAC",
                        description=f"**Projet :** `{category_name}`\n**Action :** {task_summary}",
                        color=discord.Color.gold()
                    )
                    await mac_channel.send(embed=task_embed)
    
    # 2. Direct NotebookLM Channel
    elif "notebook" in channel_name:
        async with message.channel.typing():
            response_text = await query_live_notebooklm(user_text)
            if not response_text or len(response_text) < 20:
                response_text = await ask_gemini(user_text, media_parts=media_parts, channel_name=channel_name, category_name=category_name)
            response_text = f"🧠 **NOTEBOOKLM (100 SOURCES E-COMMERCE) :**\n\n{response_text}"

    # 3. Product Hunter Channel (On-demand)
    elif "chasse-produits" in channel_name:
        async with message.channel.typing():
            # Check if user specified a niche or asked general hunt
            winners_dossier = await generate_daily_winning_products(count=5, specific_niche=user_text)
            response_text = f"🎯 **RADAR WINNERS VALIDÉS (MÉTHODE FOCUS & ZEZINHO / FRANCE) :**\n\n{winners_dossier}"
            
    # 4. All other QG and General channels
    else:
        async with message.channel.typing():
            response_text = await ask_gemini(user_text, media_parts=media_parts, channel_name=channel_name, category_name=category_name)
            
        # Google Sheet bridge extraction
        if "sheet" in user_text.lower() or "tableau" in user_text.lower():
            product_dict = parse_product_dossier_to_dict(response_text if len(response_text) > 100 else user_text)
            push_res = push_to_google_sheet(product_dict)
            if push_res.get("success"):
                response_text += f"\n\n📊 **GOOGLE SHEETS :** {push_res.get('message')}"
            elif "GOOGLE_SHEET_WEBHOOK_URL" not in os.environ or not os.environ.get("GOOGLE_SHEET_WEBHOOK_URL"):
                response_text += f"\n\n💡 *[PONT GOOGLE SHEETS PRÊT]* : Dès que tu ajoutes l'URL de ton Webhook Google Sheet, ce produit y sera injecté avec ses 36 colonnes !"

        # Mac task extraction if needed
        if "tâche mac" in user_text.lower() or "à faire sur le mac" in user_text.lower() or "a-faire-sur-le-mac" in channel_name:
            task_summary = response_text.split("\n")[0][:120] if response_text else user_text[:120]
            append_mac_task(task_summary, category=channel_name)
            guild = message.guild
            mac_channel = discord.utils.get(guild.text_channels, name="📋-a-faire-sur-le-mac")
            if mac_channel and mac_channel.id != message.channel.id:
                task_embed = discord.Embed(
                    title="📌 NOUVELLE ACTION SYNCHRONISÉE POUR LE MAC",
                    description=f"**Source :** Salon `#{channel_name}`\n**Action :** {task_summary}",
                    color=discord.Color.green()
                )
                await mac_channel.send(embed=task_embed)
    
    # Log recent activity
    mem = load_shared_memory()
    mem["recent_activities"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "category": category_name,
        "channel": channel_name,
        "user_prompt": user_text[:150],
        "bot_summary": response_text[:200]
    })
    mem["recent_activities"] = mem["recent_activities"][-50:]
    save_shared_memory(mem)
    
    # Reply split
    if len(response_text) <= 2000:
        await message.reply(response_text)
    else:
        chunks = [response_text[i:i+1950] for i in range(0, len(response_text), 1950)]
        for chunk in chunks:
            await message.channel.send(chunk)

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
