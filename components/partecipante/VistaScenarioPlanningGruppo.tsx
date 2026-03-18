"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
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
  };
}

export function VistaScenarioPlanningGruppo({ partecipante, sessioneId, socket, sessione }: Props) {
  const [messaggi, setMessaggi] = useState<Messaggio[]>([]);
  const [input, setInput] = useState("");
  const [inviando, setInviando] = useState(false);
  const [gruppoId, setGruppoId] = useState<string | null>(null);
  const [stepCorrente, setStepCorrente] = useState("intro");
  const [scenarioOutput, setScenarioOutput] = useState<ScenarioOutput | null>(null);
  const [pannelloAperto, setPannelloAperto] = useState(false);
  const [caricando, setCaricando] = useState(true);
  const chatRef = useRef<HTMLDivElement>(null);

  const caricaGruppo = useCallback(async () => {
    const res = await fetch(`/api/gruppi?codicePartecipante=${partecipante.codice}`);
    if (!res.ok) return;
    const data = await res.json();
    setGruppoId(data.gruppo.id);
    setStepCorrente(data.gruppo.stepCorrente);
    setMessaggi(data.gruppo.messaggi || []);
    if (data.gruppo.scenarioOutput) setScenarioOutput(data.gruppo.scenarioOutput);
    setCaricando(false);
  }, [partecipante.codice]);

  useEffect(() => {
    caricaGruppo();
  }, [caricaGruppo]);

  // Socket: avvio agente all'ingresso nel gruppo
  useEffect(() => {
    if (!gruppoId || !socket) return;
    socket.emit("entra_gruppo", { gruppoId });

    // Avvia agente se non ci sono messaggi
    if (messaggi.length === 0) {
      socket.emit("messaggio_utente", {
        gruppoId,
        autore: "__sistema__",
        contenuto: "__avvia__",
      });
    }

    socket.on("nuovo_messaggio", (msg: Messaggio) => {
      setMessaggi((prev) => {
        if (prev.some((m) => m.id === msg.id)) return prev;
        return [...prev, msg];
      });
    });

    socket.on("step_aggiornato", ({ step }: { step: string }) => {
      setStepCorrente(step);
    });

    socket.on("scenario_aggiornato", ({ output }: { output: ScenarioOutput }) => {
      setScenarioOutput((prev) => ({ ...prev, ...output }));
    });

    return () => {
      socket.off("nuovo_messaggio");
      socket.off("step_aggiornato");
      socket.off("scenario_aggiornato");
    };
  }, [gruppoId, socket, messaggi.length]);

  // Scroll automatico
  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
  }, [messaggi]);

  async function invia() {
    if (!input.trim() || !gruppoId) return;
    setInviando(true);
    const testo = input.trim();
    setInput("");
    socket?.emit("messaggio_utente", {
      gruppoId,
      autore: partecipante.nome,
      contenuto: testo,
    });
    setInviando(false);
  }

  if (caricando) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!gruppoId) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-gray-600">Non sei ancora stato assegnato a un gruppo.</p>
        <p className="text-gray-400 text-sm">Attendi che il facilitatore completi la fase di transizione.</p>
      </div>
    );
  }

  const completato = stepCorrente === "concluso";

  return (
    <div className="space-y-4">
      {/* Header step */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Scenario Planning</h2>
          <p className="text-sm text-gray-500">Lavorate insieme seguendo la guida dell&apos;agente</p>
        </div>
        <div className="flex items-center gap-2">
          {scenarioOutput?.titolo && (
            <Badge variante={completato ? "verde" : "default"}>
              {scenarioOutput.titolo}
            </Badge>
          )}
          {(scenarioOutput?.narrativa || (scenarioOutput?.minacce && scenarioOutput.minacce.length > 0)) && (
            <button
              onClick={() => setPannelloAperto(!pannelloAperto)}
              className="text-xs text-indigo-600 hover:underline"
            >
              {pannelloAperto ? "Nascondi scenario" : "Vedi scenario"}
            </button>
          )}
        </div>
      </div>

      {/* Pannello scenario in costruzione */}
      {pannelloAperto && scenarioOutput && (
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 space-y-3 text-sm">
          {scenarioOutput.titolo && (
            <h3 className="font-bold text-indigo-900">{scenarioOutput.titolo}</h3>
          )}
          {scenarioOutput.narrativa && (
            <p className="text-indigo-800 leading-relaxed">{scenarioOutput.narrativa}</p>
          )}
          {scenarioOutput.minacce && scenarioOutput.minacce.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-indigo-600 mb-1">Minacce identificate</p>
              <ul className="space-y-1">
                {scenarioOutput.minacce.map((m, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-red-700">
                    <span className="mt-0.5">▸</span> {m}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {scenarioOutput.opportunita && scenarioOutput.opportunita.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-indigo-600 mb-1">Opportunità identificate</p>
              <ul className="space-y-1">
                {scenarioOutput.opportunita.map((o, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-green-700">
                    <span className="mt-0.5">▸</span> {o}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Chat */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden flex flex-col" style={{ height: "calc(100vh - 320px)", minHeight: "400px" }}>
        {/* Messaggi */}
        <div ref={chatRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {messaggi
            .filter((m) => m.autore !== "__sistema__")
            .map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.ruolo === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.ruolo === "assistant" ? "bg-indigo-100" : "bg-gray-100"
                }`}>
                  {msg.ruolo === "assistant" ? (
                    <Bot size={16} className="text-indigo-600" />
                  ) : (
                    <User size={16} className="text-gray-600" />
                  )}
                </div>
                {/* Bolla */}
                <div className={`max-w-[75%] ${msg.ruolo === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                  {msg.ruolo === "user" && (
                    <span className="text-xs text-gray-400 px-1">{msg.autore}</span>
                  )}
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

        {/* Input */}
        <div className={`border-t border-gray-100 p-3 ${completato ? "bg-gray-50" : ""}`}>
          {completato ? (
            <p className="text-center text-sm text-green-600 py-1">
              Scenario completato! Attendete le istruzioni del facilitatore.
            </p>
          ) : (
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && invia()}
                placeholder="Scrivi un messaggio..."
                disabled={inviando}
                className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-50"
              />
              <Button
                onClick={invia}
                caricamento={inviando}
                disabled={!input.trim()}
                className="rounded-xl px-4"
              >
                <Send size={16} />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
