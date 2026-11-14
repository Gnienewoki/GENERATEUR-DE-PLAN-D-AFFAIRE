"use strict";
/* Questionnaire MPE : le serveur (calculs.py) fait TOUS les calculs et la validation ; ici on affiche. */
const MOIS = ["Jan", "Fév.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept", "Oct.", "Nov.", "Déc."];
const KEY = "mpe_brouillon_v1";

const LISTES = {
  "marche.concurrents": { max: 3, nom: "Concurrent", cols: [
    { k: "caracteristiques", l: "Caractéristiques du concurrent", t: "area" },
    { k: "forces", l: "Ses forces", t: "area" }, { k: "faiblesses", l: "Ses faiblesses", t: "area" }] },
  "finances.equipements": { max: 9, nom: "Équipement", cols: [
    { k: "designation", l: "Désignation" }, { k: "quantite", l: "Quantité", t: "num" },
    { k: "cout_unitaire", l: "Coût unitaire (FCFA)", t: "num" }, { k: "duree_vie", l: "Durée de vie (ans)", t: "num" }] },
  "finances.intrants": { max: 7, nom: "Marchandise", cols: [
    { k: "designation", l: "Désignation" }, { k: "cout", l: "Coût par mois (FCFA)", t: "num" }] },
  "finances.fonctionnement": { max: 6, nom: "Dépense", cols: [
    { k: "designation", l: "Désignation" }, { k: "quantite", l: "Quantité", t: "num" },
    { k: "cout_unitaire", l: "Coût unitaire par mois (FCFA)", t: "num" }] },
  "finances.ventes": { max: 5, nom: "Produit ou service", cols: [
    { k: "designation", l: "Produit ou service" }, { k: "quantite_mois", l: "Quantité vendue par mois", t: "num" },
    { k: "prix_unitaire", l: "Prix unitaire de vente (FCFA)", t: "num" }] },
};

