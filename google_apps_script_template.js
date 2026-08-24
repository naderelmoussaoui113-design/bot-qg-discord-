function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var data = JSON.parse(e.postData.contents);

    // 1. ONGLET VISUEL : FICHE DU WINNER
    var sheet = ss.getSheetByName("FICHE DU WINNER");
    if (!sheet) {
      sheet = ss.insertSheet("FICHE DU WINNER", 0);
    }
    sheet.clear();

    sheet.setColumnWidth(1, 30);
    sheet.setColumnWidth(2, 220);
    sheet.setColumnWidth(3, 380);
    sheet.setColumnWidth(4, 30);
    sheet.setColumnWidth(5, 220);
    sheet.setColumnWidth(6, 380);

    // BANNIERE TITRE
    sheet.getRange("B2:F2").merge()
      .setValue("FICHE WINNER : " + (data.nom || "PRODUIT DETECTE").toUpperCase())
      .setBackground("#111827").setFontColor("#FBBF24").setFontSize(13).setFontWeight("bold").setHorizontalAlignment("center").setVerticalAlignment("middle");
    sheet.setRowHeight(2, 40);

    sheet.getRange("B3:C3").merge()
      .setValue("Date : " + (data.date_ajout || "22/08/2026"))
      .setBackground("#1F2937").setFontColor("#E5E7EB").setFontSize(10).setVerticalAlignment("middle");

    sheet.getRange("E3:F3").merge()
      .setValue("VERDICT : " + (data.verdict || "LANCER IMMEDIATEMENT") + " (" + (data.score_total || "45/50") + ")")
      .setBackground("#064E3B").setFontColor("#34D399").setFontSize(11).setFontWeight("bold").setHorizontalAlignment("center").setVerticalAlignment("middle");
    sheet.setRowHeight(3, 28);

    // BLOC 1 : SOURCING (GAUCHE)
    sheet.getRange("B5:C5").merge().setValue("1. IDENTITE & SOURCING").setBackground("#0F766E").setFontColor("#FFFFFF").setFontWeight("bold");
    var b1 = [
      ["Niche", data.niche || "Sante / Confort"],
      ["Lien Fournisseur", data.lien_sourcing || "https://aliexpress.com"],
      ["Lien Boutique", data.lien_shop || "https://trendtrack.io"],
      ["Lien Pubs Ads", data.lien_pub || "https://facebook.com/ads/library"],
      ["Fournisseur", data.certif_fournisseur || "Trade Assurance"],
      ["Logistique", data.poids_logistique || "< 500g, 0 batterie"],
      ["Livraison France", data.delai_livraison || "7-9 jours"]
    ];
    for (var i = 0; i < b1.length; i++) {
      sheet.getRange("B" + (6+i)).setValue(b1[i][0]).setFontWeight("bold").setBackground("#F3F4F6");
      sheet.getRange("C" + (6+i)).setValue(b1[i][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // BLOC 2 : FINANCES (DROITE)
    sheet.getRange("E5:F5").merge().setValue("2. FINANCES & MARGES").setBackground("#0F766E").setFontColor("#FFFFFF").setFontWeight("bold");
    var b2 = [
      ["Prix Vente Solo", (data.prix_solo || "29.90") + " EUR"],
      ["Cout Achat (COGS)", (data.cogs || "5.80") + " EUR"],
      ["Markup Reel", data.markup || "x5.1"],
      ["Marge Brute", (data.marge_brute_eur || "24.10") + " EUR (" + (data.marge_brute_pct || "80%") + ")"],
      ["Breakeven ROAS", data.breakeven_roas || "1.24"],
      ["CAC Max Autorise", (data.cac_max || "16.00") + " EUR"],
      ["Marge Nette Estimee", (data.marge_nette_eur || "8.50") + " EUR (" + (data.marge_nette_pct || "28%") + ")"]
    ];
    for (var j = 0; j < b2.length; j++) {
      sheet.getRange("E" + (6+j)).setValue(b2[j][0]).setFontWeight("bold").setBackground("#F3F4F6");
      sheet.getRange("F" + (6+j)).setValue(b2[j][1]).setFontWeight(j >= 3 ? "bold" : "normal");
      if (j === 3 || j === 6) {
        sheet.getRange("F" + (6+j)).setBackground("#D1FAE5").setFontColor("#065F46");
      }
    }

    // BLOC 3 : MARCHE FRANCE (GAUCHE)
    sheet.getRange("B14:C14").merge().setValue("3. DATA MARCHE FRANCE").setBackground("#1E40AF").setFontColor("#FFFFFF").setFontWeight("bold");
    var b3 = [
      ["Google Trends", data.google_trends || "Stable > 60"],
      ["Volume SEO FR", data.volume_seo || "3 200 / mois"],
      ["CPC Achat", data.cpc || "2.40 EUR"],
      ["Concurrents FR", data.concurrents_fr || "1 a 3 boutiques"],
      ["Trafic Leader", data.trafic_concurrent || "48k visites"],
      ["Anciennete Pubs", data.anciennete_pubs || "42 jours actives"],
      ["Creatives Actives", data.creatives_leader || "9 creatives"]
    ];
    for (var k = 0; k < b3.length; k++) {
      sheet.getRange("B" + (15+k)).setValue(b3[k][0]).setFontWeight("bold").setBackground("#EFF6FF");
      sheet.getRange("C" + (15+k)).setValue(b3[k][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // BLOC 4 : ADS & OFFRES (DROITE)
    sheet.getRange("E14:F14").merge().setValue("4. MARKETING & SCRIPTS ADS").setBackground("#1E40AF").setFontColor("#FFFFFF").setFontWeight("bold");
    var b4 = [
      ["Offre Pack Duo", data.pack_duo || "49.90 EUR"],
      ["Probleme Client", data.probleme || "Douleur sciatique"],
      ["Effet Wow 3s", data.effet_wow || "Test oeuf assis incassable"],
      ["Angle Marketing", data.angle_marketing || "Correction posturale"],
      ["Hook Visuel #1", data.hook_visuel || "Plan serre oeuf ecrase"],
      ["Hook Verbal #1", data.hook_verbal || "Arretez de detruire votre dos"],
      ["Detail Notes /50", data.notes_detail || "Trends 9, Long 10, Conc 9, Mark 10, Eng 9"]
    ];
    for (var l = 0; l < b4.length; l++) {
      sheet.getRange("E" + (15+l)).setValue(b4[l][0]).setFontWeight("bold").setBackground("#EFF6FF");
      sheet.getRange("F" + (15+l)).setValue(b4[l][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // 2. ONGLET HISTORIQUE / BASE DE DONNEES
    var db = ss.getSheetByName("HISTORIQUE");
    if (!db) {
      db = ss.insertSheet("HISTORIQUE", 1);
      var h = ["Date", "Statut", "Produit", "Prix", "COGS", "Markup", "Marge Nette", "ROAS", "Score", "Verdict"];
      db.appendRow(h);
      db.getRange(1, 1, 1, h.length).setBackground("#111827").setFontColor("#FBBF24").setFontWeight("bold");
    }
    db.appendRow([
      data.date_ajout || "22/08/2026",
      data.statut || "Valide",
      data.nom || "Produit Detecte",
      (data.prix_solo || "29.90") + " EUR",
      (data.cogs || "5.80") + " EUR",
      data.markup || "x5.0",
      data.marge_nette_pct || "28%",
      data.breakeven_roas || "1.25",
      data.score_total || "45/50",
      data.verdict || "LANCER"
    ]);

    return ContentService.createTextOutput(JSON.stringify({"result":"success"})).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({"result":"error","error":err.toString()})).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}
