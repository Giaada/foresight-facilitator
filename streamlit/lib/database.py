import sqlite3
import json
import random
import string
import os
from pathlib import Path
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "foresight.db"

def get_db_url():
    try:
        url = st.secrets.get("DATABASE_URL")
        if url: return url
    except Exception:
        pass
    return os.environ.get("DATABASE_URL")

DB_URL = get_db_url()
IS_POSTGRES = bool(DB_URL and DB_URL.startswith("postgres"))

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

def get_conn():
    if IS_POSTGRES:
        url = DB_URL
        if "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url = url + sep + "sslmode=require"
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        conn.set_client_encoding('UTF8')
        conn.autocommit = True
        return conn
    else:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def exec_query(query, params=(), fetch=None, return_id=False):
    conn = get_conn()
    try:
        if IS_POSTGRES:
            q = query.replace("?", "%s")
            q = q.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

            if q.startswith("INSERT OR REPLACE INTO voto"):
                q = q.replace("INSERT OR REPLACE INTO voto", "INSERT INTO voto")
                q += " ON CONFLICT (partecipante_id, fenomeno_id) DO UPDATE SET posizione = EXCLUDED.posizione"

            if return_id:
                q += " RETURNING id"

            cur = conn.cursor()
            cur.execute(q, params)

            if return_id:
                res = cur.fetchone()
                val = res['id'] if res else None
                conn.close()
                return val

            if fetch == 'all':
                res = cur.fetchall()
                conn.close()
                return [dict(r) for r in res]
            elif fetch == 'one':
                res = cur.fetchone()
                conn.close()
                return dict(res) if res else None

            conn.close()
            return None
        else:
            cur = conn.execute(query, params)

            if fetch == 'all':
                res = cur.fetchall()
                conn.commit()
                conn.close()
                return [dict(r) for r in res]
            elif fetch == 'one':
                res = cur.fetchone()
                conn.commit()
                conn.close()
                return dict(res) if res else None

            if return_id:
                val = cur.lastrowid
                conn.commit()
                conn.close()
                return val

            conn.commit()
            conn.close()
    except Exception as e:
        conn.close()
        raise e

def executescript(script):
    if IS_POSTGRES:
        script = script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        conn = get_conn()
        try:
            cur = conn.cursor()
            for stmt in [s.strip() for s in script.split(';') if s.strip()]:
                try:
                    cur.execute(stmt)
                except Exception:
                    pass
        finally:
            conn.close()
    else:
        conn = get_conn()
        try:
            conn.executescript(script)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()


def init_db():
    try:
        exec_query("ALTER TABLE scenario ADD COLUMN partecipante_id INTEGER REFERENCES partecipante(id)")
    except Exception:
        pass
    try:
        exec_query("ALTER TABLE scenario ADD COLUMN locked_by_partecipante_id INTEGER REFERENCES partecipante(id)")
        exec_query("ALTER TABLE scenario ADD COLUMN titolo_finale TEXT")
        exec_query("ALTER TABLE scenario ADD COLUMN narrativa_finale TEXT")
        exec_query("ALTER TABLE scenario ADD COLUMN minacce_finale TEXT DEFAULT '[]'")
        exec_query("ALTER TABLE scenario ADD COLUMN opportunita_finale TEXT DEFAULT '[]'")
    except Exception:
        pass
    script = """
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
            locked_by_partecipante_id INTEGER,
            titolo_finale TEXT,
            narrativa_finale TEXT,
            minacce_finale TEXT DEFAULT '[]',
            opportunita_finale TEXT DEFAULT '[]',
            FOREIGN KEY (sessione_id) REFERENCES sessione(id),
            FOREIGN KEY (partecipante_id) REFERENCES partecipante(id),
            FOREIGN KEY (locked_by_partecipante_id) REFERENCES partecipante(id)
        );

        CREATE TABLE IF NOT EXISTS messaggio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            ruolo TEXT NOT NULL,
            contenuto TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scenario_id) REFERENCES scenario(id)
        );
    """
    executescript(script)


# ── Utilità ───────────────────────────────────────────────

def genera_codice(n=6):
    return "".join(random.choices(string.ascii_uppercase, k=n))

# ── Sessione ──────────────────────────────────────────────

