import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "foresight.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessione (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        CREATE TABLE IF NOT EXISTS fenomeno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessione_id INTEGER NOT NULL,
            testo TEXT NOT NULL,
            descrizione TEXT,
            priorita INTEGER DEFAULT 999,
            FOREIGN KEY (sessione_id) REFERENCES sessione(id)
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
            FOREIGN KEY (sessione_id) REFERENCES sessione(id)
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


# ── Sessione ──────────────────────────────────────────────

def crea_sessione(domanda, frame, key_points, fenomeni):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO sessione (domanda_ricerca, frame_temporale, key_points) VALUES (?, ?, ?)",
        (domanda, frame, json.dumps(key_points))
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


def get_sessione(sid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessione WHERE id = ?", (sid,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["key_points"] = json.loads(d["key_points"])
    return d


def aggiorna_sessione(sid, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [sid]
    conn = get_conn()
    conn.execute(f"UPDATE sessione SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()


def lista_sessioni():
    conn = get_conn()
    rows = conn.execute("SELECT id, domanda_ricerca, frame_temporale, stato, created_at FROM sessione ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Fenomeni ──────────────────────────────────────────────

def get_fenomeni(sid):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM fenomeno WHERE sessione_id = ? ORDER BY priorita ASC", (sid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def aggiungi_fenomeno(sid, testo, descrizione=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO fenomeno (sessione_id, testo, descrizione, priorita) VALUES (?, ?, ?, ?)",
        (sid, testo, descrizione, 999)
    )
    conn.commit()
    conn.close()


def aggiorna_priorita_fenomeni(sid, ordine_ids):
    conn = get_conn()
    for i, fid in enumerate(ordine_ids):
        conn.execute("UPDATE fenomeno SET priorita = ? WHERE id = ? AND sessione_id = ?", (i, fid, sid))
    conn.commit()
    conn.close()


def elimina_fenomeno(fid):
    conn = get_conn()
    conn.execute("DELETE FROM fenomeno WHERE id = ?", (fid,))
    conn.commit()
    conn.close()


# ── Scenari ───────────────────────────────────────────────

def crea_scenari(sid):
    quadranti = [("++", 1), ("+-", 2), ("-+", 3), ("--", 4)]
    conn = get_conn()
    conn.execute("DELETE FROM scenario WHERE sessione_id = ?", (sid,))
    for q, n in quadranti:
        conn.execute(
            "INSERT INTO scenario (sessione_id, numero, quadrante) VALUES (?, ?, ?)",
            (sid, n, q)
        )
    conn.commit()
    conn.close()


def get_scenari(sid):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM scenario WHERE sessione_id = ? ORDER BY numero", (sid,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["minacce"] = json.loads(d["minacce"] or "[]")
        d["opportunita"] = json.loads(d["opportunita"] or "[]")
        d["key_points_data"] = json.loads(d["key_points_data"] or "{}")
        result.append(d)
    return result


def get_scenario(scenario_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM scenario WHERE id = ?", (scenario_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["minacce"] = json.loads(d["minacce"] or "[]")
    d["opportunita"] = json.loads(d["opportunita"] or "[]")
    d["key_points_data"] = json.loads(d["key_points_data"] or "{}")
    return d


def aggiorna_scenario(scenario_id, **kwargs):
    if not kwargs:
        return
    # Serializza liste/dict
    for k in ["minacce", "opportunita", "key_points_data"]:
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
