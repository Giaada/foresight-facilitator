"use client";
import { useState, useRef } from "react";
import { Plus, Trash2, PlayCircle, Upload, FileSpreadsheet } from "lucide-react";
import * as XLSX from "xlsx";
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
  const [anteprima, setAnteprima] = useState<{ testo: string; descrizione: string }[] | null>(null);
  const [importando, setImportando] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleAggiungi() {
    if (!nuovoFenomeno.trim()) return;
    setAggiungendo(true);
    await onAggiungiFenomeno(nuovoFenomeno.trim(), nuovaDescr.trim() || undefined);
    setNuovoFenomeno("");
    setNuovaDescr("");
    setAggiungendo(false);
  }

  function parsaFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const data = ev.target?.result;
      const wb = XLSX.read(data, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const righe = XLSX.utils.sheet_to_json<string[]>(ws, { header: 1 });
      const risultati = righe
        .slice(1) // salta intestazione
        .map((r) => ({ testo: String(r[0] ?? "").trim(), descrizione: String(r[1] ?? "").trim() }))
        .filter((r) => r.testo.length > 0);
      setAnteprima(risultati);
    };
    reader.readAsArrayBuffer(file);
    e.target.value = "";
  }

  async function confermaImport() {
    if (!anteprima) return;
    setImportando(true);
    for (const f of anteprima) {
      await onAggiungiFenomeno(f.testo, f.descrizione || undefined);
    }
    setAnteprima(null);
    setImportando(false);
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
            {/* Anteprima import */}
            {anteprima && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 space-y-2">
                <p className="text-xs font-semibold text-indigo-700 flex items-center gap-1.5">
                  <FileSpreadsheet size={13} />
                  {anteprima.length} fenomeni pronti per l&apos;importazione
                </p>
                <ul className="text-xs text-indigo-800 space-y-0.5 max-h-24 overflow-y-auto">
                  {anteprima.map((f, i) => (
                    <li key={i} className="truncate">• {f.testo}{f.descrizione && <span className="text-indigo-400"> — {f.descrizione}</span>}</li>
                  ))}
                </ul>
                <div className="flex gap-2">
                  <Button dimensione="sm" onClick={confermaImport} caricamento={importando} className="flex-1">
                    Importa tutti
                  </Button>
                  <Button dimensione="sm" variante="ghost" onClick={() => setAnteprima(null)} className="flex-1">
                    Annulla
                  </Button>
                </div>
              </div>
            )}

            {/* Import da file */}
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              className="hidden"
              onChange={parsaFile}
            />
            <Button
              variante="ghost"
              dimensione="sm"
              onClick={() => fileRef.current?.click()}
              className="w-full border border-dashed border-gray-300 hover:border-indigo-400"
            >
              <Upload size={13} className="mr-1.5" /> Importa da Excel / CSV
            </Button>

            {/* Aggiunta manuale */}
            <input
              value={nuovoFenomeno}
              onChange={(e) => setNuovoFenomeno(e.target.value)}
              placeholder="Oppure aggiungi manualmente..."
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
