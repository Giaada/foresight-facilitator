"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { QuadrantVisualizer } from "@/components/ui/QuadrantVisualizer";
import type { Socket } from "socket.io-client";

interface Messaggio {
  id: string;
  autore: string;
  ruolo: "assistant" | "user";
  contenuto: string;
  createdAt: string;
}

interface ScenarioOutput {
  narrativa?: string | null;
  titolo?: string | null;
  minacce?: string[];
  opportunita?: string[];
}

interface Partecipante {
  id: string;
  nome: string;
  codice: string;
}

interface Props {
  partecipante: Partecipante;
  sessioneId: string;
  socket: Socket | null;
  sessione: {
    domandaRicerca: string;
    frameTemporale: string;
    driver1Nome?: string | null;
    driver1PosPolo?: string | null;
    driver1NegPolo?: string | null;
    driver2Nome?: string | null;
    driver2PosPolo?: string | null;
    driver2NegPolo?: string | null;
  };
}

export function VistaScenarioPlanningIndividuale({ partecipante, sessioneId, socket, sessione }: Props) {
  const [messaggi, setMessaggi] = useState<Messaggio[]>([]);
  const [input, setInput] = useState("");
  const [inviando, setInviando] = useState(false);
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [quadrante, setQuadrante] = useState<string | null>(null);
  const [stepCorrente, setStepCorrente] = useState("intro");
  const [scenarioOutput, setScenarioOutput] = useState<ScenarioOutput | null>(null);
  const [concluso, setConclusо] = useState(false);
  const [caricando, setCaricando] = useState(true);
  const [dichiarandoConclusо, setDichiarandoConclusо] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);
  const avviatoRef = useRef(false);

  const caricaScenario = useCallback(async () => {
    const res = await fetch(`/api/scenario-individuale?codicePartecipante=${partecipante.codice}`);
    if (!res.ok) return;
    const data = await res.json();
    const sc = data.scenario;
    setScenarioId(sc.id);
    setQuadrante(sc.quadrante);
    setStepCorrente(sc.stepCorrente);
    setConclusо(sc.concluso);
    setMessaggi(sc.messaggi || []);
    if (sc.narrativa || sc.titolo) {
      setScenarioOutput({
        narrativa: sc.narrativa,
        titolo: sc.titolo,
        minacce: sc.minacce ? JSON.parse(sc.minacce) : [],
        opportunita: sc.opportunita ? JSON.parse(sc.opportunita) : [],
      });
    }
    setCaricando(false);
  }, [partecipante.codice]);

  useEffect(() => {
    caricaScenario();
  }, [caricaScenario]);

  useEffect(() => {
    if (!scenarioId || !socket) return;

    socket.emit("entra_individuale", { scenarioIndividualeId: scenarioId });

    if (messaggi.length === 0 && !avviatoRef.current) {
      avviatoRef.current = true;
      socket.emit("messaggio_individuale", {
        scenarioIndividualeId: scenarioId,
        autore: "__sistema__",
        contenuto: "__avvia__",
      });
    }

    socket.on("nuovo_messaggio_individuale", (msg: Messaggio) => {
      setMessaggi((prev) => {
        if (prev.some((m) => m.id === msg.id)) return prev;
        return [...prev, msg];
      });
    });

    socket.on("step_individuale_aggiornato", ({ step }: { step: string }) => {
      setStepCorrente(step);
    });

    socket.on("scenario_individuale_aggiornato", ({ output }: { output: ScenarioOutput }) => {
      setScenarioOutput((prev) => ({ ...prev, ...output }));
    });

    return () => {
      socket.off("nuovo_messaggio_individuale");
      socket.off("step_individuale_aggiornato");
      socket.off("scenario_individuale_aggiornato");
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioId, socket]);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
  }, [messaggi]);

  async function invia() {
    if (!input.trim() || !scenarioId) return;
    setInviando(true);
    const testo = input.trim();
    setInput("");
    socket?.emit("messaggio_individuale", {
      scenarioIndividualeId: scenarioId,
      autore: partecipante.nome,
      contenuto: testo,
    });
    setInviando(false);
  }

  async function dichiaraConclusо() {
    if (!scenarioId) return;
    setDichiarandoConclusо(true);
    socket?.emit("individuale_concluso", {
      scenarioIndividualeId: scenarioId,
      sessioneId,
    });
    setConclusо(true);
    setDichiarandoConclusо(false);
  }

  if (caricando) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!scenarioId) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-gray-600">Non sei ancora stato assegnato a un gruppo.</p>
        <p className="text-gray-400 text-sm">Attendi che il facilitatore completi la fase di transizione.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Scenario Planning — Fase Individuale</h2>
        <p className="text-sm text-gray-500">Costruisci la tua visione personale prima del confronto con il gruppo</p>
      </div>

      {/* Bussola quadrante */}
      {quadrante && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col md:flex-row items-center gap-8 shadow-sm">
          <div className="flex-1 text-sm text-gray-700">
            <h3 className="text-base font-bold text-indigo-900 mb-2">
              Il tuo quadrante:{" "}
              <span className="text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded">
                {quadrante}
              </span>
            </h3>
            <p className="leading-relaxed">
              Esplorerai l&apos;incrocio tra{" "}
              <strong>{quadrante[0] === "+" ? (sessione.driver1PosPolo || "Alto") : (sessione.driver1NegPolo || "Basso")}</strong>{" "}
              e{" "}
              <strong>{quadrante[1] === "+" ? (sessione.driver2PosPolo || "Alto") : (sessione.driver2NegPolo || "Basso")}</strong>.
            </p>
            <p className="text-xs text-gray-400 mt-2 italic">
              La tua visione individuale verrà poi sintetizzata con quella degli altri membri del tuo gruppo.
            </p>
          </div>
          <div className="shrink-0 flex items-center justify-center p-2 pr-6">
            <QuadrantVisualizer
              quadrante={quadrante}
              d1Pos={sessione.driver1PosPolo || "Alto"}
              d1Neg={sessione.driver1NegPolo || "Basso"}
              d2Pos={sessione.driver2PosPolo || "Alto"}
              d2Neg={sessione.driver2NegPolo || "Basso"}
              size="md"
            />
          </div>
        </div>
      )}

      {/* Scenario in costruzione */}
      {scenarioOutput?.narrativa && (
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 space-y-2 text-sm">
          {scenarioOutput.titolo && (
            <h3 className="font-bold text-indigo-900">{scenarioOutput.titolo}</h3>
          )}
          <p className="text-indigo-800 leading-relaxed">{scenarioOutput.narrativa}</p>
        </div>
      )}

      {/* Chat */}
      <div
        className="bg-white border border-gray-200 rounded-xl overflow-hidden flex flex-col"
        style={{ height: "calc(100vh - 380px)", minHeight: "360px" }}
      >
        <div ref={chatRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {messaggi
            .filter((m) => m.autore !== "__sistema__")
            .map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.ruolo === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.ruolo === "assistant" ? "bg-indigo-100" : "bg-gray-100"
                }`}>
                  {msg.ruolo === "assistant" ? (
                    <Bot size={16} className="text-indigo-600" />
                  ) : (
                    <User size={16} className="text-gray-600" />
                  )}
                </div>
                <div className={`max-w-[75%] flex flex-col gap-1 ${msg.ruolo === "user" ? "items-end" : "items-start"}`}>
                  {msg.ruolo === "assistant" && (
                    <span className="text-xs text-indigo-500 font-medium px-1">Agente</span>
                  )}
                  <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.ruolo === "assistant"
                      ? "bg-indigo-50 text-gray-800 rounded-tl-sm"
                      : "bg-indigo-600 text-white rounded-tr-sm"
                  }`}>
                    {msg.contenuto}
                  </div>
                </div>
              </div>
            ))}
          {messaggi.length === 0 && (
            <div className="text-center py-8 text-gray-400 text-sm">
              L&apos;agente si sta connettendo...
            </div>
          )}
        </div>

        <div className="border-t border-gray-100 p-3">
          {concluso ? (
            <div className="text-center py-3">
              <p className="text-sm font-medium text-green-600">
                Lavoro individuale completato. Attendi che il facilitatore avvii la fase di gruppo.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && invia()}
                  placeholder="Scrivi la tua riflessione..."
                  disabled={inviando}
                  className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-50"
                />
                <Button onClick={invia} caricamento={inviando} disabled={!input.trim()} className="rounded-xl px-4">
                  <Send size={16} />
                </Button>
              </div>
              {stepCorrente === "concluso" && !concluso && (
                <Button
                  onClick={dichiaraConclusо}
                  caricamento={dichiarandoConclusо}
                  variante="secondary"
                  dimensione="sm"
                  className="w-full"
                >
                  Dichiara lavoro individuale concluso
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