def crea_sessione(domanda, frame, key_points, fenomeni):
    # Genera codice univoco
    for _ in range(20):
        codice = genera_codice(6)
        existing = exec_query("SELECT id FROM sessione WHERE codice = ?", (codice,), fetch='one')
        if not existing:
            break

    sid = exec_query(
        "INSERT INTO sessione (codice, domanda_ricerca, frame_temporale, key_points) VALUES (?, ?, ?, ?)",
        (codice, domanda, frame, json.dumps(key_points, ensure_ascii=False)),
        return_id=True
    )

    for i, f in enumerate(fenomeni):
        exec_query(
            "INSERT INTO fenomeno (sessione_id, testo, descrizione, priorita) VALUES (?, ?, ?, ?)",
            (sid, f["testo"], f.get("descrizione", ""), i)
        )
    return sid

def _parse_sessione(d):
    if not d:
        return None
    try:
        d["key_points"] = json.loads(d["key_points"])
    except Exception:
        d["key_points"] = []
    return d

@st.cache_data(ttl=10)
def get_sessione_by_id(sid):
    return _parse_sessione(exec_query("SELECT * FROM sessione WHERE id = ?", (sid,), fetch='one'))

def get_sessione_by_codice(codice):
    return _parse_sessione(exec_query("SELECT * FROM sessione WHERE codice = ?", (codice.upper(),), fetch='one'))

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
    exec_query(f"UPDATE sessione SET {fields} WHERE id = ?", values)
    get_sessione_by_id.clear()

def lista_sessioni():
    return exec_query("SELECT id, codice, domanda_ricerca, frame_temporale, stato, created_at FROM sessione ORDER BY created_at DESC", fetch='all')

# ── Fenomeni ──────────────────────────────────────────────

@st.cache_data(ttl=10)
def get_fenomeni(sessione_id):
    return exec_query("SELECT * FROM fenomeno WHERE sessione_id = ? ORDER BY priorita ASC", (sessione_id,), fetch='all')

def aggiungi_fenomeno(sessione_id, testo, descrizione=""):
    exec_query(
        "INSERT INTO fenomeno (sessione_id, testo, descrizione, priorita) VALUES (?, ?, ?, ?)",
        (sessione_id, testo, descrizione, 999)
    )
    get_fenomeni.clear()
    get_tutti_fenomeni_unici.clear()

def elimina_fenomeno(fid):
    exec_query("DELETE FROM fenomeno WHERE id = ?", (fid,))
    get_fenomeni.clear()
    get_tutti_fenomeni_unici.clear()

def aggiorna_fenomeno(fid, testo, descrizione=""):
    exec_query(
        "UPDATE fenomeno SET testo = ?, descrizione = ? WHERE id = ?",
        (testo, descrizione, fid)
    )
    get_fenomeni.clear()
    get_tutti_fenomeni_unici.clear()

def elimina_sessione(sessione_id):
    exec_query("DELETE FROM voto WHERE partecipante_id IN (SELECT id FROM partecipante WHERE sessione_id = ?)", (sessione_id,))
    exec_query("DELETE FROM messaggio WHERE scenario_id IN (SELECT id FROM scenario WHERE sessione_id = ?)", (sessione_id,))
    exec_query("DELETE FROM scenario WHERE sessione_id = ?", (sessione_id,))
    exec_query("DELETE FROM partecipante WHERE sessione_id = ?", (sessione_id,))
    exec_query("DELETE FROM fenomeno WHERE sessione_id = ?", (sessione_id,))
    exec_query("DELETE FROM sessione WHERE id = ?", (sessione_id,))
    get_sessione_by_id.clear()
    get_fenomeni.clear()
    get_partecipanti.clear()
    get_voti_aggregati.clear()
    get_scenari.clear()
    get_scenari_individuali.clear()
    get_scenario_individuale.clear()
    get_scenario.clear()
    get_tutti_fenomeni_unici.clear()

def aggiorna_priorita_fenomeni(sessione_id, ordine_ids):
    for i, fid in enumerate(ordine_ids):
        exec_query(
            "UPDATE fenomeno SET priorita = ? WHERE id = ? AND sessione_id = ?",
            (i, fid, sessione_id)
        )
    get_fenomeni.clear()

# ── Partecipanti ──────────────────────────────────────────

def registra_partecipante(sessione_id, nome):
    # Se esiste già un partecipante con lo stesso nome nella sessione, ricollegalo
    esistente = exec_query(
        "SELECT * FROM partecipante WHERE sessione_id = ? AND nome = ?",
        (sessione_id, nome),
        fetch='one'
    )
    if esistente:
        return {"id": esistente["id"], "nome": esistente["nome"], "sessione_id": sessione_id}
    pid = exec_query(
        "INSERT INTO partecipante (sessione_id, nome) VALUES (?, ?)",
        (sessione_id, nome),
        return_id=True
    )
    get_partecipanti.clear()
    return {"id": pid, "nome": nome, "sessione_id": sessione_id}

