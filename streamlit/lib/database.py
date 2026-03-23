import sqlite3
import json
import random
import string
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "foresight.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.execute("ALTER TABLE scenario ADD COLUMN partecipante_id INTEGER REFERENCES partecipante(id)")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE scenario ADD COLUMN locked_by_partecipante_id INTEGER REFERENCES partecipante(id)")
        conn.execute("ALTER TABLE scenario ADD COLUMN titolo_finale TEXT")
        conn.execute("ALTER TABLE scenario ADD COLUMN narrativa_finale TEXT")
        conn.execute("ALTER TABLE scenario ADD COLUMN minacce_finale TEXT DEFAULT '[]'")
        conn.execute("ALTER TABLE scenario ADD COLUMN opportunita_finale TEXT DEFAULT '[]'")
    except Exception:
        pass
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessione (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice TEXT UNIQUE,
            domanda_ricerca TEXT NOT NULL,
            frame_temporale TEXT NOT NULL,
            key_points TEXT NOT NULL DEFAULT '[]',
            stato TEXT NOT NULL DEFAULT 'setup',
            driver1_nome TEXT,
            driver1_pos TEXT,
            driver1_neg TEXT,
            driver2_nome TEXT,
            driver2_pos TEXT,
            driver2_neg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS modello (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            domanda_ricerca TEXT NOT NULL,
            frame_temporale TEXT NOT NULL,
            key_points TEXT NOT NULL DEFAULT '[]',
            fenomeni_raw TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fenomeno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessione_id INTEGER NOT NULL,
            testo TEXT NOT NULL,
            descrizione TEXT DEFAULT '',
            priorita INTEGER DEFAULT 999,
            FOREIGN KEY (sessione_id) REFERENCES sessione(id)
        );

        CREATE TABLE IF NOT EXISTS partecipante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessione_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            gruppo_numero INTEGER,
            votato INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (sessione_id) REFERENCES sessione(id)
        );

        CREATE TABLE IF NOT EXISTS voto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partecipante_id INTEGER NOT NULL,
            fenomeno_id INTEGER NOT NULL,
            posizione INTEGER NOT NULL,
            UNIQUE(partecipante_id, fenomeno_id),
            FOREIGN KEY (partecipante_id) REFERENCES partecipante(id),
            FOREIGN KEY (fenomeno_id) REFERENCES fenomeno(id)
        );

        CREATE TABLE IF NOT EXISTS scenario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessione_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            quadrante TEXT NOT NULL,
            titolo TEXT,
            narrativa TEXT,
            minacce TEXT DEFAULT '[]',
            opportunita TEXT DEFAULT '[]',
            key_points_data TEXT DEFAULT '{}',
            step_corrente TEXT DEFAULT 'intro',
            partecipante_id INTEGER,
            FOREIGN KEY (sessione_id) REFERENCES sessione(id),
            FOREIGN KEY (partecipante_id) REFERENCES partecipante(id)
        );

        CREATE TABLE IF NOT EXISTS messaggio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            ruolo TEXT NOT NULL,
            contenuto TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scenario_id) REFERENCES scenario(id)
        );
    """)
    conn.commit()
    conn.close()


# ── Utilità ───────────────────────────────────────────────

def genera_codice(n=6):
    return "".join(random.choices(string.ascii_uppercase, k=n))


# ── Sessione ──────────────────────────────────────────────

def crea_sessione(domanda, frame, key_points, fenomeni):
    conn = get_conn()
    # Genera codice univoco
    for _ in range(20):
        codice = genera_codice(6)
        existing = conn.execute("SELECT id FROM sessione WHERE codice = ?", (codice,)).fetchone()
        if not existing:
            break
    cur = conn.execute(
        "INSERT INTO sessione (codice, domanda_ricerca, frame_temporale, key_points) VALUES (?, ?, ?, ?)",
        (codice, domanda, frame, json.dumps(key_points, ensure_ascii=False))
    )
    sid = cur.lastrowid
    for i, f in enumerate(fenomeni):
        conn.execute(
            "INSERT INTO fenomeno (sessione_id, testo, descrizione, priorita) VALUES (?, ?, ?, ?)",
            (sid, f["testo"], f.get("descrizione", ""), i)
        )
    conn.commit()
    conn.close()
    return sid


def _parse_sessione(row):
    if not row:
        return None
    d = dict(row)
    try:
        d["key_points"] = json.loads(d["key_points"])
    except Exception:
        d["key_points"] = []
    return d


def get_sessione_by_id(sid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessione WHERE id = ?", (sid,)).fetchone()
    conn.close()
    return _parse_sessione(row)


def get_sessione_by_codice(codice):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessione WHERE codice = ?", (codice.upper(),)).fetchone()
    conn.close()
    return _parse_sessione(row)


# Alias per compatibilità
def get_sessione(sid):
    return get_sessione_by_id(sid)


def aggiorna_sessione(sid, **kwargs):
    if not kwargs:
        return
    if "key_points" in kwargs and isinstance(kwargs["key_points"], list):
        kwargs["key_points"] = json.dumps(kwargs["key_points"], ensure_ascii=False)
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [sid]
    conn = get_conn()
    conn.execute(f"UPDATE sessione SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()


def lista_sessioni():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, codice, domanda_ricerca, frame_temporale, stato, created_at FROM sessione ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Fenomeni ──────────────────────────────────────────────

def get_fenomeni(sessione_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM fenomeno WHERE sessione_id = ? ORDER BY priorita ASC",
        (sessione_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def aggiungi_fenomeno(sessione_id, testo, descrizione=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO fenomeno (sessione_id, testo, descrizione, priorita) VALUES (?, ?, ?, ?)",
        (sessione_id, testo, descrizione, 999)
    )
    conn.commit()
    conn.close()


def elimina_fenomeno(fid):
    conn = get_conn()
    conn.execute("DELETE FROM fenomeno WHERE id = ?", (fid,))
    conn.commit()
    conn.close()


def elimina_sessione(sessione_id):
    """Elimina una sessione e tutti i dati collegati (cascata manuale)."""
    conn = get_conn()
    conn.execute("""
        DELETE FROM voto WHERE partecipante_id IN (
            SELECT id FROM partecipante WHERE sessione_id = ?
        )
    """, (sessione_id,))
    conn.execute("""
        DELETE FROM messaggio WHERE scenario_id IN (
            SELECT id FROM scenario WHERE sessione_id = ?
        )
    """, (sessione_id,))
    conn.execute("DELETE FROM scenario WHERE sessione_id = ?", (sessione_id,))
    conn.execute("DELETE FROM partecipante WHERE sessione_id = ?", (sessione_id,))
    conn.execute("DELETE FROM fenomeno WHERE sessione_id = ?", (sessione_id,))
    conn.execute("DELETE FROM sessione WHERE id = ?", (sessione_id,))
    conn.commit()
    conn.close()


def aggiorna_priorita_fenomeni(sessione_id, ordine_ids):
    conn = get_conn()
    for i, fid in enumerate(ordine_ids):
        conn.execute(
            "UPDATE fenomeno SET priorita = ? WHERE id = ? AND sessione_id = ?",
            (i, fid, sessione_id)
        )
    conn.commit()
    conn.close()


# ── Partecipanti ──────────────────────────────────────────

def registra_partecipante(sessione_id, nome):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO partecipante (sessione_id, nome) VALUES (?, ?)",
        (sessione_id, nome)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": pid, "nome": nome, "sessione_id": sessione_id}


def get_partecipanti(sessione_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM partecipante WHERE sessione_id = ? ORDER BY id ASC",
        (sessione_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def aggiorna_partecipante(pid, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [pid]
    conn = get_conn()
    conn.execute(f"UPDATE partecipante SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()


# ── Voti ──────────────────────────────────────────────────

def salva_voti(partecipante_id, ranking):
    """ranking è lista di {fenomeno_id, posizione}"""
    conn = get_conn()
    conn.execute("DELETE FROM voto WHERE partecipante_id = ?", (partecipante_id,))
    for v in ranking:
        conn.execute(
            "INSERT OR REPLACE INTO voto (partecipante_id, fenomeno_id, posizione) VALUES (?, ?, ?)",
            (partecipante_id, v["fenomeno_id"], v["posizione"])
        )
    conn.execute("UPDATE partecipante SET votato = 1 WHERE id = ?", (partecipante_id,))
    conn.commit()
    conn.close()


def get_voti_aggregati(sessione_id):
    """Ritorna lista {fenomeno_id, media_posizione, conteggio} ordinata per media ASC"""
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT v.fenomeno_id, AVG(v.posizione) as media_posizione, COUNT(v.id) as conteggio
        FROM voto v
        JOIN fenomeno f ON f.id = v.fenomeno_id
        WHERE f.sessione_id = ?
        GROUP BY v.fenomeno_id
        ORDER BY media_posizione ASC
        """,
        (sessione_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Scenari ───────────────────────────────────────────────

def crea_scenari(sessione_id):
    quadranti = [(1, "++"), (2, "+-"), (3, "-+"), (4, "--")]
    quad_map = {1: "++", 2: "+-", 3: "-+", 4: "--"}
    conn = get_conn()
    conn.execute("DELETE FROM scenario WHERE sessione_id = ?", (sessione_id,))
    
    # 1. Crea scenari di gruppo
    for n, q in quadranti:
        conn.execute(
            "INSERT INTO scenario (sessione_id, numero, quadrante) VALUES (?, ?, ?)",
            (sessione_id, n, q)
        )
        
    # 2. Crea scenari individuali
    partecipanti = conn.execute("SELECT id, gruppo_numero FROM partecipante WHERE sessione_id = ? AND gruppo_numero IS NOT NULL", (sessione_id,)).fetchall()
    for p in partecipanti:
        pid = p["id"]
        gnum = p["gruppo_numero"]
        if gnum in quad_map:
            q = quad_map[gnum]
            conn.execute(
                "INSERT INTO scenario (sessione_id, numero, quadrante, partecipante_id) VALUES (?, ?, ?, ?)",
                (sessione_id, gnum, q, pid)
            )

    conn.commit()
    conn.close()


def _parse_scenario(row):
    if not row:
        return None
    d = dict(row)
    for field in ["minacce", "opportunita", "minacce_finale", "opportunita_finale"]:
        try:
            val = d.get(field)
            d[field] = json.loads(val) if val else []
        except Exception:
            d[field] = []
            
    try:
        d["key_points_data"] = json.loads(d["key_points_data"] or "{}")
    except Exception:
        d["key_points_data"] = {}
    return d


def get_scenari(sessione_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id IS NULL ORDER BY numero",
        (sessione_id,)
    ).fetchall()
    conn.close()
    return [_parse_scenario(r) for r in rows]

def get_scenari_individuali(sessione_id, gruppo_numero=None):
    conn = get_conn()
    if gruppo_numero:
        rows = conn.execute(
            "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id IS NOT NULL AND numero = ? ORDER BY id",
            (sessione_id, gruppo_numero)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id IS NOT NULL ORDER BY numero",
            (sessione_id,)
        ).fetchall()
    conn.close()
    return [_parse_scenario(r) for r in rows]

def get_scenario_individuale(sessione_id, partecipante_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id = ?",
        (sessione_id, partecipante_id)
    ).fetchone()
    conn.close()
    return _parse_scenario(row)


def get_scenario(scenario_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM scenario WHERE id = ?", (scenario_id,)).fetchone()
    conn.close()
    return _parse_scenario(row)


def aggiorna_scenario(scenario_id, **kwargs):
    if not kwargs:
        return
    for k in ["minacce", "opportunita", "key_points_data", "minacce_finale", "opportunita_finale"]:
        if k in kwargs and not isinstance(kwargs[k], str):
            kwargs[k] = json.dumps(kwargs[k], ensure_ascii=False)
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [scenario_id]
    conn = get_conn()
    conn.execute(f"UPDATE scenario SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()


# ── Messaggi ──────────────────────────────────────────────

def get_messaggi(scenario_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messaggio WHERE scenario_id = ? ORDER BY created_at ASC",
        (scenario_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def aggiungi_messaggio(scenario_id, ruolo, contenuto):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messaggio (scenario_id, ruolo, contenuto) VALUES (?, ?, ?)",
        (scenario_id, ruolo, contenuto)
    )
    conn.commit()
    conn.close()

# ── Modelli (Templates) ───────────────────────────────────

def crea_modello(nome, domanda_ricerca, frame_temporale, key_points, fenomeni_raw):
    conn = get_conn()
    conn.execute(
        "INSERT INTO modello (nome, domanda_ricerca, frame_temporale, key_points, fenomeni_raw) VALUES (?, ?, ?, ?, ?)",
        (nome, domanda_ricerca, frame_temporale, json.dumps(key_points, ensure_ascii=False), fenomeni_raw)
    )
    conn.commit()
    conn.close()

def get_modelli():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM modello ORDER BY created_at DESC").fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        try:
            d["key_points"] = json.loads(d["key_points"])
        except Exception:
            d["key_points"] = []
        res.append(d)
    return res

def get_modello_by_id(modello_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM modello WHERE id = ?", (modello_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["key_points"] = json.loads(d["key_points"])
    except Exception:
        d["key_points"] = []
    return d

def elimina_modello(modello_id):
    conn = get_conn()
    conn.execute("DELETE FROM modello WHERE id = ?", (modello_id,))
    conn.commit()
    conn.close()