/* Étapes. type: t=texte, a=zone de texte, n=nombre, s=choix, m=12 mois, L=liste, P=pourcentage, H=html spécial */
const ETAPES = [
  { id: "entreprise", titre: "Page de garde", intro: "Ces informations apparaissent sur la première page du plan.", champs: [
    { p: "entreprise.nom", t: "t", l: "Nom de l'entreprise", r: 1, ex: "Ex. : BENG PRODUCTION" },
    { p: "entreprise.activite", t: "t", l: "Activité", r: 1, aide: "En une phrase.", ex: "Ex. : Production audiovisuelle et photographie" },
    { p: "entreprise.numero_plan", t: "t", l: "Numéro du plan d'affaires", aide: "Facultatif. Laissez vide si vous n'en avez pas encore." }] },
  { id: "contexte", titre: "Contexte et justification", intro: "Vos réponses sont reprises telles quelles dans le plan. Écrivez des phrases complètes.", champs: [
    { p: "contexte.existante", t: "s", l: "L'activité existe-t-elle déjà ?", r: 1, opts: [["", "Choisir…"], ["oui", "Oui"], ["non", "Non, c'est un nouveau projet"]] },
    { p: "contexte.depuis_annees", t: "n", l: "Depuis combien d'années ?", r: 1, si: "contexte.existante=oui", ex: "Ex. : 2" },
    { p: "contexte.ca_annuel", t: "n", l: "Chiffre d'affaires annuel actuel (FCFA)", r: 1, si: "contexte.existante=oui" },
    { p: "contexte.nb_clients", t: "n", l: "Nombre de clients ou partenaires", r: 1, si: "contexte.existante=oui" },
    { p: "contexte.pourquoi", t: "a", l: "Pourquoi voulez-vous réaliser ce projet ?", r: 1, aide: "Votre motivation, le besoin que vous voyez.", ex: "Ex. : Il y a peu de studios de qualité à Abengourou et beaucoup de demandes pour des événements." },
    { p: "contexte.usage_financement", t: "a", l: "À quoi servira le financement ?", r: 1, ex: "Ex. : Acheter le matériel de tournage et de montage." },
    { p: "contexte.pourquoi_marchera", t: "a", l: "Pourquoi ce projet va-t-il marcher ?", r: 1, aide: "Vos atouts, la demande, votre expérience." }] },
  { id: "porteur", titre: "Porteur de projet et mode de gestion", champs: [
    { p: "porteur.nom_prenoms", t: "t", l: "Nom et prénoms du promoteur", r: 1 },
    { p: "porteur.nationalite", t: "t", l: "Nationalité", r: 1, ex: "Ex. : Ivoirienne" },
    { p: "porteur.sexe", t: "s", l: "Sexe", r: 1, aide: "Détermine « Promoteur » ou « Promotrice » dans l'organigramme.", opts: [["", "Choisir…"], ["Masculin", "Masculin"], ["Féminin", "Féminin"]] },
    { p: "porteur.situation_matrimoniale", t: "t", l: "Situation matrimoniale", r: 1, ex: "Ex. : Célibataire" },
    { p: "porteur.lieu_habitation", t: "t", l: "Lieu d'habitation", r: 1 },
    { p: "porteur.contacts", t: "t", l: "Contacts", r: 1, ex: "Ex. : 07 00 00 00 00" },
    { p: "porteur.formation", t: "t", l: "Formation qualifiante", r: 1 },
    { p: "porteur.situation_pro", t: "t", l: "Situation professionnelle actuelle", r: 1 },
    { p: "porteur.annees_experience", t: "t", l: "Années d'expérience dans l'activité", r: 1, ex: "Ex. : 3 ans" },
    { p: "porteur.maitrise_technique", t: "a", l: "Maîtrise des aspects techniques", r: 1 },
    { p: "gestion.mode", t: "a", l: "Mode de gestion envisagé par l'entreprise", r: 1, aide: "Qui dirige, qui fait quoi.", ex: "Ex. : Je dirige l'entreprise avec un gérant qui suit les activités au quotidien." },
    { p: "gestion.commentaires", t: "a", l: "Commentaires sur l'organisation", aide: "Facultatif." }] },
  { id: "marche", titre: "Analyse du marché", champs: [
    { p: "marche.description", t: "a", l: "Description du marché", r: 1, aide: "Qui achète, où, combien de personnes." },
    { p: "marche.tendance", t: "a", l: "Tendance du marché", r: 1, aide: "Le marché progresse-t-il, stagne-t-il ?" },
    { t: "H", h: "<h3 class='t'>Niveau d'intensité de la demande par mois <span class='req'>*</span></h3><p class='aide'>Un seul niveau par mois : Élevé, Moyen, Bas ou Arrêt.</p>" },
    { p: "marche.demande", t: "m", r: 1, opts: [["", "—"], ["E", "Élevé"], ["M", "Moyen"], ["B", "Bas"], ["A", "Arrêt"]] },
    { t: "H", h: "<h3 class='t'>Niveau d'existence de l'offre par mois <span class='req'>*</span></h3><p class='aide'>Un seul niveau par mois : Élevé, Moyen ou Bas.</p>" },
    { p: "marche.offre", t: "m", r: 1, opts: [["", "—"], ["E", "Élevé"], ["M", "Moyen"], ["B", "Bas"]] }] },
  { id: "strategie", titre: "Concurrence et stratégie commerciale", champs: [
    { p: "marche.concurrence", t: "a", l: "Concurrence actuelle ou potentielle", r: 1, aide: "Qui sont vos concurrents et où sont-ils ?" },
    { t: "L", p: "marche.concurrents", l: "Analyse de la concurrence", r: 1, aide: "Jusqu'à 3 concurrents." },
    { p: "marche.clients", t: "a", l: "Nos potentiels clients sont…", r: 1 },
    { p: "marche.strategie_produit", t: "a", l: "Stratégie de produit ou service", r: 1 },
    { p: "marche.strategie_prix", t: "a", l: "Stratégie de prix", r: 1 }] },
  { id: "technique", titre: "Description technique", champs: [
    { p: "technique.process", t: "a", l: "Description du process de production ou de prestation", r: 1, aide: "Étape par étape. Une étape par ligne.", ex: "1. Prise de contact\n2. Tournage\n3. Montage\n4. Livraison" },
    { p: "technique.competences", t: "a", l: "Description des compétences requises", r: 1, aide: "Une compétence par ligne." }] },
  { id: "investissements", titre: "Investissements", intro: "Entrez 0 si une rubrique ne vous concerne pas.", champs: [
    { p: "finances.frais_rc", t: "n", l: "Frais de registre de commerce (FCFA)", r: 1, ex: "Ex. : 25000" },
    { p: "finances.amenagement.montant", t: "n", l: "Aménagement (FCFA)", r: 1, aide: "Travaux d'installation du local. 0 si aucun." },
    { p: "finances.amenagement.description", t: "t", l: "Description des travaux d'aménagement", si: "finances.amenagement.montant>0", r: 1 },
    { p: "finances.amenagement.duree_vie", t: "n", l: "Durée de vie de l'aménagement (ans)", si: "finances.amenagement.montant>0", r: 1 },
    { t: "L", p: "finances.equipements", l: "Équipements", r: 1, aide: "Jusqu'à 9 équipements." }] },
  { id: "exploitation", titre: "Exploitation : charges et ventes", champs: [
    { t: "L", p: "finances.intrants", l: "Marchandises ou intrants (facultatif)", aide: "Ce que vous achetez chaque mois pour produire ou revendre. Jusqu'à 7 lignes." },
    { t: "L", p: "finances.fonctionnement", l: "Dépenses de fonctionnement par mois", r: 1, aide: "Loyer, salaires, électricité, transport… Jusqu'à 6 lignes." },
    { t: "L", p: "finances.ventes", l: "Ventes mensuelles", r: 1, aide: "Jusqu'à 5 produits ou services." },
    { t: "H", h: "<h3 class='t'>Hypothèses (facultatif)</h3><p class='aide'>Si vous laissez vide : 0 % de hausse, 1 mois de fonds de roulement, 5 % d'imprévus.</p>" },
    { p: "finances.hausse_ventes", t: "n", l: "Hausse annuelle des ventes (%)", ex: "Ex. : 5" },
    { p: "finances.hausse_charges", t: "n", l: "Hausse annuelle des charges (%)" },
    { p: "finances.mois_fonds_roulement", t: "n", l: "Mois de fonds de roulement", ex: "Ex. : 1" },
    { p: "finances.imprevus_pct", t: "n", l: "Imprévus (% du coût total)", ex: "Ex. : 5" }] },
  { id: "financement", titre: "Financement et crédit", intro: "Répartissez le coût total du projet entre les trois sources. Le total doit faire 100 %.", champs: [
    { p: "financement.apport_pct", t: "n", l: "Apport personnel (%)", r: 1, ex: "Ex. : 10" },
    { p: "financement.subvention_pct", t: "n", l: "Subvention (%)", r: 1, ex: "Ex. : 60" },
    { p: "financement.credit_pct", t: "n", l: "Crédit IMF (%)", r: 1, ex: "Ex. : 30" },
    { t: "H", id: "pct-total", h: "" },
    { p: "credit.duree_mois", t: "n", l: "Durée du crédit (mois, de 12 à 24)", r: 1, si: "financement.credit_pct>0", ex: "Ex. : 12" },
    { p: "credit.taux_annuel", t: "n", l: "Taux d'intérêt annuel de la banque (%)", r: 1, si: "financement.credit_pct>0", ex: "Ex. : 9,6" }] },
  { id: "final", titre: "Conclusion et téléchargement", champs: [
    { p: "conclusion", t: "a", l: "Conclusion", aide: "Facultatif. Si vous laissez vide, une conclusion est rédigée à partir de vos chiffres." },
    { t: "H", id: "apercu", h: "" }] },
];

