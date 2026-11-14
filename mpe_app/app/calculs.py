# -*- coding: utf-8 -*-
"""
Moteur de calcul du plan d'affaires MPE.

Principes
- Tout est calculé en Decimal, arrondi à l'unité (FCFA) avec ROUND_HALF_UP.
- Chaque total affiché est la somme exacte des lignes affichées (pas d'écart de 1 FCFA).
- Aucune valeur imposée : pourcentages de financement, durée et taux du crédit sont saisis.
- Ce module ne dépend ni de Word ni du web : il est testable seul.
"""
from decimal import Decimal, ROUND_HALF_UP, getcontext, InvalidOperation
import re

getcontext().prec = 40
D = Decimal

MOIS = ["Jan", "Fév.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept", "Oct.", "Nov.", "Déc."]

# Capacités de chaque liste (lignes du modèle + lignes ajoutées par clonage)
CAP_EQUIPEMENTS = 9
CAP_INTRANTS = 7
CAP_FONCTIONNEMENT = 6
CAP_VENTES = 5
CAP_CONCURRENTS = 3
DUREE_MIN, DUREE_MAX = 12, 24
TAUX_MAX = D(50)


# ----------------------------------------------------------------------------- utilitaires
def to_dec(x, default=None):
    """Convertit un nombre saisi (int, float, '1 000', '12,5') en Decimal, ou default."""
    if x is None or isinstance(x, bool):
        return default
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, float)):
        try:
            return D(str(x))
        except InvalidOperation:
            return default
    s = str(x).strip().replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    s = s.replace("%", "")
    if s == "":
        return default
    try:
        v = D(s)
    except InvalidOperation:
        return default
    return v if v.is_finite() else default


def rnd(x):
    """Arrondi à l'unité, 0,5 vers le haut."""
    return int(D(x).quantize(D(1), rounding=ROUND_HALF_UP))


def fmt(n):
    """1851150 -> '1 851 150' (espace insécable). 0 -> '0'."""
    n = int(n)
    s = f"{abs(n):,}".replace(",", " ")
    return f"-{s}" if n < 0 else s


