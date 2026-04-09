"use client";
import { useState } from "react";
import { CheckCircle, Clock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface Partecipante {
  id: string;
  nome: string;
  scenarioIndividuale?: { concluso: boolean; stepCorrente: string } | null;
}

interface Props {
  dati: {
    id: string;
    partecipanti: Partecipante[];
  };
  codiceFacilitatore: string;
  conclusiCount: number;
  onSintetizzaEAvanza: () => void;
}

export function VistaScenarioIndividuale({ dati, codiceFacilitatore, conclusiCount, onSintetizzaEAvanza }: Props) {
  const [sintetizzando, setSintetizzando] = useState(false);

  const totale = dati.partecipanti.length;
  const tuttiConclusi = conclusiCount >= totale && totale > 0;

  async function sintetizzaEAvanza() {
    setSintetizzando(true);
    await fetch("/api/scenario-individuale/sintetizza", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codiceFacilitatore }),
    });
    onSintetizzaEAvanza();
    setSintetizzando(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Scenario Planning — Fase Individuale</h2>
          <p className="text-sm text-gray-500">
            Ogni partecipante sta costruendo la propria visione con l&apos;agente
          </p>
        </div>
        <Badge variante={tuttiConclusi ? "verde" : "default"}>
          {conclusiCount}/{totale} conclusi
        </Badge>
      </div>

      {/* Barra progresso */}
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className="h-2 rounded-full bg-indigo-500 transition-all duration-500"
          style={{ width: totale > 0 ? `${(conclusiCount / totale) * 100}%` : "0%" }}
        />
      </div>

      {/* Lista partecipanti */}
      <Card>
        <div className="space-y-2">
          {dati.partecipanti.map((p) => {
            const sc = p.scenarioIndividuale;
            const fatto = sc?.concluso ?? false;
            return (
              <div
                key={p.id}
                className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
              >
                <span className="text-sm text-gray-800">{p.nome}</span>
                <div className="flex items-center gap-2">
                  {sc && !fatto && (
                    <span className="text-xs text-gray-400">{sc.stepCorrente}</span>
                  )}
                  {fatto ? (
                    <CheckCircle size={16} className="text-green-500" />
                  ) : sc ? (
                    <Clock size={16} className="text-gray-300" />
                  ) : (
                    <span className="text-xs text-gray-300">in attesa</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Pulsante sintesi */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-3">
        <p className="text-sm text-amber-800">
          <strong>Quando tutti hanno finito</strong>, clicca per generare le bozze di gruppo.
          Claude (Sonnet) sintetizzerà le visioni individuali di ogni gruppo in una narrativa condivisa,
          evidenziando punti comuni e divergenze.
        </p>
        <Button
          onClick={sintetizzaEAvanza}
          caricamento={sintetizzando}
          disabled={!tuttiConclusi && !sintetizzando}
          dimensione="lg"
          className="w-full"
        >
          {sintetizzando ? (
            <>
              <Loader2 size={16} className="mr-2 animate-spin" />
              Generazione bozze in corso...
            </>
          ) : (
            "Genera bozze di gruppo e avanza"
          )}
        </Button>
        {!tuttiConclusi && (
          <p className="text-xs text-amber-600 text-center">
            Attendi che tutti i partecipanti concludano il lavoro individuale
          </p>
        )}
      </div>
    </div>
  );
}
