"use client";
import { useState } from "react";
import { Plus, Trash2, PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface Props {
  dati: {
    domandaRicerca: string;
    frameTemporale: string;
    keyPoints: string[];
    fenomeni: { id: string; testo: string; descrizione?: string | null; autore: string }[];
    partecipanti: { id: string; nome: string }[];
  };
  onAvviaHorizonScanning: () => void;
  onAggiungiFenomeno: (testo: string, descrizione?: string) => Promise<void>;
}

export function VistaPannelloSetup({ dati, onAvviaHorizonScanning, onAggiungiFenomeno }: Props) {
  const [nuovoFenomeno, setNuovoFenomeno] = useState("");
  const [nuovaDescr, setNuovaDescr] = useState("");
  const [aggiungendo, setAggiungendo] = useState(false);

  async function handleAggiungi() {
    if (!nuovoFenomeno.trim()) return;
    setAggiungendo(true);
    await onAggiungiFenomeno(nuovoFenomeno.trim(), nuovaDescr.trim() || undefined);
    setNuovoFenomeno("");
    setNuovaDescr("");
    setAggiungendo(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Pannello Setup</h2>
          <p className="text-sm text-gray-500">Verifica la configurazione e avvia la sessione quando sei pronto</p>
        </div>
        <Button onClick={onAvviaHorizonScanning} dimensione="lg">
          <PlayCircle size={18} className="mr-2" />
          Avvia Horizon Scanning
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Riepilogo configurazione */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Configurazione sessione</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-400 text-xs">Domanda</span>
              <p className="text-gray-800">{dati.domandaRicerca}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs">Orizzonte temporale</span>
              <p className="text-gray-800 font-medium">{dati.frameTemporale}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs">Key Points</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {dati.keyPoints.map((kp, i) => (
                  <Badge key={i} variante="default">{kp}</Badge>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Fenomeni */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Fenomeni ({dati.fenomeni.length})
          </h3>
          <div className="space-y-1.5 max-h-48 overflow-y-auto mb-3">
            {dati.fenomeni.map((f) => (
              <div key={f.id} className="flex items-start gap-2 text-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                <span className="text-gray-700">{f.testo}</span>
              </div>
            ))}
          </div>
          <div className="border-t pt-3 space-y-2">
            <input
              value={nuovoFenomeno}
              onChange={(e) => setNuovoFenomeno(e.target.value)}
              placeholder="Nuovo fenomeno..."
              className="w-full text-sm rounded-lg border border-gray-300 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              onKeyDown={(e) => e.key === "Enter" && handleAggiungi()}
            />
            <input
              value={nuovaDescr}
              onChange={(e) => setNuovaDescr(e.target.value)}
              placeholder="Descrizione opzionale"
              className="w-full text-xs rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
            <Button
              variante="secondary"
              dimensione="sm"
              onClick={handleAggiungi}
              caricamento={aggiungendo}
              className="w-full"
            >
              <Plus size={13} className="mr-1" /> Aggiungi
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