let etat = {}, courant = 0, valides = new Set(), erreurs = [], res = null, timer = null;

/* ---------- état ---------- */
const get = (p, o = etat) => p.split(".").reduce((a, k) => (a == null ? undefined : a[k]), o);
function set(p, v) {
  const ks = p.split("."); let o = etat;
  ks.slice(0, -1).forEach((k, i) => { if (o[k] == null) o[k] = /^\d+$/.test(ks[i + 1]) ? [] : {}; o = o[k]; });
  o[ks[ks.length - 1]] = v;
}
function defauts() {
  etat = { marche: { demande: Array(12).fill(""), offre: Array(12).fill(""), concurrents: [{}] },
    finances: { equipements: [{}], intrants: [], fonctionnement: [{}], ventes: [{}], amenagement: {} } };
}
function sauver() { try { localStorage.setItem(KEY, JSON.stringify({ etat, courant })); } catch (e) {} }
function charger() {
  try { const s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && s.etat) { etat = s.etat; courant = s.courant || 0; return true; } } catch (e) {}
  return false;
}
function complete() { // garantit la présence des tableaux attendus
  const d = (function () { const e = etat; defauts(); const x = etat; etat = e; return x; })();
  ["marche.demande", "marche.offre", "marche.concurrents", "finances.equipements", "finances.intrants", "finances.fonctionnement", "finances.ventes"]
    .forEach(p => { if (!Array.isArray(get(p))) set(p, get(p, d)); });
  ["demande", "offre"].forEach(k => { const a = etat.marche[k]; while (a.length < 12) a.push(""); });
  if (!etat.finances.amenagement) etat.finances.amenagement = {};
}

