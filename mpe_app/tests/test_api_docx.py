import io, docx
from fastapi.testclient import TestClient
from app.main import app, MAX_BODY
from app.docx_filler import TEMPLATE
from beng import beng

cl = TestClient(app)

def textes(d):
    return [p.text.strip() for p in d.paragraphs if p.text.strip() and not set(p.text.strip()) <= set("…. ")]

def test_healthz(): assert cl.get("/healthz").json() == {"ok": True}

def test_calcul_et_generation():
    r = cl.post("/api/calcul", json=beng()); j = r.json()
    assert j["erreurs"] == [] and j["resultats"]["financement"]["credit"] == 555345
    g = cl.post("/api/generer", json=beng()); assert g.status_code == 200
    d = docx.Document(io.BytesIO(g.content)); t = docx.Document(str(TEMPLATE))
    assert len(d.tables) == len(t.tables) == 12
    titres = ["CONTEXTE ET JUSTIFICATION", "PRESENTATION DU PORTEUR DE PROJET ET MODE DE GESTION", "ANALYSE DU MARCHE ET STRATEGIE COMMERCIALE",
              "DESCRIPTION TECHNIQUE DU PROJET", "ETUDE FINANCIERE DU PROJET", "CONCLUSION"]
    ts = textes(d)
    pos = [ts.index(x) for x in titres]
    assert pos == sorted(pos)
    full = "\n".join(p.text for p in d.paragraphs) + "".join(c.text for tb in d.tables for r in tb.rows for c in r.cells)
    assert "1 851 150" in full.replace(" ", " ") and "BENG PRODUCTION" in full

def test_generation_bloquee_si_incomplet():
    b = beng(entreprise={"nom": "", "activite": "x", "numero_plan": ""})
    g = cl.post("/api/generer", json=b); assert g.status_code == 422 and g.json()["erreurs"]

def test_promotrice():
    b = beng(porteur=beng()["porteur"] | {"sexe": "Féminin"})
    g = cl.post("/api/generer", json=b)
    import zipfile; x = zipfile.ZipFile(io.BytesIO(g.content)).read("word/document.xml").decode()
    assert "Promotrice" in x and "Promoteur<" not in x.replace("promoteur", "")

def test_pas_de_points_residuels_dans_organigramme():
    g = cl.post("/api/generer", json=beng())
    import zipfile; x = zipfile.ZipFile(io.BytesIO(g.content)).read("word/document.xml").decode()
    assert "KOUASSI Jean" in x and "BENG PRODUCTION" in x

def test_taille_limite():
    r = cl.post("/api/calcul", content=b"{" + b" " * (MAX_BODY + 10) + b"}", headers={"content-type": "application/json"})
    assert r.status_code == 413

def test_json_invalide():
    assert cl.post("/api/calcul", content=b"pas du json").status_code == 400
    assert cl.post("/api/calcul", content=b"[]").status_code == 400

def test_limitation():
    from app import main
    main._hits.clear()
    codes = [cl.post("/api/generer", json={}).status_code for _ in range(14)]
    assert 429 in codes; main._hits.clear()
