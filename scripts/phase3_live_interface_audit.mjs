import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import AxeBuilder from "@axe-core/playwright";
import { chromium, firefox } from "playwright";

const reportRoot = path.resolve(process.env.REPORT_ROOT || "phase3-live-interface-baseline");
const screenshotRoot = path.join(reportRoot, "screenshots");
const targets = [
  { id: "atlas-home", label: "Atlas Systems home", url: "https://atlas-systems.uk/" },
  { id: "atlas-systems", label: "Systems directory", url: "https://atlas-systems.uk/systems/" },
  { id: "atlas-proof-chain", label: "Proof Chain", url: "https://atlas-systems.uk/lab/proof-chain/" },
  { id: "status", label: "Status", url: "https://status.atlas-systems.uk/" },
  { id: "ramone", label: "Ramone", url: "https://ramone.atlas-systems.uk/" },
  { id: "api-docs", label: "Public API Docs", url: "https://api.atlas-systems.uk/v1/docs" },
  { id: "cv", label: "CV", url: "https://cv.atlas-systems.uk/" },
];
const profiles = [
  { id: "chromium-desktop", browser: "chromium", viewport: { width: 1440, height: 900 }, performance: true },
  { id: "chromium-mobile", browser: "chromium", viewport: { width: 375, height: 812 }, performance: false },
  { id: "firefox-desktop", browser: "firefox", viewport: { width: 1440, height: 900 }, performance: false },
];
const headerNames = [
  "cache-control",
  "content-security-policy",
  "content-type",
  "permissions-policy",
  "referrer-policy",
  "strict-transport-security",
  "x-content-type-options",
  "x-frame-options",
];

await fs.mkdir(screenshotRoot, { recursive: true });

async function inspectHeaders(target) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(`${target.url}${target.url.includes("?") ? "&" : "?"}phase3-audit=${Date.now()}`, {
      headers: {
        "cache-control": "no-cache",
        pragma: "no-cache",
        "user-agent": "Atlas-Systems-Phase3-Audit/1.0",
      },
      redirect: "follow",
      signal: controller.signal,
    });
    const headers = Object.fromEntries(
      headerNames.map((name) => [name, response.headers.get(name)]),
    );
    await response.body?.cancel();
    return {
      ok: response.ok,
      status: response.status,
      final_url: response.url,
      headers,
      missing_security_headers: [
        "content-security-policy",
        "permissions-policy",
        "referrer-policy",
        "strict-transport-security",
        "x-content-type-options",
      ].filter((name) => !headers[name]),
    };
  } catch (error) {
    return { ok: false, error: String(error), headers: {}, missing_security_headers: headerNames };
  } finally {
    clearTimeout(timeout);
  }
}

function summarizeViolations(results) {
  const impactCounts = { critical: 0, serious: 0, moderate: 0, minor: 0, unknown: 0 };
  for (const violation of results.violations) {
    impactCounts[violation.impact || "unknown"] += violation.nodes.length;
  }
  return {
    violation_count: results.violations.length,
    affected_node_count: results.violations.reduce((sum, item) => sum + item.nodes.length, 0),
    impact_counts: impactCounts,
    violations: results.violations.slice(0, 20).map((item) => ({
      id: item.id,
      impact: item.impact,
      help: item.help,
      help_url: item.helpUrl,
      nodes: item.nodes.slice(0, 8).map((node) => ({ target: node.target, summary: node.failureSummary })),
    })),
  };
}

