"use client";
import { useState, useEffect } from "react";
import { ChevronRight, GripVertical, Users } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface Fenomeno {
  id: string;
  testo: string;
  approvato: boolean;
}

interface Partecipante {
  id: string;
  nome: string;
  gruppoId?: string | null;
}

interface RankingItem {
  fenomenoId: string;
  mediaPostazione: number;
  conteggio: number;
}

interface Props {
  dati: {
    id: string;
    fenomeni: Fenomeno[];
    partecipanti: Partecipante[];
    rankingAggregato: RankingItem[];
    driver1Nome?: string | null;
    driver1PosPolo?: string | null;
    driver1NegPolo?: string | null;
    driver2Nome?: string | null;
    driver2PosPolo?: string | null;
    driver2NegPolo?: string | null;
  };
  codiceFacilitatore: string;
  onAvviaScenarioPlanning: () => void;
  onAggiorna: () => void;
}

type Assegnazione = Record<number, string[]>; // gruppoIndex → partecipanteIds

export function VistaTransizione({ dati, codiceFacilitatore, onAvviaScenarioPlanning, onAggiorna }: Props) {
  const [driver1, setDriver1] = useState({
    nome: dati.driver1Nome || "",
    posPolo: dati.driver1PosPolo || "",
    negPolo: dati.driver1NegPolo || "",
  });
  const [driver2, setDriver2] = useState({
    nome: dati.driver2Nome || "",
    posPolo: dati.driver2PosPolo || "",
    negPolo: dati.driver2NegPolo || "",
  });

  const [assegnazione, setAssegnazione] = useState<Assegnazione>({ 0: [], 1: [], 2: [], 3: [] });
  const [salvando, setSalvando] = useState(false);
  const [avviando, setAvviando] = useState(false);

  const partecipantiNonAssegnati = dati.partecipanti.filter(
    (p) => !Object.values(assegnazione).flat().includes(p.id)
  );

  const quadranti = [
    { index: 0, label: "Quadrante 1", simbolo: "++", desc: `${driver1.posPolo || "+"} × ${driver2.posPolo || "+"}` },
    { index: 1, label: "Quadrante 2", simbolo: "+-", desc: `${driver1.posPolo || "+"} × ${driver2.negPolo || "−"}` },
    { index: 2, label: "Quadrante 3", simbolo: "-+", desc: `${driver1.negPolo || "−"} × ${driver2.posPolo || "+"}` },
    { index: 3, label: "Quadrante 4", simbolo: "--", desc: `${driver1.negPolo || "−"} × ${driver2.negPolo || "−"}` },
  ];

  function sposta(partecipanteId: string, gruppoIndex: number) {
    setAssegnazione((prev) => {
      const nuovo = { ...prev };
      // Rimuovi da tutti i gruppi
      for (const k in nuovo) {
        nuovo[k] = nuovo[k].filter((id) => id !== partecipanteId);
      }
      // Aggiungi al gruppo target (max 4)
      if (nuovo[gruppoIndex].length < 4) {
        nuovo[gruppoIndex] = [...nuovo[gruppoIndex], partecipanteId];
      }
      return nuovo;
    });
  }

  function rimuovi(partecipanteId: string) {
    setAssegnazione((prev) => {
      const nuovo = { ...prev };
      for (const k in nuovo) {
        nuovo[k] = nuovo[k].filter((id) => id !== partecipanteId);
      }
      return nuovo;
    });
  }

  async function salvaEAvvia() {
    setAvviando(true);

    // Salva driver
    await fetch("/api/sessione/facilitatore", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        codice: codiceFacilitatore,
        driver1Nome: driver1.nome,
        driver1PosPolo: driver1.posPolo,
        driver1NegPolo: driver1.negPolo,
        driver2Nome: driver2.nome,
        driver2PosPolo: driver2.posPolo,
        driver2NegPolo: driver2.negPolo,
      }),
    });

    // Crea gruppi
    const gruppi = quadranti.map((q) => ({
      numero: q.index + 1,
      quadrante: q.simbolo,
      partecipantiIds: assegnazione[q.index],
    }));

    await fetch("/api/gruppi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codiceFacilitatore, gruppi }),
    });

    onAggiorna();
    onAvviaScenarioPlanning();
    setAvviando(false);
  }

  // Ranking top fenomeni
  const topFenomeni = dati.rankingAggregato
    .slice(0, 8)
    .map((r) => ({ ...r, fenomeno: dati.fenomeni.find((f) => f.id === r.fenomenoId) }))
    .filter((r) => r.fenomeno?.approvato);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Transizione</h2>
          <p className="text-sm text-gray-500">Seleziona i 2 driver, definisci gli assi e crea i gruppi</p>
        </div>
      </div>

      {/* Top fenomeni */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Top fenomeni per priorità</h3>
        <div className="grid grid-cols-2 gap-2">
          {topFenomeni.map((r, i) => (
            <div key={r.fenomenoId} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
              <span className={`text-xs font-bold w-4 ${i < 2 ? "text-indigo-600" : "text-gray-400"}`}>
                {i + 1}
              </span>
              <span className="text-sm text-gray-700 truncate flex-1">{r.fenomeno?.testo}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Selezione driver */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: "Driver 1 (Asse X)", stato: driver1, setStato: setDriver1 },
          { label: "Driver 2 (Asse Y)", stato: driver2, setStato: setDriver2 },
        ].map(({ label, stato, setStato }) => (
          <Card key={label}>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">{label}</h3>
            <div className="space-y-2">
              <input
                value={stato.nome}
                onChange={(e) => setStato({ ...stato, nome: e.target.value })}
                placeholder="Nome del driver (es. Centralizzazione)"
                className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  value={stato.posPolo}
                  onChange={(e) => setStato({ ...stato, posPolo: e.target.value })}
                  placeholder="Polo positivo"
                  className="text-sm rounded-lg border border-gray-300 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-green-400"
                />
                <input
                  value={stato.negPolo}
                  onChange={(e) => setStato({ ...stato, negPolo: e.target.value })}
                  placeholder="Polo negativo"
                  className="text-sm rounded-lg border border-gray-300 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-red-400"
                />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Matrice 2x2 con assegnazione gruppi */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700">Assegnazione gruppi</h3>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Users size={13} />
            <span>{partecipantiNonAssegnati.length} non assegnati</span>
          </div>
        </div>

        {/* Partecipanti da assegnare */}
        {partecipantiNonAssegnati.length > 0 && (
          <div className="mb-4 p-3 bg-yellow-50 rounded-lg">
            <p className="text-xs font-medium text-yellow-700 mb-2">Trascina nei gruppi:</p>
            <div className="flex flex-wrap gap-2">
              {partecipantiNonAssegnati.map((p) => (
                <select
                  key={p.id}
                  onChange={(e) => e.target.value !== "" && sposta(p.id, parseInt(e.target.value))}
                  value=""
                  className="text-xs bg-white border border-yellow-300 rounded-md px-2 py-1 cursor-pointer"
                >
                  <option value="">{p.nome}</option>
                  {quadranti.map((q) => (
                    <option key={q.index} value={q.index}>
                      → {q.label}
                    </option>
                  ))}
                </select>
              ))}
            </div>
          </div>
        )}

        {/* Griglia quadranti */}
        <div className="grid grid-cols-2 gap-3">
          {quadranti.map((q) => (
            <div
              key={q.index}
              className="border-2 border-dashed border-gray-200 rounded-xl p-3 min-h-[100px]"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-600">{q.label}</span>
                <Badge variante="grigio">{q.simbolo}</Badge>
              </div>
              <p className="text-xs text-gray-400 mb-2">{q.desc}</p>
              <div className="space-y-1">
                {assegnazione[q.index].map((pid) => {
                  const p = dati.partecipanti.find((x) => x.id === pid);
                  return p ? (
                    <div key={pid} className="flex items-center justify-between bg-indigo-50 rounded-md px-2 py-1">
                      <span className="text-xs text-indigo-800">{p.nome}</span>
                      <button
                        onClick={() => rimuovi(pid)}
                        className="text-indigo-300 hover:text-red-400 text-xs"
                      >
                        ×
                      </button>
                    </div>
                  ) : null;
                })}
                {assegnazione[q.index].length === 0 && (
                  <p className="text-xs text-gray-300 italic">Nessun partecipante</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Button
        onClick={salvaEAvvia}
        caricamento={avviando}
        dimensione="lg"
        className="w-full"
        disabled={!driver1.nome || !driver2.nome}
      >
        Avvia Scenario Planning <ChevronRight size={16} className="ml-1" />
      </Button>
    </div>
  );
}
