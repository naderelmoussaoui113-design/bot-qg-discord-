import os
import json
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

TRENDTRACK_API_KEY = os.getenv("TRENDTRACK_API_KEY", "sk_tt_64KrPQ4G8EpLqUJUB5FkzfLuvucHzK1LYdmtC2pbhiLaP4DDfR8ArvGe71dNM5XKy51F2x1HNTxRjseHKCqtBWvC")
BASE_URL = "https://api.trendtrack.io/v1"

def get_headers():
    return {
        "Authorization": f"Bearer {TRENDTRACK_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Antigravity-Ecom-Hunter/1.0"
    }

def fetch_scaling_shops(limit=10, category=None):
    """Récupère les boutiques Shopify qui scalent actuellement"""
    url = f"{BASE_URL}/shops?limit={limit}"
    req = urllib.request.Request(url, headers=get_headers())
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", [])
    except Exception as e:
        print(f"Error fetching shops from TrendTrack: {e}")
        return []

def fetch_top_hooks():
    """Récupère les meilleurs Hooks publicitaires extraits par TrendTrack"""
    url = f"{BASE_URL}/workspace/hooks"
    req = urllib.request.Request(url, headers=get_headers())
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", [])
    except Exception as e:
        print(f"Error fetching hooks from TrendTrack: {e}")
        return []

def fetch_tiktok_ads(limit=10):
    """Récupère les top vidéos publicitaires TikTok depuis TrendTrack"""
    url = f"{BASE_URL}/tiktok/library?limit={limit}"
    req = urllib.request.Request(url, headers=get_headers())
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", [])
    except Exception as e:
        print(f"Error fetching TikTok ads from TrendTrack: {e}")
        return []

def get_live_trendtrack_summary():
    """Génère un résumé complet du marché actuel depuis TrendTrack"""
    shops = fetch_scaling_shops(limit=5)
    hooks = fetch_top_hooks()
    tiktok_ads = fetch_tiktok_ads(limit=5)
    
    summary = {
        "scaling_shops_count": len(shops),
        "recent_scaling_domains": [s.get("domain") for s in shops if s.get("domain")],
        "top_hooks_sample": [h.get("text") or h.get("hook") for h in hooks[:5] if h],
        "tiktok_creatives_count": len(tiktok_ads)
    }
    return summary

if __name__ == "__main__":
    print("Testing TrendTrack Client...")
    print(get_live_trendtrack_summary())
