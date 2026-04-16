"""
Recupera i dati degli scenari individuali da una sessione esportata in JSON.
Estrae narrativa, titolo, minacce e opportunita direttamente dalla cronologia
dei messaggi, senza chiamate API.

Uso:
  python tools/recupera_scenari.py <path_json> [--apply]

  <path_json>  : percorso al file JSON esportato (es. sessione_1_KJFIPQ.json)
  --apply      : applica le modifiche al DB Postgres (richiede DATABASE_URL)

Senza --apply stampa i risultati e genera un file *_recovery.sql.
"""

import sys
import json
import re
from pathlib import Path


# ── Pattern ───────────────────────────────────────────────────────────────────

_NARRATIVA_SIGNAL = re.compile(
    r"(tessere insieme|costruire la narrativa|racconto coerente|"
    r"costruire il racconto|scenario che abbiamo costruito|"
    r"lascia che ti racconti|provo.*a tessere|"
    r"lasciami.*tessere|eccola\b)",
    re.IGNORECASE,
)

_NARRATIVA_START = re.compile(r"In questo scenario[\s,]", re.IGNORECASE)

_TITOLO_SIGNAL = re.compile(
    r"(titolo|nome a questo scenario|dare un nome|diamo un nome)", re.IGNORECASE
)

# Richieste dell'utente per avere suggerimenti (non è un titolo)
_TITOLO_REQUEST = re.compile(
    r"^(suggerisci|suggeriscimi|proponi|proponi tu|proponi delle opzioni|"
    r"suggerisci tu|proponi.*opzioni|dimmi tu|decidi tu|scegli tu|"
    r"nessun[ao]?\b|fai altre|altre opzioni|non mi convinc)"
    r"(\s+.*)?$",
    re.IGNORECASE,
)

# Selezione numerata dell'utente
_OPZIONE_SELECTION = re.compile(
    r"^(la|il|scelgo la?|prendo la?|preferisco la?)?\s*(prim[ao]|second[ao]|terz[ao])\b",
    re.IGNORECASE,
)

_MINACCE_SIGNAL = re.compile(
    r"(minacce?|rischi?|cosa potrebbe andare storto|forze che potrebbero|"
    r"preoccupa di più|rischi principali)",
    re.IGNORECASE,
)

_OPPORT_SIGNAL = re.compile(
    r"(opportunit|cosa potrebbe funzionare|possibilit|punti di forza|"
    r"potrebbe funzionare davvero bene)",
    re.IGNORECASE,
)

# Transizione EFFETTIVA da minacce a opportunita: il facilitatore AFFERMA che si passa,
# non fa una domanda. "possiamo passare alle opportunità?" NON deve scattare.
_OPPORT_PHASE_START = re.compile(
    r"(passiamo (ora |dunque |allora |adesso )?(alle|a) opportunit"
    r"|entriamo (ora )?(nelle|in|a parlare di) opportunit"
    r"|parliamo (ora |adesso )?(delle|di) opportunit"
    r"|passiamo (alle|a) opportunit)",
    re.IGNORECASE,
)

_CONCLUSO_SIGNAL = re.compile(
    r"(riepilog|scenario che abbiamo costruito insieme|ecco.*riepilog|"
    r"percorso.*(conclus|terminat|finit))",
    re.IGNORECASE,
)

# Risposte brevi utente che segnalano avanzamento, non contenuto
_SKIP_USER = re.compile(
    r"^(si|sì|no|ok|okay|certo|esatto|perfetto|corretto|giusto|"
    r"procedi|procedi pure|puoi procedere|procediamo|vai avanti|"
    r"andiamo avanti|puoi pro(cedere|dere)|continua|avanti|"
    r"passiamo.*tema|passiamo.*opportunit|passiamo.*minacc|"
    r"grazie|grazie mille|ti ringrazio|"
    r"va bene|va bene (cosi|così|questa|tutto)|tutto ok|"
    r"conclusa|concluso|finito|"
    r"mi rispondi\?)[\s\.\!\,]*$",
    re.IGNORECASE,
)


