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

  const python = spawn("python3", ["engine/backtest_engine.py"], {
    stdio: ["pipe", "pipe", "pipe"],
  });

  let stdout = "";
  let stderr = "";

  python.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });

  python.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  python.on("close", (code) => {
    if (code !== 0) {
      console.error("Python stderr:", stderr);
      return res.status(500).json({
        error: "Python backtest failed",
        detail: stderr,
      });
    }

    try {
      const parsed = JSON.parse(stdout.trim());

      // 🔍 DEBUG QUAN TRỌNG
      console.log("BACKTEST RESULT KEYS:", Object.keys(parsed));
      console.log("SUMMARY:", parsed.summary);

      return res.json({
        success: true,
        result: parsed, // ⬅️ TRẢ NGUYÊN KHỐI
      });
    } catch (err) {
      console.error("Raw python output:", stdout);
      return res.status(500).json({
        error: "Invalid JSON from Python",
        raw: stdout,
      });
    }
  });

  // gửi strategy sang Python
  python.stdin.write(JSON.stringify(strategy));
  python.stdin.end();
});

// ===== START SERVER =====
app.listen(PORT, () => {
  console.log(`API running on port ${PORT}`);
});
