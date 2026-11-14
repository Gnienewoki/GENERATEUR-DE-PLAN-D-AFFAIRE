# -*- coding: utf-8 -*-
"""Remplit template.docx (modèle officiel MPE) sans ajouter ni retirer de titre, de tableau ou de libellé.
Seules extensions : lignes clonées (équipements, fonds de roulement, fonctionnement, concurrents, mois du crédit)."""
import copy
import io
import re
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from .calculs import fmt, fmt_pct, fmt_qte, MOIS

TEMPLATE = Path(__file__).with_name("template.docx")
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
DOTS = re.compile("[…\\.]{3,}")


# ------------------------------------------------------------------ mise en forme des textes
def mettre_en_forme(texte):
    """Point unique où brancher plus tard une reformulation par IA. Aujourd'hui : texte repris tel quel,
    avec une majuscule initiale et un point final par paragraphe."""
    t = re.sub(r"[ \t]+", " ", str(texte or "")).strip()
    if not t:
        return t
    t = t[0].upper() + t[1:]
    if t[-1] not in ".!?…:;)":
        t += "."
    return t


def lignes_texte(texte):
    return [mettre_en_forme(l) for l in str(texte or "").split("\n") if l.strip()]


# ------------------------------------------------------------------ outils bas niveau
def _runs(p):
    return p.findall(qn("w:r"))


def _set_text_in_run(r, text):
    ts = r.findall(qn("w:t"))
    if not ts:
        t = r.makeelement(qn("w:t"), {})
        r.append(t)
        ts = [t]
    ts[0].text = text
    ts[0].set(XML_SPACE, "preserve")
    for extra in ts[1:]:
        r.remove(extra)


def set_par_text(p, text):
    """Place le texte dans le premier run (garde sa mise en forme), supprime les autres runs."""
    runs = [r for r in _runs(p) if not list(r.iter(qn("w:drawing")))]
    if not runs:
        r = p.makeelement(qn("w:r"), {})
        p.append(r)
        runs = [r]
    _set_text_in_run(runs[0], text)
    for r in runs[1:]:
        p.remove(r)


def replace_dots(p, valeur):
    """Remplace la 1re suite de points par la valeur, supprime les autres suites de points."""
    done = False
    for t in p.iter(qn("w:t")):
        if not t.text or not DOTS.search(t.text):
            continue
        if not done:
            t.text = DOTS.sub(lambda m: valeur, t.text, count=1)
            t.text = DOTS.sub("", t.text)
            done = True
        else:
            t.text = DOTS.sub("", t.text)
        t.set(XML_SPACE, "preserve")
    return done


