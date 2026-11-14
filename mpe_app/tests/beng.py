import copy
BENG = {
 "entreprise": {"nom": "BENG PRODUCTION", "activite": "Production audiovisuelle", "numero_plan": ""},
 "contexte": {"existante": "non", "pourquoi": "Je veux produire.", "usage_financement": "Acheter du matériel.", "pourquoi_marchera": "La demande est forte."},
 "porteur": {"nom_prenoms": "KOUASSI Jean", "nationalite": "Ivoirienne", "sexe": "Masculin", "situation_matrimoniale": "Célibataire",
   "lieu_habitation": "Abengourou", "contacts": "0700000000", "formation": "BTS", "situation_pro": "Sans emploi",
   "annees_experience": "3", "maitrise_technique": "Oui"},
 "gestion": {"mode": "Gérance directe.", "commentaires": ""},
 "marche": {"description": "Marché local.", "tendance": "En hausse.", "demande": list("EEMMBBMMEEEE"), "offre": list("MMMBBBMMMEEE"),
   "concurrence": "Deux concurrents.", "concurrents": [{"caracteristiques": "A", "forces": "x", "faiblesses": "y"}],
   "clients": "Entreprises.", "strategie_produit": "Qualité.", "strategie_prix": "Compétitif."},
 "technique": {"process": "1. Tournage", "competences": "Montage"},
 "finances": {"frais_rc": 25000, "amenagement": {"description": "", "montant": 0, "duree_vie": ""},
   "equipements": [{"designation": "Caméra", "quantite": 1, "cout_unitaire": 1488000, "duree_vie": 5}],
   "intrants": [],
   "fonctionnement": [{"designation": "Charges", "quantite": 1, "cout_unitaire": 250000}],
   "ventes": [{"designation": "A", "quantite_mois": 8, "prix_unitaire": 50000}, {"designation": "B", "quantite_mois": 8, "prix_unitaire": 20000},
              {"designation": "C", "quantite_mois": 2, "prix_unitaire": 25000}],
   "hausse_ventes": 0, "hausse_charges": 0, "mois_fonds_roulement": 1, "imprevus_pct": 5},
 "financement": {"apport_pct": 10, "subvention_pct": 60, "credit_pct": 30},
 "credit": {"duree_mois": 12, "taux_annuel": 9.6},
 "conclusion": "",
}
def beng(**ov):
    d = copy.deepcopy(BENG)
    for k, v in ov.items():
        sect, _, key = k.partition("__")
        if key: d[sect][key] = v
        else: d[sect] = v
    return d
