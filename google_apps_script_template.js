/**
 * GOOGLE APPS SCRIPT - DASHBOARD EXECUTIVE & TRACKER LUXE E-COMMERCE (NADER QG)
 * 
 * Ce script crée automatiquement 2 ONGLETS ultra-esthétiques :
 * 1. 📱 "FICHE DERNIER WINNER" : Une mise en page "Carte d'Investissement / VC Dashboard"
 *    avec des blocs visuels, des couleurs soignées, du texte aéré et lisible sans défiler à l'infini !
 * 2. 📋 "BASE DE DONNÉES" : Le tableau comparatif global pour archiver tous tes winners.
 */

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);

    // ==========================================
    // 1. ONGLET "📱 FICHE WINNER" (DESIGN DASHBOARD)
    // ==========================================
    var cardSheet = ss.getSheetByName("📱 FICHE DU WINNER");
    if (!cardSheet) {
      cardSheet = ss.insertSheet("📱 FICHE DU WINNER", 0);
    }
    cardSheet.clear();
    cardSheet.setGridlines(true);

    // Configuration des largeurs de colonnes pour un affichage parfait
    cardSheet.setColumnWidth(1, 40);   // Marge gauche
    cardSheet.setColumnWidth(2, 220);  // Libellé / Clé
    cardSheet.setColumnWidth(3, 380);  // Données / Valeur
    cardSheet.setColumnWidth(4, 30);   // Séparateur central
    cardSheet.setColumnWidth(5, 220);  // Libellé Droite
    cardSheet.setColumnWidth(6, 380);  // Données Droite

    // HEADER PRINCIPAL (Bannière Sombre & Or)
    cardSheet.getRange("B2:F2").merge()
      .setValue("🏆 FICHE D'ÉVALUATION EXECUTIVE - " + (data.nom || "PRODUIT DÉTECTÉ").toUpperCase())
      .setBackground("#111827")
      .setFontColor("#FBBF24")
      .setFontSize(14)
      .setFontWeight("bold")
      .setHorizontalAlignment("center")
      .setVerticalAlignment("middle");
    cardSheet.setRowHeight(2, 45);

    // SOUS-HEADER : DATE & VERDICT
    cardSheet.getRange("B3:C3").merge()
      .setValue("📅 Date d'analyse : " + (data.date_ajout || Utilities.formatDate(new Date(), "GMT+2", "dd/MM/yyyy")))
      .setBackground("#1F2937").setFontColor("#E5E7EB").setFontSize(10).setVerticalAlignment("middle");
    cardSheet.getRange("E3:F3").merge()
      .setValue("⚖️ VERDICT : " + (data.verdict || "🟢 LANCER IMMÉDIATEMENT") + " (" + (data.score_total || "45/50") + ")")
      .setBackground("#064E3B").setFontColor("#34D399").setFontSize(11).setFontWeight("bold").setHorizontalAlignment("center").setVerticalAlignment("middle");
    cardSheet.setRowHeight(3, 30);

    // --- BLOC 1 (GAUCHE) : IDENTITÉ & SOURCING ---
    cardSheet.getRange("B5:C5").merge().setValue("📦 1. IDENTITÉ & SOURCING").setBackground("#0F766E").setFontColor("#FFFFFF").setFontWeight("bold");
    var leftIdentity = [
      ["Niche / Marché", data.niche || "Santé / Confort"],
      ["Lien Fournisseur", data.lien_sourcing || "https://aliexpress.com"],
      ["Lien Boutique Leader", data.lien_shop || "https://trendtrack.io"],
      ["Lien Ads Concurrent", data.lien_pub || "https://facebook.com/ads/library"],
      ["Certification Usine", data.certif_fournisseur || "Trade Assurance + Verified"],
      ["Poids & Logistique", data.poids_logistique || "< 500g, 0 lithium, incassable"],
      ["Délai Livraison France", data.delai_livraison || "7-9 jours ouvrés"]
    ];
    for (var i = 0; i < leftIdentity.length; i++) {
      var r = 6 + i;
      cardSheet.getRange("B" + r).setValue(leftIdentity[i][0]).setFontWeight("bold").setBackground("#F3F4F6");
      cardSheet.getRange("C" + r).setValue(leftIdentity[i][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // --- BLOC 2 (DROITE) : FINANCE & MARGES ---
    cardSheet.getRange("E5:F5").merge().setValue("💰 2. PLAN FINANCIER & MARGES").setBackground("#0F766E").setFontColor("#FFFFFF").setFontWeight("bold");
    var rightFinance = [
      ["Coût Livré (COGS)", (data.cogs || "5.80") + " €"],
      ["Prix Vente Solo", (data.prix_solo || "29.90") + " €"],
      ["Markup Réel", data.markup || "x5.1"],
      ["Marge Brute", (data.marge_brute_eur || "24.10") + " € (" + (data.marge_brute_pct || "80%") + ")"],
      ["Breakeven ROAS", data.breakeven_roas || "1.24"],
      ["CAC Max Autorisé", (data.cac_max || "16.00") + " €"],
      ["Marge Nette Estimée", (data.marge_nette_eur || "8.50") + " € (" + (data.marge_nette_pct || "28%") + ")"]
    ];
    for (var j = 0; j < rightFinance.length; j++) {
      var r = 6 + j;
      cardSheet.getRange("E" + r).setValue(rightFinance[j][0]).setFontWeight("bold").setBackground("#F3F4F6");
      cardSheet.getRange("F" + r).setValue(rightFinance[j][1]).setFontWeight(j >= 3 ? "bold" : "normal");
      if (j === 3 || j === 6) {
        cardSheet.getRange("F" + r).setBackground("#D1FAE5").setFontColor("#065F46"); // Vert doux pour marges
      }
    }

    // --- BLOC 3 (GAUCHE) : DEMANDE & DATA FRANCE ---
    var r3_start = 14;
    cardSheet.getRange("B" + r3_start + ":C" + r3_start).merge().setValue("📈 3. DATA MARCHÉ FRANCE").setBackground("#1E40AF").setFontColor("#FFFFFF").setFontWeight("bold");
    var leftMarket = [
      ["Google Trends (5a/90j/30j)", data.google_trends || "Stable > 60, fort momentum"],
      ["Volume Recherche SEO FR", data.volume_seo || "3 200 / mois"],
      ["CPC Intention d'Achat", data.cpc || "2.40 €"],
      ["Concurrents Meta FR", data.concurrents_fr || "1 à 3 boutiques actives"],
      ["Trafic Concurrent Leader", data.trafic_concurrent || "48k visites (+22%)"],
      ["Ancienneté des Pubs", data.anciennete_pubs || "42 jours actives"],
      ["Créatives Actives Leader", data.creatives_leader || "9 créatives en scaling"]
    ];
    for (var k = 0; k < leftMarket.length; k++) {
      var r = r3_start + 1 + k;
      cardSheet.getRange("B" + r).setValue(leftMarket[k][0]).setFontWeight("bold").setBackground("#EFF6FF");
      cardSheet.getRange("C" + r).setValue(leftMarket[k][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // --- BLOC 4 (DROITE) : MARKETING & OFFRE $100M ---
    cardSheet.getRange("E" + r3_start + ":F" + r3_start).merge().setValue("🎯 4. STRATÉGIE ADS & $100M OFFERS").setBackground("#1E40AF").setFontColor("#FFFFFF").setFontWeight("bold");
    var rightMarketing = [
      ["Offre Pack Duo ($100M)", data.pack_duo || "49.90 € (Marge : 38.30 €)"],
      ["Problème Viscéral", data.probleme || "Douleur sciatique et inconfort assis"],
      ["Effet Wow / Démo 3s", data.effet_wow || "Test de l'œuf incassable assis"],
      ["Angle Marketing Principal", data.angle_marketing || "Soulagement immédiat posturale"],
      ["Hook Visuel #1 (Arrêt de scroll)", data.hook_visuel || "Plan serré sur œuf écrasé"],
      ["Hook Verbal #1 (Script 3s)", data.hook_verbal || "Arrêtez de détruire votre dos."],
      ["Détail des Notes (/50)", data.notes_detail || "Trends 9, Long 10, Conc 9, Mark 10, Eng 9"]
    ];
    for (var l = 0; l < rightMarketing.length; l++) {
      var r = r3_start + 1 + l;
      cardSheet.getRange("E" + r).setValue(rightMarketing[l][0]).setFontWeight("bold").setBackground("#EFF6FF");
      cardSheet.getRange("F" + r).setValue(rightMarketing[l][1]).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
    }

    // Encadrements esthétiques
    cardSheet.getRange("B5:C12").setBorder(true, true, true, true, true, true, "#D1D5DB", SpreadsheetApp.BorderStyle.SOLID);
    cardSheet.getRange("E5:F12").setBorder(true, true, true, true, true, true, "#D1D5DB", SpreadsheetApp.BorderStyle.SOLID);
    cardSheet.getRange("B14:C21").setBorder(true, true, true, true, true, true, "#D1D5DB", SpreadsheetApp.BorderStyle.SOLID);
    cardSheet.getRange("E14:F21").setBorder(true, true, true, true, true, true, "#D1D5DB", SpreadsheetApp.BorderStyle.SOLID);


    // ==========================================
    // 2. ONGLET "📋 BASE DE DONNÉES" (TABLEAU GLOBAL)
    // ==========================================
    var dbSheet = ss.getSheetByName("📋 BASE DE DONNÉES");
    if (!dbSheet) {
      dbSheet = ss.insertSheet("📋 BASE DE DONNÉES", 1);
    }

    if (dbSheet.getLastRow() === 0) {
      var headers = [
        "Date", "Statut", "Nom du Produit", "Niche", "Prix Solo (€)", "COGS (€)", "Markup", "Marge Nette (%)",
        "Breakeven ROAS", "Score (/50)", "Verdict", "Concurrents FR", "Trafic Leader", "Lien Sourcing", "Lien Concurrent"
      ];
      dbSheet.appendRow(headers);
      var headerRange = dbSheet.getRange(1, 1, 1, headers.length);
      headerRange.setBackground("#111827").setFontColor("#FBBF24").setFontWeight("bold").setHorizontalAlignment("center");
      dbSheet.setFrozenRows(1);
    }

    var summaryRow = [
      data.date_ajout || Utilities.formatDate(new Date(), "GMT+2", "dd/MM/yyyy"),
      data.statut || "🟢 Validé",
      data.nom || "Produit Détecté",
      data.niche || "Général",
      (data.prix_solo || "29.90") + " €",
      (data.cogs || "5.80") + " €",
      data.markup || "x5.0",
      data.marge_nette_pct || "28%",
      data.breakeven_roas || "1.25",
      data.score_total || "45/50",
      data.verdict || "🟢 LANCER",
      data.concurrents_fr || "1-3",
      data.trafic_concurrent || "40k+",
      data.lien_sourcing || "",
      data.lien_shop || ""
    ];
    dbSheet.appendRow(summaryRow);
    dbSheet.autoResizeColumns(1, 15);

    return ContentService.createTextOutput(JSON.stringify({
      "result": "success",
      "status": "Dashboard Fiche + Base de Données mis à jour avec succès !"
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