/* ---------- rendu ---------- */
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nb = n => (n == null ? "" : Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " "));
const pct = n => String(n).replace(".", ",");

function visible(ch) {
  if (!ch.si) return true;
  const m = ch.si.match(/^(.+?)(=|>)(.+)$/); const v = get(m[1]);
  if (m[2] === "=") return v === m[3];
  return parseFloat(String(v ?? "").replace(",", ".").replace(/\s/g, "")) > parseFloat(m[3]);
}
const star = r => (r ? "<span class='req' aria-hidden='true'>*</span><span class='sr' hidden> (obligatoire)</span>" : "");
const idp = p => "f_" + p.replace(/\./g, "_");

function champHtml(ch) {
  if (ch.t === "H") return ch.id ? `<div id="${ch.id}">${ch.h}</div>` : ch.h;
  if (ch.t === "L") return listeHtml(ch);
  const id = idp(ch.p), aide = ch.aide ? `<p class="aide" id="${id}_a">${esc(ch.aide)}</p>` : "";
  const ex = ch.ex ? `<p class="ex">${esc(ch.ex)}</p>` : "";
  const err = `<p class="msg" data-err="${ch.p}" role="alert" hidden></p>`;
  if (ch.t === "m") {
    const cells = MOIS.map((m, i) => `<div><label for="${id}_${i}">${m}</label><select id="${id}_${i}" data-p="${ch.p}.${i}">` +
      ch.opts.map(([v, l]) => `<option value="${v}"${get(ch.p + "." + i) === v ? " selected" : ""}>${l}</option>`).join("") + "</select>" +
      `<p class="msg" data-err="${ch.p}.${i}" hidden></p></div>`).join("");
    return `<div class="champ"><div class="mois">${cells}</div></div>`;
  }
  let inp;
  const v = esc(get(ch.p) ?? "");
  if (ch.t === "a") inp = `<textarea id="${id}" data-p="${ch.p}" aria-describedby="${id}_a">${v}</textarea>`;
  else if (ch.t === "s") inp = `<select id="${id}" data-p="${ch.p}">` + ch.opts.map(([o, l]) => `<option value="${o}"${get(ch.p) === o ? " selected" : ""}>${l}</option>`).join("") + "</select>";
  else inp = `<input id="${id}" data-p="${ch.p}" ${ch.t === "n" ? 'inputmode="decimal"' : ""} value="${v}" autocomplete="off">`;
  return `<div class="champ" data-si="${ch.si || ""}"><label for="${id}">${esc(ch.l)}${star(ch.r)}</label>${aide}${inp}${ex}${err}</div>`;
}

