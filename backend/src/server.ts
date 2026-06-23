// src/server.ts
import fs from "fs";
import path from "path";
import express from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import { config } from "./config";
import apiRouter from "./router";
import { logger } from "./lib/logger";
import { errorHandler } from "./errors/errorHandler";
import { ensureSolverRunning } from "./lib/solverLauncher";

const app = express();
const PORT = config.PORT;
const staticDir = config.STATIC_DIR;
const serveFrontend = fs.existsSync(path.join(staticDir, "index.html"));

app.use(pinoHttp({ logger }));
app.use(cors());
app.use(express.json());

app.use("/api/v1", apiRouter);

if (serveFrontend) {
  app.use(express.static(staticDir));

  app.get(/^(?!\/api).*/, (_req, res) => {
    res.sendFile(path.join(staticDir, "index.html"));
  });

  logger.info({ staticDir }, "Serving frontend from static directory");
}

app.use(errorHandler);

const bootstrap = async () => {
  await ensureSolverRunning();

  app.listen(PORT, () => {
    logger.info({ port: PORT, serveFrontend }, "Server started");
  });
};

bootstrap().catch((err) => {
  logger.error({ err }, "Failed to start server");
  process.exit(1);
});
