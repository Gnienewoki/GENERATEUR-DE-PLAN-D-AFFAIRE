# Générateur de plan d'affaires MPE

Application web : l'entrepreneur remplit un questionnaire en 10 étapes, l'application calcule tous les tableaux financiers et fournit le plan d'affaires Word (.docx) au format officiel du Projet C2D Emploi des Jeunes – Phase 3 – Cohorte 2.

## Ce que fait l'application
- Remplit le modèle officiel (`app/template.docx`) sans ajouter ni retirer de titre, tableau ou libellé.
- Calcule automatiquement : coût du projet, charges d'exploitation, ventes, amortissements, plan de remboursement (mensualité constante), compte de résultat sur 5 ans, structure du financement.
- Pourcentages de financement (apport / subvention / crédit IMF, total 100 %), durée du crédit (12 à 24 mois) et taux de la banque : saisis par l'utilisateur.
- Aucune donnée n'est enregistrée sur le serveur ; le brouillon reste dans le navigateur.

## Publier l'application en ligne (sans jargon)

### Ce qu'il vous faut
1. Un compte **GitHub** (gratuit) : https://github.com
2. Un compte **Render** (gratuit, connexion possible avec GitHub) : https://render.com
Coût : **0 FCFA** avec l'offre gratuite. Limite de l'offre gratuite : le site « s'endort » après ~15 minutes sans visite et met environ une minute à se réveiller à la visite suivante. Pour un site toujours réveillé, Render propose une offre payante (environ 7 USD/mois). Railway (https://railway.app) est une alternative, payante après un crédit d'essai.

### Étapes sur Render
1. Sur GitHub : cliquez sur **New repository**, nommez-le `plan-affaires-mpe`, puis **Upload files** et glissez tout le contenu de ce dossier (sauf `tests` et `old`, facultatifs). Validez avec **Commit changes**.
2. Sur Render : **New +** → **Web Service** → choisissez votre dépôt GitHub `plan-affaires-mpe`.
3. Render détecte le fichier `Dockerfile`. Laissez **Language : Docker** et **Instance Type : Free**.
4. Cliquez **Create Web Service**. Attendez 3 à 5 minutes ; quand l'état affiche **Live**, cliquez sur le lien `https://….onrender.com` en haut : c'est l'adresse à partager.
5. HTTPS est activé automatiquement par Render.

### Étapes sur Railway (alternative)
1. railway.app → **New Project** → **Deploy from GitHub repo** → votre dépôt.
2. Railway détecte le `Dockerfile`. Dans **Settings → Networking**, cliquez **Generate Domain**.

## Utiliser en local (développeur)
```
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
```
Puis ouvrir http://localhost:8000.

## Organisation du code
- `app/calculs.py` : normalisation, validation (champs obligatoires) et tous les calculs (Decimal, arrondi à l'unité).
- `app/docx_filler.py` : remplissage du modèle Word (lignes clonées si besoin). `mettre_en_forme()` est le point unique où brancher plus tard une reformulation par IA.
- `app/main.py` : API (`/api/calcul`, `/api/generer`, `/healthz`), limite de taille, limitation de débit, aucun stockage.
- `app/static/` : interface (HTML/CSS/JS sans dépendance).
- `tests/` : 30 tests (calculs, validation, API, structure du Word).
