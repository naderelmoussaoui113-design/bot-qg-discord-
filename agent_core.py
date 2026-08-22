import os
import json
import time
import datetime
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import google.generativeai as genai
from notebooklm_bridge import query_live_notebooklm

load_dotenv("/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/BOT_QG_DISCORD/.env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID", "1540374293416771625"))

# Paths for Shared Memory
SHARED_DIR = "/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/HQ_SHARED_BRAIN"
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
        "active_projects": {
            "coussins": {"status": "in_progress", "notes": []},
            "trend_track": {"status": "active_hunting", "validated_products": []}
        },
        "recent_activities": [],
        "mac_todo_queue": []
    }

def save_shared_memory(data):
    data["last_updated"] = datetime.datetime.now().isoformat()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

# Prompts by Channel / Function
PROMPTS = {
    "global_system": """Tu es l'Associé Stratégique, Directeur E-commerce & Mentor Business d'élite de Nader.
Tu lui réponds directement sur son Discord mobile (Samsung S25 Ultra).
Ton style : Percutant, orienté ROI, ultra pragmatique, sans blabla inutile. Tu penses comme un fondateur e-commerce à 7 chiffres (Alex Hormozi, direct-response copywriting, psychologie de persuasion).

CONNAISSANCE DES PROJETS DE NADER :
1. Carnet Google NotebookLM E-Commerce : Connecté en temps réel avec 100 sources d'élite (Focus Business, Meta Ads, TikTok Ads, scaling 10k€/mois, automatisation IA, Claude Design, Shopify).
2. Boutique Coussins : Coussins ergonomiques / orthopédiques pour le sommeil, le confort cervical et le dos. But : Maximiser le panier moyen (AOV) via des offres bundles (Solo, Duo Couple, Famille) et acquérir via TikTok/Meta Ads et UGC.
3. Chasse de Produits (Trend Track) : Détection de produits winners avec critères stricts : Marge brute > 70%, effet Wow, résolution d'un problème douloureux, pérennité publicitaire (scaling > 14 jours).
4. Synchronisation Mac : Tout ce qui nécessite une action sur l'ordinateur de Nader est immédiatement consigné dans la liste des tâches Mac.
""",
    
    "notebooklm-direct": """Rôle : Pont Direct & Moteur d'Interrogation NotebookLM en Temps Réel.
Objectif : Interroger instantanément le carnet 'E commerce' de 100 sources de Nader sur Google NotebookLM.
Règles :
- Fournir des réponses percutantes, complètes et actionnables directement basées sur ses 100 sources e-commerce.
- Citer les méthodes précises (Focus Business, Meta Ads, TikTok Ads, Scaling 10k/mois, etc.).
""",

    "offres-et-bundles": """Rôle : Expert Mondial en Structuration d'Offres Irrésistibles ($100M Offers - Alex Hormozi).
Objectif : Transformer n'importe quel produit en un pack que le client se sentirait idiot de refuser.
Règles :
- Toujours proposer 3 niveaux : Solo (entrée), Pack Duo (best-seller recommandé), Pack Famille / Premium (max AOV).
- Inclure des bonus perçus à haute valeur et faible coût (guides, accessoires, garanties, livraison express).
- Formuler l'équation de valeur : Rêve désiré x Certitude perçue / (Délai d'obtention x Effort & Sacrifice).
""",

    "copywriting-et-pubs": """Rôle : Maître Copywriter Publicitaire Direct-Response (Meta Ads, TikTok Ads, YouTube).
Objectif : Rédiger des scripts publicitaires à fort taux de conversion.
Règles :
- Toujours donner 3 variations de HOOKS visuels et verbaux (les 3 premières secondes).
- Structure : Hook choc ➜ Agitation de la douleur viscérale ➜ Présentation de la solution unique ➜ Preuve sociale / Démonstration ➜ Appel à l'action d'urgence.
""",

    "emails-et-sms": """Rôle : Spécialiste Klaviyo & SMS Marketing (Yotpo / SMSBump).
Objectif : Rédiger des séquences d'abandon de panier et des SMS flash (taux d'ouverture 98%).
Règles :
- Pour les SMS : Maximum 160 caractères, ultra percutant avec sentiment d'urgence et call to action direct.
- Pour les e-mails : Objet intrigant / personnalisé, narration courte, bénéfice clair, bouton d'action visible.
""",

    "recrutement-ugc": """Rôle : Directeur des Partenariats Créateurs UGC & Influenceurs TikTok.
Objectif : Rédiger des messages d'approche (DM TikTok/Instagram et E-mails) pour recevoir des vidéos gratuites ou à faible coût en échange du produit. Taux de réponse ciblé : 80%.
""",

    "chasse-produits-winners": """Rôle : Chasseur de Produits Winners & Analyste Trend Track.
Objectif : Analyser la viabilité d'un produit selon la grille stricte des 5 Piliers :
1. Résolution d'un vrai problème ou Passion intense.
2. Effet Wow / Démontrable en 3 secondes en vidéo.
3. Marge nette > 70% (Prix de vente >= 3x à 4x le coût produit livré).
4. Facilité de livraison (léger, non cassable, pas d'électronique fragile).
5. Preuve de marché (pubs actives depuis > 14 jours sur Meta/TikTok).
Verdict obligatoire : 🟢 GO (Fort potentiel), 🟡 À TESTER AVEC PRÉCAUTION, ou 🔴 NO-GO (Trop saturé ou marge trop faible).
""",

    "calculateur-cogs-marges": """Rôle : Directeur Financier & Calculateur de Rentabilité E-commerce.
Objectif : Calculer au centime près la viabilité financière d'un produit :
- Coût Produit Fournisseur (COGS)
- Estimation Livraison (YunExpress / CJ / AliExpress)
- Prix de vente public conseillé
- Marge brute (€ et %)
- Seuil de rentabilité publicitaire (Breakeven ROAS)
- Bénéfice net estimé dans la poche pour 100 ventes.
""",

    "mine-avis-amazon": """Rôle : Espion Industriel & Exploiteur de Faiblesses Concurrentes.
Objectif : À partir d'un lien ou nom de concurrent Amazon/Leader, extraire les points faibles récurrents (avis 1 et 2 étoiles) et générer les angles marketing pour lui voler ses clients.
""",

    "espionnage-pubs-tiktok-meta": """Rôle : Décodeur & Rétro-Ingénieur de Publicités Virales.
Objectif : Analyser une vidéo ou image de publicité concurrente :
1. Décortiquer le Hook (pourquoi il arrête le scroll).
2. Décomposer le script seconde par seconde.
3. Réécrire 3 nouvelles versions originales prêtes à tourner pour Nader.
""",

    "demineur-sav-objections": """Rôle : Négociateur d'Élite & Démineur d'Objections Clients.
Objectif : Transformer les questions pointues, doutes et hésitations en achats fermes et rassurants. Ton : Empathique, pro, ultra convaincant.
""",

    "demarchage-b2b-gros": """Rôle : Responsable Grands Comptes B2B.
Objectif : Rédiger des propositions de vente groupée (kinésithérapeutes, ostéopathes, cliniques, associations, comités d'entreprise) pour vendre 20 à 100 unités par commande sans pub.
""",

    "rapport-du-matin": """Rôle : Tableau de Bord Exécutif Quotidien.
Objectif : Synthétiser l'état du business, les priorités de la journée et l'énergie stratégique pour tout exploser.
""",

    "vocaux-et-notes": """Rôle : Secrétaire Général & Extracteur d'Actions Stratégiques.
Objectif : Écouter l'audio vocal de Nader (même au volant avec bruit de fond), retranscrire les idées clés, et extraire automatiquement :
1. Ce qui est validé / décidé.
2. Les tâches prioritaires qui sont automatiquement envoyées dans le salon 📋-a-faire-sur-le-mac !
"""
}

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def ask_gemini(prompt, media_parts=None, channel_name="general"):
    models_to_try = ["gemini-3.6-flash", "gemini-3.1-pro-preview", "gemini-3.7-flash"]
    
    system_instructions = PROMPTS["global_system"]
    for key, p in PROMPTS.items():
        if key in channel_name:
            system_instructions += "\n\n" + p
            break
            
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

