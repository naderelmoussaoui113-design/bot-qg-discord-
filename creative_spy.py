import os
import json
import asyncio
import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from trendtrack_client import fetch_top_hooks, fetch_tiktok_ads, fetch_scaling_shops
from notebooklm_bridge import get_notebooklm_knowledge

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_daily_creative_spy(specific_niche=None):
    """
    Scraper et Analyseur Automatique de Publicités Gagnantes (TikTok & Meta Ads France/Europe) :
    - Récupère les données réelles de scaling via TrendTrack (Top Hooks, Créatives TikTok, Shops à 6-7 chiffres).
    - Décortique les 3 créatives les plus rentables du moment selon la méthode Focus & Zezinho.
    - Fournit les Hooks visuels 0-3s, les scripts mot à mot et 3 déclinaisons UGC prêtes à tourner.
    """
    hooks_data = fetch_top_hooks()
    tiktok_ads = fetch_tiktok_ads(limit=10)
    scaling_shops = fetch_scaling_shops(limit=8)
    knowledge = get_notebooklm_knowledge()
    
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    context_str = f"Date d'analyse : {current_date}\n"
    if hooks_data:
        context_str += f"• Hooks publicitaires en forte traction : {json.dumps(hooks_data[:5], ensure_ascii=False)}\n"
    if tiktok_ads:
        context_str += f"• Créatives TikTok scalées détectées : {json.dumps(tiktok_ads[:5], ensure_ascii=False)}\n"
    if scaling_shops:
        context_str += f"• Boutiques Shopify en hyper-croissance (>20k€/mois) : {json.dumps([s.get('domain') for s in scaling_shops if isinstance(s, dict)], ensure_ascii=False)}\n"
        
    niche_focus = f"Focus demandé par Nader : {specific_niche}" if specific_niche else "Toutes niches e-commerce rentables (Problème viscéral, Wow Effect 3s, Santé/Ergonomie, Maison/Pratique, Auto, Animaux, Bébés)"

    prompt = f"""Tu es le Directeur Créatif Ads & Expert en Vidéos Publicitaires TikTok / Meta Ads à 7 chiffres de Nader.
Tu appliques STRICTEMENT la stratégie d'Arbitrage Géographique "Machine à Remonter le Temps" de la méthode Focus & Zezinho (NotebookLM) :

STRATÉGIE FOCUS & ZEZINHO D'ARBITRAGE GÉOGRAPHIQUE :
1. Tu espionnes en priorité les marchés précurseurs qui ont 3 à 6 mois d'avance : USA, UK, ALLEMAGNE (DE) et TIKTOK GLOBAL.
2. Tu repères les créatives virales qui scalent actuellement à plusieurs dizaines de milliers de dollars/euros par jour là-bas.
3. Tu vérifies la saturation sur le marché FRANCE (Timing parfait : 0 à 5 concurrents actifs sur la France).
4. Tu réécris et adaptes les Hooks et les Scripts en français natif percutant (avec les codes culturels et la psychologie d'achat française).

DONNÉES MARCHÉ EN DIRECT (TrendTrack USA/UK/EU & TikTok Global) :
{context_str}

{niche_focus}

MISSION :
Génère le dossier d'espionnage publicitaire du jour : analyse les 3 MEILLEURES CRÉATIVES PUBLICITAIRES VIRALES qui cartonnent aux USA / UK / EUROPE et fournis leur déclinaison prête à lancer et dominer le marché français.

Pour chacune des 3 publicités, fournis une structure chirurgicale :

═══════════════════════════════════════════════════════════════════════════════
🎬 CRÉATIVE WINNER #[1-3] : [NOM DU PRODUIT / ANGLE PUBLICITAIRE]
Marché d'origine : [USA / UK / DE / Global] ➔ Cible d'arbitrage : FRANCE (Boulevard sans concurrence)
Niche : [Niche] | Format : [TikTok Ads / Reels Meta] | Durée idéale : 25-35s
═══════════════════════════════════════════════════════════════════════════════

1. ⚡ LE HOOK D'ARRÊT DE SCROLL (0-3 SECONDES) :
- Hook Visuel : [Description précise de l'action choquante, inattendue ou du mouvement caméra utilisé aux USA/EU]
- Hook Verbal US/Source : "[Phrase d'accroche originale en anglais/source]"
- Hook Verbal ADAPTÉ FRANCE (Mot à mot) : "[Phrase d'accroche percutante en français parlé naturel, sans bla-bla]"
- Texte à l'écran (Overlay) : "[Texte court en gros caractère contrasté]"
- Déclencheur psychologique : [Curiosité / Peur de rater / Douleur aiguë / Comparaison Avant-Après]

2. 🧠 STRUCTURE DU SCRIPT DÉCORTIQUÉE (Framework PAS / AIDA) :
- 00:00 - 00:03 (Hook) : [Accroche et rupture de pattern]
- 00:03 - 00:10 (Agitation du problème) : [Identification viscérale à la douleur du prospect]
- 00:10 - 00:20 (Découverte & Démonstration Wow) : [Preuve visuelle irréfutable du produit en action]
- 00:20 - 00:30 (Offre irrésistible & Appel à l'action) : [Scarcity + Bundle / Promo d'urgence]

3. 🎙️ SCRIPT COMPLET MOT À MOT EN FRANÇAIS (PRÊT À LIRE PAR LE CRÉATEUR UGC) :
"[Rédige le script intégral mot à mot que le créateur de contenu doit réciter devant sa caméra avec les indications de jeu d'acteur entre parenthèses]"

4. 🔄 3 VARIANTES DE HOOKS POUR L'A/B TESTING :
- Variante A (Angle 'J'ai testé...') : "[Hook verbal]"
- Variante B (Angle 'Arrête de faire ça...') : "[Hook verbal]"
- Variante C (Angle 'Le secret des pros...') : "[Hook verbal]"

---
RÈGLE OBLIGATOIRE : Sois percutant, moderne, utilise le vocabulaire du marché français e-commerce 2026. Complète les 3 créatives de #1 à #3 intégralement sans couper.
"""

    models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    for m in models:
        try:
            model = genai.GenerativeModel(
                model_name=m,
                generation_config={"temperature": 0.75, "max_output_tokens": 8192}
            )
            res = await asyncio.to_thread(model.generate_content, prompt)
            if res and res.text:
                return res.text
        except Exception as e:
            print(f"Error in creative_spy model {m}: {e}")
            continue
            
    return "⚠️ Impossible de générer l'espionnage de créatives pour le moment."
