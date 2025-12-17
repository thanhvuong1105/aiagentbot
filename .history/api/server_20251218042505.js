// api/server.js
const express = require("express");
const { parsePineStrategy } = require("./agent/parsePine");

const app = express();
const PORT = 3001;

app.use(express.json());

// health check
app.get("/", (req, res) => {
  res.json({
    status: "ok",
    message: "AI Backtest Platform API is running"
  });
});

// AI Agent: parse Pine Script
app.post("/parse-pine", (req, res) => {
  const { pineCode } = req.body;

  if (!pineCode) {
    return res.status(400).json({
      error: "pineCode is required"
    });
  }

  const strategyJson = parsePineStrategy(pineCode);

  res.json({
    success: true,
    strategy: strategyJson
  });
});

app.listen(PORT, () => {
  console.log(`API running at http://localhost:${PORT}`);
});
