import os
import asyncio
import discord
from dotenv import load_dotenv

load_dotenv("/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/BOT_QG_DISCORD/.env")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "1540374293416771625"))

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if guild:
        qg_cat = discord.utils.get(guild.categories, name="👑 PILOTAGE & QG")
        if qg_cat:
            # Check if channel already exists in QG
            chan = discord.utils.get(qg_cat.channels, name="🧠-notebooklm-direct")
            if not chan:
                # Check if it was in another category
                old_chan = discord.utils.get(guild.channels, name="🧠-interrogation-notebooklm")
                if old_chan:
                    await old_chan.edit(name="🧠-notebooklm-direct", category=qg_cat, topic="Pont direct vers tous tes carnets, notes et recherches Google NotebookLM en temps réel.")
                    print("Moved and renamed channel to 👑 PILOTAGE & QG!")
                else:
                    new_chan = await guild.create_text_channel(name="🧠-notebooklm-direct", category=qg_cat, topic="Pont direct vers tous tes carnets, notes et recherches Google NotebookLM en temps réel.")
                    print("Created 🧠-notebooklm-direct in 👑 PILOTAGE & QG!")
    await client.close()

client.run(TOKEN)
