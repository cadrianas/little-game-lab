"use strict";

const { chromium } = require("playwright-core");

async function main() {
  const [browserPath, url, expected] = process.argv.slice(2);
  if (!browserPath || !url || !expected) {
    throw new Error("usage: headless_gate.cjs BROWSER URL EXPECTED_RESULT");
  }

  const browser = await chromium.launch({
    executablePath: browserPath,
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });

  try {
    const page = await browser.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(url, { waitUntil: "load", timeout: 15_000 });
    await page.waitForFunction(
      () => window.__BROWSER_GATE__?.status !== "running",
      null,
      { timeout: 120_000 }
    );

    const result = await page.evaluate(() => window.__BROWSER_GATE__);
    const summary = await page.locator("#summary").innerText();
    if (pageErrors.length) {
      throw new Error("browser page errors: " + pageErrors.join("; "));
    }
    if (result.status !== "passed" || result.failures.length) {
      throw new Error(
        "browser gate failed: " + (result.failures.join("; ") || summary)
      );
    }
    if (summary !== expected) {
      throw new Error(`unexpected browser summary: ${summary}`);
    }
    console.log(summary);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
