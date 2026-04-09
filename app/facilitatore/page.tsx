"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Plus, LogIn, Compass, Trash2, Upload, FileSpreadsheet } from "lucide-react";
import * as XLSX from "xlsx";
import { Button } from "@/components/ui/Button";

interface Fenomeno {
  testo: string;
  descrizione: string;
}

export default function PaginaFacilitatore() {
  const router = useRouter();
  const [vista, setVista] = useState<"home" | "crea" | "accedi">("home");

  // Form nuova sessione
  const [domanda, setDomanda] = useState("");
  const [frameTemporale, setFrameTemporale] = useState("");
  const [keyPoints, setKeyPoints] = useState<string[]>([""]);
  const [fenomeni, setFenomeni] = useState<Fenomeno[]>([{ testo: "", descrizione: "" }]);
  const [caricamento, setCaricamento] = useState(false);
  const [errore, setErrore] = useState("");
  const fileRefCreazione = useRef<HTMLInputElement>(null);

  function parsaFileCreazione(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const wb = XLSX.read(ev.target?.result, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const righe = XLSX.utils.sheet_to_json<string[]>(ws, { header: 1 });
      const importati = righe
        .slice(1)
        .map((r) => ({ testo: String(r[0] ?? "").trim(), descrizione: String(r[1] ?? "").trim() }))
        .filter((r) => r.testo.length > 0);
      setFenomeni((prev) => {
        const esistenti = prev.filter((f) => f.testo.trim());
        return [...esistenti, ...importati];
      });
    };
    reader.readAsArrayBuffer(file);
    e.target.value = "";
  }

  // Form accesso sessione esistente
  const [codiceAccesso, setCodiceAccesso] = useState("");
  const [erroreAccesso, setErroreAccesso] = useState("");

  async function creaSessione() {
    if (!domanda.trim() || !frameTemporale.trim()) {
      setErrore("Domanda di ricerca e orizzonte temporale sono obbligatori.");
      return;
    }
    const kpValidi = keyPoints.filter((k) => k.trim());
    const fenomeniValidi = fenomeni.filter((f) => f.testo.trim());

    setCaricamento(true);
    setErrore("");

    const res = await fetch("/api/sessione", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        domandaRicerca: domanda.trim(),
        frameTemporale: frameTemporale.trim(),
        keyPoints: kpValidi,
        fenomeni: fenomeniValidi,
      }),
    });

    if (!res.ok) {
      setErrore("Errore nella creazione della sessione.");
      setCaricamento(false);
      return;
    }

    const data = await res.json();
    sessionStorage.setItem("codiceFacilitatore", data.codiceFacilitatore);
    router.push(`/facilitatore/${data.codiceFacilitatore}`);
  }

  async function accediSessione() {
    if (!codiceAccesso.trim()) {
      setErroreAccesso("Inserisci il codice facilitatore.");
      return;
    }
    const res = await fetch(`/api/sessione/facilitatore?codice=${codiceAccesso.trim().toUpperCase()}`);
    if (!res.ok) {
      setErroreAccesso("Codice non valido.");
      return;
    }
    sessionStorage.setItem("codiceFacilitatore", codiceAccesso.trim().toUpperCase());
    router.push(`/facilitatore/${codiceAccesso.trim().toUpperCase()}`);
  }

  if (vista === "home") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-purple-600 rounded-2xl mb-2">
              <Compass size={28} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Area Facilitatore</h1>
            <p className="text-gray-500 text-sm">Crea e gestisci sessioni di Strategic Foresight</p>
          </div>

          <div className="grid gap-4">
            <button
              onClick={() => setVista("crea")}
              className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 text-left hover:border-purple-300 hover:shadow-md transition-all group"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                  <Plus size={18} className="text-purple-700" />
                </div>
                <span className="font-semibold text-gray-900">Nuova sessione</span>
              </div>
              <p className="text-sm text-gray-500 ml-12">
                Configura domanda di ricerca, fenomeni e key points
              </p>
            </button>

            <button
              onClick={() => setVista("accedi")}
              className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 text-left hover:border-indigo-300 hover:shadow-md transition-all group"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 bg-indigo-100 rounded-lg flex items-center justify-center group-hover:bg-indigo-200 transition-colors">
                  <LogIn size={18} className="text-indigo-700" />
                </div>
                <span className="font-semibold text-gray-900">Riprendi sessione</span>
              </div>
              <p className="text-sm text-gray-500 ml-12">
                Accedi a una sessione già creata con il codice facilitatore
              </p>
            </button>
          </div>

          <p className="text-center text-sm text-gray-400">
            <a href="/" className="hover:text-gray-600">← Torna alla homepage</a>
          </p>
        </div>
      </div>
    );
  }

  if (vista === "accedi") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center p-4">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <h2 className="text-xl font-bold text-gray-900">Riprendi sessione</h2>
            <p className="text-sm text-gray-500 mt-1">Inserisci il codice facilitatore (8 caratteri)</p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
            <input
              type="text"
              value={codiceAccesso}
              onChange={(e) => setCodiceAccesso(e.target.value.toUpperCase())}
              placeholder="es. ABCD1234"
              maxLength={8}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-purple-500"
              onKeyDown={(e) => e.key === "Enter" && accediSessione()}
            />
            {erroreAccesso && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{erroreAccesso}</p>
            )}
            <Button onClick={accediSessione} className="w-full">Accedi</Button>
            <button onClick={() => setVista("home")} className="w-full text-sm text-gray-500 hover:text-gray-700">
              Indietro
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Vista creazione sessione
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <button onClick={() => setVista("home")} className="text-gray-400 hover:text-gray-600">
            ←
          </button>
          <h1 className="text-xl font-bold text-gray-900">Nuova sessione</h1>
        </div>

        {/* Sezione 1: Contesto */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">Contesto della sessione</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domanda di ricerca <span className="text-red-500">*</span>
            </label>
            <textarea
              value={domanda}
              onChange={(e) => setDomanda(e.target.value)}
              rows={3}
              placeholder="Es. Come evolverà il sistema educativo nei prossimi 10 anni?"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Orizzonte temporale <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={frameTemporale}
              onChange={(e) => setFrameTemporale(e.target.value)}
              placeholder="Es. 2035, 2030-2040, prossimi 10 anni"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        {/* Sezione 2: Key Points */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Key Points per lo Scenario Planning</h2>
            <span className="text-xs text-gray-400">Dimensioni da esplorare in ogni scenario</span>
          </div>

          <div className="space-y-2">
            {keyPoints.map((kp, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={kp}
                  onChange={(e) => {
                    const nuovi = [...keyPoints];
                    nuovi[i] = e.target.value;
                    setKeyPoints(nuovi);
                  }}
                  placeholder={`Es. Tecnologia, Lavoro, Governance...`}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {keyPoints.length > 1 && (
                  <button
                    onClick={() => setKeyPoints(keyPoints.filter((_, j) => j !== i))}
                    className="text-gray-400 hover:text-red-500 p-2"
                  >
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>

          <Button
            variante="ghost"
            dimensione="sm"
            onClick={() => setKeyPoints([...keyPoints, ""])}
          >
            <Plus size={14} className="mr-1" /> Aggiungi key point
          </Button>
        </div>

        {/* Sezione 3: Fenomeni */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Fenomeni / Trend iniziali</h2>
            <span className="text-xs text-gray-400">I partecipanti potranno aggiungerne altri</span>
          </div>

          <div className="space-y-3">
            {fenomeni.map((f, i) => (
              <div key={i} className="border border-gray-200 rounded-xl p-4 space-y-3 bg-gray-50/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Fenomeno {i + 1}</span>
                  {fenomeni.length > 1 && (
                    <button
                      onClick={() => setFenomeni(fenomeni.filter((_, j) => j !== i))}
                      className="text-gray-400 hover:text-red-500 p-1 rounded"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Nome</label>
                  <input
                    type="text"
                    value={f.testo}
                    onChange={(e) => {
                      const nuovi = [...fenomeni];
                      nuovi[i] = { ...nuovi[i], testo: e.target.value };
                      setFenomeni(nuovi);
                    }}
                    placeholder="Es. Intelligenza Artificiale generativa"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Descrizione <span className="text-gray-400 font-normal">(opzionale)</span></label>
                  <input
                    type="text"
                    value={f.descrizione}
                    onChange={(e) => {
                      const nuovi = [...fenomeni];
                      nuovi[i] = { ...nuovi[i], descrizione: e.target.value };
                      setFenomeni(nuovi);
                    }}
                    placeholder="Breve descrizione del fenomeno o trend"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            ))}
          </div>

          <Button
            variante="ghost"
            dimensione="sm"
            onClick={() => setFenomeni([...fenomeni, { testo: "", descrizione: "" }])}
          >
            <Plus size={14} className="mr-1" /> Aggiungi fenomeno
          </Button>
          <input
            ref={fileRefCreazione}
            type="file"
            accept=".xlsx,.xls,.csv"
            className="hidden"
            onChange={parsaFileCreazione}
          />
          <Button
            variante="ghost"
            dimensione="sm"
            onClick={() => fileRefCreazione.current?.click()}
            className="w-full border border-dashed border-gray-300 hover:border-indigo-400"
          >
            <Upload size={14} className="mr-1" />
            <FileSpreadsheet size={14} className="mr-1" /> Importa da Excel / CSV
          </Button>
        </div>

        {errore && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-3">{errore}</p>
        )}

        <Button
          onClick={creaSessione}
          caricamento={caricamento}
          dimensione="lg"
          className="w-full"
        >
          Crea sessione
        </Button>
      </div>
    </div>
  );
}
