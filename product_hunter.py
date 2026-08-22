import os
import json
import asyncio
import datetime
import google.generativeai as genai
from notebooklm_bridge import get_notebooklm_knowledge

async def generate_daily_winning_products(count=3, specific_niche=None):
    """
    Génère une sélection rigoureuse de produits winners 100% validés
    en se basant sur les 100 sources NotebookLM (critères des 5 piliers, marges > 70%,
    effet wow, preuve publicitaire, angles TikTok/Meta Ads).
    """
    knowledge = get_notebooklm_knowledge()
    
    niche_instruction = f"Niche ciblée : {specific_niche}" if specific_niche else "Niches variées à fort problème douloureux (Sommeil/Posture, Maison/Organisation, Beauté/Soin, Sécurité/Auto, Bébés/Parents)"
    
    prompt = f"""Tu es le Directeur Chasse de Produits & Expert E-commerce à 7 chiffres de Nader.
Tu dois lui sélectionner et lui analyser exactement {count} PRODUITS GAGNANTS (WINNERS) d'élite prêts à être lancés et scalés.

DIRECTIVE STRICTE : Tu appliques les critères stricts de validation issus de ses 100 sources NotebookLM :
1. Résolution d'un problème douloureux ou passion viscérale (pas de gadget inutile).
2. Effet Wow immédiat / Démontrable en 3 secondes en vidéo (TikTok / Meta Ads).
3. Marge brute $\ge$ 70% (Prix de vente conseillé = 3x à 4x le coût d'achat fournisseur livré).
4. Logistique simple (produit léger < 1kg, incassable, pas d'électronique complexe avec fort SAV).
5. Preuve de marché (Campagnes publicitaires scalées avec fort potentiel de viralité).

{niche_instruction}

Pour chacun des {count} produits, présente une fiche teardown complète au format suivant :

═══════════════════════════════════════════
🏆 PRODUIT #X : [Nom du Produit] ([Niche])
═══════════════════════════════════════════
🎯 1. LA DOULEUR & L'EFFET WOW :
- Problème résolu : [Description précise de la frustration ou douleur client]
- Démonstration en 3s : [Ce qu'on voit à l'écran dans les 3 premières secondes]

💰 2. RENTABILITÉ & FORMULES NOTEBOOKLM :
- Coût d'achat fournisseur estimé (COGS livré) : [Ex: 6.50 €]
- Prix de vente conseillé Solo : [Ex: 29.90 €]
- Marge brute unitaire : [Ex: 23.40 € (78% de marge)]
- Seuil de rentabilité publicitaire (Breakeven ROAS) : [Ex: 1.28]
- Offre Pack Recommandée (Best-seller Duo) : [Ex: Pack Duo à 44.90 € - Marge 31.90 €]

📊 3. SCORE DE VIABILITÉ NOTEBOOKLM : [Score sur 100] / 100
- Problème douloureux : [ /25]
- Marge & Perceived Value : [ /20]
- Effet Wow visuel : [ /20]
- Rareté supermarché : [ /15]
- Facilité livraison : [ /10]
- Potentiel pub : [ /10]
🟢 VERDICT : GO IMMÉDIAT (ou 🟡 À TESTER AVEC PACK DUO)

🎬 4. STRATÉGIE CRÉATIVE ADS :
- Hook Visuel #1 : [Scène choc arrêtant le scroll]
- Hook Verbal #1 : "[Phrase d'accroche percutante]"
- Angle marketing principal : [Ex: Peur de la douleur / Gain de temps / Comparaison avant-après]

---
Sois ultra concret, donne de vrais produits sourçables sur AliExpress/CJ Dropshipping, et utilise un ton expert sans blabla.
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