function listeHtml(ch) {
  const cfg = LISTES[ch.p], arr = get(ch.p) || [];
  const lignes = arr.map((row, i) => {
    const cells = cfg.cols.map(c => {
      const p = `${ch.p}.${i}.${c.k}`, id = idp(p), val = esc(row[c.k] ?? "");
      const inp = c.t === "area" ? `<textarea id="${id}" data-p="${p}" style="min-height:80px">${val}</textarea>`
        : `<input id="${id}" data-p="${p}" ${c.t === "num" ? 'inputmode="decimal"' : ""} value="${val}" autocomplete="off">`;
      return `<div class="cell"><label for="${id}">${esc(c.l)}</label>${inp}<p class="msg" data-err="${p}" hidden></p></div>`;
    }).join("");
    return `<div class="ligne"><div class="ligne-tete"><span>${cfg.nom} ${i + 1}</span><button type="button" class="btn sec petit" data-del="${ch.p}" data-i="${i}" aria-label="Supprimer ${cfg.nom} ${i + 1}">Supprimer</button></div>${cells}</div>`;
  }).join("");
  const plein = arr.length >= cfg.max;
  return `<div class="champ"><span class="lab">${esc(ch.l)}${star(ch.r)}</span>${ch.aide ? `<p class="aide">${esc(ch.aide)}</p>` : ""}
    <p class="msg" data-err="${ch.p}" role="alert" hidden></p>${lignes}
    <button type="button" class="btn sec petit" data-add="${ch.p}" ${plein ? "disabled" : ""}>+ Ajouter (${arr.length}/${cfg.max})</button></div>`;
}

function rendreEtapes() {
  document.getElementById("etapes").innerHTML = ETAPES.map((e, i) =>
    `<button type="button" class="etape${i === courant ? " actuelle" : ""}${valides.has(i) ? " ok" : ""}" data-go="${i}" ${i === courant ? 'aria-current="step"' : ""}>${valides.has(i) ? "✓ " : ""}${i + 1}. ${esc(e.titre)}</button>`).join("");
  document.getElementById("barre").style.width = ((courant + 1) / ETAPES.length * 100) + "%";
  const act = document.querySelector(".etape.actuelle"); if (act && act.scrollIntoView) act.scrollIntoView({ inline: "center", block: "nearest" });
}

function rendre() {
  const e = ETAPES[courant];
  const dernier = courant === ETAPES.length - 1;
  document.getElementById("contenu").innerHTML =
    `<p class="intro" style="margin:0 0 2px">Étape ${courant + 1} sur ${ETAPES.length} · les champs marqués <span class="req">*</span> sont obligatoires</p>
     <h2>${esc(e.titre)}</h2>${e.intro ? `<p class="intro">${esc(e.intro)}</p>` : ""}
     <div id="bandeau"></div><form id="form" novalidate>${e.champs.map(champHtml).join("")}</form>
     <div class="nav"><button type="button" class="btn sec" id="prec" ${courant === 0 ? "disabled" : ""}>Précédent</button>
     ${dernier ? `<button type="button" class="btn vert" id="telecharger">Télécharger le plan d'affaires (.docx)</button>` : `<button type="button" class="btn" id="suiv">Suivant</button>`}</div>`;
  majVisibilite(); rendreEtapes();
  if (e.id === "financement") majPct();
  if (dernier) apercu();
}

function majVisibilite() {
  const e = ETAPES[courant];
  document.querySelectorAll(".champ[data-si]").forEach(div => {
    const si = div.dataset.si; if (!si) return;
    div.hidden = !visible({ si });
  });
}

/* ---------- erreurs ---------- */
function montrerErreurs(liste) {
  document.querySelectorAll(".msg").forEach(m => { m.hidden = true; m.textContent = ""; });
  document.querySelectorAll(".invalide").forEach(i => i.classList.remove("invalide"));
  let premier = null;
  liste.forEach(er => {
    const m = document.querySelector(`[data-err="${CSS.escape(er.champ)}"]`);
    if (m) { m.hidden = false; m.textContent = er.message; }
    const inp = document.querySelector(`[data-p="${CSS.escape(er.champ)}"]`);
    if (inp) { inp.classList.add("invalide"); inp.setAttribute("aria-invalid", "true"); if (!premier) premier = inp; }
    else if (m && !premier) premier = m;
  });
  const b = document.getElementById("bandeau");
  const horsChamp = liste.filter(er => !document.querySelector(`[data-err="${CSS.escape(er.champ)}"]`));
  b.innerHTML = liste.length ? `<div class="alerte" role="alert"><strong>${liste.length} réponse${liste.length > 1 ? "s" : ""} à compléter ou corriger.</strong>${horsChamp.map(x => `<br>${esc(x.message)}`).join("")}</div>` : "";
  if (premier && premier.scrollIntoView) { premier.scrollIntoView({ block: "center", behavior: "smooth" }); if (premier.focus) premier.focus({ preventScroll: true }); }
}

