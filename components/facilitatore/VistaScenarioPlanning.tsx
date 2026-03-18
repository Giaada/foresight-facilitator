"use client";
import { useState } from "react";
import { CheckCircle, Clock, MessageSquare, FileText, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const LABEL_STEP: Record<string, string> = {
  intro: "Introduzione",
  key_points: "Key Points",
  narrativa: "Narrativa",
  titolo: "Titolo",
  minacce: "Minacce",
  opportunita: "Opportunità",
  concluso: "Completato",
};

const STEP_ORDINE = ["intro", "key_points", "narrativa", "titolo", "minacce", "opportunita", "concluso"];

interface Gruppo {
  id: string;
  numero: number;
  quadrante: string;
  nomeScenario?: string | null;
  stepCorrente: string;
  partecipanti: { id: string; nome: string }[];
  scenarioOutput?: {
    narrativa?: string | null;
    titolo?: string | null;
    minacce?: string[];
    opportunita?: string[];
  } | null;
}

interface Props {
  dati: {
    stato: string;
    gruppi: Gruppo[];
    driver1Nome?: string | null;
    driver1PosPolo?: string | null;
    driver1NegPolo?: string | null;
    driver2Nome?: string | null;
    driver2PosPolo?: string | null;
    driver2NegPolo?: string | null;
  };
  onChiudiSessione: () => void;
  onAggiorna: () => void;
}

export function VistaScenarioPlanning({ dati, onChiudiSessione, onAggiorna }: Props) {
  const [gruppoAperto, setGruppoAperto] = useState<string | null>(null);

  const tuttiCompletati = dati.gruppi.length > 0 && dati.gruppi.every((g) => g.stepCorrente === "concluso");

  function progressoStep(step: string): number {
    const idx = STEP_ORDINE.indexOf(step);
    return idx >= 0 ? Math.round((idx / (STEP_ORDINE.length - 1)) * 100) : 0;
  }

  function descrizionePolo(quadrante: string) {
    const asseX = quadrante[0] === "+" ? dati.driver1PosPolo || "+" : dati.driver1NegPolo || "−";
    const asseY = quadrante[1] === "+" ? dati.driver2PosPolo || "+" : dati.driver2NegPolo || "−";
    return `${asseX} × ${asseY}`;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Scenario Planning</h2>
          <p className="text-sm text-gray-500">
            {dati.driver1Nome && dati.driver2Nome
              ? `Driver: ${dati.driver1Nome} × ${dati.driver2Nome}`
              : "Monitoraggio avanzamento gruppi"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variante="secondary" onClick={onAggiorna} dimensione="sm">
            Aggiorna
          </Button>
          {tuttiCompletati && dati.stato !== "concluso" && (
            <Button onClick={onChiudiSessione}>
              Chiudi sessione
            </Button>
          )}
          {dati.stato === "concluso" && (
            <a href={`/report`}>
              <Button variante="secondary">
                <FileText size={15} className="mr-1.5" /> Vedi Report
              </Button>
            </a>
          )}
        </div>
      </div>

      {/* Matrice 2x2 overview */}
      <div className="grid grid-cols-2 gap-4">
        {dati.gruppi.map((gruppo) => {
          const aperto = gruppoAperto === gruppo.id;
          const progresso = progressoStep(gruppo.stepCorrente);
          const completato = gruppo.stepCorrente === "concluso";

          return (
            <Card key={gruppo.id} className={`transition-all ${completato ? "border-green-200 bg-green-50" : ""}`}>
              <div
                className="flex items-start justify-between cursor-pointer"
                onClick={() => setGruppoAperto(aperto ? null : gruppo.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-gray-500">Gruppo {gruppo.numero}</span>
                    <Badge variante={completato ? "verde" : "default"}>
                      {LABEL_STEP[gruppo.stepCorrente] || gruppo.stepCorrente}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 truncate">
                    {gruppo.scenarioOutput?.titolo || descrizionePolo(gruppo.quadrante)}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-3 shrink-0">
                  {completato ? (
                    <CheckCircle size={18} className="text-green-500" />
                  ) : (
                    <Clock size={18} className="text-gray-300" />
                  )}
                  {aperto ? <ChevronUp size={15} className="text-gray-400" /> : <ChevronDown size={15} className="text-gray-400" />}
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-3 w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${completato ? "bg-green-500" : "bg-indigo-500"}`}
                  style={{ width: `${progresso}%` }}
                />
              </div>

              {/* Partecipanti */}
              <div className="mt-2 flex flex-wrap gap-1">
                {gruppo.partecipanti.map((p) => (
                  <span key={p.id} className="text-xs bg-gray-100 text-gray-600 rounded px-2 py-0.5">
                    {p.nome}
                  </span>
                ))}
              </div>

              {/* Dettaglio espanso */}
              {aperto && gruppo.scenarioOutput && (
                <div className="mt-4 border-t pt-4 space-y-3 text-sm">
                  {gruppo.scenarioOutput.narrativa && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">Narrativa</p>
                      <p className="text-gray-700 text-xs leading-relaxed bg-white rounded-lg p-3 border">
                        {gruppo.scenarioOutput.narrativa}
                      </p>
                    </div>
                  )}
                  {gruppo.scenarioOutput.minacce && gruppo.scenarioOutput.minacce.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">Minacce</p>
                      <ul className="space-y-1">
                        {gruppo.scenarioOutput.minacce.map((m, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-red-700">
                            <span className="text-red-400 mt-0.5">▸</span> {m}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {gruppo.scenarioOutput.opportunita && gruppo.scenarioOutput.opportunita.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">Opportunità</p>
                      <ul className="space-y-1">
                        {gruppo.scenarioOutput.opportunita.map((o, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-green-700">
                            <span className="text-green-500 mt-0.5">▸</span> {o}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