def _is_skip(testo):
    t = testo.strip()
    if _SKIP_USER.match(t):
        return True
    # "passiamo a..." / "passiamo alle opportunità" — gli accenti bloccano il $ finale
    if re.match(r"^passiamo\b", t, re.IGNORECASE):
        return True
    return False


def _is_negation(testo):
    """Risposta negativa breve, es. 'Non credo', 'Non saprei'."""
    return bool(re.match(r"^(non (credo|saprei|penso|direi)|nessun[ao]?|no grazie)[\s\.\!\,]*$",
                         testo.strip(), re.IGNORECASE))


# ── Estrazione narrativa ───────────────────────────────────────────────────────

def _clean_msg(testo):
    """
    Rimuove il JSON grezzo dell'agente dalla fine del messaggio.
    I messaggi dell'agente spesso terminano con {"testo": "", "nuovo_step": ...}
    che contiene parole chiave (minacce, opportunita, ecc.) che confondono il parser.
    """
    for marker in ('{\n  "testo"', '{"testo"', '\n{'):
        idx = testo.find(marker)
        if idx > 50:  # lascia almeno 50 chars di testo reale
            return testo[:idx].strip()
    return testo


def _extract_narrativa_from_msg(testo):
    """
    Estrae il blocco narrativo da un messaggio del facilitatore.
    Richiede che 'In questo scenario' compaia come inizio di paragrafo.
    """
    match = _NARRATIVA_START.search(testo)
    if not match:
        return None

    start = match.start()

    # Verifica che sia inizio di paragrafo (preceduto da newline o inizio testo)
    precedente = testo[:start]
    if precedente and not re.search(r"\n\s*$", precedente):
        return None

    testo_da = testo[start:]

    # Taglia al successivo segnale di cambio argomento
    stop = re.search(
        r"\n\n|\nOra\b|\nPerfetto\b|\nPassiamo\b|\nTi propongo\b|\nHai già\b"
        r"|\nArriviamo\b|\nAbbiamo\b|\nPrima di\b",
        testo_da,
    )
    if stop and stop.start() > 50:
        testo_da = testo_da[: stop.start()]

    narrativa = testo_da.strip()
    if len(narrativa) < 100:
        return None
    return narrativa


# ── Estrazione titolo ─────────────────────────────────────────────────────────

# Solo virgolette tipografiche o doppie (NO apostrofi — confondono l'italiano)
_TITOLO_QUOTED = re.compile(r'["\u201c\u00ab]([^"\u201d\u00bb\n]{5,100})["\u201d\u00bb]')
_OPZIONI_NUMBERED = re.compile(
    r'[Ll]a (prima|seconda|terza)\s+[eèé]\s+[""«]([^""»\n]{3,100})[""»]'
)


def _estrai_opzioni_titolo(testo):
    """Estrae le tre opzioni di titolo proposte dal facilitatore."""
    opzioni = []
    for m in _OPZIONI_NUMBERED.finditer(testo):
        opzioni.append((m.group(1).lower(), m.group(2).strip()))
    # Ordina: prima, seconda, terza
    ordine = {"prima": 1, "seconda": 2, "terza": 3}
    opzioni.sort(key=lambda x: ordine.get(x[0], 9))
    return [o[1] for o in opzioni]


def _titolo_da_conferma_facilitatore(testo):
    """
    Estrae il titolo confermato dal facilitatore ('Titolo' — mi piace...).
    NON usato su messaggi con proposte multiple (La prima è / La seconda è).
    """
    # Se il messaggio contiene proposte numerate, non estrarre (è una lista di opzioni)
    if _OPZIONI_NUMBERED.search(testo):
        return None
    # Rimuovi la parte JSON se presente (contenuto spazzatura dell'agente)
    clean = testo
    json_idx = testo.find('"testo"')
    if json_idx > 0:
        clean = testo[:json_idx]
    for m in _TITOLO_QUOTED.finditer(clean):
        candidato = m.group(1).strip()
        # Almeno 8 caratteri (evita JSON keys come "testo", "titolo")
        if 8 <= len(candidato) <= 80 and "?" not in candidato and ":" not in candidato:
            return candidato
    return None