def par_text(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


def cell_p(tc):
    return tc.findall(qn("w:p"))[0]


def _is_bold(tc):
    for r in cell_p(tc).iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is not None:
            b = rpr.find(qn("w:b"))
            if b is not None and b.get(qn("w:val")) not in ("0", "false"):
                return True
    return False


def set_cell(tc, text, bold=None, align=None):
    p = cell_p(tc)
    text = "" if text is None else str(text)
    old = _runs(p)
    rpr_src = None
    for r in old:
        if r.find(qn("w:rPr")) is not None:
            rpr_src = r.find(qn("w:rPr"))
            break
    if rpr_src is None:
        ppr = p.find(qn("w:pPr"))
        if ppr is not None and ppr.find(qn("w:rPr")) is not None:
            rpr_src = ppr.find(qn("w:rPr"))
    for r in old:
        p.remove(r)
    for extra in tc.findall(qn("w:p"))[1:]:
        tc.remove(extra)
    if text == "":
        return
    r = p.makeelement(qn("w:r"), {})
    if rpr_src is not None:
        rpr = copy.deepcopy(rpr_src)
        for tag in ("w:rStyle", "w:u"):
            for e in rpr.findall(qn(tag)):
                rpr.remove(e)
        r.append(rpr)
    else:
        rpr = r.makeelement(qn("w:rPr"), {})
        r.append(rpr)
    if bold is not None:
        for tag in ("w:b", "w:bCs"):
            for e in rpr.findall(qn(tag)):
                rpr.remove(e)
        if bold:
            rpr.insert(0, rpr.makeelement(qn("w:b"), {}))
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i:
            r.append(r.makeelement(qn("w:br"), {}))
        t = r.makeelement(qn("w:t"), {})
        t.text = line
        t.set(XML_SPACE, "preserve")
        r.append(t)
    p.append(r)
    if align is not None:
        Paragraph(p, None).alignment = align


C, R, L = WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT


def clone_after(tr, n=1):
    last = tr
    out = []
    for _ in range(n):
        c = copy.deepcopy(tr)
        last.addnext(c)
        last = c
        out.append(c)
    return out


def fill_row(tr, valeurs, aligns=None, bold=None, start=1):
    """valeurs : liste écrite à partir de la cellule `start`."""
    tcs = tr.findall(qn("w:tc"))
    b = _is_bold(tcs[0]) if bold is None else bold
    for k, v in enumerate(valeurs):
        if start + k >= len(tcs):
            break
        al = (aligns[k] if aligns else R)
        set_cell(tcs[start + k], v, bold=b, align=al)


def clear_row(tr, start=0):
    for tc in tr.findall(qn("w:tc"))[start:]:
        set_cell(tc, "")


def tr_list(tbl):
    return tbl._tbl.findall(qn("w:tr"))


def f(n):
    return fmt(n)


# ------------------------------------------------------------------ blocs de texte
def fill_block(paras, texte):
    """Remplit les paragraphes pointillés d'un bloc. Plus de lignes que de pointillés : on clone ;
    moins : on supprime les pointillés restants."""
    lignes = lignes_texte(texte)
    if not lignes:
        return
    parent = paras[0].getparent()
    for i, p in enumerate(paras):
        if i < len(lignes):
            set_par_text(p, lignes[i])
    if len(lignes) > len(paras):
        last = paras[-1]
        for l in lignes[len(paras):]:
            c = copy.deepcopy(last)
            set_par_text(c, l)
            last.addnext(c)
            last = c
    else:
        for p in paras[len(lignes):]:
            parent.remove(p)


def _sentence_existante(ctx):
    if not ctx["existante"]:
        return ""
    ans = ctx["depuis_annees"]
    parts = []
    if ans is not None:
        parts.append(f"L'activité existe depuis {fmt_qte(ans)} an{'s' if ans > 1 else ''}")
    if ctx["ca_annuel"] is not None:
        parts.append(f"son chiffre d'affaires annuel actuel est de {f(ctx['ca_annuel'])} FCFA")
    if ctx["nb_clients"] is not None:
        parts.append(f"elle compte {fmt_qte(ctx['nb_clients'])} client{'s' if ctx['nb_clients'] > 1 else ''} ou partenaire{'s' if ctx['nb_clients'] > 1 else ''}")
    return ", ".join(parts)


def conclusion_auto(c, r):
    nom = c["entreprise"]["nom"]
    inv = r["investissement"]
    fi = r["financement"]
    net = r["compte_resultat"]["resultat_net"]
    return (f"Le projet {nom} nécessite un coût total de {f(inv['cout_total_demarrage'])} FCFA au démarrage, "
            f"financé à hauteur de {fmt_pct(fi['apport_pct'])} % par apport personnel, {fmt_pct(fi['subvention_pct'])} % par subvention "
            f"et {fmt_pct(fi['credit_pct'])} % par crédit IMF. Le résultat net d'exploitation de la première année est de "
            f"{f(net[1])} FCFA.")


# ------------------------------------------------------------------ génération
def generer(c, r):
    """c : réponses normalisées et validées ; r : résultat de calculer(c). Retourne les octets du .docx."""
    d = docx.Document(str(TEMPLATE))
    body = d.element.body
    B = list(body.iterchildren())          # références figées avant toute modification
    T = [t for t in d.tables]
    TR = {i: tr_list(t) for i, t in enumerate(T)}   # lignes figées avant clonage

    # ---- page de garde
    ent = c["entreprise"]
    replace_dots(TR[0][0].findall(qn("w:tc"))[0], ent["nom"].upper())
    replace_dots(TR[0][2].findall(qn("w:tc"))[0], mettre_en_forme(ent["activite"]).rstrip("."))
    if ent["numero_plan"]:
        replace_dots(B[5], ent["numero_plan"])

    # ---- contexte (3 paragraphes)
    ctx = c["contexte"]
    ctx1 = " ".join(x for x in (mettre_en_forme(_sentence_existante(ctx)), mettre_en_forme(ctx["pourquoi"])) if x)
    for p, txt in zip((B[15], B[16], B[17]), (ctx1, ctx["usage_financement"], ctx["pourquoi_marchera"])):
        fill_block([p], txt)

    # ---- porteur
    por = c["porteur"]
    cles = ["nom_prenoms", "nationalite", "sexe", "situation_matrimoniale", "lieu_habitation", "contacts",
            "formation", "situation_pro", "annees_experience", "maitrise_technique"]
    for tr, k in zip(TR[1], cles):
        set_cell(tr.findall(qn("w:tc"))[1], por[k], bold=False, align=L)

    # ---- mode de gestion + organigramme + commentaires
    fill_block([B[23], B[24]], c["gestion"]["mode"])
    promoteur_label = "Promotrice" if por["sexe"] == "Féminin" else "Promoteur"
    _organigramme(B[25], B[26], ent["nom"], por["nom_prenoms"], promoteur_label)
    com = c["gestion"]["commentaires"]
    if com:
        replace_dots(B[30], " ".join(lignes_texte(com)))
    else:
        replace_dots(B[30], "")

    # ---- marché
    m = c["marche"]
    fill_block([B[35], B[36]], m["description"])
    fill_block([B[39], B[40]], m["tendance"])
    for i, niv in enumerate(m["demande"]):
        row = {"E": 1, "M": 2, "B": 3, "A": 4}[niv]
        set_cell(TR[2][row].findall(qn("w:tc"))[1 + i], "X", bold=True, align=C)
    for i, niv in enumerate(m["offre"]):
        row = {"E": 1, "M": 2, "B": 3}[niv]
        set_cell(TR[3][row].findall(qn("w:tc"))[1 + i], "X", bold=True, align=C)
    fill_block([B[50], B[51]], m["concurrence"])
    rows = [TR[4][1]] + clone_after(TR[4][1], max(0, len(m["concurrents"]) - 1))
    for tr, cc in zip(rows, m["concurrents"]):
        for tc, k in zip(tr.findall(qn("w:tc")), ("caracteristiques", "forces", "faiblesses")):
            set_cell(tc, mettre_en_forme(cc[k]), bold=False, align=L)
    fill_block([B[58]], m["clients"])
    fill_block([B[63], B[64], B[65]], m["strategie_produit"])
    fill_block([B[68], B[69]], m["strategie_prix"])
    fill_block(B[74:80], c["technique"]["process"])
    fill_block(B[82:87], c["technique"]["competences"])

    # ---- finances
    _t5(TR[5], r["investissement"])
    _t6(TR[6], r["charges"])
    _t7(TR[7], r["ventes"])
    _t8(TR[8], r["amortissements"], r["investissement"])
    _reduire(TR[7][2:], 14)
    _reduire(TR[8][3:], 14)
    _t9(TR[9], r["remboursement"], por["nom_prenoms"])
    _t10(TR[10], r["compte_resultat"])
    _t11(TR[11], r["financement"])

    # ---- conclusion : nouveau paragraphe normal après le titre
    concl = lignes_texte(c["conclusion"]) or [conclusion_auto(c, r)]
    modele = B[15]          # paragraphe normal (déjà rempli, non pointillé)
    last = B[113]
    for l in concl:
        p = copy.deepcopy(modele)
        set_par_text(p, l)
        last.addnext(p)
        last = p

    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def _organigramme(p_ent, p_prom, nom_ent, nom_prom, label):
    for tx in p_ent.iter(qn("w:txbxContent")):
        txt = par_text(tx)
        ts = list(tx.iter(qn("w:t")))
        if "Promotrice" in txt:
            for t in ts:
                if t.text == "Promotrice":
                    t.text = label
        elif DOTS.search(txt):
            _remplir_boite(ts, nom_ent.upper())
    for tx in p_prom.iter(qn("w:txbxContent")):
        if DOTS.search(par_text(tx)):
            _remplir_boite(list(tx.iter(qn("w:t"))), nom_prom)


def _remplir_boite(ts, valeur):
    first = True
    for t in ts:
        if first and t.text and DOTS.search(t.text):
            t.text = valeur
            first = False
        elif t.text and DOTS.search(t.text):
            t.text = ""


# ------------------------------------------------------------------ tableaux financiers
def _t5(tr, i):
    # désignation | quantité | coût unitaire | coût global
    fill_row(tr[3], ["1", f(i["frais_rc"]), f(i["frais_rc"])], [C, R, R])
    fill_row(tr[4], [None, None, f(i["sous_total_1"])], bold=True)
    am = i["amenagement"]
    if am["montant"] > 0:
        set_cell(tr[6].findall(qn("w:tc"))[0], "Aménagement : " + am["description"], bold=False, align=L)
        fill_row(tr[6], ["1", f(am["montant"]), f(am["montant"])], [C, R, R], bold=False)
    else:
        fill_row(tr[6], ["-", "-", "-"], [C, R, R], bold=False)
    fill_row(tr[7], [None, None, f(i["sous_total_2"])], bold=True)
    # équipements : 8 lignes dans le modèle, 9 permises
    eq = i["equipements"]
    zone = tr[9:17]
    if len(eq) > len(zone):
        zone = zone + clone_after(zone[-1], len(eq) - len(zone))
    for row, e in zip(zone, eq):
        set_cell(row.findall(qn("w:tc"))[0], e["designation"], bold=False, align=L)
        fill_row(row, [fmt_qte(e["quantite"]), f(e["cout_unitaire"]), f(e["cout_global"])], [C, R, R], bold=False)
    fill_row(tr[17], [None, None, f(i["sous_total_3"])], bold=True)
    fill_row(tr[18], [f(i["total_investissement"])], [R], bold=True)
    # fonds de roulement : 10 lignes dans le modèle, 13 permises
    fr = i["fonds_roulement"]
    zone = tr[20:30]
    if len(fr) > len(zone):
        zone = zone + clone_after(zone[-1], len(fr) - len(zone))
    for row, l in zip(zone, fr):
        set_cell(row.findall(qn("w:tc"))[0], l["designation"], bold=False, align=L)
        fill_row(row, [fmt_qte(l["quantite"]), f(l["cout_unitaire"]), f(l["cout_global"])], [C, R, R], bold=False)
    fill_row(tr[30], [f(i["cout_total"])], [R], bold=True)
    fill_row(tr[31], [f(i["imprevu"])], [R], bold=True)
    fill_row(tr[32], [f(i["cout_total_demarrage"])], [R], bold=True)


def _annees(vals):
    return [f(v) for v in vals]


def _t6(tr, ch):
    def ligne(row, l):
        set_cell(row.findall(qn("w:tc"))[0], l["designation"], bold=False, align=L)
        fill_row(row, [f(l["mensuel"])] + _annees(l["annees"]), bold=False)
    for row, l in zip(tr[3:10], ch["marchandises"]):
        ligne(row, l)
    st = ch["sous_total_marchandises"]
    fill_row(tr[10], [f(st["mensuel"])] + _annees(st["annees"]), bold=True)
    fonct = ch["fonctionnement"]
    zone = tr[12:17]
    if len(fonct) > len(zone):
        zone = zone + clone_after(zone[-1], len(fonct) - len(zone))
    for row, l in zip(zone, fonct):
        ligne(row, l)
    st = ch["sous_total_fonctionnement"]
    fill_row(tr[17], [f(st["mensuel"])] + _annees(st["annees"]), bold=True)
    t = ch["total"]
    fill_row(tr[18], [f(t["mensuel"])] + _annees(t["annees"]), bold=True)


def _t7(tr, v):
    for row, l in zip(tr[2:7], v["lignes"]):
        set_cell(row.findall(qn("w:tc"))[0], l["designation"], bold=False, align=L)
        fill_row(row, [fmt_qte(l["quantite"]), f(l["prix_unitaire"]), f(l["ca_mois"])] + _annees(l["annees"]),
                 [C, R, R] + [R] * 5, bold=False)
    fill_row(tr[7], [f(v["total_mois"])] + _annees(v["total_annees"]), [R] * 6, bold=True, start=3)


def _reduire(rows, sz):
    """Réduit la police des chiffres (colonnes étroites) pour éviter les retours à la ligne."""
    for tr in rows:
        for tc in tr.findall(qn("w:tc"))[1:]:
            for rr in tc.iter(qn("w:r")):
                rpr = rr.find(qn("w:rPr"))
                if rpr is None:
                    continue
                for tag in ("w:sz", "w:szCs"):
                    for e in rpr.findall(qn(tag)):
                        rpr.remove(e)
                    n = rpr.makeelement(qn(tag), {qn("w:val"): str(sz)})
                    rpr.append(n)


def _t8(tr, a, i):
    fill_row(tr[3], [f(a["frais_rc"])], [R], bold=False)       # frais RC : valeur seule, « - » conservés dans le modèle
    fill_row(tr[5], [f(a["frais_rc"])], [R], bold=True)
    am = a["amenagement"]
    if am:
        fill_row(tr[7], [f(am["valeur"]), str(am["duree_vie"])] + _annees(am["annees"]), [R, C] + [R] * 5, bold=False)
    else:
        fill_row(tr[7], ["-"] * 7, [C] * 7, bold=False)
    s2 = a["sous_total_2"]
    fill_row(tr[8], [f(s2["valeur"]), None] + _annees(s2["annees"]), [R, C] + [R] * 5, bold=True)
    eq = a["equipements"]
    zone = tr[10:18]
    if len(eq) > len(zone):
        zone = zone + clone_after(zone[-1], len(eq) - len(zone))
    for row, e in zip(zone, eq):
        set_cell(row.findall(qn("w:tc"))[0], e["designation"], bold=False, align=L)
        fill_row(row, [f(e["valeur"]), str(e["duree_vie"])] + _annees(e["annees"]), [R, C] + [R] * 5, bold=False)
    s3 = a["sous_total_3"]
    fill_row(tr[18], [f(s3["valeur"]), None] + _annees(s3["annees"]), [R, C] + [R] * 5, bold=True)
    fill_row(tr[19], [None, None] + _annees(a["total_annees"]), [R, C] + [R] * 5, bold=True)


def _t9(tr, rb, nom):
    tcs = tr[1].findall(qn("w:tc"))
    set_cell(tcs[2], nom, bold=True, align=L)
    tcs = tr[2].findall(qn("w:tc"))
    set_cell(tcs[2], f(rb["montant_pret"]), bold=True, align=R)
    set_cell(tcs[4], fmt_pct(rb["taux_annuel"]) + " %", bold=True, align=R)
    zone = tr[4:16]
    if len(rb["lignes"]) > len(zone):
        zone = zone + clone_after(zone[-1], len(rb["lignes"]) - len(zone))
    for row, l in zip(zone, rb["lignes"]):
        tcs = row.findall(qn("w:tc"))
        set_cell(tcs[0], str(l["mois"]), bold=False, align=C)
        fill_row(row, [f(l["capital"]), f(l["amortissement"]), f(l["interet"]), f(l["mensualite"]), f(l["restant"])], bold=False)
    fill_row(tr[16], [f(rb["total_amortissement"]), f(rb["total_interet"]), f(rb["total_mensualites"])], bold=True)


def _t10(tr, cr):
    cles = ["ventes", "charges_exploitation", "marge_brute", "charges_fonctionnement", "ebe",
            "dotations", "rbe", "remboursement", "resultat_net"]
    for row, k in zip(tr[1:10], cles):
        fill_row(row, [f(v) for v in cr[k]], bold=None)


def _t11(tr, fi):
    fill_row(tr[2], [f(fi["cout_total"])], [R], bold=True)
    for row, k, pk in ((tr[3], "apport", "apport_pct"), (tr[4], "subvention", "subvention_pct"), (tr[5], "credit", "credit_pct")):
        fill_row(row, [f(fi[k])], [R], bold=False)
        lab = row.findall(qn("w:tc"))[0]
        for t in lab.iter(qn("w:t")):
            if t.text and "%" in t.text:
                t.text = re.sub(r"\(\s*\d+(?:[.,]\d+)?\s*%\s*\)", f"({fmt_pct(fi[pk])}%)", t.text)
        # le « % » peut être réparti sur plusieurs runs : on le gère en dernier recours
        txt = par_text(lab)
        if f"({fmt_pct(fi[pk])}%)" not in txt:
            _reecrire_pourcentage(lab, fi[pk])


def _reecrire_pourcentage(lab, pct):
    ts = list(lab.iter(qn("w:t")))
    full = "".join(t.text or "" for t in ts)
    nouveau = re.sub(r"\(\s*\d+(?:[.,]\d+)?\s*%\s*\)", f"({fmt_pct(pct)}%)", full)
    ts[0].text = nouveau
    ts[0].set(XML_SPACE, "preserve")
    for t in ts[1:]:
        t.text = ""