/* ---------- serveur ---------- */
async function appeler(chemin) {
  const r = await fetch(chemin, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(etat) });
  return r;
}
async function actualiser() {
  try {
    const r = await appeler("/api/calcul"); if (!r.ok) return null;
    const j = await r.json(); erreurs = j.erreurs; res = j.resultats; recap(); majPct();
    ETAPES.forEach((e, i) => { if (!erreurs.some(x => x.etape === e.id) && i < ETAPES.length - 1 && valides.has(i) === false && false) valides.add(i); });
    return j;
  } catch (e) { return null; }
}
function planifier() { sauver(); clearTimeout(timer); timer = setTimeout(actualiser, 400); }

function recap() {
  const el = document.getElementById("recap");
  if (!res) { el.innerHTML = "<dt>Saisissez vos montants pour voir le récapitulatif.</dt>"; return; }
  const f = res.financement, r = res.remboursement;
  el.innerHTML = `<dt>Coût total au démarrage</dt><dd class="grand">${nb(f.cout_total)} FCFA</dd>
   <dt>Apport personnel (${pct(f.apport_pct)} %)</dt><dd>${nb(f.apport)} FCFA</dd>
   <dt>Subvention (${pct(f.subvention_pct)} %)</dt><dd>${nb(f.subvention)} FCFA</dd>
   <dt>Crédit IMF (${pct(f.credit_pct)} %)</dt><dd>${nb(f.credit)} FCFA</dd>
   <dt>Mensualité estimée</dt><dd>${f.credit > 0 ? nb(r.mensualite) + " FCFA" : "—"}</dd>`;
}

function majPct() {
  const box = document.getElementById("pct-total"); if (!box) return;
  const n = p => { const v = parseFloat(String(get(p) ?? "").replace(",", ".").replace(/\s/g, "")); return isNaN(v) ? 0 : v; };
  const t = n("financement.apport_pct") + n("financement.subvention_pct") + n("financement.credit_pct");
  const bon = Math.abs(t - 100) <= 0.01;
  const m = res ? res.financement : null;
  box.innerHTML = `<div class="pct-total ${bon ? "bon" : "mauvais"}" role="status">Total : ${pct(Math.round(t * 100) / 100)} % ${bon ? "✓" : "— il doit faire 100 %"}</div>` +
    (m ? `<p class="aide">Apport : ${nb(m.apport)} FCFA · Subvention : ${nb(m.subvention)} FCFA · Crédit IMF : ${nb(m.credit)} FCFA</p>` : "");
}

