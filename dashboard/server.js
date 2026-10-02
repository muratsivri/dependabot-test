/*
 * !!! BILEREK GUVENSIZ ORNEK PANEL !!!
 *
 * Airflow DAG'larini listeleyen kucuk bir Express paneli. CodeQL'in
 * JavaScript kodunda neler yakaladigini gostermek icin yazildi.
 * Uretimde KULLANMAYIN, internete ACMAYIN.
 *
 * Beklenen CodeQL bulgulari (endpoint -> kural):
 *   /greet     -> js/reflected-xss            (girdi HTML'e kacissiz)
 *   /proxy     -> js/request-forgery          (SSRF: URL kullanicidan)
 *   /settings  -> js/prototype-pollution      (lodash.merge + girdi)
 *   /whoami    -> js/jwt-missing-verification (imza dogrulanmiyor)
 */

const express = require("express");
const axios = require("axios");
const jwt = require("jsonwebtoken");
const _ = require("lodash");
const moment = require("moment");
const minimist = require("minimist");

const app = express();
app.use(express.json());

const DAGS = [
  { dagId: "hello_world", schedule: "@daily", lastRun: "2026-10-01T09:00:00Z" },
  { dagId: "etl_example", schedule: "@hourly", lastRun: "2026-10-02T21:00:00Z" },
  { dagId: "insecure_example", schedule: null, lastRun: null },
];

const settings = { theme: "dark", refreshSeconds: 30 };

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/dags", (req, res) => {
  res.json(
    DAGS.map((d) => ({
      ...d,
      lastRunHuman: d.lastRun ? moment(d.lastRun).fromNow() : "hic calismadi",
    }))
  );
});

app.get("/greet", (req, res) => {
  // KOTU: Girdi HTML'e kacis yapilmadan yaziliyor (XSS).
  res.send(`<h1>Merhaba ${req.query.name}</h1>`);
});

app.get("/proxy", async (req, res) => {
  // KOTU: Sunucu, kullanicinin verdigi herhangi bir adrese istek atiyor (SSRF).
  try {
    const response = await axios.get(req.query.url, { timeout: 3000 });
    res.send(response.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});

app.post("/settings", (req, res) => {
  // KOTU: Kullanici JSON'u dogrudan nesneye birlestiriliyor (prototype pollution).
  _.merge(settings, req.body);
  res.json(settings);
});

app.get("/whoami", (req, res) => {
  // KOTU: JWT imzasi dogrulanmadan icerigine guveniliyor.
  const payload = jwt.decode(req.query.token);
  res.json({ user: payload && payload.sub });
});

if (require.main === module) {
  const args = minimist(process.argv.slice(2));
  const port = Number(args.port) || 3000;
  app.listen(port, () => console.log(`Panel http://localhost:${port} adresinde`));
}

module.exports = app;