# ── Estrazione minacce/opportunita ────────────────────────────────────────────

def _split_voci(testo):
    """Divide un testo in voci distinte."""
    # Lista numerata
    if re.search(r"^\d+[.\)]\s", testo, re.MULTILINE):
        voci = re.split(r"\n?\d+[.\)]\s+", testo)
        return [v.strip() for v in voci if len(v.strip()) > 10]
    # Lista puntata
    if re.search(r"^[-•*]\s", testo, re.MULTILINE):
        voci = re.split(r"\n[-•*]\s+", testo)
        return [v.strip() for v in voci if len(v.strip()) > 10]
    t = testo.strip()
    return [t] if len(t) > 15 else []


# ── Macchina a stati principale ───────────────────────────────────────────────

def estrai_dati_scenario(messaggi, scenario_esistente):
    narrativa = scenario_esistente.get("narrativa")
    titolo = scenario_esistente.get("titolo")
    minacce = list(scenario_esistente.get("minacce") or [])
    opportunita = list(scenario_esistente.get("opportunita") or [])

    # Parte sempre da key_points indipendentemente dai dati già presenti nel DB.
    # Il flag "non sovrascrivere" è gestito in fase di output (genera_sql_update),
    # così la macchina a stati trova i punti giusti della conversazione sempre.
    fase = None  # key_points

    # Buffer per l'ultima narrativa scritta dal facilitatore (usiamo l'ultima versione)
    ultima_narrativa_candidata = None

    for i, m in enumerate(messaggi):
        ruolo = m.get("ruolo")
        testo = m.get("contenuto", "").strip()

        if ruolo == "assistant":
            testo = _clean_msg(testo)  # rimuovi JSON grezzo dalla coda

            if fase is None:
                # Siamo in key_points: cerca il segnale narrativa
                if _NARRATIVA_SIGNAL.search(testo):
                    fase = "narrativa_wait"
                    nar = _extract_narrativa_from_msg(testo)
                    if nar:
                        ultima_narrativa_candidata = nar

            elif fase == "narrativa_wait":
                # Aggiorna la narrativa candidata se il facilitatore la riscrive
                nar = _extract_narrativa_from_msg(testo)
                if nar:
                    ultima_narrativa_candidata = nar
                # Passa al titolo se il facilitatore chiede direttamente
                if _TITOLO_SIGNAL.search(testo):
                    if ultima_narrativa_candidata and not narrativa:
                        narrativa = ultima_narrativa_candidata
                    fase = "titolo"
                    t = _titolo_da_conferma_facilitatore(testo)
                    if t:
                        titolo = t

            elif fase == "titolo":
                # Il facilitatore conferma il titolo
                if not titolo:
                    t = _titolo_da_conferma_facilitatore(testo)
                    if t:
                        titolo = t
                # Passa alle minacce
                if titolo and _MINACCE_SIGNAL.search(testo):
                    fase = "minacce"
                elif titolo and _OPPORT_SIGNAL.search(testo):
                    fase = "opportunita"

            elif fase == "minacce":
                if _OPPORT_PHASE_START.search(testo):
                    fase = "opportunita"
                elif _CONCLUSO_SIGNAL.search(testo):
                    fase = "concluso"

            elif fase == "opportunita":
                if _CONCLUSO_SIGNAL.search(testo):
                    fase = "concluso"

        elif ruolo == "user":

            # ── GESTIONE TITOLO: prima dello skip check ──────────────────────
            if fase == "titolo" and not titolo:
                # 1. Selezione numerata ("la seconda")
                scelta_m = _OPZIONE_SELECTION.match(testo)
                if scelta_m:
                    nome_opzione = scelta_m.group(2).lower()
                    n = {"prima": 1, "primo": 1, "seconda": 2, "secondo": 2,
                         "terza": 3, "terzo": 3}.get(nome_opzione, 0)
                    if n:
                        for j in range(i - 1, -1, -1):
                            if messaggi[j].get("ruolo") == "assistant":
                                opts = _estrai_opzioni_titolo(messaggi[j].get("contenuto", ""))
                                if len(opts) >= n:
                                    titolo = opts[n - 1]
                                break
                    fase = "minacce" if titolo else "titolo"
                    continue

                # 2. Richiesta di suggerimenti ("Suggeriscimi delle opzioni")
                if _TITOLO_REQUEST.match(testo) or re.search(r"\?$", testo):
                    continue  # aspetta la risposta del facilitatore

                # 3. Citazione diretta dell'utente ("Metterei il terzo al plurale 'Titolo'")
                mods = re.search(
                    r"(metterei|prenderei|sceglierei|preferisco|direi).*"
                    r"(prim[ao]|second[ao]|terz[ao])",
                    testo, re.IGNORECASE
                )
                if mods:
                    nome_opzione = mods.group(2).lower()
                    n = {"prima": 1, "primo": 1, "seconda": 2, "secondo": 2,
                         "terza": 3, "terzo": 3}.get(nome_opzione, 0)
                    # Cerca un titolo quotato nella stessa risposta
                    q = _TITOLO_QUOTED.search(testo)
                    if q:
                        titolo = q.group(1).strip()
                    elif n:
                        for j in range(i - 1, -1, -1):
                            if messaggi[j].get("ruolo") == "assistant":
                                opts = _estrai_opzioni_titolo(messaggi[j].get("contenuto", ""))
                                if len(opts) >= n:
                                    titolo = opts[n - 1]
                                break
                    fase = "minacce" if titolo else "titolo"
                    continue

                # 4. Proposta diretta (testo breve, niente domande)
                if not _is_skip(testo) and "?" not in testo and not _TITOLO_REQUEST.match(testo):
                    clean = re.sub(
                        r"^(metterei|propongo|direi|scelgo|preferisco|vorrei|"
                        r"opterei per|user[oò]|prenderei|andrei con|mi piace)\s+",
                        "", testo, flags=re.IGNORECASE,
                    ).strip().strip('"\'«»\u201c\u201d')
                    if 4 < len(clean) <= 120:
                        titolo = clean
                    fase = "minacce" if titolo else "titolo"
                    continue

            # ── SKIP UTENTE ──────────────────────────────────────────────────
            # Le negazioni ("non credo", "non saprei") NON avanzano la fase:
            # segnalano solo assenza di contributo per la fase corrente.
            if _is_negation(testo):
                continue  # no data, no phase change

            if _is_skip(testo):
                if fase == "narrativa_wait":
                    if ultima_narrativa_candidata and not narrativa:
                        narrativa = ultima_narrativa_candidata
                    if narrativa:
                        fase = "titolo"
                elif fase == "titolo" and titolo:
                    fase = "minacce"
                elif fase == "minacce":
                    fase = "opportunita"
                elif fase == "opportunita":
                    fase = "concluso"
                continue

            # ── RACCOLTA MINACCE / OPPORTUNITA ──────────────────────────────
            if fase == "minacce" and len(testo) > 15:
                voci = _split_voci(testo)
                for v in voci:
                    if v not in minacce:
                        minacce.append(v)

            elif fase == "opportunita" and len(testo) > 15:
                voci = _split_voci(testo)
                for v in voci:
                    if v not in opportunita:
                        opportunita.append(v)

    # Consolida narrativa se non ancora salvata
    if not narrativa and ultima_narrativa_candidata:
        narrativa = ultima_narrativa_candidata

    return {
        "narrativa": narrativa,
        "titolo": titolo,
        "minacce": minacce,
        "opportunita": opportunita,
    }


