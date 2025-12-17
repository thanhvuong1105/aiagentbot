import express from "express";
import rateLimit from "express-rate-limit";
import { spawn } from "child_process";
import { parsePineStrategy } from "./agent/parsePine.js";

const app = express();
const PORT = process.env.PORT || 3002;

// ===== Middleware =====
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
});

app.use(limiter);
app.use(express.json({ limit: "200kb" }));

app.use((req, _, next) => {
  console.log(new Date().toISOString(), req.method, req.url);
  next();
});

// ===== Health check =====
app.get("/", (req, res) => {
  res.json({
    status: "ok",
    message: "AI Backtest Platform API is running",
  });
});

// ===== Parse Pine =====
app.post("/parse-pine", (req, res) => {
  const { pineCode } = req.body;
  if (!pineCode) {
    return res.status(400).json({ error: "pineCode is required" });
  }

  const strategy = parsePineStrategy(pineCode);
  res.json({ success: true, strategy });
});

// ===== Run Backtest =====
app.post("/run-backtest", (req, res) => {
  const { strategy } = req.body;
  if (!strategy) {
    return res.status(400).json({ error: "strategy is required" });
  }

  const python = spawn("python3", ["engine/backtest_engine.py"]);

  let output = "";
  let errorOutput = "";

  python.stdout.on("data", (d) => (output += d.toString()));
  python.stderr.on("data", (d) => (errorOutput += d.toString()));

  python.on("close", (code) => {
    if (code !== 0) {
      return res.status(500).json({
        error: "Python backtest failed",
        detail: errorOutput,
      });
    }

    try {
      res.json({ success: true, result: JSON.parse(output) });
    } catch {
      res.status(500).json({ error: "Invalid JSON from Python", raw: output });
    }
  });

  python.stdin.write(JSON.stringify(strategy));
  python.stdin.end();
});

// ===== START SERVER (DUY NHẤT 1 LẦN) =====
app.listen(PORT, () => {
  console.log(`API running on port ${PORT}`);
});