/* ---------- aperçu ---------- */
const T = (titre, ent, lignes) => `<h3 class="t">${titre}</h3><div class="tbl-wrap"><table class="apercu"><thead><tr>${ent.map(e => `<th scope="col">${e}</th>`).join("")}</tr></thead><tbody>${lignes.map(l => `<tr${l.tot ? ' class="tot"' : ""}>${l.c.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const a5 = v => v.map(nb);

async function apercu() {
  const zone = document.getElementById("apercu"); if (!zone) return;
  const j = await actualiser();
  if (!res) { zone.innerHTML = "<p class='aide'>Complétez les étapes précédentes pour voir l'aperçu.</p>"; return; }
  const i = res.investissement, ch = res.charges, v = res.ventes, am = res.amortissements, rb = res.remboursement, cr = res.compte_resultat, f = res.financement;
  const ok = erreurs.length === 0;
  const manque = erreurs.length ? `<div class="alerte" role="alert"><strong>${erreurs.length} réponse(s) obligatoire(s) manquante(s) ou incorrecte(s).</strong> Les étapes concernées sont marquées ci-dessus ; le téléchargement est bloqué tant qu'elles ne sont pas complétées.<ul>${[...new Set(erreurs.map(x => x.etape))].map(id => { const k = ETAPES.findIndex(e => e.id === id); return `<li><a href="#" data-go="${k}">${esc(ETAPES[k].titre)}</a></li>`; }).join("")}</ul></div>` : `<div class="ok-msg">Toutes les réponses obligatoires sont remplies. Vous pouvez télécharger votre plan.</div>`;
  const dl = document.getElementById("telecharger"); if (dl) dl.disabled = !ok;
  zone.innerHTML = manque + "<h2 style='font-size:1.1rem;color:var(--marine)'>Aperçu des tableaux financiers</h2>" +
    T("Coût total du projet", ["Désignation", "Quantité", "Coût unitaire", "Coût global"], [
      { c: ["Frais de registre de commerce", "1", nb(i.frais_rc), nb(i.frais_rc)] },
      { c: ["Aménagement", "", "", nb(i.amenagement.montant)] },
      ...i.equipements.map(e => ({ c: [esc(e.designation), e.quantite, nb(e.cout_unitaire), nb(e.cout_global)] })),
      { tot: 1, c: ["Total investissement", "", "", nb(i.total_investissement)] },
      ...i.fonds_roulement.map(e => ({ c: [esc(e.designation) + " (fonds de roulement)", e.quantite, nb(e.cout_unitaire), nb(e.cout_global)] })),
      { tot: 1, c: ["Coût total", "", "", nb(i.cout_total)] }, { c: ["Imprévus", "", "", nb(i.imprevu)] },
      { tot: 1, c: ["Coût total du projet au démarrage", "", "", nb(i.cout_total_demarrage)] }]) +
    T("Charges d'exploitation", ["", "Par mois", "Année 1", "Année 2", "Année 3", "Année 4", "Année 5"], [
      ...ch.marchandises.map(l => ({ c: [esc(l.designation), nb(l.mensuel), ...a5(l.annees)] })),
      ...ch.fonctionnement.map(l => ({ c: [esc(l.designation), nb(l.mensuel), ...a5(l.annees)] })),
      { tot: 1, c: ["Total", nb(ch.total.mensuel), ...a5(ch.total.annees)] }]) +
    T("Estimation des ventes", ["", "Qté/mois", "Prix", "CA/mois", "Année 1", "Année 2", "Année 3", "Année 4", "Année 5"], [
      ...v.lignes.map(l => ({ c: [esc(l.designation), l.quantite, nb(l.prix_unitaire), nb(l.ca_mois), ...a5(l.annees)] })),
      { tot: 1, c: ["Total des ventes", "", "", nb(v.total_mois), ...a5(v.total_annees)] }]) +
    T("Amortissements", ["Désignation", "Valeur", "Durée", "Année 1", "Année 2", "Année 3", "Année 4", "Année 5"], [
      ...(am.amenagement ? [{ c: ["Aménagement", nb(am.amenagement.valeur), am.amenagement.duree_vie, ...a5(am.amenagement.annees)] }] : []),
      ...am.equipements.map(l => ({ c: [esc(l.designation), nb(l.valeur), l.duree_vie, ...a5(l.annees)] })),
      { tot: 1, c: ["Total amortissement", "", "", ...a5(am.total_annees)] }]) +
    T(`Plan de remboursement (${rb.duree_mois} mois, ${pct(rb.taux_annuel)} %)`, ["Mois", "Capital", "Amortissement", "Intérêt", "Mensualité", "Capital restant dû"], [
      ...rb.lignes.map(l => ({ c: [l.mois, nb(l.capital), nb(l.amortissement), nb(l.interet), nb(l.mensualite), nb(l.restant)] })),
      { tot: 1, c: ["Totaux", "", nb(rb.total_amortissement), nb(rb.total_interet), nb(rb.total_mensualites), ""] }]) +
    T("Compte de résultat sur 5 ans", ["", "Mensuel", "Année 1", "Année 2", "Année 3", "Année 4", "Année 5"], [
      ["Total des ventes", "ventes"], ["Total charges d'exploitation", "charges_exploitation"], ["Marge brute", "marge_brute"],
      ["Charges de fonctionnement", "charges_fonctionnement"], ["Excédent brut d'exploitation", "ebe"], ["Dotations aux amortissements", "dotations"],
      ["Résultat brut d'exploitation", "rbe"], ["Remboursement", "remboursement"], ["Résultat net d'exploitation", "resultat_net"]]
      .map(([l, k]) => ({ tot: ["marge_brute", "ebe", "rbe", "resultat_net"].includes(k), c: [l, ...a5(cr[k])] }))) +
    T("Structure du financement", ["Rubrique", "Montant"], [
      { c: ["Coût total du projet", nb(f.cout_total)] }, { c: [`Apport personnel (${pct(f.apport_pct)}%)`, nb(f.apport)] },
      { c: [`Subvention (${pct(f.subvention_pct)}%)`, nb(f.subvention)] }, { c: [`Crédit IMF (${pct(f.credit_pct)}%)`, nb(f.credit)] }]);
}

/* ---------- actions ---------- */
async function valider(etapeId) {
  const j = await actualiser();
  if (!j) { montrerErreurs([]); document.getElementById("bandeau").innerHTML = "<div class='alerte' role='alert'>Impossible de joindre le serveur. Vérifiez votre connexion.</div>"; return false; }
  const liste = j.erreurs.filter(x => x.etape === etapeId);
  montrerErreurs(liste);
  return liste.length === 0;
}
async function aller(i) { courant = Math.max(0, Math.min(ETAPES.length - 1, i)); sauver(); rendre(); document.getElementById("contenu").focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: "smooth" }); }

