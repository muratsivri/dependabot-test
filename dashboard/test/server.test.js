// Panelin temel islevlerinin testleri (Node'un yerlesik test araci ile).
const { test, before, after } = require("node:test");
const assert = require("node:assert");
const jwt = require("jsonwebtoken");
const app = require("../server");

let server;
let baseUrl;

before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once("listening", resolve));
  baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

test("health", async () => {
  const res = await fetch(`${baseUrl}/health`);
  assert.deepStrictEqual(await res.json(), { status: "ok" });
});

test("dags listesi", async () => {
  const dags = await (await fetch(`${baseUrl}/dags`)).json();
  assert.strictEqual(dags.length, 3);
  assert.strictEqual(dags[2].lastRunHuman, "hic calismadi");
});

test("greet", async () => {
  const text = await (await fetch(`${baseUrl}/greet?name=Murat`)).text();
  assert.match(text, /Merhaba Murat/);
});

test("settings", async () => {
  const res = await fetch(`${baseUrl}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshSeconds: 60 }),
  });
  assert.strictEqual((await res.json()).refreshSeconds, 60);
});

test("whoami", async () => {
  const token = jwt.sign({ sub: "murat" }, "test-anahtari");
  const body = await (await fetch(`${baseUrl}/whoami?token=${token}`)).json();
  assert.deepStrictEqual(body, { user: "murat" });
});
