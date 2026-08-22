function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);

    // 1. ONGLET FICHE DU WINNER
    var cardSheet = ss.getSheetByName("FICHE WINNER");
    if (!cardSheet) {
      cardSheet = ss.insertSheet("FICHE WINNER", 0);
    }
    cardSheet.clear();
    cardSheet.setGridlines(true);

    cardSheet.setColumnWidth(1, 40);
    cardSheet.setColumnWidth(2, 220);
    cardSheet.setColumnWidth(3, 380);
    cardSheet.setColumnWidth(4, 30);
    cardSheet.setColumnWidth(5, 220);
    cardSheet.setColumnWidth(6, 380);

    cardSheet.getRange("B2:F2").merge()
      .setValue("FICHE D EVALUATION EXECUTIVE - " + (data.nom || "PRODUIT DETECTE").toUpperCase())
      .setBackground("#111827")
      .setFontColor("#FBBF24")
      .setFontSize(13)
      .setFontWeight("bold")
      .setHorizontalAlignment("center")
      .setVerticalAlignment("middle");
    cardSheet.setRowHeight(2, 45);

    cardSheet.getRange("B3:C3").merge()
      .setValue("Date : " + (data.date_ajout || "22/08/2026"))
      .setBackground("#1F2937")
      .setFontColor("#E5E7EB")
      .setFontSize(10)
      .setVerticalAlignment("middle");

    cardSheet.getRange("E3:F3").merge()
      .setValue("VERDICT : " + (data.verdict || "LANCER IMMEDIATEMENT") + " (" + (data.score_total || "45/50") + ")")
      .setBackground("#064E3B")
      .setFontColor("#34D399")
      .setFontSize(11)
      .setFontWeight("bold")
      .setHorizontalAlignment("center")
      .setVerticalAlignment("middle");
    cardSheet.setRowHeight(3, 30);

    // BLOC 1 : IDENTITE & SOURCING
    cardSheet.getRange("B5:C5").merge().setValue("1. IDENTITE ET SOURCING").setBackground("#0F766E").setFontColor("#FFFFFF").setFontWeight("bold");
    var leftIdentity = [
      ["Niche / Marche", data.niche || "Sante / Confort"],
      ["Lien Fournisseur", data.lien_sourcing || "https://aliexpress.com"],
      ["Lien Boutique Leader", data.lien_shop || "https://trendtrack.io"],
      ["Lien Ads Concurrent", data.lien_pub || "https://facebook.com/ads/library"],
      ["Certification Usine", data.certif_fournisseur || "Trade Assurance + Verified"],
      ["Poids & Logistique", data.poids_logistique || "< 500g, 0 lithium, incassable"],
      ["Delai Livraison France", data.delai_livraison || "7-9 jours ouvres"]
    ];
    for (var i = 0; i < leftIdentity.length; i++) {
      var r = 6 + i;
      cardSheet.getRange("B" + r).setValue(leftIdentity[i][0]).setFontWeight("bold").setBackground("#F3F4F6");
      cardSheet.getRange("C" + r).setValue(leftIdentity[i][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // BLOC 2 : FINANCE & MARGES
    cardSheet.getRange("E5:F5").merge().setValue("2. PLAN FINANCIER ET MARGES").setBackground("#0F766E").setFontColor("#FFFFFF").setFontWeight("bold");
    var rightFinance = [
      ["Cout Livre (COGS)", (data.cogs || "5.80") + " EUR"],
      ["Prix Vente Solo", (data.prix_solo || "29.90") + " EUR"],
      ["Markup Reel", data.markup || "x5.1"],
      ["Marge Brute", (data.marge_brute_eur || "24.10") + " EUR (" + (data.marge_brute_pct || "80%") + ")"],
      ["Breakeven ROAS", data.breakeven_roas || "1.24"],
      ["CAC Max Autorise", (data.cac_max || "16.00") + " EUR"],
      ["Marge Nette Estimee", (data.marge_nette_eur || "8.50") + " EUR (" + (data.marge_nette_pct || "28%") + ")"]
    ];
    for (var j = 0; j < rightFinance.length; j++) {
      var r = 6 + j;
      cardSheet.getRange("E" + r).setValue(rightFinance[j][0]).setFontWeight("bold").setBackground("#F3F4F6");
      cardSheet.getRange("F" + r).setValue(rightFinance[j][1]).setFontWeight(j >= 3 ? "bold" : "normal");
      if (j === 3 || j === 6) {
        cardSheet.getRange("F" + r).setBackground("#D1FAE5").setFontColor("#065F46");
      }
    }

    // BLOC 3 : DATA MARCHE FRANCE
    var r3_start = 14;
    cardSheet.getRange("B" + r3_start + ":C" + r3_start).merge().setValue("3. DATA MARCHE FRANCE").setBackground("#1E40AF").setFontColor("#FFFFFF").setFontWeight("bold");
    var leftMarket = [
      ["Google Trends (5a/90j/30j)", data.google_trends || "Stable > 60, fort momentum"],
      ["Volume Recherche SEO FR", data.volume_seo || "3 200 / mois"],
      ["CPC Intention d Achat", data.cpc || "2.40 EUR"],
      ["Concurrents Meta FR", data.concurrents_fr || "1 a 3 boutiques actives"],
      ["Trafic Concurrent Leader", data.trafic_concurrent || "48k visites (+22%)"],
      ["Anciennete des Pubs", data.anciennete_pubs || "42 jours actives"],
      ["Creatives Actives Leader", data.creatives_leader || "9 creatives en scaling"]
    ];
    for (var k = 0; k < leftMarket.length; k++) {
      var r = r3_start + 1 + k;
      cardSheet.getRange("B" + r).setValue(leftMarket[k][0]).setFontWeight("bold").setBackground("#EFF6FF");
      cardSheet.getRange("C" + r).setValue(leftMarket[k][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // BLOC 4 : STRATEGIE MARKETING
    cardSheet.getRange("E" + r3_start + ":F" + r3_start).merge().setValue("4. STRATEGIE ADS ET OFFRE 100M").setBackground("#1E40AF").setFontColor("#FFFFFF").setFontWeight("bold");
    var rightMarketing = [
      ["Offre Pack Duo (100M)", data.pack_duo || "49.90 EUR (Marge : 38.30 EUR)"],
      ["Probleme Visceral", data.probleme || "Douleur sciatique et inconfort assis"],
      ["Effet Wow / Demo 3s", data.effet_wow || "Test de l oeuf incassable assis"],
      ["Angle Marketing Principal", data.angle_marketing || "Soulagement immediat posturale"],
      ["Hook Visuel #1 (Arret scroll)", data.hook_visuel || "Plan serre sur oeuf ecrase"],
      ["Hook Verbal #1 (Script 3s)", data.hook_verbal || "Arretez de detruire votre dos."],
      ["Detail des Notes (/50)", data.notes_detail || "Trends 9, Long 10, Conc 9, Mark 10, Eng 9"]
    ];
    for (var l = 0; l < rightMarketing.length; l++) {
      var r = r3_start + 1 + l;
      cardSheet.getRange("E" + r).setValue(rightMarketing[l][0]).setFontWeight("bold").setBackground("#EFF6FF");
      cardSheet.getRange("F" + r).setValue(rightMarketing[l][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // 2. ONGLET BASE DE DONNEES
    var dbSheet = ss.getSheetByName("BASE DE DONNEES");
    if (!dbSheet) {
      dbSheet = ss.insertSheet("BASE DE DONNEES", 1);
    }
    if (dbSheet.getLastRow() === 0) {
      var headers = [
        "Date", "Statut", "Nom du Produit", "Niche", "Prix Solo (EUR)", "COGS (EUR)", "Markup", "Marge Nette (%)",
        "Breakeven ROAS", "Score (/50)", "Verdict", "Concurrents FR", "Trafic Leader", "Lien Sourcing", "Lien Concurrent"
      ];
      dbSheet.appendRow(headers);
      var headerRange = dbSheet.getRange(1, 1, 1, headers.length);
      headerRange.setBackground("#111827").setFontColor("#FBBF24").setFontWeight("bold").setHorizontalAlignment("center");
      dbSheet.setFrozenRows(1);
    }

    var summaryRow = [
      data.date_ajout || "22/08/2026",
      data.statut || "Valide",
      data.nom || "Produit Detecte",
      data.niche || "General",
      (data.prix_solo || "29.90") + " EUR",
      (data.cogs || "5.80") + " EUR",
      data.markup || "x5.0",
      data.marge_nette_pct || "28%",
      data.breakeven_roas || "1.25",
      data.score_total || "45/50",
      data.verdict || "LANCER",
      data.concurrents_fr || "1-3",
      data.trafic_concurrent || "40k+",
      data.lien_sourcing || "",
      data.lien_shop || ""
    ];
    dbSheet.appendRow(summaryRow);
    dbSheet.autoResizeColumns(1, 15);

    return ContentService.createTextOutput(JSON.stringify({
      "result": "success"
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
