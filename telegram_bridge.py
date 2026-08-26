import os
import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger("telegram_bridge")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8855830231:AAG2xiJeVUA09M2bs5kOENC9eNWp-64Jylg")
API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

async def send_telegram_chunks(session, chat_id, text, max_len=3900):
    if not text:
        return
    
    chunks = []
    lines = text.split("\n")
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_len:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk
        }
        try:
            async with session.post(f"{API_BASE}/sendMessage", json=payload) as resp:
                if resp.status != 200:
                    await session.post(f"{API_BASE}/sendMessage", json={"chat_id": chat_id, "text": chunk})
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
        await asyncio.sleep(0.4)

async def send_chat_action(session, chat_id, action="typing"):
    try:
        await session.post(f"{API_BASE}/sendChatAction", json={"chat_id": chat_id, "action": action})
    except Exception:
        pass

async def download_file_bytes(session, file_id):
    try:
        async with session.get(f"{API_BASE}/getFile", params={"file_id": file_id}) as resp:
            data = await resp.json()
            if data.get("ok"):
                file_path = data["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                async with session.get(download_url) as file_resp:
                    if file_resp.status == 200:
                        return await file_resp.read()
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
    return None

async def start_telegram_polling(ask_gemini_func, push_to_sheet_func=None, parse_product_func=None):
    print("🚀 Démarrage du moteur Telegram 24h/24 pour @Witcher130_bot...")
    offset = 0
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {"offset": offset, "timeout": 25}
                async with session.get(f"{API_BASE}/getUpdates", params=params, timeout=30) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(5)
                        continue
                    
                    data = await resp.json()
                    if not data.get("ok"):
                        await asyncio.sleep(5)
                        continue
                    
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        message = update.get("message")
                        if not message:
                            continue
                        
                        chat_id = message["chat"]["id"]
                        user_text = message.get("text") or message.get("caption") or ""
                        media_parts = []
                        is_voice = False
                        
                        # 1. Traitement des Vocaux / Audio
                        if "voice" in message or "audio" in message:
                            is_voice = True
                            await send_chat_action(session, chat_id, "record_voice")
                            voice_obj = message.get("voice") or message.get("audio")
                            file_id = voice_obj["file_id"]
                            audio_bytes = await download_file_bytes(session, file_id)
                            if audio_bytes:
                                media_parts.append({"mime_type": "audio/ogg", "data": audio_bytes})
                                if not user_text:
                                    user_text = "Écoute cet enregistrement vocal de Nader (PDG). Retranscris les points essentiels, analyse sa demande et propose les actions concrètes immédiates."
                        
                        # 2. Traitement des Photos / Captures d'écran S-Pen
                        elif "photo" in message:
                            await send_chat_action(session, chat_id, "upload_photo")
                            photos = message["photo"]
                            best_photo = photos[-1]
                            photo_bytes = await download_file_bytes(session, best_photo["file_id"])
                            if photo_bytes:
                                media_parts.append({"mime_type": "image/jpeg", "data": photo_bytes})
                                if not user_text:
                                    user_text = "Analyse attentivement cette image ou capture d'écran de Nader. Décortique les opportunités e-commerce, le copywriting ou les éléments clés."
                        
                        if not user_text and not media_parts:
                            continue
                        
                        # Action en cours de frappe
                        await send_chat_action(session, chat_id, "typing")
                        
                        channel_name = "general"
                        u_lower = user_text.lower()
                        if any(k in u_lower for k in ["winner", "produit", "chasse", "fournisseur", "ali"]):
                            channel_name = "chasse-produits"
                        elif any(k in u_lower for k in ["pub", "ad", "tiktok", "meta", "hook", "script", "creative"]):
                            channel_name = "espionnage"
                            
                        # Appel du Cerveau Gemini
                        typing_task = asyncio.create_task(_keep_typing(session, chat_id))
                        try:
                            response_text = await ask_gemini_func(
                                user_text,
                                media_parts=media_parts,
                                channel_name=channel_name,
                                category_name="TELEGRAM_MOBILE"
                            )
                        except Exception as e:
                            response_text = f"⚠️ Erreur IA : {e}"
                        finally:
                            typing_task.cancel()
                        
                        # Détection export Google Sheet
                        if push_to_sheet_func and parse_product_func:
                            if any(k in u_lower for k in ["sheet", "tableau", "transfèr", "export", "enregistr", "ajoute au sheet"]):
                                context_for_sheet = response_text + "\n\n" + user_text
                                p_dict = parse_product_func(context_for_sheet)
                                if p_dict:
                                    success = await push_to_sheet_func(p_dict)
                                    if success:
                                        response_text += "\n\n📊 **SUCCÈS : Produit automatiquement injecté dans votre Google Sheet QG !**"
                                    else:
                                        response_text += "\n\n⚠️ *Erreur lors de l'injection dans le Google Sheet.*"
                        
                        await send_telegram_chunks(session, chat_id, response_text)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(5)

async def _keep_typing(session, chat_id):
    while True:
        try:
            await send_chat_action(session, chat_id, "typing")
            await asyncio.sleep(4.5)
        except asyncio.CancelledError:
            break
        except Exception:
            pass