def get_partecipante_by_id(pid):
    row = exec_query("SELECT * FROM partecipante WHERE id = ?", (pid,), fetch='one')
    if row:
        return {"id": row["id"], "nome": row["nome"], "sessione_id": row["sessione_id"]}
    return None

@st.cache_data(ttl=15)
def get_partecipanti(sessione_id):
    return exec_query("SELECT * FROM partecipante WHERE sessione_id = ? ORDER BY id ASC", (sessione_id,), fetch='all')

def aggiorna_partecipante(pid, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [pid]
    exec_query(f"UPDATE partecipante SET {fields} WHERE id = ?", values)
    get_partecipanti.clear()
    get_scenario_individuale.clear()

# ── Voti ──────────────────────────────────────────────────

def salva_voti(partecipante_id, ranking):
    exec_query("DELETE FROM voto WHERE partecipante_id = ?", (partecipante_id,))
    for v in ranking:
        exec_query(
            "INSERT OR REPLACE INTO voto (partecipante_id, fenomeno_id, posizione) VALUES (?, ?, ?)",
            (partecipante_id, v["fenomeno_id"], v["posizione"])
        )
    exec_query("UPDATE partecipante SET votato = 1 WHERE id = ?", (partecipante_id,))
    get_voti_aggregati.clear()
    get_partecipanti.clear()

@st.cache_data(ttl=15)
def get_voti_aggregati(sessione_id):
    return exec_query(
        """
        SELECT v.fenomeno_id, AVG(v.posizione) as media_posizione, COUNT(v.id) as conteggio
        FROM voto v
        JOIN fenomeno f ON f.id = v.fenomeno_id
        WHERE f.sessione_id = ?
        GROUP BY v.fenomeno_id
        ORDER BY media_posizione ASC
        """,
        (sessione_id,),
        fetch='all'
    )

# ── Scenari ───────────────────────────────────────────────

def crea_scenari(sessione_id):
    quadranti = [(1, "-+"), (2, "++"), (3, "+-"), (4, "--")]
    quad_map = {1: "-+", 2: "++", 3: "+-", 4: "--"}

    exec_query("DELETE FROM scenario WHERE sessione_id = ?", (sessione_id,))

    for n, q in quadranti:
        exec_query(
            "INSERT INTO scenario (sessione_id, numero, quadrante) VALUES (?, ?, ?)",
            (sessione_id, n, q)
        )

    partecipanti = exec_query("SELECT id, gruppo_numero FROM partecipante WHERE sessione_id = ? AND gruppo_numero IS NOT NULL", (sessione_id,), fetch='all')
    for p in partecipanti or []:
        pid = p["id"]
        gnum = p["gruppo_numero"]
        if gnum in quad_map:
            q = quad_map[gnum]
            exec_query(
                "INSERT INTO scenario (sessione_id, numero, quadrante, partecipante_id) VALUES (?, ?, ?, ?)",
                (sessione_id, gnum, q, pid)
            )
    get_scenari.clear()
    get_scenari_individuali.clear()
    get_scenario_individuale.clear()
    get_scenario.clear()

def aggiungi_partecipante_a_gruppo(sessione_id, partecipante_id, gruppo_numero):
    """Assegna un partecipante a un gruppo e crea il suo scenario individuale
    senza toccare gli scenari già esistenti degli altri partecipanti."""
    quad_map = {1: "-+", 2: "++", 3: "+-", 4: "--"}
    aggiorna_partecipante(partecipante_id, gruppo_numero=gruppo_numero)
    q = quad_map.get(gruppo_numero)
    if q:
        exec_query(
            "INSERT INTO scenario (sessione_id, numero, quadrante, partecipante_id) VALUES (?, ?, ?, ?)",
            (sessione_id, gruppo_numero, q, partecipante_id)
        )
    get_scenari_individuali.clear()
    get_scenario_individuale.clear()
    get_partecipanti.clear()

def _parse_scenario(d):
    if not d:
        return None
    for field in ["minacce", "opportunita", "minacce_finale", "opportunita_finale"]:
        try:
            val = d.get(field)
            parsed = json.loads(val) if val else []
            d[field] = parsed if isinstance(parsed, list) else []
        except Exception:
            d[field] = []

    try:
        d["key_points_data"] = json.loads(d["key_points_data"] or "{}")
    except Exception:
        d["key_points_data"] = {}
    return d

@st.cache_data(ttl=10)
def get_scenari(sessione_id):
    rows = exec_query("SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id IS NULL ORDER BY numero", (sessione_id,), fetch='all')
    return [_parse_scenario(r) for r in (rows or [])]

@st.cache_data(ttl=10)
def get_scenari_individuali(sessione_id, gruppo_numero=None):
    if gruppo_numero:
        rows = exec_query(
            "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id IS NOT NULL AND numero = ? ORDER BY id",
            (sessione_id, gruppo_numero),
            fetch='all'
        )
    else:
        rows = exec_query(
            "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id IS NOT NULL ORDER BY numero",
            (sessione_id,),
            fetch='all'
        )
    return [_parse_scenario(r) for r in (rows or [])]

@st.cache_data(ttl=10)
def get_scenario_individuale(sessione_id, partecipante_id):
    return _parse_scenario(exec_query(
        "SELECT * FROM scenario WHERE sessione_id = ? AND partecipante_id = ?",
        (sessione_id, partecipante_id),
        fetch='one'
    ))

@st.cache_data(ttl=5)
def get_scenario(scenario_id):
    return _parse_scenario(exec_query("SELECT * FROM scenario WHERE id = ?", (scenario_id,), fetch='one'))

def aggiorna_scenario(scenario_id, **kwargs):
    if not kwargs:
        return
    for k in ["minacce", "opportunita", "key_points_data", "minacce_finale", "opportunita_finale"]:
        if k in kwargs and not isinstance(kwargs[k], str):
            kwargs[k] = json.dumps(kwargs[k], ensure_ascii=False)
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [scenario_id]
    exec_query(f"UPDATE scenario SET {fields} WHERE id = ?", values)
    get_scenario.clear()
    get_scenari.clear()
    get_scenari_individuali.clear()
    get_scenario_individuale.clear()

# ── Messaggi ──────────────────────────────────────────────

def get_messaggi(scenario_id):
    return exec_query("SELECT * FROM messaggio WHERE scenario_id = ? ORDER BY created_at ASC", (scenario_id,), fetch='all')

def aggiungi_messaggio(scenario_id, ruolo, contenuto):
    exec_query(
        "INSERT INTO messaggio (scenario_id, ruolo, contenuto) VALUES (?, ?, ?)",
        (scenario_id, ruolo, contenuto)
    )

# ── Modelli (Templates) ───────────────────────────────────

def crea_modello(nome, domanda_ricerca, frame_temporale, key_points, fenomeni_raw):
    exec_query(
        "INSERT INTO modello (nome, domanda_ricerca, frame_temporale, key_points, fenomeni_raw) VALUES (?, ?, ?, ?, ?)",
        (nome, domanda_ricerca, frame_temporale, json.dumps(key_points, ensure_ascii=False), fenomeni_raw)
    )
    get_modelli.clear()

@st.cache_data(ttl=30)
def get_modelli():
    rows = exec_query("SELECT * FROM modello ORDER BY created_at DESC", fetch='all')
    res = []
    for d in (rows or []):
        try:
            d["key_points"] = json.loads(d["key_points"])
        except Exception:
            d["key_points"] = []
        res.append(d)
    return res

def get_modello_by_id(modello_id):
    d = exec_query("SELECT * FROM modello WHERE id = ?", (modello_id,), fetch='one')
    if not d:
        return None
    try:
        d["key_points"] = json.loads(d["key_points"])
    except Exception:
        d["key_points"] = []
    return d

def elimina_modello(modello_id):
    exec_query("DELETE FROM modello WHERE id = ?", (modello_id,))
    get_modelli.clear()

@st.cache_data(ttl=30)
def get_tutti_fenomeni_unici():
    """Restituisce tutti i fenomeni unici (testo + descrizione) da tutte le sessioni,
    deduplicati per testo (case-insensitive), ordinati per testo."""
    rows = exec_query(
        "SELECT DISTINCT testo, descrizione FROM fenomeno ORDER BY testo ASC",
        fetch='all'
    )
    if not rows:
        return []
    # Deduplicazione case-insensitive, tenendo la prima occorrenza
    seen = set()
    result = []
    for r in rows:
        key = r["testo"].strip().lower()
        if key not in seen:
            seen.add(key)
            result.append({"testo": r["testo"], "descrizione": r.get("descrizione", "") or ""})
    return result
