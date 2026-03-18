import { createServer } from "http";
import { parse } from "url";
import next from "next";
import { Server as SocketIOServer } from "socket.io";
import { prisma } from "./lib/prisma";
import { eseguiStepAgente } from "./lib/agent";

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
        // Salva messaggio utente
        const msg = await prisma.messaggioChat.create({
          data: { gruppoId, autore, ruolo: "user", contenuto },
        });

        // Broadcast al gruppo
        io.to(`gruppo:${gruppoId}`).emit("nuovo_messaggio", {
          id: msg.id,
          autore: msg.autore,
          ruolo: msg.ruolo,
          contenuto: msg.contenuto,
          createdAt: msg.createdAt,
        });

        // Esegui risposta agente
        try {
          const risposta = await eseguiStepAgente(gruppoId, contenuto);
          if (risposta) {
            // Salva messaggio agente
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

              // Notifica facilitatore
              const gruppo = await prisma.gruppo.findUnique({
                where: { id: gruppoId },
              });
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
          }
        } catch (err) {
          console.error("[Agente] errore:", err);
        }
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
