"""
Recupera i dati degli scenari individuali da una sessione esportata in JSON.
Per ogni scenario con dati mancanti (narrativa, titolo, minacce, opportunita),
analizza la cronologia dei messaggi e usa l'API Anthropic per ricostruire i dati.

Uso:
  python tools/recupera_scenari.py <path_json> [--apply]

  <path_json>  : percorso al file JSON esportato (es. sessione_1_KJFIPQ.json)
  --apply      : applica le modifiche al DB (richiede DATABASE_URL nel .env o env)

Senza --apply, stampa solo gli UPDATE SQL per revisione manuale.
"""

import sys
import json
import os
import re
from pathlib import Path

def carica_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_transcript(messaggi):
    """Converte la lista messaggi in un testo leggibile."""
    lines = []
    for m in messaggi:
        role = "FACILITATORE" if m.get("ruolo") == "assistant" else "PARTECIPANTE"
        lines.append(f"[{role}] {m.get('contenuto', '').strip()}")
    return "\n\n".join(lines)


def estrai_dati_da_conversazione(transcript, scenario_id, quadrante, api_key):
    """Chiede a Claude di estrarre narrativa/titolo/minacce/opportunita dal trascritto."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Hai davanti la trascrizione completa di una conversazione di Scenario Planning.
Il partecipante stava costruendo uno scenario futuro per il quadrante: {quadrante}

TRASCRITTO:
{transcript}

Analizza attentamente la conversazione e restituisci un JSON con i campi che puoi ricavare:
{{
  "narrativa": "testo della narrativa dello scenario (3-5 frasi) se emersa, altrimenti null",
  "titolo": "titolo dello scenario se stabilito, altrimenti null",
  "minacce": ["elenco delle minacce emerse dalla conversazione, lista vuota se non emerse"],
  "opportunita": ["elenco delle opportunita emerse dalla conversazione, lista vuota se non emerse"]
}}

REGOLE:
- Estrai SOLO ciò che è esplicitamente presente nella conversazione.
- La narrativa è spesso nell'ultimo lungo messaggio del FACILITATORE prima delle domande su titolo/minacce.
- Il titolo è quello scelto o accettato dal PARTECIPANTE.
- Le minacce e opportunita sono le risposte del PARTECIPANTE a quelle specifiche domande.
- Se un campo non è recuperabile, metti null (narrativa, titolo) o lista vuota (minacce, opportunita).
- Rispondi SOLO con il JSON, nessun testo fuori dal JSON."""

    risposta = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt},
                  {"role": "assistant", "content": "{"}],
    )
    testo = "{" + risposta.content[0].text

    # Parse
    match = re.search(r'\{.*\}', testo, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(testo)


def genera_sql_update(scenario_id, dati):
    """Genera la stringa SQL UPDATE per lo scenario."""
    sets = []
    params_commento = []

    if dati.get("narrativa"):
        nar = dati["narrativa"].replace("'", "''")
        sets.append(f"narrativa = '{nar}'")
        params_commento.append("narrativa")

    if dati.get("titolo"):
        tit = dati["titolo"].replace("'", "''")
        sets.append(f"titolo = '{tit}'")
        params_commento.append("titolo")

    if dati.get("minacce"):
        minacce_json = json.dumps(dati["minacce"], ensure_ascii=False).replace("'", "''")
        sets.append(f"minacce = '{minacce_json}'")
        params_commento.append("minacce")

    if dati.get("opportunita"):
        opp_json = json.dumps(dati["opportunita"], ensure_ascii=False).replace("'", "''")
        sets.append(f"opportunita = '{opp_json}'")
        params_commento.append("opportunita")

    if not sets:
        return None

    sql = f"UPDATE scenari SET {', '.join(sets)} WHERE id = {scenario_id};"
    return sql, params_commento


def applica_update(scenario_id, dati, db_url):
    """Applica gli aggiornamenti direttamente al DB Postgres."""
    import psycopg2
    from psycopg2.extras import Json

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    fields = {}
    if dati.get("narrativa"):
        fields["narrativa"] = dati["narrativa"]
    if dati.get("titolo"):
        fields["titolo"] = dati["titolo"]
    if dati.get("minacce"):
        fields["minacce"] = json.dumps(dati["minacce"], ensure_ascii=False)
    if dati.get("opportunita"):
        fields["opportunita"] = json.dumps(dati["opportunita"], ensure_ascii=False)

    if not fields:
        conn.close()
        return False

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [scenario_id]
    cur.execute(f"UPDATE scenari SET {set_clause} WHERE id = %s", values)
    conn.close()
    return True


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    json_path = args[0]
    apply_mode = "--apply" in args

    # Leggi API key da env o da secrets.toml
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # prova secrets.toml di Streamlit
        secrets_path = Path(__file__).parent.parent / "streamlit" / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            for line in secrets_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ANTHROPIC_API_KEY"):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not api_key:
        # prova .env alla radice
        env_path = Path(__file__).parent.parent / ".env"
        if not env_path.exists():
            env_path = Path(__file__).parent.parent / "streamlit" / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"')
    if not api_key:
        print("ERRORE: ANTHROPIC_API_KEY non trovata.")
        print("Imposta la variabile d'ambiente oppure aggiungila a:")
        print("  streamlit/.streamlit/secrets.toml  come:  ANTHROPIC_API_KEY = \"sk-ant-...\"")
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL", "")
    if apply_mode and not db_url:
        print("ERRORE: --apply richiede DATABASE_URL impostata.")
        sys.exit(1)

    data = carica_json(json_path)
    sessione = data.get("sessione", {})
    scenari = data.get("scenari_individuali", [])

    driver_info = (
        f"{sessione.get('driver1_nome', 'Driver 1')} × {sessione.get('driver2_nome', 'Driver 2')}"
    )

    print(f"\n=== RECUPERO DATI SCENARI — Sessione {sessione.get('codice')} ===")
    print(f"Domanda: {sessione.get('domanda_ricerca')}")
    print(f"Driver: {driver_info}\n")

    sql_totali = []

    for s in scenari:
        sid = s["id"]
        pid = s.get("nome_partecipante", s.get("partecipante_id", "?"))
        messaggi = s.get("messaggi") or []

        # Verifica quali campi mancano
        mancanti = []
        if not s.get("narrativa"):
            mancanti.append("narrativa")
        if not s.get("titolo"):
            mancanti.append("titolo")
        if not s.get("minacce"):
            mancanti.append("minacce")
        if not s.get("opportunita"):
            mancanti.append("opportunita")

        if not mancanti or len(messaggi) <= 1:
            print(f"Scenario {sid} (pid={pid}): OK o nessun messaggio da analizzare — salto.")
            continue

        # Descrivi il quadrante
        q = s.get("quadrante", "??")
        d1_val = sessione.get("driver1_pos") if "+" in q[:1] else sessione.get("driver1_neg")
        d2_val = sessione.get("driver2_pos") if len(q) > 1 and "+" in q[1:2] else sessione.get("driver2_neg")
        quadrante_desc = f"{sessione.get('driver1_nome')}: {d1_val} × {sessione.get('driver2_nome')}: {d2_val}"

        print(f"Scenario {sid} (pid={pid}) | quadrante={q} | mancanti: {mancanti}")
        print(f"  Analisi conversazione ({len(messaggi)} messaggi)...", end=" ", flush=True)

        try:
            transcript = build_transcript(messaggi)
            dati_estratti = estrai_dati_da_conversazione(
                transcript, sid, quadrante_desc, api_key
            )
            print("OK")

            # Mostra risultato
            for campo in mancanti:
                valore = dati_estratti.get(campo)
                if valore:
                    preview = str(valore)[:120] + ("..." if len(str(valore)) > 120 else "")
                    print(f"  {campo}: {preview}")
                else:
                    print(f"  {campo}: non recuperabile dalla conversazione")

            # Genera SQL
            risultato_sql = genera_sql_update(sid, dati_estratti)
            if risultato_sql:
                sql_str, campi_aggiornati = risultato_sql
                sql_totali.append(sql_str)
                print(f"  SQL generato per: {campi_aggiornati}")
            else:
                print(f"  Nessun dato recuperabile.")

            # Applica se richiesto
            if apply_mode:
                ok = applica_update(sid, dati_estratti, db_url)
                print(f"  {'Aggiornato nel DB.' if ok else 'Nessun aggiornamento necessario.'}")

        except Exception as e:
            print(f"ERRORE: {e}")

        print()

    if sql_totali:
        print("\n" + "="*60)
        print("SQL DA ESEGUIRE (copia e incolla nel DB Postgres):")
        print("="*60)
        for sql in sql_totali:
            print(sql)
        print("="*60)

        # Salva anche su file
        out_path = Path(json_path).stem + "_recovery.sql"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("-- Recovery SQL generato da recupera_scenari.py\n")
            f.write(f"-- Sessione: {sessione.get('codice')}\n\n")
            for sql in sql_totali:
                f.write(sql + "\n")
        print(f"\nSQL salvato in: {out_path}")
    else:
        print("\nNessun dato da recuperare.")


if __name__ == "__main__":
    main()
