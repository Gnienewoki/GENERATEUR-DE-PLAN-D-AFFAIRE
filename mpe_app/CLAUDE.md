# Générateur de plan d'affaires MPE (Projet C2D Emploi des Jeunes – Phase 3 – Cohorte 2)

Langue de travail : français. Réponses courtes et directes.

## But
Un questionnaire (application web) produit un plan d'affaires Word **identique au modèle officiel** avec tous les tableaux financiers calculés automatiquement.

## Règle d'or
**Aucun ajout, aucun retrait** par rapport à `app/template.docx` : mêmes titres, ordre, tableaux, libellés. On remplit le modèle, on ne le reconstruit jamais. Extensions autorisées (lignes clonées) : concurrents (3), équipements (9), fonds de roulement (13), fonctionnement (6), plan de remboursement (12 à 24 lignes). Seuls changements de libellés : les % de « Structure du financement ».

## Le modèle (`app/template.docx` = modèle officiel d'origine, 12 tableaux)
0 garde · 1 porteur · 2 demande (E/M/B/Arrêt) · 3 offre (E/M/B, pas « Arrêt ») · 4 concurrence · 5 coût du projet · 6 charges · 7 ventes · 8 amortissements · 9 remboursement · 10 compte de résultat · 11 financement. Organigramme = zones de texte (Choice + Fallback dupliqués : remplir les deux). Le modèle d'origine a 8 lignes d'équipements, 5 de fonctionnement, 10 de fonds de roulement : le code clone des lignes pour atteindre 9 / 6 / 13. (Une ancienne note disait que le modèle avait 9 et 6 lignes : c'était faux.)

## Décisions
- Financement : 3 pourcentages saisis (somme 100 %, chacun 0–100). Montant = % × coût total arrondi ; le crédit IMF prend le reste (somme exacte). Si crédit = 0 %, la subvention prend le reste.
- Crédit : durée entière 12–24 mois, taux annuel 0–50 % saisis ; mensualité constante, dernière échéance ajustée ; ignorés si crédit = 0.
- Obligatoires : toutes les questions sauf Q3 (n° du plan), Q10 (commentaires), Q25 (marchandises), Q28 (hypothèses), Q31 (conclusion). 0 accepté, vide refusé. Défauts : hausses 0 %, fonds de roulement 1 mois, imprévus 5 %.
- Amortissement = valeur ÷ durée, dernière annuité ajustée ; frais de registre non amortis (« - »).
- Compte de résultat : « Total Charges d'exploitation » = marchandises/intrants seuls (le fonctionnement a sa propre ligne) — À CONFIRMER avec le propriétaire.
- Textes repris tels quels (majuscule + point), pas d'IA en v1 ; `mettre_en_forme()` = point d'extension. Conclusion auto si vide.
- Données personnelles jamais stockées côté serveur ; limite 300 Ko, débit limité, en-têtes de sécurité.
- Palette : #183060 marine, #E8801A orange (jamais en texte sur blanc), #0B7A3E vert, #F5F7FA fond, #1B2433 texte, #C0392B erreur. Pas de logos officiels dans l'interface web.

## Pièges
- Toujours recalculer : l'exemple BENG contient des totaux faux.
- Cellules : adresser les cellules physiques (`w:tc`), pas la grille (gridSpan).
- Cas de référence BENG : investissement 1 513 000 ; coût démarrage 1 851 150 ; 10/60/30 → 185 115 / 1 110 690 / 555 345 ; mensualité 12 mois à 9,6 % = 48 720.

## Commandes
`pytest` (30 tests) · `uvicorn app.main:app --reload`