def fmt_pct(p):
    """D('12.50') -> '12,5' ; D('10') -> '10'."""
    p = D(p).normalize()
    s = format(p, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def fmt_qte(q):
    q = D(q)
    return fmt_pct(q) if q != q.to_integral_value() else str(int(q))


def croissance(base_annuel, taux_pct):
    """5 valeurs : année 1 = base, puis hausse annuelle composée."""
    g = 1 + D(taux_pct) / 100
    return [rnd(D(base_annuel) * g ** k) for k in range(5)]


# ----------------------------------------------------------------------------- normalisation
def _s(x):
    return "" if x is None else re.sub(r"[ \t]+", " ", str(x)).strip()


def _vide(row, cles):
    return all(_s(row.get(c)) == "" for c in cles)


def _lignes(liste, cles_texte, cles_nombre):
    out = []
    for row in (liste or []):
        if not isinstance(row, dict):
            continue
        if _vide(row, list(cles_texte) + list(cles_nombre)):
            continue
        r = {c: _s(row.get(c)) for c in cles_texte}
        for c in cles_nombre:
            r[c] = to_dec(row.get(c))
        out.append(r)
    return out


def _niveaux(liste, autorises):
    liste = list(liste or [])[:12]
    liste += [""] * (12 - len(liste))
    out = []
    for v in liste:
        v = _s(v).upper()[:1]
        out.append(v if v in autorises else "")
    return out


def normaliser(raw):
    """Nettoie les réponses brutes. Tolérant : ne lève jamais d'erreur, met None/'' si absent."""
    raw = raw if isinstance(raw, dict) else {}
    g = lambda k: raw.get(k) if isinstance(raw.get(k), dict) else {}
    ent, ctx, por, ges, mar, tec, fin, fi2, cre = (
        g("entreprise"), g("contexte"), g("porteur"), g("gestion"), g("marche"),
        g("technique"), g("finances"), g("financement"), g("credit"))
    am = fin.get("amenagement") if isinstance(fin.get("amenagement"), dict) else {}
    ex = _s(ctx.get("existante")).lower()
    return {
        "entreprise": {k: _s(ent.get(k)) for k in ("nom", "activite", "numero_plan")},
        "contexte": {
            "existante": {"oui": True, "non": False}.get(ex),
            "depuis_annees": to_dec(ctx.get("depuis_annees")),
            "ca_annuel": to_dec(ctx.get("ca_annuel")),
            "nb_clients": to_dec(ctx.get("nb_clients")),
            "pourquoi": _s(ctx.get("pourquoi")) if "\n" not in str(ctx.get("pourquoi") or "") else str(ctx.get("pourquoi")).strip(),
            "usage_financement": str(ctx.get("usage_financement") or "").strip(),
            "pourquoi_marchera": str(ctx.get("pourquoi_marchera") or "").strip(),
        },
        "porteur": {k: _s(por.get(k)) for k in (
            "nom_prenoms", "nationalite", "sexe", "situation_matrimoniale", "lieu_habitation",
            "contacts", "formation", "situation_pro", "annees_experience", "maitrise_technique")},
        "gestion": {"mode": str(ges.get("mode") or "").strip(), "commentaires": str(ges.get("commentaires") or "").strip()},
        "marche": {
            "description": str(mar.get("description") or "").strip(),
            "tendance": str(mar.get("tendance") or "").strip(),
            "demande": _niveaux(mar.get("demande"), "EMBA"),
            "offre": _niveaux(mar.get("offre"), "EMB"),
            "concurrence": str(mar.get("concurrence") or "").strip(),
            "concurrents": _lignes(mar.get("concurrents"), ("caracteristiques", "forces", "faiblesses"), ()),
            "clients": str(mar.get("clients") or "").strip(),
            "strategie_produit": str(mar.get("strategie_produit") or "").strip(),
            "strategie_prix": str(mar.get("strategie_prix") or "").strip(),
        },
        "technique": {"process": str(tec.get("process") or "").strip(),
                      "competences": str(tec.get("competences") or "").strip()},
        "finances": {
            "frais_rc": to_dec(fin.get("frais_rc")),
            "amenagement": {"description": _s(am.get("description")),
                            "montant": to_dec(am.get("montant")),
                            "duree_vie": to_dec(am.get("duree_vie"))},
            "equipements": _lignes(fin.get("equipements"), ("designation",), ("quantite", "cout_unitaire", "duree_vie")),
            "intrants": _lignes(fin.get("intrants"), ("designation",), ("cout",)),
            "fonctionnement": _lignes(fin.get("fonctionnement"), ("designation",), ("quantite", "cout_unitaire")),
            "ventes": _lignes(fin.get("ventes"), ("designation",), ("quantite_mois", "prix_unitaire")),
            "hausse_ventes": to_dec(fin.get("hausse_ventes")),
            "hausse_charges": to_dec(fin.get("hausse_charges")),
            "mois_fonds_roulement": to_dec(fin.get("mois_fonds_roulement")),
            "imprevus_pct": to_dec(fin.get("imprevus_pct")),
        },
        "financement": {k: to_dec(fi2.get(k)) for k in ("apport_pct", "subvention_pct", "credit_pct")},
        "credit": {"duree_mois": to_dec(cre.get("duree_mois")), "taux_annuel": to_dec(cre.get("taux_annuel"))},
        "conclusion": str(raw.get("conclusion") or "").strip(),
    }


# ----------------------------------------------------------------------------- validation stricte
def valider(c):
    """Retourne la liste des erreurs (vide = prêt à générer).
    Chaque erreur : {etape, champ, message}. Les questions facultatives : Q3, Q10, Q25, Q28, Q31."""
    E = []

    def err(etape, champ, msg):
        E.append({"etape": etape, "champ": champ, "message": msg})

    def req(etape, champ, valeur, msg):
        if valeur is None or valeur == "":
            err(etape, champ, msg)
            return False
        return True

    ent = c["entreprise"]
    req("entreprise", "entreprise.nom", ent["nom"], "Indiquez le nom de l'entreprise.")
    req("entreprise", "entreprise.activite", ent["activite"], "Décrivez l'activité en une phrase.")

    ctx = c["contexte"]
    if ctx["existante"] is None:
        err("contexte", "contexte.existante", "Dites si l'activité existe déjà.")
    elif ctx["existante"]:
        for k, lib in (("depuis_annees", "depuis combien de temps l'activité existe"),
                       ("ca_annuel", "le chiffre d'affaires annuel actuel"),
                       ("nb_clients", "le nombre de clients ou de partenaires")):
            v = ctx[k]
            if v is None:
                err("contexte", f"contexte.{k}", f"Indiquez {lib}.")
            elif v < 0:
                err("contexte", f"contexte.{k}", "Cette valeur ne peut pas être négative.")
    req("contexte", "contexte.pourquoi", ctx["pourquoi"], "Expliquez pourquoi vous voulez réaliser ce projet.")
    req("contexte", "contexte.usage_financement", ctx["usage_financement"], "Indiquez à quoi servira le financement.")
    req("contexte", "contexte.pourquoi_marchera", ctx["pourquoi_marchera"], "Expliquez pourquoi ce projet va marcher.")

    p = c["porteur"]
    libs = {"nom_prenoms": "Nom et prénoms", "nationalite": "Nationalité", "sexe": "Sexe",
            "situation_matrimoniale": "Situation matrimoniale", "lieu_habitation": "Lieu d'habitation",
            "contacts": "Contacts", "formation": "Formation qualifiante",
            "situation_pro": "Situation professionnelle actuelle", "annees_experience": "Années d'expérience",
            "maitrise_technique": "Maîtrise des aspects techniques"}
    for k, lib in libs.items():
        req("porteur", f"porteur.{k}", p[k], f"{lib} : champ obligatoire.")
    if p["sexe"] and p["sexe"] not in ("Masculin", "Féminin"):
        err("porteur", "porteur.sexe", "Le sexe doit être « Masculin » ou « Féminin ».")
    req("porteur", "gestion.mode", c["gestion"]["mode"], "Décrivez comment l'entreprise sera gérée.")

    m = c["marche"]
    req("marche", "marche.description", m["description"], "Décrivez votre marché.")
    req("marche", "marche.tendance", m["tendance"], "Décrivez l'évolution du marché.")
    for i, v in enumerate(m["demande"]):
        if v == "":
            err("marche", f"marche.demande.{i}", f"Demande : choisissez un niveau pour {MOIS[i]}.")
    for i, v in enumerate(m["offre"]):
        if v == "":
            err("marche", f"marche.offre.{i}", f"Offre : choisissez un niveau (Élevé, Moyen ou Bas) pour {MOIS[i]}.")
    req("strategie", "marche.concurrence", m["concurrence"], "Décrivez vos concurrents.")
    if not m["concurrents"]:
        err("strategie", "marche.concurrents", "Décrivez au moins un concurrent (forces et faiblesses).")
    if len(m["concurrents"]) > CAP_CONCURRENTS:
        err("strategie", "marche.concurrents", f"{CAP_CONCURRENTS} concurrents au maximum.")
    for i, r in enumerate(m["concurrents"]):
        for k, lib in (("caracteristiques", "le concurrent"), ("forces", "ses forces"), ("faiblesses", "ses faiblesses")):
            if not r[k]:
                err("strategie", f"marche.concurrents.{i}.{k}", f"Concurrent {i + 1} : renseignez {lib}.")
    req("strategie", "marche.clients", m["clients"], "Décrivez vos clients potentiels.")
    req("strategie", "marche.strategie_produit", m["strategie_produit"], "Décrivez votre stratégie de produit ou de service.")
    req("strategie", "marche.strategie_prix", m["strategie_prix"], "Décrivez votre stratégie de prix.")

    t = c["technique"]
    req("technique", "technique.process", t["process"], "Décrivez le processus étape par étape.")
    req("technique", "technique.competences", t["competences"], "Décrivez les compétences requises.")

    f = c["finances"]

    def montant(etape, champ, v, lib, strict_pos=False):
        if v is None:
            err(etape, champ, f"{lib} : indiquez un nombre (0 si aucun).")
        elif v < 0 or (strict_pos and v == 0):
            err(etape, champ, f"{lib} : valeur {'strictement positive' if strict_pos else 'positive ou nulle'} attendue.")

    montant("investissements", "finances.frais_rc", f["frais_rc"], "Frais de registre de commerce")
    am = f["amenagement"]
    montant("investissements", "finances.amenagement.montant", am["montant"], "Aménagement")
    if am["montant"] is not None and am["montant"] > 0:
        req("investissements", "finances.amenagement.description", am["description"], "Aménagement : décrivez les travaux.")
        d = am["duree_vie"]
        if d is None or d < 1 or d > 50 or d != d.to_integral_value():
            err("investissements", "finances.amenagement.duree_vie", "Aménagement : durée de vie entière de 1 à 50 ans.")

    if not f["equipements"]:
        err("investissements", "finances.equipements", "Ajoutez au moins un équipement.")
    if len(f["equipements"]) > CAP_EQUIPEMENTS:
        err("investissements", "finances.equipements", f"{CAP_EQUIPEMENTS} équipements au maximum.")
    for i, r in enumerate(f["equipements"]):
        n = f"Équipement {i + 1}"
        req("investissements", f"finances.equipements.{i}.designation", r["designation"], f"{n} : indiquez la désignation.")
        montant("investissements", f"finances.equipements.{i}.quantite", r["quantite"], f"{n} : quantité", True)
        montant("investissements", f"finances.equipements.{i}.cout_unitaire", r["cout_unitaire"], f"{n} : coût unitaire")
        d = r["duree_vie"]
        if d is None or d < 1 or d > 50 or d != d.to_integral_value():
            err("investissements", f"finances.equipements.{i}.duree_vie", f"{n} : durée de vie entière de 1 à 50 ans.")

    if len(f["intrants"]) > CAP_INTRANTS:
        err("exploitation", "finances.intrants", f"{CAP_INTRANTS} lignes de marchandises au maximum.")
    for i, r in enumerate(f["intrants"]):
        n = f"Marchandise {i + 1}"
        req("exploitation", f"finances.intrants.{i}.designation", r["designation"], f"{n} : indiquez la désignation.")
        montant("exploitation", f"finances.intrants.{i}.cout", r["cout"], f"{n} : coût par mois")
    if not f["fonctionnement"]:
        err("exploitation", "finances.fonctionnement", "Ajoutez au moins une dépense mensuelle de fonctionnement.")
    if len(f["fonctionnement"]) > CAP_FONCTIONNEMENT:
        err("exploitation", "finances.fonctionnement", f"{CAP_FONCTIONNEMENT} dépenses de fonctionnement au maximum.")
    for i, r in enumerate(f["fonctionnement"]):
        n = f"Dépense {i + 1}"
        req("exploitation", f"finances.fonctionnement.{i}.designation", r["designation"], f"{n} : indiquez la désignation.")
        montant("exploitation", f"finances.fonctionnement.{i}.quantite", r["quantite"], f"{n} : quantité", True)
        montant("exploitation", f"finances.fonctionnement.{i}.cout_unitaire", r["cout_unitaire"], f"{n} : coût unitaire par mois")
    if not f["ventes"]:
        err("exploitation", "finances.ventes", "Ajoutez au moins un produit ou service vendu.")
    if len(f["ventes"]) > CAP_VENTES:
        err("exploitation", "finances.ventes", f"{CAP_VENTES} produits ou services au maximum.")
    for i, r in enumerate(f["ventes"]):
        n = f"Vente {i + 1}"
        req("exploitation", f"finances.ventes.{i}.designation", r["designation"], f"{n} : indiquez le produit ou service.")
        montant("exploitation", f"finances.ventes.{i}.quantite_mois", r["quantite_mois"], f"{n} : quantité par mois", True)
        montant("exploitation", f"finances.ventes.{i}.prix_unitaire", r["prix_unitaire"], f"{n} : prix unitaire")

    def borne(champ, v, lo, hi, lib):
        if v is not None and not (lo <= v <= hi):
            err("exploitation", champ, f"{lib} : valeur entre {lo} et {hi}.")
    borne("finances.hausse_ventes", f["hausse_ventes"], -50, 200, "Hausse des ventes (%)")
    borne("finances.hausse_charges", f["hausse_charges"], -50, 200, "Hausse des charges (%)")
    borne("finances.mois_fonds_roulement", f["mois_fonds_roulement"], 0, 24, "Mois de fonds de roulement")
    borne("finances.imprevus_pct", f["imprevus_pct"], 0, 100, "Imprévus (%)")

    fi = c["financement"]
    ok = True
    for k, lib in (("apport_pct", "Apport personnel"), ("subvention_pct", "Subvention"), ("credit_pct", "Crédit IMF")):
        v = fi[k]
        if v is None:
            err("financement", f"financement.{k}", f"{lib} : indiquez un pourcentage (0 si aucun).")
            ok = False
        elif not (0 <= v <= 100):
            err("financement", f"financement.{k}", f"{lib} : pourcentage entre 0 et 100.")
            ok = False
    if ok and abs(fi["apport_pct"] + fi["subvention_pct"] + fi["credit_pct"] - 100) > D("0.01"):
        total = fi["apport_pct"] + fi["subvention_pct"] + fi["credit_pct"]
        err("financement", "financement.total",
            f"Les trois pourcentages font {fmt_pct(total)} % : le total doit être égal à 100 %.")
    cr = c["credit"]
    if ok and fi["credit_pct"] > 0:
        d = cr["duree_mois"]
        if d is None or d != d.to_integral_value() or not (DUREE_MIN <= d <= DUREE_MAX):
            err("financement", "credit.duree_mois", f"Durée du crédit : entier entre {DUREE_MIN} et {DUREE_MAX} mois.")
        tx = cr["taux_annuel"]
        if tx is None or not (0 <= tx <= TAUX_MAX):
            err("financement", "credit.taux_annuel", f"Taux d'intérêt annuel : valeur entre 0 et {int(TAUX_MAX)} %.")
    return E


# ----------------------------------------------------------------------------- calcul
def _plan_remboursement(principal, duree, taux_annuel):
    """Mensualité constante. Entiers : la dernière ligne solde exactement le capital."""
    n = int(duree)
    if principal <= 0:
        return {"mensualite": 0, "lignes": [
            {"mois": m, "capital": 0, "amortissement": 0, "interet": 0, "mensualite": 0, "restant": 0}
            for m in range(1, n + 1)]}
    r = D(taux_annuel) / 100 / 12
    mens = rnd(D(principal) / n) if r == 0 else rnd(D(principal) * r / (1 - (1 + r) ** (-n)))
    lignes, restant = [], int(principal)
    for m in range(1, n + 1):
        interet = rnd(D(restant) * r)
        amort = restant if m == n else min(mens - interet, restant)
        lignes.append({"mois": m, "capital": restant, "amortissement": amort, "interet": interet,
                       "mensualite": amort + interet, "restant": restant - amort})
        restant -= amort
    return {"mensualite": mens, "lignes": lignes}


def _amortissement_ligne(valeur, duree):
    """5 annuités : valeur/durée, la dernière annuité solde l'arrondi."""
    duree = int(duree)
    out, cumul = [], 0
    for an in range(1, 6):
        if an < duree:
            a = rnd(D(valeur) / duree)
        elif an == duree:
            a = valeur - cumul
        else:
            a = 0
        out.append(a)
        cumul += a
    return out


def calculer(c):
    """c : réponses normalisées (tolérant aux champs manquants). Retourne tous les tableaux en entiers."""
    f = c["finances"]
    z = lambda v, d=0: d if v is None else v
    mois_fdr = z(f["mois_fonds_roulement"], D(1))
    imprev = z(f["imprevus_pct"], D(5))
    g_v, g_c = z(f["hausse_ventes"], D(0)), z(f["hausse_charges"], D(0))

    # --- 5.1 coût total
    frais = rnd(z(f["frais_rc"]))
    am = f["amenagement"]
    am_val = rnd(z(am["montant"]))
    equip = []
    for e in f["equipements"]:
        q, u = z(e["quantite"]), z(e["cout_unitaire"])
        equip.append({"designation": e["designation"], "quantite": q, "cout_unitaire": rnd(u),
                      "cout_global": rnd(q * u), "duree_vie": max(1, int(z(e["duree_vie"], D(1))))})
    st1, st2 = frais, am_val
    st3 = sum(e["cout_global"] for e in equip)
    total_inv = st1 + st2 + st3

    fdr = []
    for i_ in f["intrants"]:
        cout = z(i_["cout"])
        fdr.append({"designation": i_["designation"], "quantite": mois_fdr, "cout_unitaire": rnd(cout),
                    "cout_global": rnd(cout * mois_fdr)})
    for r in f["fonctionnement"]:
        q, u = z(r["quantite"]), z(r["cout_unitaire"])
        fdr.append({"designation": r["designation"], "quantite": q * mois_fdr, "cout_unitaire": rnd(u),
                    "cout_global": rnd(q * u * mois_fdr)})
    fdr_total = sum(l["cout_global"] for l in fdr)
    cout_total = total_inv + fdr_total
    imprevu = rnd(D(cout_total) * imprev / 100)
    cout_demarrage = cout_total + imprevu
    investissement = {
        "frais_rc": frais, "amenagement": {"description": am["description"], "montant": am_val,
                                           "duree_vie": max(1, int(z(am["duree_vie"], D(1))))},
        "equipements": equip, "sous_total_1": st1, "sous_total_2": st2, "sous_total_3": st3,
        "total_investissement": total_inv, "fonds_roulement": fdr, "fonds_roulement_total": fdr_total,
        "cout_total": cout_total, "imprevu": imprevu, "cout_total_demarrage": cout_demarrage,
    }

    # --- 5.2 charges d'exploitation (mensuel + 5 ans)
    def ligne_charge(des, mensuel_exact):
        return {"designation": des, "mensuel": rnd(mensuel_exact),
                "annees": croissance(mensuel_exact * 12, g_c)}
    march = [ligne_charge(i_["designation"], z(i_["cout"])) for i_ in f["intrants"]]
    fonct = [ligne_charge(r["designation"], z(r["quantite"]) * z(r["cout_unitaire"])) for r in f["fonctionnement"]]
    s = lambda lignes: {"mensuel": sum(l["mensuel"] for l in lignes),
                        "annees": [sum(l["annees"][k] for l in lignes) for k in range(5)]}
    st_m, st_f = s(march), s(fonct)
    charges = {"marchandises": march, "fonctionnement": fonct, "sous_total_marchandises": st_m,
               "sous_total_fonctionnement": st_f,
               "total": {"mensuel": st_m["mensuel"] + st_f["mensuel"],
                         "annees": [st_m["annees"][k] + st_f["annees"][k] for k in range(5)]}}

    # --- 5.3 ventes
    lv = []
    for v in f["ventes"]:
        q, p = z(v["quantite_mois"]), z(v["prix_unitaire"])
        lv.append({"designation": v["designation"], "quantite": q, "prix_unitaire": rnd(p),
                   "ca_mois": rnd(q * p), "annees": croissance(q * p * 12, g_v)})
    ventes = {"lignes": lv, "total_mois": sum(l["ca_mois"] for l in lv),
              "total_annees": [sum(l["annees"][k] for l in lv) for k in range(5)]}

    # --- 5.4 amortissements (les frais de registre ne sont pas amortis : le modèle affiche « - »)
    lignes_am = []
    if am_val > 0:
        lignes_am.append({"designation": "Aménagement", "valeur": am_val, "duree_vie": investissement["amenagement"]["duree_vie"],
                          "annees": _amortissement_ligne(am_val, investissement["amenagement"]["duree_vie"])})
    amort_equip = [{"designation": e["designation"], "valeur": e["cout_global"], "duree_vie": e["duree_vie"],
                    "annees": _amortissement_ligne(e["cout_global"], e["duree_vie"])} for e in equip]
    y2 = [sum(l["annees"][k] for l in lignes_am) for k in range(5)]
    y3 = [sum(l["annees"][k] for l in amort_equip) for k in range(5)]
    amortissements = {"frais_rc": frais, "amenagement": lignes_am[0] if lignes_am else None, "equipements": amort_equip,
                      "sous_total_2": {"valeur": st2, "annees": y2}, "sous_total_3": {"valeur": st3, "annees": y3},
                      "total_annees": [y2[k] + y3[k] for k in range(5)]}

    # --- 5.5 financement (pourcentages saisis -> montants ; le crédit prend le reste)
    fi = c["financement"]
    pa, ps, pc = (z(fi[k]) for k in ("apport_pct", "subvention_pct", "credit_pct"))
    apport = rnd(D(cout_demarrage) * pa / 100)
    if pc == 0:
        subv = cout_demarrage - apport
        credit = 0
    else:
        subv = rnd(D(cout_demarrage) * ps / 100)
        credit = cout_demarrage - apport - subv
    financement = {"cout_total": cout_demarrage, "apport": apport, "subvention": subv, "credit": credit,
                   "apport_pct": pa, "subvention_pct": ps, "credit_pct": pc}

    # --- 5.6 remboursement
    cr = c["credit"]
    duree = min(60, max(1, int(cr["duree_mois"]))) if cr["duree_mois"] is not None and credit > 0 else 12
    taux = z(cr["taux_annuel"])
    plan = _plan_remboursement(credit, duree, taux)
    lignes = plan["lignes"]
    remb_an = [sum(l["mensualite"] for l in lignes if (l["mois"] - 1) // 12 == k) for k in range(5)]
    remboursement = {"montant_pret": credit, "taux_annuel": taux, "duree_mois": duree, "mensualite": plan["mensualite"],
                     "lignes": lignes, "total_amortissement": sum(l["amortissement"] for l in lignes),
                     "total_interet": sum(l["interet"] for l in lignes),
                     "total_mensualites": sum(l["mensualite"] for l in lignes), "par_annee": remb_an}

    # --- 5.7 compte de résultat : [valeur mensuelle, année 1 .. année 5]
    sub = lambda a, b: [x - y for x, y in zip(a, b)]
    v_ = [ventes["total_mois"]] + ventes["total_annees"]
    m_ = [st_m["mensuel"]] + st_m["annees"]
    f_ = [st_f["mensuel"]] + st_f["annees"]
    d_ = [rnd(D(amortissements["total_annees"][0]) / 12)] + amortissements["total_annees"]
    r_ = [lignes[0]["mensualite"] if lignes else 0] + remb_an
    marge = sub(v_, m_)
    ebe = sub(marge, f_)
    rbe = sub(ebe, d_)
    net = sub(rbe, r_)
    compte = {"ventes": v_, "charges_exploitation": m_, "marge_brute": marge, "charges_fonctionnement": f_,
              "ebe": ebe, "dotations": d_, "rbe": rbe, "remboursement": r_, "resultat_net": net}

    return {"investissement": investissement, "charges": charges, "ventes": ventes,
            "amortissements": amortissements, "financement": financement, "remboursement": remboursement,
            "compte_resultat": compte}
