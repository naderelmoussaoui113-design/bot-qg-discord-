const { chromium } = require("/Users/naderelmoussaoui/.npm/_npx/616f69621f722dde/node_modules/playwright");
const path = require("path");
const os = require("os");

const profileDir = path.join(os.homedir(), ".notebooklm-mcp", "chrome-auth-profile");
const notebookUrl = "https://notebooklm.google.com/notebook/397457b7-3be4-4feb-89b8-704983a134c3";

async function queryNotebookLM(prompt) {
  let context;
  try {
    context = await chromium.launchPersistentContext(profileDir, {
      headless: true,
      args: ["--disable-blink-features=AutomationControlled"]
    });

    const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
    await page.goto(notebookUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForTimeout(3000);

    const textarea = await page.waitForSelector("textarea[aria-label='Zone de requête'], textarea.query-box-input", { timeout: 8000 });
    if (!textarea) {
      throw new Error("Textarea non trouvée");
    }

    await textarea.click();
    await textarea.fill(prompt);
    await page.keyboard.press("Enter");

    // Click submit button if Enter didn't submit
    try {
      const sendBtn = await page.$("button[aria-label*='Envoyer'], button.send-button, [data-send-button]");
      if (sendBtn) await sendBtn.click();
    } catch(e) {}

    // Wait for response to generate
    await page.waitForTimeout(6000);

    // Extract the latest response
    const response = await page.evaluate(() => {
      const messages = document.querySelectorAll(".chat-message, [data-message-author='bot'], .response-bubble, .model-response, [role='article'], div");
      let longest = "";
      for (const m of messages) {
        const text = m.innerText ? m.innerText.trim() : "";
        if (text.length > 80 && !text.includes("Ajouter des sources") && !text.includes("Zone de requête") && text.length > longest.length) {
          longest = text;
        }
      }
      return longest;
    });

    console.log("RÉPONSE DIRECTE DU NOTEBOOKLM E-COMMERCE :\n" + (response || "Aucune réponse extraite"));
  } catch (err) {
    console.error("Erreur Query NotebookLM:", err.message);
  } finally {
    if (context) await context.close();
  }
}

const q = process.argv[2] || "Quel est le dernier document ajouté ?";
queryNotebookLM(q);
