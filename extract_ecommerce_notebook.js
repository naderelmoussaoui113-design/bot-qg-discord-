const { chromium } = require("/Users/naderelmoussaoui/.npm/_npx/616f69621f722dde/node_modules/playwright");
const fs = require("fs");
const path = require("path");
const os = require("os");

const profileDir = path.join(os.homedir(), ".notebooklm-mcp", "chrome-auth-profile");
const targetDir = "/Users/naderelmoussaoui/Documents/MON_ESPACE_IA/HQ_SHARED_BRAIN/knowledge/NOTEBOOKLM_ECOMMERCE";

async function run() {
  console.log("🚀 Ouverture du carnet NotebookLM...");
  fs.mkdirSync(targetDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    args: ["--disable-blink-features=AutomationControlled"]
  });

  const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
  await page.goto("https://notebooklm.google.com", { waitUntil: "networkidle", timeout: 60000 });

  await page.waitForTimeout(3000);

  // Click on the recent notebook card
  console.log("🖱️ Clic sur le carnet...");
  const card = await page.$("div:has-text('👨‍🏫'), [role='button']:has-text('👨‍🏫')");
  if (card) {
    await card.click();
  } else {
    // try clicking second element in recent list
    const cards = await page.$$("div[role='button']");
    if (cards.length > 0) {
      await cards[0].click();
    }
  }

  await page.waitForTimeout(6000);

  console.log("📍 URL du carnet:", page.url());

  // Save screenshot of notebook inside
  await page.screenshot({ path: path.join(targetDir, "screen_notebook_inside.png") });

  // Get full text / notes / sources from the notebook
  const notebookData = await page.evaluate(() => {
    const title = document.querySelector("h1, [aria-label*='titre'], [data-notebook-title]")?.innerText || document.title;
    
    // Extract sources
    const sourceElements = document.querySelectorAll("[role='listitem'], [data-source-id], div");
    const sources = [];
    for (const el of sourceElements) {
      const t = el.innerText ? el.innerText.trim() : "";
      if (t.length > 20 && !sources.includes(t)) {
        sources.push(t);
      }
    }

    // Extract all text content
    const allText = document.body.innerText;

    return {
      title,
      url: window.location.href,
      allText,
      sourcesCount: sources.length
    };
  });

  console.log("📔 Titre du carnet:", notebookData.title);
  console.log("📄 Longueur du texte extrait:", notebookData.allText.length);

  // Write the full extracted notebook content to markdown
  const outputFile = path.join(targetDir, "CARNET_ECOMMERCE_EXTRAIT.md");
  fs.writeFileSync(outputFile, `# NOTEBOOKLM : ${notebookData.title}\nURL: ${notebookData.url}\nDate d'extraction: ${new Date().toISOString()}\n\n${notebookData.allText}`, "utf-8");
  console.log("✅ Contenu sauvegardé dans:", outputFile);

  await context.close();
}

run().catch(e => console.error("Erreur:", e));
