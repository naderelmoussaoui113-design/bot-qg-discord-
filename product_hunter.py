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

import random

NICHE_ROTATOR = [
    "Santé, Ergonomie & Récupération physique (Cervicales, sciatique, fasciite, posture dynamique, micro-massage)",
    "Maison, Rangement astucieux & Gain de place (Dressing, cuisine, buanderie, placards suspendus)",
    "Sécurité & Accessoires habitacle Auto / Moto (Organisation ergonomique, pare-soleil thermique, maintien)",
    "Animaux de compagnie & Bien-être anti-anxiété (Toilettage sans douleur, litière propre, griffes, brosses vapeur)",
    "Bébés & Parentalité simplifiée (Sécurité maison, transition sommeil, repas autonomes sans dégât)",
    "Beauté & Soins dermatologiques maison (Micro-courant, gua sha thermique, soin cuir chevelu, cils)",
    "Bricolage malin & Outils multi-angles ergonomiques (Gabarits de découpe, serrage magnétique, ponçage)",
    "Cuisine pratique & Conservation alimentaire (Sous-vide manuel, découpe express, décongélation rapide)",
    "Outdoor, Randonnée & Voyage nomade (Accessoires ultra-légers, confort avion/train, étanchéité)",
    "Organisation bureau & Accessoires nomades sans batterie (Support ergonomique ajustable, tapis thermique)"
]

