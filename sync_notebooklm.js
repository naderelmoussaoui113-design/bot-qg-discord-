const { chromium } = require("/Users/naderelmoussaoui/.npm/_npx/616f69621f722dde/node_modules/playwright");
const fs = require("fs");
const path = require("path");
const os = require("os");

const profileDir = path.join(os.homedir(), ".notebooklm-mcp", "chrome-auth-profile");
const targetDir = "/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/HQ_SHARED_BRAIN/knowledge/NOTEBOOKLM_ECOMMERCE";

async function run() {
  console.log("🚀 Connexion directe au profil NotebookLM...");
  fs.mkdirSync(targetDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    args: ["--disable-blink-features=AutomationControlled"]
  });

  const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
  await page.goto("https://notebooklm.google.com", { waitUntil: "networkidle", timeout: 60000 });

  console.log("📍 URL actuelle:", page.url());
  
  // Wait a bit to render notebooks
  await page.waitForTimeout(4000);

  // Take screenshot to verify
  await page.screenshot({ path: path.join(targetDir, "screen_home.png") });
  console.log("📸 Capture d'écran enregistrée.");

  // Extract all visible notebook titles and links
  const notebooks = await page.evaluate(() => {
    const items = [];
    const elements = document.querySelectorAll("a, [role='button'], [data-notebook-id], div");
    for (const el of elements) {
      const text = el.innerText ? el.innerText.trim() : "";
      if (text.toLowerCase().includes("ecom") || text.toLowerCase().includes("commerce") || text.length > 3) {
        items.push({ text: text.substring(0, 100), tag: el.tagName, href: el.href || "" });
      }
    }
    return items;
  });

  console.log("📓 Éléments détectés:", JSON.stringify(notebooks.slice(0, 15), null, 2));

  await context.close();
}

run().catch(e => console.error("Erreur:", e));
