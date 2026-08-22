import asyncio
import subprocess
import os

NODE_SCRIPT = "/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/BOT_QG_DISCORD/query_notebooklm_live.js"

async def query_live_notebooklm(question: str) -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", NODE_SCRIPT, question,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out_text = stdout.decode("utf-8")
        
        # Parse response after separator
        if "RÉPONSE DIRECTE DU NOTEBOOKLM E-COMMERCE :" in out_text:
            ans = out_text.split("RÉPONSE DIRECTE DU NOTEBOOKLM E-COMMERCE :")[1].strip()
            return ans
        return out_text
    except Exception as e:
        return f"Erreur live NotebookLM: {str(e)}"
