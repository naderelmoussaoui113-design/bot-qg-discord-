import os
import asyncio
import discord
from dotenv import load_dotenv

load_dotenv("/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/BOT_QG_DISCORD/.env")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "1540374293416771625"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

STRUCTURE = [
    {
        "category": "👑 PILOTAGE & QG",
        "channels": [
            ("☀️-rapport-du-matin", "Briefing matinal automatique (Shopify, CA, commandes, priorités du jour)."),
            ("🎙️-vocaux-et-notes", "Envoie tes vocaux en vrac, le bot les écoute et les structure en tâches."),
            ("📋-a-faire-sur-le-mac", "Liste synchronisée des tâches et actions à exécuter sur ton Mac."),
            ("💡-brainstorming-general", "Discussion stratégique libre et réflexion business.")
        ]
    },
    {
        "category": "🛏️ PROJET : BOUTIQUE COUSSINS",
        "channels": [
            ("🛍️-offres-et-bundles", "Création d'offres irrésistibles ($100M Offers), packs solo/duo/famille pour booster le panier moyen."),
            ("✍️-copywriting-et-pubs", "Scripts TikTok/Meta Ads, hooks et angles marketing pour les coussins."),
            ("📧-emails-et-sms", "Séquences d'abandon de panier, e-mails de bienvenue et SMS flash."),
            ("🤝-recrutement-ugc", "Scripts de démarchage pour influenceurs et créateurs de contenu TikTok.")
        ]
    },
    {
        "category": "📖 PROJET : EBOOK HANDICAP",
        "channels": [
            ("📖-strategie-et-volume-2", "Stratégie globale du livre, chapitres, retours et préparation du Volume 2."),
            ("🧠-interrogation-notebooklm", "Interroge en direct tes carnets et sources NotebookLM sur le handicap."),
            ("✍️-pubs-et-acquisition", "Angles d'attaque publicitaires et hooks poignants pour vendre l'ebook.")
        ]
    },
    {
        "category": "🎯 TREND TRACK & SOURCING",
        "channels": [
            ("🎯-chasse-produits-winners", "Validation de produits Trend Track selon tes critères stricts (Verdict GO/NO-GO)."),
            ("🧮-calculateur-cogs-marges", "Calculateur express de prix d'achat, livraison, seuil de rentabilité ROAS et marge nette > 70%."),
            ("⛏️-mine-avis-amazon", "Analyse des avis 1-2 étoiles des leaders pour exploiter leurs faiblesses et leur voler leurs clients.")
        ]
    },
    {
        "category": "🕵️ INTELLIGENCE & SAV",
        "channels": [
            ("🕵️-espionnage-pubs-tiktok-meta", "Envoie une vidéo ou photo de pub concurrente ➜ Décomposition du Hook et réécriture de 3 versions."),
            ("🛡️-demineur-sav-objections", "Réponses persuasives en 5s pour transformer les clients hésitants ou mécontents en acheteurs."),
            ("🏢-demarchage-b2b-gros", "Pitchs de vente en gros pour kinésithérapeutes, ostéopathes et associations.")
        ]
    },
    {
        "category": "🚀 NOUVEAUX SHOPS",
        "channels": [
            ("🚀-lancement-nouveau-projet", "Incubateur prêt à accueillir n'importe quelle nouvelle marque ou nouveau projet.")
        ]
    }
]

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"Guild {GUILD_ID} not found. Available guilds: {[g.name for g in client.guilds]}")
        guild = client.guilds[0] if client.guilds else None
    
    if not guild:
        print("No guild found!")
        await client.close()
        return
        
    print(f"Connected to Server: {guild.name} (ID: {guild.id})")
    
    # Create Categories & Channels
    for section in STRUCTURE:
        cat_name = section["category"]
        existing_cat = discord.utils.get(guild.categories, name=cat_name)
        if not existing_cat:
            print(f"Creating category: {cat_name}")
            existing_cat = await guild.create_category(cat_name)
        else:
            print(f"Category already exists: {cat_name}")
            
        for chan_name, topic in section["channels"]:
            existing_chan = discord.utils.get(existing_cat.channels, name=chan_name)
            if not existing_chan:
                print(f" - Creating channel: {chan_name}")
                new_chan = await guild.create_text_channel(name=chan_name, category=existing_cat, topic=topic)
                # Send welcome message
                embed = discord.Embed(
                    title=f"Bienvenue dans le salon {chan_name}",
                    description=topic,
                    color=discord.Color.from_rgb(192, 0, 101)
                )
                embed.set_footer(text="Mon Associé IA • 24h/24 connecté à Gemini Pro & Google Search")
                await new_chan.send(embed=embed)
            else:
                print(f" - Channel already exists: {chan_name}")

    print("\n✅ All Categories and Channels are successfully verified / created!")
    await client.close()

client.run(TOKEN)
