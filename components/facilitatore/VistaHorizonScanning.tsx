"use client";
import { useState } from "react";
import { CheckCircle, Clock, Plus, Check, X, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface Fenomeno {
  id: string;
  testo: string;
  descrizione?: string | null;
  autore: string;
  approvato: boolean;
}

interface Partecipante {
  id: string;
  nome: string;
  votato: boolean;
}

interface Props {
  dati: {
    id: string;
    fenomeni: Fenomeno[];
    partecipanti: Partecipante[];
    rankingAggregato: { fenomenoId: string; mediaPostazione: number; conteggio: number }[];
  };
  onApprovaFenomeno: (fenomenoId: string, approvato: boolean) => Promise<void>;
  onAggiungiFenomeno: (testo: string, descrizione?: string) => Promise<void>;
  onChiudiFase: () => void;
}

export function VistaHorizonScanning({ dati, onApprovaFenomeno, onAggiungiFenomeno, onChiudiFase }: Props) {
  const [nuovoFenomeno, setNuovoFenomeno] = useState("");
  const [aggiungendo, setAggiungendo] = useState(false);

  const votati = dati.partecipanti.filter((p) => p.votato).length;
  const totale = dati.partecipanti.length;
  const percentuale = totale > 0 ? Math.round((votati / totale) * 100) : 0;

  const fenomeniInAttesa = dati.fenomeni.filter((f) => !f.approvato);
  const fenomeniApprovati = dati.fenomeni.filter((f) => f.approvato);

  // Ranking aggregato con nome fenomeno
  const rankingConNome = dati.rankingAggregato.map((r) => ({
    ...r,
    fenomeno: dati.fenomeni.find((f) => f.id === r.fenomenoId),
  })).filter((r) => r.fenomeno?.approvato);

  async function handleAggiungi() {
    if (!nuovoFenomeno.trim()) return;
    setAggiungendo(true);
    await onAggiungiFenomeno(nuovoFenomeno.trim());
    setNuovoFenomeno("");
    setAggiungendo(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Horizon Scanning</h2>
          <p className="text-sm text-gray-500">I partecipanti stanno votando i fenomeni</p>
        </div>
        <Button onClick={onChiudiFase} variante="secondary">
          Chiudi fase <ChevronRight size={16} className="ml-1" />
        </Button>
      </div>

      {/* Progress partecipanti */}
      <Card>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700">Avanzamento partecipanti</h3>
          <span className="text-sm text-gray-500">{votati}/{totale} completato</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
          <div
            className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${percentuale}%` }}
          />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {dati.partecipanti.map((p) => (
            <div
              key={p.id}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                p.votato ? "bg-green-50 text-green-800" : "bg-gray-50 text-gray-500"
              }`}
            >
              {p.votato ? (
                <CheckCircle size={14} className="text-green-600 shrink-0" />
              ) : (
                <Clock size={14} className="text-gray-400 shrink-0" />
              )}
              <span className="truncate">{p.nome}</span>
            </div>
          ))}
          {totale === 0 && (
            <p className="col-span-4 text-sm text-gray-400 text-center py-2">
              Nessun partecipante connesso ancora
            </p>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        {/* Fenomeni da approvare */}
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Aggiunti dai partecipanti</h3>
            {fenomeniInAttesa.length > 0 && (
              <Badge variante="giallo">{fenomeniInAttesa.length} in attesa</Badge>
            )}
          </div>

          {fenomeniInAttesa.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">Nessun fenomeno in attesa</p>
          ) : (
            <div className="space-y-2">
              {fenomeniInAttesa.map((f) => (
                <div key={f.id} className="flex items-start justify-between gap-2 bg-yellow-50 rounded-lg p-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800">{f.testo}</p>
                    <p className="text-xs text-gray-400 mt-0.5">aggiunto da {f.autore}</p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button
                      onClick={() => onApprovaFenomeno(f.id, true)}
                      className="p-1 rounded-md text-green-600 hover:bg-green-100"
                      title="Approva"
                    >
                      <Check size={15} />
                    </button>
                    <button
                      onClick={() => onApprovaFenomeno(f.id, false)}
                      className="p-1 rounded-md text-red-400 hover:bg-red-50"
                      title="Rifiuta"
                    >
                      <X size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Aggiungi fenomeno manualmente */}
          <div className="border-t mt-3 pt-3 space-y-2">
            <p className="text-xs text-gray-400 font-medium">Aggiungi manualmente</p>
            <div className="flex gap-2">
              <input
                value={nuovoFenomeno}
                onChange={(e) => setNuovoFenomeno(e.target.value)}
                placeholder="Nuovo fenomeno..."
                className="flex-1 text-sm rounded-lg border border-gray-300 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                onKeyDown={(e) => e.key === "Enter" && handleAggiungi()}
              />
              <Button
                variante="secondary"
                dimensione="sm"
                onClick={handleAggiungi}
                caricamento={aggiungendo}
              >
                <Plus size={14} />
              </Button>
            </div>
          </div>
        </Card>

        {/* Ranking aggregato live */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Ranking aggregato live
          </h3>
          {rankingConNome.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">
              I risultati appariranno man mano che i partecipanti votano
            </p>
          ) : (
            <div className="space-y-2">
              {rankingConNome.slice(0, 10).map((r, i) => (
                <div key={r.fenomenoId} className="flex items-center gap-3">
                  <span className={`text-xs font-bold w-5 text-right shrink-0 ${
                    i < 3 ? "text-indigo-600" : "text-gray-400"
                  }`}>
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800 truncate">{r.fenomeno?.testo}</p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div
                      className="h-1.5 rounded-full bg-indigo-400"
                      style={{
                        width: `${Math.max(8, 60 - i * 5)}px`,
                      }}
                    />
                    <span className="text-xs text-gray-400">{r.conteggio} voti</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
