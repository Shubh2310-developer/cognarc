// =============================================================
// COGNARC — Structured Logger (TypeScript)
// packages/logger/src/index.ts
// Per §17 — no console.log in committed code. Use this logger.
// =============================================================

type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  service?: string;
  [key: string]: unknown;
}

interface LoggerOptions {
  service?: string;
  pretty?: boolean; // human-readable in development
}

function formatEntry(entry: LogEntry, pretty: boolean): string {
  if (pretty) {
    const { level, message, timestamp, ...rest } = entry;
    const icon = { debug: "🔍", info: "ℹ️", warn: "⚠️", error: "❌" }[level];
    const extras = Object.keys(rest).length > 0 ? ` ${JSON.stringify(rest)}` : "";
    return `${icon} [${timestamp}] ${level.toUpperCase()} — ${message}${extras}`;
  }
  return JSON.stringify(entry);
}

function createLogger(options: LoggerOptions = {}) {
  const { service, pretty = process.env["NODE_ENV"] === "development" } = options;

  function log(level: LogLevel, message: string, context: Record<string, unknown> = {}): void {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...(service ? { service } : {}),
      ...context,
    };
    const output = formatEntry(entry, pretty);
    if (level === "error") {
      process.stderr.write(output + "\n");
    } else {
      process.stdout.write(output + "\n");
    }
  }

  return {
    debug: (message: string, context?: Record<string, unknown>) => log("debug", message, context),
    info: (message: string, context?: Record<string, unknown>) => log("info", message, context),
    warn: (message: string, context?: Record<string, unknown>) => log("warn", message, context),
    error: (message: string, context?: Record<string, unknown>) => log("error", message, context),
  };
}

// Default singleton logger
export const logger = createLogger({ service: "cognarc" });

// Factory for service-specific loggers
export { createLogger };
export type { LogLevel, LogEntry, LoggerOptions };