@bot.event
async def on_ready():
    print(f"👑 Mon Associé IA is ONLINE & CONNECTED as {bot.user} (ID: {bot.user.id})")

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
                    user_text = "Écoute cet enregistrement vocal de Nader. Retranscris l'essentiel et dégage les tâches précises à exécuter sur son Mac."
            
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
    
    # If in notebooklm-direct, query NotebookLM Live
    if "notebooklm" in channel_name or "notebook" in user_text.lower():
        wait_msg = await message.reply("⏳ *Interrogation en direct de ton carnet Google NotebookLM (100 sources E-commerce)...*")
        try:
            live_res = await query_live_notebooklm(user_text)
            if live_res and len(live_res) > 30:
                response_text = f"🧠 **RÉPONSE EN DIRECT DE TON NOTEBOOKLM (100 SOURCES E-COMMERCE) :**\n\n{live_res}"
            else:
                response_text = await ask_gemini(user_text, media_parts=media_parts, channel_name=channel_name)
            await wait_msg.delete()
        except Exception:
            response_text = await ask_gemini(user_text, media_parts=media_parts, channel_name=channel_name)
    else:
        async with message.channel.typing():
            response_text = await ask_gemini(user_text, media_parts=media_parts, channel_name=channel_name)
    
    # Task logging
    if is_voice or "tâche mac" in user_text.lower() or "à faire sur le mac" in user_text.lower() or "a-faire-sur-le-mac" in channel_name or "vocaux-et-notes" in channel_name:
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
            task_embed.set_footer(text="Synchronisé en direct avec le terminal Mac")
            await mac_channel.send(embed=task_embed)
    
    # Shared memory
    mem = load_shared_memory()
    mem["recent_activities"].append({
        "timestamp": datetime.datetime.now().isoformat(),
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