document.addEventListener("click", async ev => {
  const t = ev.target.closest("button, a"); if (!t) return;
  if (t.dataset.go !== undefined) { ev.preventDefault(); return aller(+t.dataset.go); }
  if (t.id === "prec") return aller(courant - 1);
  if (t.id === "suiv") { const ok = await valider(ETAPES[courant].id); if (ok) { valides.add(courant); aller(courant + 1); } return; }
  if (t.dataset.add) { const a = get(t.dataset.add); if (a.length < LISTES[t.dataset.add].max) a.push({}); sauver(); rendre(); return actualiser(); }
  if (t.dataset.del) { get(t.dataset.del).splice(+t.dataset.i, 1); sauver(); rendre(); return actualiser(); }
  if (t.id === "telecharger") return telecharger(t);
  if (t.id === "exporter") return exporter();
  if (t.id === "effacer") { if (confirm("Effacer toutes vos réponses sur cet appareil ?")) { try { localStorage.removeItem(KEY); } catch (e) {} defauts(); valides = new Set(); courant = 0; res = null; rendre(); recap(); } }
});
document.addEventListener("input", ev => {
  const p = ev.target.dataset && ev.target.dataset.p; if (!p) return;
  set(p, ev.target.value); ev.target.classList.remove("invalide");
  if (ev.target.tagName === "SELECT") majVisibilite();
  else if (/^(contexte\.existante|finances\.amenagement\.montant|financement\.credit_pct)$/.test(p)) majVisibilite();
  majVisibilite(); planifier(); majPct();
});
document.addEventListener("change", ev => { if (ev.target.id === "importer") importer(ev.target); });

async function telecharger(btn) {
  const j = await actualiser();
  if (j && j.erreurs.length) { apercu(); return; }
  btn.disabled = true; const txt = btn.textContent; btn.textContent = "Génération en cours…";
  try {
    const r = await appeler("/api/generer");
    if (!r.ok) { const e = await r.json().catch(() => ({})); document.getElementById("bandeau").innerHTML = `<div class="alerte" role="alert">${esc(e.erreur || "Erreur de génération.")}</div>`; return; }
    const blob = await r.blob(); const a = document.createElement("a");
    const nom = (etat.entreprise && etat.entreprise.nom || "entreprise").replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 40);
    a.href = URL.createObjectURL(blob); a.download = `Plan_affaires_MPE_${nom}.docx`; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  } catch (e) { document.getElementById("bandeau").innerHTML = "<div class='alerte' role='alert'>Impossible de joindre le serveur.</div>"; }
  finally { btn.textContent = txt; btn.disabled = false; }
}
function exporter() {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(etat, null, 2)], { type: "application/json" }));
  a.download = "mes_reponses_plan_affaires.json"; document.body.appendChild(a); a.click(); a.remove();
}
function importer(input) {
  const f = input.files[0]; if (!f) return;
  const rd = new FileReader();
  rd.onload = () => { try { const o = JSON.parse(rd.result); if (!o || typeof o !== "object") throw 0; etat = o; complete(); courant = 0; valides = new Set(); sauver(); rendre(); actualiser(); }
    catch (e) { alert("Ce fichier n'est pas valide."); } input.value = ""; };
  rd.readAsText(f);
}

/* ---------- démarrage ---------- */
if (!charger()) defauts();
complete(); rendre(); actualiser();
