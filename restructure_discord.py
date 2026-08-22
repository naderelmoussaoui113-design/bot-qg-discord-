import os
import asyncio
import discord
from dotenv import load_dotenv

load_dotenv("/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/BOT_QG_DISCORD/.env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "1540374293416771625"))

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

# Target structure
NEW_CATEGORIES = {
    "👑 PILOTAGE ET QG": [
        "🌅-rapport-du-matin",
        "💡-brainstorming-general",
        "🧠-notebook-lm-direct",
        "📈-strategie-marketing",
        "🎯-offres-et-bundles",
        "🎬-copywriting-pubs-acquisition",
        "✉️-emails-et-sms",
        "🎯-chasse-produits-winners",
        "🔢-calculateur-cogs-marges",
        "⛏️-mine-avis-amazon",
        "🕵️-espionnage-pubs-tiktok-meta",
        "🛡️-demineur-sav-objections",
        "🏢-demarchage-b2b-gros",
        "📋-a-faire-sur-le-mac"
    ],
    "🛋️ PROJET BOUTIQUE COUSSINS": [
        "🎙️-vocaux-et-notes"
    ],
    "📚 PROJET EBOOK HANDICAP": [
        "🎙️-vocaux-et-notes"
    ]
}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"Guild {GUILD_ID} not found!")
        await client.close()
        return

    print(f"Restructuring Guild: {guild.name} ({guild.id})")

    # 1. Clean up old channels / categories
    # Map existing categories
    existing_cats = {c.name.lower(): c for c in guild.categories}
    
    # We will build categories
    for cat_name, channels in NEW_CATEGORIES.items():
        # Look for category
        target_cat = None
        for c in guild.categories:
            if cat_name.lower().replace("👑 ", "").replace("🛋️ ", "").replace("📚 ", "") in c.name.lower():
                target_cat = c
                if c.name != cat_name:
                    await c.edit(name=cat_name)
                break
        
        if not target_cat:
            print(f"Creating category: {cat_name}")
            target_cat = await guild.create_category(name=cat_name)
        
        # Create/move channels
        for ch_name in channels:
            # Check if channel exists anywhere
            existing_ch = None
            clean_ch = ch_name.split("-", 1)[-1] if "-" in ch_name else ch_name
            for ch in guild.text_channels:
                if clean_ch in ch.name:
                    existing_ch = ch
                    break
            
            if existing_ch:
                print(f"Updating channel {existing_ch.name} -> {ch_name} under {cat_name}")
                await existing_ch.edit(name=ch_name, category=target_cat)
            else:
                print(f"Creating channel {ch_name} under {cat_name}")
                await guild.create_text_channel(name=ch_name, category=target_cat)

    # 2. Clean up obsolete channels and categories
    valid_cat_ids = []
    for c in guild.categories:
        # Check if category name matches any of our target categories
        is_valid_cat = any(k.lower().replace("👑 ", "").replace("🛋️ ", "").replace("📚 ", "") in c.name.lower() for k in NEW_CATEGORIES.keys())
        if not is_valid_cat:
            print(f"Deleting obsolete category: {c.name}")
            for ch in c.channels:
                print(f"Deleting obsolete channel: {ch.name}")
                await ch.delete()
            await c.delete()

    print("Restructuring COMPLETE!")
    await client.close()

if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)
