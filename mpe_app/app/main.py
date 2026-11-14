# -*- coding: utf-8 -*-
"""Application web : questionnaire -> plan d'affaires MPE (.docx). Aucune donnée n'est conservée."""
import json
import re
import time
from collections import defaultdict, deque
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .calculs import normaliser, valider, calculer
from .docx_filler import generer

STATIC = Path(__file__).with_name("static")
MAX_BODY = 300_000          # octets
LIMITES = {"/api/calcul": 120, "/api/generer": 12}   # requêtes par minute et par adresse
_hits = defaultdict(deque)

app = FastAPI(title="Générateur de plan d'affaires MPE", docs_url=None, redoc_url=None, openapi_url=None)


def _json(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    raise TypeError


def reponse_json(data, status=200):
    return Response(json.dumps(data, default=_json, ensure_ascii=False), status_code=status,
                    media_type="application/json")


def _ip(request):
    fwd = request.headers.get("x-forwarded-for")
    return (fwd.split(",")[0].strip() if fwd else request.client.host) if (fwd or request.client) else "?"


@app.middleware("http")
async def garde_fous(request: Request, call_next):
    path = request.url.path
    if path in LIMITES:
        cle, now = (path, _ip(request)), time.time()
        q = _hits[cle]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= LIMITES[path]:
            return reponse_json({"erreur": "Trop de demandes. Réessayez dans une minute."}, 429)
        q.append(now)
        if int(request.headers.get("content-length") or 0) > MAX_BODY:
            return reponse_json({"erreur": "Données trop volumineuses."}, 413)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store" if path.startswith("/api") else "no-cache"
    resp.headers["Content-Security-Policy"] = ("default-src 'self'; style-src 'self' 'unsafe-inline'; "
                                               "img-src 'self' data:; frame-ancestors 'none'")
    return resp


async def _lire(request):
    corps = await request.body()
    if len(corps) > MAX_BODY:
        return None
    try:
        data = json.loads(corps or b"{}")
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/api/calcul")
async def api_calcul(request: Request):
    data = await _lire(request)
    if data is None:
        return reponse_json({"erreur": "Requête invalide."}, 400)
    c = normaliser(data)
    erreurs = valider(c)
    try:
        res = calculer(c)
    except Exception:           # saisie incomplète : on ne bloque pas l'aperçu
        res = None
    return reponse_json({"erreurs": erreurs, "resultats": res})


@app.post("/api/generer")
async def api_generer(request: Request):
    data = await _lire(request)
    if data is None:
        return reponse_json({"erreur": "Requête invalide."}, 400)
    c = normaliser(data)
    erreurs = valider(c)
    if erreurs:
        return reponse_json({"erreur": "Des réponses obligatoires manquent ou sont incorrectes.", "erreurs": erreurs}, 422)
    contenu = generer(c, calculer(c))
    nom = re.sub(r"[^A-Za-z0-9]+", "_", c["entreprise"]["nom"]).strip("_")[:40] or "entreprise"
    return Response(contenu, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="Plan_affaires_MPE_{nom}.docx"'})


@app.get("/")
def accueil():
    return FileResponse(STATIC / "index.html")


app.mount("/", StaticFiles(directory=str(STATIC)), name="static")
