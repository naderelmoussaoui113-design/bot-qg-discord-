import os
import json
import asyncio
import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from notebooklm_bridge import get_notebooklm_knowledge
from trendtrack_client import get_live_trendtrack_summary, fetch_scaling_shops, fetch_tiktok_ads

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_daily_winning_products(count=3, specific_niche=None):
    """
    Génère une sélection de produits gagnants (winners) d'élite en croisant :
    1. L'API TrendTrack en direct (Boutiques scalées, TikTok Library, Top Ads)
    2. Les critères stricts des 100 sources NotebookLM (Les 5 piliers, Marges > 70%, Effet Wow)
    3. Les formules de direct-response marketing (Score sur 100, Hooks TikTok/Meta).
    """
    knowledge = get_notebooklm_knowledge()
    trendtrack_data = get_live_trendtrack_summary()
    
    niche_instruction = f"Niche ciblée par Nader : {specific_niche}" if specific_niche else "Niches variées à fort problème douloureux (Sommeil/Ergonomie, Maison/Pratique, Beauté/Soin, Bébés/Sécurité, Confort/Auto)"
    
    prompt = f"""Tu es le Directeur Chasse de Produits d'Élite & Expert E-commerce à 7 chiffres de Nader.
Tu disposes d'une connexion directe à l'API TrendTrack et à l'intégralité des 100 sources NotebookLM de Nader.

DONNÉES EN DIRECT DE L'API TRENDTRACK :
- Boutiques scalées surveillées : {trendtrack_data.get('recent_scaling_domains')}
- Volume de créatives TikTok en scaling : {trendtrack_data.get('tiktok_creatives_count')} annonces analysées

DIRECTIVES DE VALIDATION STRICTE (ISSUES DES 100 SOURCES NOTEBOOKLM) :
1. Résolution d'un vrai problème physique ou émotionnel (douleur, stress, sommeil, posture, temps, sécurité).
2. Effet Wow immédiat / Démontrable en moins de 3 secondes en vidéo (Hook visuel évident).
3. Marge brute $\ge$ 70% (Prix de vente conseillé = 3x à 4x le coût fournisseur livré).
4. Logistique fluide (produit léger < 1kg, incassable, pas d'électronique sensible avec retours).
5. Preuve de marché (Campagnes publicitaires scalées sur Meta Ad Library et TikTok Ads).

{niche_instruction}

Sélectionne exactement {count} PRODUITS GAGNANTS D'ÉLITE et présente une fiche Teardown complète pour chacun :

═══════════════════════════════════════════
🏆 PRODUIT #X : [Nom du Produit] ([Niche])
═══════════════════════════════════════════
🎯 1. LA DOULEUR & L'EFFET WOW :
- Problème résolu : [Description précise de la frustration ou douleur viscérale]
- Démonstration en 3s : [Ce qu'on voit à l'écran dans les 3 premières secondes de vidéo]

💰 2. RENTABILITÉ & FORMULES NOTEBOOKLM :
- Coût d'achat fournisseur estimé (COGS livré AliExpress/CJ) : [Ex: 6.80 €]
- Prix de vente conseillé Solo : [Ex: 29.90 €]
- Marge brute unitaire : [Ex: 23.10 € (77% de marge)]
- Seuil de rentabilité publicitaire (Breakeven ROAS) : [Ex: 1.29]
- Offre Pack Recommandée ($100M Offers Duo) : [Ex: Pack Duo à 44.90 € - Marge 31.30 €]

📊 3. SCORE DE VIABILITÉ NOTEBOOKLM : [Score sur 100] / 100
- Problème douloureux : [ /25]
- Marge & Perceived Value : [ /20]
- Effet Wow visuel : [ /20]
- Rareté supermarché : [ /15]
- Facilité livraison : [ /10]
- Potentiel publicitaire : [ /10]
🟢 VERDICT : GO IMMÉDIAT (ou 🟡 À TESTER AVEC OFFRE DUO)

🎬 4. STRATÉGIE CRÉATIVE ADS (TIKTOK & META) :
- Hook Visuel #1 : [Scène choc arrêtant le scroll]
- Hook Verbal #1 : "[Phrase d'accroche percutante]"
- Angle marketing principal : [Angle psychologique : Soulagement / Peur de rater / Avant-Après]

---
Sois ultra concret, donne de vrais produits concrets sourçables et des chiffres mathématiquement rentables.
"""

    models = ["gemini-3.6-flash", "gemini-3.1-pro-preview", "gemini-3.7-flash"]
    for m in models:
        try:
            model = genai.GenerativeModel(
                model_name=m,
                generation_config={"temperature": 0.7, "max_output_tokens": 4096}
            )
            res = await asyncio.to_thread(model.generate_content, prompt)
            if res and res.text:
                return res.text
        except Exception:
            continue
            
    return "⚠️ Impossible de générer la sélection de produits pour le moment."
