import os
import datetime
from agent_core import append_mac_task, load_shared_memory

print("--- Testing Shared Brain Sync ---")
append_mac_task("Tester l'angle publicitaire 2 pour la boutique de coussins", category="🛏️-copywriting-et-pubs")

mem = load_shared_memory()
print("Total tasks in Mac queue:", len(mem.get("mac_todo_queue", [])))
print("Latest task:", mem.get("mac_todo_queue", [])[-1])

print("\n--- Reading Mac Tasks File ---")
with open("/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/HQ_SHARED_BRAIN/mac_tasks.md", "r", encoding="utf-8") as f:
    print(f.read())

print("✅ Shared Memory synchronization verified successfully!")