async function inspectPage(browserType, profile, target) {
  const browser = await browserType.launch({ headless: true });
  const context = await browser.newContext({
    viewport: profile.viewport,
    reducedMotion: "reduce",
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  page.on("requestfailed", (request) => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText || "unknown" });
  });

  try {
    const response = await page.goto(
      `${target.url}${target.url.includes("?") ? "&" : "?"}phase3-browser=${Date.now()}`,
      { waitUntil: "domcontentloaded", timeout: 45_000 },
    );
    await page.waitForTimeout(2_000);
    const screenshot = path.join(screenshotRoot, `${target.id}-${profile.id}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    const accessibility = summarizeViolations(await new AxeBuilder({ page }).analyze());
    const documentState = await page.evaluate(() => ({
      title: document.title,
      lang: document.documentElement.lang,
      h1_count: document.querySelectorAll("h1").length,
      main_count: document.querySelectorAll("main").length,
      horizontal_overflow_px: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
      active_element: document.activeElement?.tagName || null,
    }));
    let performance = null;
    if (profile.performance) {
      performance = await page.evaluate(() => {
        const navigation = performance.getEntriesByType("navigation")[0];
        const resources = performance.getEntriesByType("resource");
        const fcp = performance.getEntriesByName("first-contentful-paint")[0];
        const sum = (field) => resources.reduce((total, entry) => total + (Number(entry[field]) || 0), 0);
        return {
          response_start_ms: Math.round(navigation?.responseStart || 0),
          dom_content_loaded_ms: Math.round(navigation?.domContentLoadedEventEnd || 0),
          load_event_ms: Math.round(navigation?.loadEventEnd || 0),
          first_contentful_paint_ms: Math.round(fcp?.startTime || 0),
          request_count: resources.length + 1,
          transfer_size_bytes: Math.round((navigation?.transferSize || 0) + sum("transferSize")),
          encoded_body_bytes: Math.round((navigation?.encodedBodySize || 0) + sum("encodedBodySize")),
          decoded_body_bytes: Math.round((navigation?.decodedBodySize || 0) + sum("decodedBodySize")),
        };
      });
    }
    return {
      ok: Boolean(response?.ok()),
      status: response?.status() || null,
      final_url: page.url(),
      screenshot: path.relative(reportRoot, screenshot),
      document: documentState,
      accessibility,
      performance,
      console_errors: consoleErrors.slice(0, 20),
      page_errors: pageErrors.slice(0, 20),
      failed_requests: failedRequests.slice(0, 30),
    };
  } catch (error) {
    return {
      ok: false,
      error: String(error),
      console_errors: consoleErrors.slice(0, 20),
      page_errors: pageErrors.slice(0, 20),
      failed_requests: failedRequests.slice(0, 30),
    };
  } finally {
    await context.close();
    await browser.close();
  }
}

const report = {
  schema_version: "atlas-systems/phase3-live-interface-baseline/v1",
  generated_at: new Date().toISOString(),
  budget_policy: "measurement-only; blocking thresholds are deferred until owner review",
  targets: [],
};

for (const target of targets) {
  const record = { ...target, headers: await inspectHeaders(target), profiles: {} };
  for (const profile of profiles) {
    const browserType = profile.browser === "firefox" ? firefox : chromium;
    record.profiles[profile.id] = await inspectPage(browserType, profile, target);
  }
  report.targets.push(record);
}

await fs.writeFile(path.join(reportRoot, "baseline.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");

const markdown = [
  "# Atlas Systems Phase 3 live interface baseline",
  "",
  `Generated: ${report.generated_at}`,
  "",
  "No blocking performance thresholds are applied in this baseline. Measurements are evidence for a later budget decision.",
  "",
  "| Surface | HTTP | Missing security headers | Chromium desktop axe nodes | FCP | Load | Requests | Transfer |",
  "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
];
for (const target of report.targets) {
  const desktop = target.profiles["chromium-desktop"];
  const perf = desktop.performance || {};
  markdown.push(
    `| ${target.label} | ${target.headers.status ?? "error"} | ${target.headers.missing_security_headers?.join(", ") || "none"} | ${desktop.accessibility?.affected_node_count ?? "error"} | ${perf.first_contentful_paint_ms ?? "n/a"} ms | ${perf.load_event_ms ?? "n/a"} ms | ${perf.request_count ?? "n/a"} | ${perf.transfer_size_bytes ?? "n/a"} B |`,
  );
}
markdown.push("", "## Notes", "");
for (const target of report.targets) {
  const critical = Object.values(target.profiles).reduce(
    (sum, profile) => sum + (profile.accessibility?.impact_counts?.critical || 0),
    0,
  );
  const serious = Object.values(target.profiles).reduce(
    (sum, profile) => sum + (profile.accessibility?.impact_counts?.serious || 0),
    0,
  );
  const overflow = Object.values(target.profiles).filter(
    (profile) => (profile.document?.horizontal_overflow_px || 0) > 0,
  ).length;
  markdown.push(`- **${target.label}:** critical axe nodes ${critical}; serious axe nodes ${serious}; profiles with horizontal overflow ${overflow}.`);
}
await fs.writeFile(path.join(reportRoot, "baseline.md"), `${markdown.join("\n")}\n`, "utf8");

const unreachable = report.targets.filter(
  (target) => !target.headers.ok || Object.values(target.profiles).some((profile) => !profile.ok),
);
if (unreachable.length > 0) {
  console.error(`Audit completed with unreachable profiles: ${unreachable.map((item) => item.id).join(", ")}`);
}
console.log(`Wrote Phase 3 baseline for ${report.targets.length} public surfaces to ${reportRoot}`);
