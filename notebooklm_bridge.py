import os
import asyncio
import google.generativeai as genai

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FILE = os.path.join(CURRENT_DIR, "knowledge", "ECOMMERCE_100_SOURCES.txt")

def get_notebooklm_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return ""

async def query_live_notebooklm(question: str) -> str:
    knowledge_text = get_notebooklm_knowledge()
    
    prompt = f"""Tu es le moteur d'interrogation officiel du carnet Google NotebookLM 'E commerce' (100 sources) de Nader.
Voici l'intégralité du contenu et des index des 100 sources du carnet :

=== DÉBUT DES 100 SOURCES DU CARNET NOTEBOOKLM ===
{knowledge_text}
=== FIN DES SOURCES ===

Question de Nader : {question}

Directives de réponse :
1. Réponds de manière complète, ultra précise et actionnable en te basant fidèlement sur ces sources.
2. Si la question porte sur TrendTrack, cite les filtres exacts (produits ajoutés récemment, seuils de ventes/croissance, boutiques scaling, formats ads).
3. Si la question porte sur les Ads (Meta/TikTok/Snap), les Offres ($100M Offers), la fiscalité LLC ou Shopify, cite les étapes concrètes contenues dans les sources.
4. Utilise un formatage soigné avec emojis, puces et gras pour une lisibilité parfaite sur Discord mobile.
"""
    
    models = ["gemini-3.6-flash", "gemini-3.1-pro-preview", "gemini-3.7-flash"]
    for m in models:
        try:
            model = genai.GenerativeModel(model_name=m)
            res = await asyncio.to_thread(model.generate_content, prompt)
            if res and res.text:
                return res.text
        except Exception:
            continue
            
    return "Désolé, impossible d'interroger la base NotebookLM pour le moment."
