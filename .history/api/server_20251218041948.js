// api/server.js
const express = require("express");

const app = express();
const PORT = 3001;

app.use(express.json());

app.get("/", (req, res) => {
  res.json({
    status: "ok",
    message: "AI Backtest Platform API is running"
  });
});

app.listen(PORT, () => {
  console.log(`API running at http://localhost:${PORT}`);
});
