import pytest
from beng import beng
from app.calculs import normaliser, valider, calculer

def run(**ov):
    c = normaliser(beng(**ov)); return c, valider(c), calculer(c)

def test_beng_base():
    c, e, r = run()
    assert e == []
    i = r["investissement"]
    assert i["total_investissement"] == 1513000 and i["cout_total"] == 1763000
    assert i["imprevu"] == 88150 and i["cout_total_demarrage"] == 1851150
    assert r["ventes"]["total_mois"] == 610000
    assert r["charges"]["total"]["mensuel"] == 250000

@pytest.mark.parametrize("p,exp", [((10,60,30),(185115,1110690,555345)), ((20,50,30),(370230,925575,555345)), ((10,70,20),(185115,1295805,370230))])
def test_cas_ABC(p, exp):
    _, e, r = run(financement={"apport_pct": p[0], "subvention_pct": p[1], "credit_pct": p[2]})
    f = r["financement"]
    assert e == [] and (f["apport"], f["subvention"], f["credit"]) == exp and sum(exp) == 1851150

@pytest.mark.parametrize("fin", [(10,60,20),(-5,65,40),(110,0,-10)])
def test_erreurs_pourcentages(fin):
    _, e, _ = run(financement={"apport_pct": fin[0], "subvention_pct": fin[1], "credit_pct": fin[2]})
    assert e

@pytest.mark.parametrize("d,t", [(11, 9.6), (25, 9.6), (12, -1), (12.5, 9.6)])
def test_erreurs_credit(d, t):
    _, e, _ = run(credit={"duree_mois": d, "taux_annuel": t})
    assert any(x["champ"].startswith("credit") for x in e)

@pytest.mark.parametrize("duree", [12, 24])
def test_remboursement_solde(duree):
    _, e, r = run(credit={"duree_mois": duree, "taux_annuel": 9.6})
    rb = r["remboursement"]
    assert e == [] and len(rb["lignes"]) == duree
    assert rb["lignes"][-1]["restant"] == 0
    assert rb["total_amortissement"] == r["financement"]["credit"]
    assert rb["lignes"][0]["capital"] == r["financement"]["credit"]
    assert sum(rb["par_annee"]) == rb["total_mensualites"]

def test_taux_zero():
    _, e, r = run(credit={"duree_mois": 12, "taux_annuel": 0})
    assert e == [] and r["remboursement"]["total_interet"] == 0 and r["remboursement"]["lignes"][-1]["restant"] == 0

def test_credit_zero():
    _, e, r = run(financement={"apport_pct": 10, "subvention_pct": 90, "credit_pct": 0}, credit={"duree_mois": "", "taux_annuel": ""})
    assert e == [] and r["financement"]["credit"] == 0
    assert r["remboursement"]["total_mensualites"] == 0 and all(x == 0 for x in r["compte_resultat"]["remboursement"])
    f = r["financement"]; assert f["apport"] + f["subvention"] == 1851150

def test_amortissement():
    _, _, r = run(finances=beng()["finances"] | {"amenagement": {"description": "x", "montant": 100000, "duree_vie": 3},
        "equipements": [{"designation": "E", "quantite": 2, "cout_unitaire": 100000, "duree_vie": 3}]})
    a = r["amortissements"]
    assert a["amenagement"]["annees"] == [33333, 33333, 33334, 0, 0]
    assert a["equipements"][0]["annees"] == [66667, 66667, 66666, 0, 0]
    assert sum(a["equipements"][0]["annees"]) == 200000

def test_hausse_et_marchandises():
    fin = beng()["finances"] | {"hausse_ventes": 10, "hausse_charges": 5,
        "intrants": [{"designation": "M", "cout": 100000}]}
    c, e, r = run(finances=fin)
    assert e == []
    assert r["ventes"]["total_annees"][0] == 610000 * 12
    assert r["ventes"]["total_annees"][1] == round(610000 * 12 * 1.1)
    cr = r["compte_resultat"]
    assert cr["marge_brute"][1] == cr["ventes"][1] - cr["charges_exploitation"][1]
    assert cr["resultat_net"][1] == cr["rbe"][1] - cr["remboursement"][1]
    assert cr["remboursement"][1] == r["remboursement"]["par_annee"][0]

def test_aucun_amenagement_ok():
    _, e, r = run(); assert r["amortissements"]["amenagement"] is None

def test_champs_obligatoires():
    c = normaliser({}); assert len(valider(c)) > 20
    _, e, _ = run(entreprise={"nom": "", "activite": "x", "numero_plan": ""})
    assert any(x["champ"] == "entreprise.nom" for x in e)

def test_zero_accepte_vide_refuse():
    _, e, _ = run(finances=beng()["finances"] | {"frais_rc": 0}); assert e == []
    _, e, _ = run(finances=beng()["finances"] | {"frais_rc": ""}); assert e

def test_offre_arret_refuse():
    _, e, _ = run(marche=beng()["marche"] | {"offre": list("MMMBBBMMMEEA")})
    assert any(x["champ"].startswith("marche.offre") for x in e)

def test_independant_beng_remboursement():
    # recalcul indépendant (float) : 555345 à 9,6 %/an sur 12 mois
    P, r, n = 555345, 0.096/12, 12
    m = P*r/(1-(1+r)**-n)
    _, _, res = run()
    assert abs(res["remboursement"]["mensualite"] - m) <= 1
