/**
 * GOOGLE APPS SCRIPT - PONT DISCORD VERS GOOGLE SHEET (NADER QG)
 * 
 * Instructions pour activer le pont en 1 minute :
 * 1. Ouvre ton Google Sheet (vide ou existant).
 * 2. Clique dans le menu en haut sur : Extensions > Apps Script.
 * 3. Supprime tout le code existant et colle l'intégralité de ce script.
 * 4. Clique sur "Déployer" (en haut à droite en bleu) > "Nouveau déploiement".
 * 5. Choisis le type : "Application Web".
 *    - Description : Pont Discord Bot
 *    - Exécuter en tant que : Moi
 *    - Qui a accès : Tout le monde (Anyone)
 * 6. Clique sur "Déployer" et copie l'URL générée (l'URL de l'application Web).
 * 7. Colle cette URL dans le Discord ou donne-la à ton assistant !
 */

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);

    // Si la feuille est vide, on ajoute les en-têtes avec style
    if (sheet.getLastRow() === 0) {
      var headers = [
        "Date d'Ajout", "Statut", "Nom du Produit", "Niche", "Lien Sourcing", "Lien Shop Concurrent", "Lien Pub Ads",
        "Problème Viscéral", "Effet Wow 3s", "Poids & Logistique", "Introuvable Magasin", "Saisonnalité France",
        "Google Trends (5a/90j/30j)", "Volume SEO France", "CPC Intention Achat", "Concurrents Meta FR",
        "Coût Livré (COGS €)", "Prix Vente Solo (€)", "Markup (x)", "Marge Brute (€)", "Marge Brute (%)",
        "Breakeven ROAS", "CAC Max Autorisé (€)", "Frais Stripe (€)", "Marge Nette (€)", "Marge Nette (%)",
        "Prix Pack Duo ($100M €)", "Délai Livraison France", "Ancienneté Pubs", "Créatives Actives Leader",
        "Trafic Shop Concurrent", "Certification Fournisseur", "Notes Détail (/50)", "SCORE TOTAL (/50)", "Verdict Officiel",
        "Hook Visuel #1", "Hook Verbal #1", "Angle Marketing"
      ];
      sheet.appendRow(headers);
      
      // Style des en-têtes (Vert Émeraude / Texte Blanc Gras)
      var headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setBackground("#0F5132");
      headerRange.setFontColor("#FFFFFF");
      headerRange.setFontWeight("bold");
      headerRange.setHorizontalAlignment("center");
      sheet.setFrozenRows(1);
    }

    // Préparation de la nouvelle ligne
    var row = [
      data.date_ajout || Utilities.formatDate(new Date(), "GMT+2", "dd/MM/yyyy"),
      data.statut || "🟢 Validé pour test",
      data.nom || "Produit Détecté",
      data.niche || "Général",
      data.lien_sourcing || "",
      data.lien_shop || "",
      data.lien_pub || "",
      data.probleme || "",
      data.effet_wow || "",
      data.poids_logistique || "",
      data.introuvable || "Oui",
      data.saisonnalite || "> 90 jours",
      data.google_trends || "",
      data.volume_seo || "",
      data.cpc || "",
      data.concurrents_fr || "",
      data.cogs || "",
      data.prix_solo || "",
      data.markup || "",
      data.marge_brute_eur || "",
      data.marge_brute_pct || "",
      data.breakeven_roas || "",
      data.cac_max || "",
      data.frais_stripe || "",
      data.marge_nette_eur || "",
      data.marge_nette_pct || "",
      data.pack_duo || "",
      data.delai_livraison || "< 10 jours",
      data.anciennete_pubs || "",
      data.creatives_leader || "",
      data.trafic_concurrent || "",
      data.certif_fournisseur || "Trade Assurance",
      data.notes_detail || "",
      data.score_total || "",
      data.verdict || "",
      data.hook_visuel || "",
      data.hook_verbal || "",
      data.angle_marketing || ""
    ];

    sheet.appendRow(row);
    
    // Auto-ajustement des colonnes
    sheet.autoResizeColumns(1, 10);

    return ContentService.createTextOutput(JSON.stringify({
      "result": "success",
      "row": sheet.getLastRow()
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "result": "error",
      "error": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}
