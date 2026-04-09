import "dotenv/config";
import { createServer } from "http";
import { parse } from "url";
import next from "next";
import { Server as SocketIOServer } from "socket.io";
import { prisma } from "./lib/prisma";
import { eseguiStepAgente, eseguiStepAgenteIndividuale } from "./lib/agent";

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const httpServer = createServer((req, res) => {
    const parsedUrl = parse(req.url!, true);
    handle(req, res, parsedUrl);
  });

  const io = new SocketIOServer(httpServer, {
    cors: { origin: "*", methods: ["GET", "POST"] },
  });

  // Coda sequenziale per gruppo: evita chiamate API concorrenti per lo stesso gruppo
  const gruppoQueue = new Map<string, Promise<void>>();

  function accodaPerGruppo(gruppoId: string, fn: () => Promise<void>): void {
    const prev = gruppoQueue.get(gruppoId) ?? Promise.resolve();
    const next = prev
      .then(fn)
      .catch((err) => console.error("[Agente] errore in coda:", err))
      .finally(() => {
        if (gruppoQueue.get(gruppoId) === next) gruppoQueue.delete(gruppoId);
      });
    gruppoQueue.set(gruppoId, next);
  }

  // Mappa: sessioneId → socket rooms
  io.on("connection", (socket) => {
    console.log("[Socket] connesso:", socket.id);

    // Partecipante o facilitatore entra in una stanza
    socket.on("entra_sessione", ({ sessioneId, ruolo }: { sessioneId: string; ruolo: string }) => {
      socket.join(`sessione:${sessioneId}`);
      socket.join(`sessione:${sessioneId}:${ruolo}`);
      console.log(`[Socket] ${socket.id} entra in sessione:${sessioneId} come ${ruolo}`);
    });

    // Membro di gruppo entra nella stanza del gruppo
    socket.on("entra_gruppo", ({ gruppoId }: { gruppoId: string }) => {
      socket.join(`gruppo:${gruppoId}`);
      console.log(`[Socket] ${socket.id} entra in gruppo:${gruppoId}`);
    });

    // Messaggio utente nel gruppo
    socket.on(
      "messaggio_utente",
      async ({
        gruppoId,
        autore,
        contenuto,
      }: {
        gruppoId: string;
        autore: string;
        contenuto: string;
      }) => {
        // Messaggi reali (non di sistema): salva e broadcast immediatamente
        if (autore !== "__sistema__") {
          const msg = await prisma.messaggioChat.create({
            data: { gruppoId, autore, ruolo: "user", contenuto },
          });
          io.to(`gruppo:${gruppoId}`).emit("nuovo_messaggio", {
            id: msg.id,
            autore: msg.autore,
            ruolo: msg.ruolo,
            contenuto: msg.contenuto,
            createdAt: msg.createdAt,
          });
        }

        // Accoda risposta agente: sequenziale per gruppo, nessuna chiamata concorrente
        accodaPerGruppo(gruppoId, async () => {
          // Deduplicazione __avvia__: salta se l'agente ha già risposto
          if (autore === "__sistema__" && contenuto === "__avvia__") {
            const count = await prisma.messaggioChat.count({
              where: { gruppoId, ruolo: "assistant" },
            });
            if (count > 0) return;
          }

          const risposta = await eseguiStepAgente(gruppoId, contenuto);
          if (!risposta) return;

          // Salva e broadcast risposta agente
          const msgAgente = await prisma.messaggioChat.create({
            data: { gruppoId, autore: "agente", ruolo: "assistant", contenuto: risposta.testo },
          });
          io.to(`gruppo:${gruppoId}`).emit("nuovo_messaggio", {
            id: msgAgente.id,
            autore: "agente",
            ruolo: "assistant",
            contenuto: msgAgente.contenuto,
            createdAt: msgAgente.createdAt,
          });

          // Aggiorna step se cambiato
          if (risposta.nuovoStep) {
            await prisma.gruppo.update({
              where: { id: gruppoId },
              data: { stepCorrente: risposta.nuovoStep },
            });
            io.to(`gruppo:${gruppoId}`).emit("step_aggiornato", {
              gruppoId,
              step: risposta.nuovoStep,
            });
            const gruppo = await prisma.gruppo.findUnique({ where: { id: gruppoId } });
            if (gruppo) {
              io.to(`sessione:${gruppo.sessioneId}:facilitatore`).emit("gruppo_aggiornato", {
                gruppoId,
                step: risposta.nuovoStep,
              });
            }
          }

          // Aggiorna scenario output se presente
          if (risposta.outputAggiornato) {
            const { narrativa, titolo, minacce, opportunita, keyPointsData } =
              risposta.outputAggiornato;
            await prisma.scenarioOutput.upsert({
              where: { gruppoId },
              create: {
                gruppoId,
                narrativa: narrativa ?? null,
                titolo: titolo ?? null,
                minacce: minacce ? JSON.stringify(minacce) : null,
                opportunita: opportunita ? JSON.stringify(opportunita) : null,
                keyPointsData: keyPointsData ? JSON.stringify(keyPointsData) : null,
              },
              update: {
                narrativa: narrativa ?? undefined,
                titolo: titolo ?? undefined,
                minacce: minacce ? JSON.stringify(minacce) : undefined,
                opportunita: opportunita ? JSON.stringify(opportunita) : undefined,
                keyPointsData: keyPointsData ? JSON.stringify(keyPointsData) : undefined,
              },
            });
            io.to(`gruppo:${gruppoId}`).emit("scenario_aggiornato", {
              gruppoId,
              output: risposta.outputAggiornato,
            });
          }
        });
      }
    );

    // Partecipante entra nella stanza individuale
    socket.on("entra_individuale", ({ scenarioIndividualeId }: { scenarioIndividualeId: string }) => {
      socket.join(`individuale:${scenarioIndividualeId}`);
    });

    // Messaggio individuale (fase scenario_planning_individuale)
    socket.on(
      "messaggio_individuale",
      async ({
        scenarioIndividualeId,
        autore,
        contenuto,
      }: {
        scenarioIndividualeId: string;
        autore: string;
        contenuto: string;
      }) => {
        if (autore !== "__sistema__") {
          const msg = await prisma.messaggioChatIndividuale.create({
            data: { scenarioIndividualeId, autore, ruolo: "user", contenuto },
          });
          socket.emit("nuovo_messaggio_individuale", {
            id: msg.id, autore: msg.autore, ruolo: msg.ruolo,
            contenuto: msg.contenuto, createdAt: msg.createdAt,
          });
        }

        accodaPerGruppo(`ind:${scenarioIndividualeId}`, async () => {
          if (autore === "__sistema__" && contenuto === "__avvia__") {
            const count = await prisma.messaggioChatIndividuale.count({
              where: { scenarioIndividualeId, ruolo: "assistant" },
            });
            if (count > 0) return;
          }

          const risposta = await eseguiStepAgenteIndividuale(scenarioIndividualeId, contenuto);
          if (!risposta) return;

          const msgAgente = await prisma.messaggioChatIndividuale.create({
            data: { scenarioIndividualeId, autore: "agente", ruolo: "assistant", contenuto: risposta.testo },
          });
          io.to(`individuale:${scenarioIndividualeId}`).emit("nuovo_messaggio_individuale", {
            id: msgAgente.id, autore: "agente", ruolo: "assistant",
            contenuto: msgAgente.contenuto, createdAt: msgAgente.createdAt,
          });

          if (risposta.nuovoStep) {
            await prisma.scenarioIndividuale.update({
              where: { id: scenarioIndividualeId },
              data: { stepCorrente: risposta.nuovoStep },
            });
            socket.emit("step_individuale_aggiornato", { step: risposta.nuovoStep });
          }

          if (risposta.outputAggiornato) {
            const { narrativa, titolo, minacce, opportunita, keyPointsData } = risposta.outputAggiornato;
            await prisma.scenarioIndividuale.update({
              where: { id: scenarioIndividualeId },
              data: {
                narrativa: narrativa ?? undefined,
                titolo: titolo ?? undefined,
                minacce: minacce ? JSON.stringify(minacce) : undefined,
                opportunita: opportunita ? JSON.stringify(opportunita) : undefined,
                keyPointsData: keyPointsData ? JSON.stringify(keyPointsData) : undefined,
              },
            });
            socket.emit("scenario_individuale_aggiornato", { output: risposta.outputAggiornato });
          }
        });
      }
    );

    // Partecipante dichiara lavoro individuale concluso
    socket.on(
      "individuale_concluso",
      async ({ scenarioIndividualeId, sessioneId }: { scenarioIndividualeId: string; sessioneId: string }) => {
        await prisma.scenarioIndividuale.update({
          where: { id: scenarioIndividualeId },
          data: { concluso: true, stepCorrente: "concluso" },
        });
        const totale = await prisma.scenarioIndividuale.count({ where: { sessioneId } });
        const conclusi = await prisma.scenarioIndividuale.count({ where: { sessioneId, concluso: true } });
        io.to(`sessione:${sessioneId}:facilitatore`).emit("individuale_completato", {
          scenarioIndividualeId, conclusi, totale,
        });
      }
    );

    // Evento voto completato da partecipante
    socket.on(
      "voto_completato",
      ({ sessioneId, partecipanteId }: { sessioneId: string; partecipanteId: string }) => {
        io.to(`sessione:${sessioneId}:facilitatore`).emit("voto_completato", { partecipanteId });
      }
    );

    // Facilitatore aggiunge fenomeno
    socket.on(
      "fenomeno_aggiunto",
      ({ sessioneId, fenomeno }: { sessioneId: string; fenomeno: object }) => {
        io.to(`sessione:${sessioneId}`).emit("fenomeno_aggiunto", { fenomeno });
      }
    );

    // Facilitatore approva fenomeno
    socket.on(
      "fenomeno_approvato",
      ({ sessioneId, fenomenoId }: { sessioneId: string; fenomenoId: string }) => {
        io.to(`sessione:${sessioneId}`).emit("fenomeno_approvato", { fenomenoId });
      }
    );

    // Facilitatore cambia stato sessione
    socket.on("stato_aggiornato", ({ sessioneId, stato }: { sessioneId: string; stato: string }) => {
      io.to(`sessione:${sessioneId}`).emit("stato_aggiornato", { stato });
    });

    socket.on("disconnect", () => {
      console.log("[Socket] disconnesso:", socket.id);
    });
  });

  const porta = parseInt(process.env.PORT || "3000", 10);
  httpServer.listen(porta, () => {
    console.log(`> Server avviato su http://localhost:${porta}`);
  });
});
