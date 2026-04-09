"use client";
import { useState, useEffect } from "react";
import { GripVertical, Plus, CheckCircle, Send, Info } from "lucide-react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Button } from "@/components/ui/Button";
import type { Socket } from "socket.io-client";

interface Fenomeno {
  id: string;
  testo: string;
  descrizione?: string | null;
}

interface Sessione {
  id: string;
  fenomeni: Fenomeno[];
}

interface Partecipante {
  id: string;
  nome: string;
  codice: string;
}

interface Props {
  sessione: Sessione;
  partecipante: Partecipante;
  socket: Socket | null;
}

function zonaStile(posizione: number, totale: number) {
  const terzo = Math.ceil(totale / 3);
  if (posizione <= terzo) return {
    border: "border-l-green-400",
    badge: "text-green-700 bg-green-50",
  };
  if (posizione <= terzo * 2) return {
    border: "border-l-amber-400",
    badge: "text-amber-700 bg-amber-50",
  };
  return {
    border: "border-l-gray-300",
    badge: "text-gray-500 bg-gray-100",
  };
}

function ItemSortable({ fenomeno, posizione, totale }: { fenomeno: Fenomeno; posizione: number; totale: number }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: fenomeno.id,
  });
  const [mostraDesc, setMostraDesc] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  const stile = zonaStile(posizione, totale);

  return (
    <div ref={setNodeRef} style={style} className="relative">
      <div className={`flex items-center gap-2 bg-white border border-gray-200 border-l-4 ${stile.border} rounded-lg px-3 py-1.5 shadow-sm transition-colors hover:border-r-gray-300`}>
        <span className={`text-xs font-bold w-6 text-center shrink-0 rounded px-1 py-0.5 ${stile.badge}`}>
          {posizione}
        </span>
        <button
          {...attributes}
          {...listeners}
          className="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing shrink-0"
        >
          <GripVertical size={15} />
        </button>
        <p className="flex-1 min-w-0 text-sm text-gray-800 truncate">{fenomeno.testo}</p>
        {fenomeno.descrizione && (
          <button
            onPointerDown={(e) => e.stopPropagation()}
            onClick={() => setMostraDesc((v) => !v)}
            className={`shrink-0 transition-colors ${mostraDesc ? "text-indigo-500" : "text-gray-300 hover:text-indigo-400"}`}
          >
            <Info size={14} />
          </button>
        )}
      </div>
      {mostraDesc && fenomeno.descrizione && (
        <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-gray-800 text-white text-xs rounded-lg px-3 py-2 shadow-lg leading-relaxed">
          {fenomeno.descrizione}
        </div>
      )}
    </div>
  );
}

export function VistaHorizonScanningPartecipante({ sessione, partecipante, socket }: Props) {
  const [items, setItems] = useState<Fenomeno[]>(sessione.fenomeni);
  const [votato, setVotato] = useState(false);
  const [inviando, setInviando] = useState(false);
  const [nuovoFenomeno, setNuovoFenomeno] = useState("");
  const [aggiungi, setAggiungi] = useState(false);
  const [aggiungendo, setAggiungendo] = useState(false);

  // Aggiorna lista quando sessione cambia
  useEffect(() => {
    setItems((prev) => {
      const nuovi = sessione.fenomeni.filter((f) => !prev.some((p) => p.id === f.id));
      return [...prev, ...nuovi];
    });
  }, [sessione.fenomeni]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((i) => i.id === active.id);
        const newIndex = items.findIndex((i) => i.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }

  async function inviaVoto() {
    setInviando(true);
    const ranking = items.map((f, i) => ({ fenomenoId: f.id, posizione: i + 1 }));

    await fetch("/api/voti", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codicePartecipante: partecipante.codice, ranking }),
    });

    socket?.emit("voto_completato", {
      sessioneId: sessione.id,
      partecipanteId: partecipante.id,
    });

    setVotato(true);
    setInviando(false);
  }

  async function handleAggiungiFenomeno() {
    if (!nuovoFenomeno.trim()) return;
    setAggiungendo(true);

    const res = await fetch("/api/fenomeni", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        testo: nuovoFenomeno.trim(),
        sessioneId: sessione.id,
        codicePartecipante: partecipante.codice,
      }),
    });

    const fenomeno = await res.json();
    // Aggiunge localmente anche se non ancora approvato (per visibilità)
    setItems((prev) => [...prev, fenomeno]);
    socket?.emit("fenomeno_aggiunto", { sessioneId: sessione.id, fenomeno });
    setNuovoFenomeno("");
    setAggiungi(false);
    setAggiungendo(false);
  }

  if (votato) {
    return (
      <div className="text-center py-16 space-y-4">
        <div className="w-16 h-16 bg-green-100 rounded-full mx-auto flex items-center justify-center">
          <CheckCircle size={32} className="text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900">Voto inviato!</h2>
        <p className="text-gray-500 text-sm max-w-sm mx-auto">
          Hai completato l&apos;Horizon Scanning. Attendi che il facilitatore avvii la fase di Scenario Planning.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Horizon Scanning</h2>
        <p className="text-gray-500 text-sm">
          Ordina i fenomeni dal più al meno rilevante rispetto alla domanda di ricerca. Trascina per riordinare.
        </p>
      </div>

      {/* Legenda zone */}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-green-400 inline-block" /> Alta priorità</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-amber-400 inline-block" /> Media</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-gray-300 inline-block" /> Bassa priorità</span>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-1.5">
            {items.map((f, i) => (
              <ItemSortable key={f.id} fenomeno={f} posizione={i + 1} totale={items.length} />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Aggiungi fenomeno */}
      {!aggiungi ? (
        <button
          onClick={() => setAggiungi(true)}
          className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-xl py-3 text-sm text-gray-400 hover:border-indigo-300 hover:text-indigo-500 transition-colors"
        >
          <Plus size={16} />
          Aggiungi un fenomeno non presente
        </button>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <p className="text-sm font-medium text-gray-700">Nuovo fenomeno</p>
          <input
            value={nuovoFenomeno}
            onChange={(e) => setNuovoFenomeno(e.target.value)}
            placeholder="Descrivi il fenomeno o trend..."
            className="w-full text-sm rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            autoFocus
            onKeyDown={(e) => e.key === "Enter" && handleAggiungiFenomeno()}
          />
          <div className="flex gap-2">
            <Button
              onClick={handleAggiungiFenomeno}
              caricamento={aggiungendo}
              dimensione="sm"
            >
              <Send size={13} className="mr-1" /> Proponi
            </Button>
            <Button
              variante="ghost"
              dimensione="sm"
              onClick={() => { setAggiungi(false); setNuovoFenomeno(""); }}
            >
              Annulla
            </Button>
          </div>
          <p className="text-xs text-gray-400">Il facilitatore potrà approvare o rifiutare il fenomeno proposto</p>
        </div>
      )}

      {/* Invio voto */}
      <div className="sticky bottom-4 pt-2">
        <Button
          onClick={inviaVoto}
          caricamento={inviando}
          dimensione="lg"
          className="w-full shadow-lg"
        >
          Conferma il mio ranking
        </Button>
      </div>
    </div>
  );
}
