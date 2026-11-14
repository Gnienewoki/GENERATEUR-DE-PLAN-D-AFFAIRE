import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from app.calculs import normaliser, valider, calculer
from app.docx_filler import generer
from beng import beng
def make(out, **ov):
    c = normaliser(beng(**ov)); assert valider(c) == [], valider(c)
    pathlib.Path(out).write_bytes(generer(c, calculer(c)))
if __name__ == "__main__":
    make("/tmp/r/beng.docx")
