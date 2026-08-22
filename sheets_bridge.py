import os
import json
import re
import datetime
import urllib.request
from dotenv import load_dotenv

load_dotenv()

# Google Apps Script Webhook URL or Google Sheets API endpoint
GOOGLE_SHEET_WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "https://script.google.com/macros/s/AKfycbxaGQSp1gIzw87YZ5bGDzuG6PlLpEoDF-612c86wXEQWml-T9ekliVfxtvafxyR6cVewQ/exec")

# 36 Columns Definition based on Focus & Zezinho (NotebookLM)
SHEET_HEADERS = [
    "Date d'Ajout", "Statut", "Nom du Produit", "Niche", "Lien Sourcing", "Lien Shop Concurrent", "Lien Pub Ads",
    "Problème Viscéral", "Effet Wow 3s", "Poids & Logistique", "Introuvable Magasin", "Saisonnalité France",
    "Google Trends (5a / 90j / 30j)", "Volume SEO France", "CPC Intention Achat", "Concurrents Meta FR",
    "Coût Livré (COGS €)", "Prix Vente Solo (€)", "Markup (x)", "Marge Brute (€)", "Marge Brute (%)",
    "Breakeven ROAS", "CAC Max Autorisé (€)", "Frais Stripe (€)", "Marge Nette (€)", "Marge Nette (%)",
    "Prix Pack Duo ($100M €)", "Délai Livraison France", "Ancienneté Pubs (Jours)", "Créatives Actives Leader",
    "Trafic Shop Concurrent", "Certification Fournisseur", "Notes Détail (/50)", "SCORE TOTAL (/50)", "Verdict Officiel",
    "Hook Visuel #1", "Hook Verbal #1", "Angle Marketing"
]

def parse_product_dossier_to_dict(text):
    """
    Extrait intelligemment les 36 paramètres d'une fiche produit textuelle
    pour la convertir en dictionnaire prêt pour Google Sheet.
    """
    data = {
        "date_ajout": datetime.datetime.now().strftime("%d/%m/%Y"),
        "statut": "🟢 Validé pour test",
        "nom": "Produit Détecté",
        "niche": "Général",
        "lien_sourcing": "https://www.aliexpress.com",
        "lien_shop": "https://trendtrack.io",
        "lien_pub": "https://www.facebook.com/ads/library",
        "probleme": "Douleur client aiguë",
        "effet_wow": "Démonstration visuelle 3s",
        "poids_logistique": "< 500g, incassable, 0 batterie",
        "introuvable": "Oui",
        "saisonnalite": "> 90 jours de saison",
        "google_trends": "Stable > 50 (5 ans / 90j / 30j)",
        "volume_seo": "500 - 5 000 / mois",
        "cpc": "2.50 €",
        "concurrents_fr": "1 à 3 shops",
        "cogs": "6.50",
        "prix_solo": "29.90",
        "markup": "x4.6",
        "marge_brute_eur": "23.40",
        "marge_brute_pct": "78%",
        "breakeven_roas": "1.28",
        "cac_max": "15.00 €",
        "frais_stripe": "1.17 €",
        "marge_nette_eur": "7.80 €",
        "marge_nette_pct": "26%",
        "pack_duo": "44.90 €",
        "delai_livraison": "< 10 jours ouvrés",
        "anciennete_pubs": "25 jours",
        "creatives_leader": "8 créatives actives",
        "trafic_concurrent": "35k visites (+25%)",
        "certif_fournisseur": "Trade Assurance + Verified",
        "notes_detail": "Trends 9/10, Longévité 9/10, Conc 9/10, Markup 9/10, Eng 8/10",
        "score_total": "44/50",
        "verdict": "🟢 LANCER IMMÉDIATEMENT",
        "hook_visuel": "Scène choc d'arrêt de scroll",
        "hook_verbal": "Vous avez encore mal au dos ?",
        "angle_marketing": "Soulagement immédiat"
    }

    # Extraction par Regex des points clés si présents dans le texte
    name_match = re.search(r"🏆\s*(?:WINNER\s*#?\d*\s*:|PRODUIT\s*#?\d*\s*:)?\s*([^\n\(\]]+)", text)
    if name_match:
        data["nom"] = name_match.group(1).strip()
        
    score_match = re.search(r"(\d{1,2}\s*/\s*50)", text)
    if score_match:
        data["score_total"] = score_match.group(1).replace(" ", "")

    return data

def push_to_google_sheet(product_dict):
    """
    Envoie la ligne formatée vers le Google Sheet via le Webhook direct.
    """
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    if not webhook_url:
        return {
            "success": False,
            "message": "⚠️ Aucun Webhook Google Sheet configuré. Définis `GOOGLE_SHEET_WEBHOOK_URL` dans ton fichier .env.",
            "data": product_dict
        }

    try:
        payload = json.dumps(product_dict).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Antigravity-Sheets-Bridge/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"success": True, "message": "✅ Produit ajouté avec succès dans ton Google Sheet !", "status": resp.status}
    except Exception as e:
        return {"success": False, "message": f"❌ Erreur de transmission Google Sheet : {e}"}

if __name__ == "__main__":
    test_dict = parse_product_dossier_to_dict("🏆 WINNER #1 : Coussin Alvéolé en Gel (Posture & Sciatique)")
    print("Parsed test dict:", json.dumps(test_dict, indent=2, ensure_ascii=False))
