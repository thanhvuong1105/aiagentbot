// api/server.js
const express = require("express");
const { parsePineStrategy } = require("./agent/parsePine");
const { spawn } = require("child_process");

const app = express();
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`API running at http://localhost:${PORT}`);
});


app.use(express.json());

// health check
app.get("/", (req, res) => {
  res.json({
    status: "ok",
    message: "AI Backtest Platform API is running"
  });
});

// parse Pine Script
app.post("/parse-pine", (req, res) => {
  const { pineCode } = req.body;

  if (!pineCode) {
    return res.status(400).json({ error: "pineCode is required" });
  }

  const strategyJson = parsePineStrategy(pineCode);

  res.json({
    success: true,
    strategy: strategyJson
  });
});

// 🚀 RUN BACKTEST (NodeJS → Python)
app.post("/run-backtest", (req, res) => {
  const { strategy } = req.body;

  if (!strategy) {
    return res.status(400).json({ error: "strategy is required" });
  }

  const python = spawn("python3", ["engine/backtest_engine.py"]);

  let output = "";
  let errorOutput = "";

  python.stdout.on("data", (data) => {
    output += data.toString();
  });

  python.stderr.on("data", (data) => {
    errorOutput += data.toString();
  });

  python.on("close", (code) => {
    if (code !== 0) {
      return res.status(500).json({
        error: "Python backtest failed",
        detail: errorOutput
      });
    }

    try {
      const result = JSON.parse(output);
      res.json({
        success: true,
        result
      });
    } catch (e) {
      res.status(500).json({
        error: "Invalid JSON from Python",
        raw: output
      });
    }
  });

  // gửi strategy sang Python qua stdin
  python.stdin.write(JSON.stringify(strategy));
  python.stdin.end();
});

app.listen(PORT, () => {
  console.log(`API running at http://localhost:${PORT}`);
});