# ── SQL ───────────────────────────────────────────────────────────────────────

def genera_sql_update(scenario_id, dati_nuovi, dati_esistenti):
    sets = []
    if dati_nuovi.get("narrativa") and not dati_esistenti.get("narrativa"):
        nar = dati_nuovi["narrativa"].replace("'", "''")
        sets.append(f"narrativa = '{nar}'")
    if dati_nuovi.get("titolo") and not dati_esistenti.get("titolo"):
        tit = dati_nuovi["titolo"].replace("'", "''")
        sets.append(f"titolo = '{tit}'")
    if dati_nuovi.get("minacce") and not dati_esistenti.get("minacce"):
        mj = json.dumps(dati_nuovi["minacce"], ensure_ascii=False).replace("'", "''")
        sets.append(f"minacce = '{mj}'")
    if dati_nuovi.get("opportunita") and not dati_esistenti.get("opportunita"):
        oj = json.dumps(dati_nuovi["opportunita"], ensure_ascii=False).replace("'", "''")
        sets.append(f"opportunita = '{oj}'")
    if not sets:
        return None
    return f"UPDATE scenari SET {', '.join(sets)} WHERE id = {scenario_id};"


def applica_update(scenario_id, dati_nuovi, dati_esistenti, db_url):
    import psycopg2
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    fields = {}
    if dati_nuovi.get("narrativa") and not dati_esistenti.get("narrativa"):
        fields["narrativa"] = dati_nuovi["narrativa"]
    if dati_nuovi.get("titolo") and not dati_esistenti.get("titolo"):
        fields["titolo"] = dati_nuovi["titolo"]
    if dati_nuovi.get("minacce") and not dati_esistenti.get("minacce"):
        fields["minacce"] = json.dumps(dati_nuovi["minacce"], ensure_ascii=False)
    if dati_nuovi.get("opportunita") and not dati_esistenti.get("opportunita"):
        fields["opportunita"] = json.dumps(dati_nuovi["opportunita"], ensure_ascii=False)
    if not fields:
        conn.close()
        return False
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [scenario_id]
    cur.execute(f"UPDATE scenari SET {set_clause} WHERE id = %s", values)
    conn.close()
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import os
    sys.stdout.reconfigure(encoding="utf-8")

    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    json_path = args[0]
    apply_mode = "--apply" in args

    db_url = os.environ.get("DATABASE_URL", "")
    if apply_mode and not db_url:
        print("ERRORE: --apply richiede DATABASE_URL impostata.")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sessione = data.get("sessione", {})
    scenari = data.get("scenari_individuali", [])

    print(f"\n=== RECUPERO SCENARI - Sessione {sessione.get('codice')} ===")
    print(f"Domanda: {sessione.get('domanda_ricerca')}\n")

    sql_list = []

    for s in scenari:
        sid = s["id"]
        pid = s.get("nome_partecipante", s.get("partecipante_id", "?"))
        messaggi = s.get("messaggi") or []

        mancanti = [
            c for c in ("narrativa", "titolo", "minacce", "opportunita") if not s.get(c)
        ]

        if not mancanti or len(messaggi) <= 1:
            print(f"Scenario {sid} (pid={pid}): OK o nessun contenuto - salto.")
            continue

        print(f"\nScenario {sid} (pid={pid}) | quadrante={s.get('quadrante')} | mancanti: {mancanti}")

        estratti = estrai_dati_scenario(messaggi, s)

        for campo in ("narrativa", "titolo", "minacce", "opportunita"):
            if s.get(campo):
                continue  # gia' presente
            valore = estratti.get(campo)
            if valore:
                preview = str(valore)[:160] + ("..." if len(str(valore)) > 160 else "")
                print(f"  {campo}: {preview}")
            else:
                print(f"  {campo}: non trovato")

        sql = genera_sql_update(sid, estratti, s)
        if sql:
            sql_list.append(sql)
            print(f"  -> SQL generato")
        else:
            print(f"  -> Nessun dato nuovo estraibile")

        if apply_mode:
            ok = applica_update(sid, estratti, s, db_url)
            print(f"  -> {'Aggiornato nel DB' if ok else 'Nessun aggiornamento'}")

    if sql_list:
        out_path = Path(json_path).with_suffix("").as_posix() + "_recovery.sql"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"-- Recovery SQL - Sessione {sessione.get('codice')}\n\n")
            for sql in sql_list:
                f.write(sql + "\n")

        print(f"\n{'='*60}")
        print("SQL DA ESEGUIRE:")
        print("=" * 60)
        for sql in sql_list:
            print(sql)
        print("=" * 60)
        print(f"\nSalvato in: {out_path}")
    else:
        print("\nNessun dato da recuperare.")


if __name__ == "__main__":
    main()