async def generate_daily_winning_products(count=5, specific_niche=None):
    """
    Moteur de Sélection Ultime selon la méthode FOCUS & ZEZINHO (100 Sources NotebookLM) :
    - Rotation dynamique sur 10 niches différentes à chaque génération pour 0 répétition.
    - Double Cadrage (Phase 0 & 1) : Markup >= x3.5, Poids < 1kg, 0 batterie/verre
    - Validation Demande & Concurrence (Phase 2) : Trends 5 ans, SEO 500-5000 / Viral CTR >1.2%, Meta FR 1-5 shops
    - Validation Financière (Phase 3) : Formule profit, Marge nette >= 20%, Profit >= 8-15€, Livraison FR < 10j
    - Signaux Rentabilité (Phase 4 & 5) : TrendTrack Shops (10k-100k +20%), Ads actives > 14-60j, TikTok Top Ads
    - 4 Règles de Sécurité : Runway saisonnier France > 60j, Verrouillage Markup x3.5, Bundle anti-Amazon, Concurrence FR
    - Scoring /50 et Sortie de 5 Propositions Classées de #1 à #5
    """
    knowledge = get_notebooklm_knowledge()
    trendtrack_data = get_live_trendtrack_summary()
    
    current_month = datetime.datetime.now().strftime("%B %Y")
    
    if specific_niche:
        niche_instruction = f"Niche ciblée par Nader : {specific_niche}"
    else:
        sample_count = min(count, len(NICHE_ROTATOR))
        selected_niches = random.sample(NICHE_ROTATOR, sample_count)
        niche_instruction = "Tu DOIS OBLIGATOIREMENT attribuer à chaque winner une niche DIFFÉRENTE et NON RÉPÉTITIVE parmi ce tirage du jour :\n"
        for idx, n_name in enumerate(selected_niches):
            niche_instruction += f"• Winner #{idx+1} : Niche [{n_name}]\n"
        niche_instruction += "\nINTERDICTION FORMELLE de ressortir les mêmes produits récurrents (ex: masque de sommeil 3D basique, cale siège auto standard ou correcteur de posture classique). Cherche des pépites innovantes et fraîches !"
    
    prompt = f"""Tu es le Directeur Chasse de Produits d'Élite & Expert E-commerce à 7 chiffres de Nader.
Tu appliques STRICTEMENT ET SANS DÉVIATION la Méthode Complète Focus & Zezinho (issue de ses 100 sources NotebookLM).

CONTEXTE TEMPOREL & ARBITRAGE GÉOGRAPHIQUE (MÉTHODE FOCUS & ZEZINHO) :
- Stratégie "Machine à Remonter le Temps" : Tu surveilles et détectes les pépites qui scalent et valident des millions aux USA, UK, ALLEMAGNE (DE) ou NORDICS.
- Marché de déploiement de Nader : FRANCE (Union Européenne - Données réelles Meta Ad Library DSA).
- Validation Saturation France : Sweet Spot de 0 à 5 concurrents actifs sur le marché français (boulevard vierge et timing parfait pour s'imposer en leader).
- Période actuelle : {current_month} (Vérifier obligatoirement le Runway de saisonnalité > 60 jours).
- Données en direct API TrendTrack : {trendtrack_data.get('scaling_shops_count')} shops scalés scannés ({trendtrack_data.get('recent_scaling_domains')}), {trendtrack_data.get('tiktok_creatives_count')} créatives TikTok actives.

{niche_instruction}

═══════════════════════════════════════════════════════════════════════════════
GRILLE D'ÉVALUATION ET FILTRES À RESPECTER MATHÉMATIQUEMENT :
═══════════════════════════════════════════════════════════════════════════════

1. PHASE 0 & 1 (Cadrage & Filtrage Rapide 15 min - 6/7 OUI obligatoires) :
- Problème viscéral ou Effet Wow 3s.
- Prix de vente cible : 25 € à 100 € (Sweet spot : 29.90 € - 59.90 €).
- Markup d'entrée : Strictement $\ge$ x3.5 à x5 (Marge brute avant pub $\ge$ 70%).
- Logistique : Poids < 1 kg, incassable, zéro batterie lithium, zéro verre, zéro électronique complexe.
- Introuvable facilement en supermarché ou pharmacie.

2. PHASE 2 (Validation Demande & Concurrence France 30 min) :
- Google Trends France (TRIPLE VÉRIFICATION TEMPORELLE OBLIGATOIRE) :
  • Vue Macro (5 ans) : Valide la pérennité, la récurrence annuelle et élimine les modes éteintes.
  • Vue Trimestre (90 jours / 3 mois) : Valide la tendance de fond actuelle (courbe stable ou ascendante).
  • Vue Micro (30 jours / 1 mois) : Valide le MOMENTUM IMMÉDIAT (accélération des recherches pour un lancement parfait cette semaine).
- Volume SEO National France : Sweet Spot 500 à 5 000 recherches/mois (ou si produit viral pur, CTR TikTok > 1.2%).
- CPC Intention d'achat : 2 € à 5 €.
- Concurrence Meta Ad Library France : 1 à 5 concurrents actifs (Timing parfait) ou 5 à 20 (Sain). Rejet si > 50.

3. PHASE 3 (Validation Financière Chirurgicale 10 min) :
- Formule Profit : Prix TTC - Sourcing - Port - CAC (< 30% prix) - Frais Stripe (2.9% + 0.30€) - Retours.
- Marge Nette cible : $\ge$ 20 % à 25 %.
- Bénéfice Net Unitaire : $\ge$ 8 € à 15 € / commande.
- Livraison France : Strictement < 10 jours ouvrés (YunExpress / Special Line FR).

4. PHASE 4 & 5 (Signaux de Rentabilité & Filtres TrendTrack) :
- Longévité des pubs : 15 à 60+ jours actives.
- Volume créatives concurrent : 6 à 10+ créatives en scaling.
- Données TrendTrack : Shops 10k à 100k visites avec croissance > +20%, âge < 6 mois, pixel Meta.
- Sourcing : Usine Alibaba/1688 Trade Assurance, Verified Supplier, Ancienneté > 3 ans.

5. SYSTÈME DE SCORING SUR 50 :
- Trends France (/10) + Longévité Pubs (/10) + Concurrence saine FR (/10) + Markup $\ge$ x3.5 (/10) + Engagement (/10).
- Verdict : 40-50 / 50 ➜ 🟢 LANCER IMMÉDIATEMENT | 30-39 / 50 ➜ 🟡 TEST PRUDENT (Pack Duo) | < 30 / 50 ➜ 🔴 REJET.

═══════════════════════════════════════════════════════════════════════════════
FORMAT DE SORTIE OBLIGATOIRE POUR CHACUNE DES {count} PROPOSITIONS (CLASSÉES DE #1 À #{count}) :
═══════════════════════════════════════════════════════════════════════════════

Pour chaque produit, fournis la fiche Teardown complète suivante :

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 WINNER #{count-1} : [NOM DU PRODUIT] ([NICHE])
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 1. CADRAGE & DOULEUR RÉSOLUE (PHASE 0 & 1) :
- Problème viscéral résolu : [Description de la frustration client]
- Effet Wow en 3s : [Scène visuelle qui stoppe le scroll]
- Poids & Logistique : [Poids estimé, robustesse, zéro batterie/verre]
- Saisonnalité France ({current_month}) : [Runway estimé > 60-90 jours]

📊 2. VALIDATION DATA & MARCHÉ FRANCE (PHASE 2) :
- Google Trends France :
  • 5 ans (Macro/Saisonnalité) : [Tendance générale & stabilité]
  • 90 jours (Trimestre) : [Tendance actuelle]
  • 30 jours (Momentum immédiat) : [Accélération récente / Timing de lancement]
- SEO France / Intention : [Volume estimé + CPC moyen]
- Concurrents Meta Ad Library FR : [Nombre estimé de shops actifs en France]

💰 3. CALCUL FINANCIER CHIRURGICAL (PHASE 3) :
- Coût d'achat fournisseur livré (COGS) : [X.XX €]
- Prix de vente conseillé Solo : [XX.XX €] (Markup : x[X.X])
- Marge brute unitaire : [XX.XX € ([XX]%)]
- Seuil de rentabilité (Breakeven ROAS) : [X.XX]
- Marge nette estimée après pub & Stripe : [XX.XX € ([XX]%)]
- Offre $100M Recommandée : [Pack Duo Best-seller à XX.XX € avec Ebook / Garantie 30 nuits]

📈 4. SIGNAUX TRENDTRACK & PREUVES CONCURRENTIELLES (PHASE 4) :
- Ancienneté des pubs actives : [X jours / Semaines]
- Volume de créatives en scaling : [X créatives actives]
- Profil boutique concurrente (TrendTrack) : [Trafic 10k-100k, croissance, Shopify]

🔢 5. SCORING DE VALIDATION NOTEBOOKLM : [Score] / 50
- Google Trends : [ /10] | Pubs actives >7j : [ /10] | Concurrence FR : [ /10] | Markup $\ge$ x3.5 : [ /10] | Engagement : [ /10]
👉 **VERDICT OFFICIEL :** 🟢 **LANCER IMMÉDIATEMENT (Score $\ge$ 40/50)** ou 🟡 **TEST PRUDENT**

🎬 6. STRATÉGIE CRÉATIVE ADS (TIKTOK & META FRANCE) :
- Hook Visuel #1 : [Scène d'arrêt de scroll]
- Hook Verbal #1 : "[Phrase d'accroche percutante en français]"
- Angle psychologique : [Peur de la douleur / Gain de temps / Comparaison Avant-Après]

---
Sois d'une précision chirurgicale, donne de vrais produits concrets et des chiffres réels.
RÈGLE CRUCIALE : Tu DOIS terminer et compléter l'intégralité des {count} fiches produits de #1 à #{count} sans jamais couper ni abréger.
"""

    models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    for m in models:
        try:
            model = genai.GenerativeModel(
                model_name=m,
                generation_config={"temperature": 0.7, "max_output_tokens": 8192}
            )
            res = await asyncio.to_thread(model.generate_content, prompt)
            if res and res.text:
                return res.text
        except Exception as e:
            print(f"Model error {m}: {e}")
            continue
            
    return "⚠️ Impossible de générer la sélection de produits pour le moment."
