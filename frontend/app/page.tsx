"use client";

import { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface Incident {
  incident_id: string;
  service: string;
  severity: "P1" | "P2" | "P3" | "P4";
  title: string;
  description: string;
  started_at: string;
  resolved_at: string | null;
  symptoms: string[];
}

interface Evidence {
  source: string;
  source_type: string;
  description: string;
  timestamp: string | null;
  observation: string | null;
  service: string | null;
  chunk_index: number | null;
}

interface InvestigationReport {
  status: string;
  incident_id: string | null;
  summary: string;
  timeline: string[];
  evidence: Evidence[];
  root_cause: {
    hypothesis: string;
    confidence: number;
    reasoning: string;
    claim_level: string;
  };
  recommendations: string[];
  uncertainties: string[];
}

interface InvestigationHistoryItem {
  id: number;
  incident_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  summary: string | null;
  confidence: number | null;
  claim_level: string | null;
  evidence: Evidence[];
}

export default function Home() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [investigating, setInvestigating] = useState<string | null>(null);
  const [investigationStatus, setInvestigationStatus] = useState<string | null>(
    null
  );
  const [investigationTools, setInvestigationTools] = useState<
    Record<string, string[]>
  >({});
  const [investigationHistory, setInvestigationHistory] = useState<
    InvestigationHistoryItem[]
  >([]);
  const [reports, setReports] = useState<
    Record<string, InvestigationReport>
  >({});
  const [expandedReports, setExpandedReports] = useState<
    Record<string, boolean>
  >({});
  const [error, setError] = useState<string | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [showStartupBanner, setShowStartupBanner] = useState(false);

  useEffect(() => {
    async function fetchIncidents() {
      const bannerTimer = setTimeout(() => {
        setShowStartupBanner(true);
      }, 1000);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/incidents`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch incidents");
        }

        const data = await response.json();
        setIncidents(data);

        const historyResults = await Promise.all(
          data.map(async (incident: Incident) => {
            try {
              const historyResponse = await fetch(
                `${API_BASE_URL}/api/v1/investigations/${incident.incident_id}/history`
              );

              if (!historyResponse.ok) {
                return [];
              }

              const historyData = await historyResponse.json();
              return historyData.investigations ?? [];
            } catch (historyError) {
              console.error(
                `Failed to fetch investigation history for ${incident.incident_id}:`,
                historyError
              );
              return [];
            }
          })
        );

        setInvestigationHistory(historyResults.flat());
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
        setError("Unable to load production incidents.");
      } finally {
        clearTimeout(bannerTimer);
        setInitialLoading(false);
        setShowStartupBanner(false);
      }
    }

    fetchIncidents();
  }, []);

  const getSeverityClasses = (severity: Incident["severity"]) => {
    switch (severity) {
      case "P1":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "P2":
        return "bg-orange-500/10 text-orange-400 border-orange-500/20";
      case "P3":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  const getClaimLevelClasses = (claimLevel: string) => {
    switch (claimLevel) {
      case "confirmed":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "strongly_supported":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "likely":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  const formatClaimLevel = (claimLevel: string) => {
    return claimLevel
      .replaceAll("_", " ")
      .replace(/\w/g, (letter) => letter.toUpperCase());
  };

  const getToolLabel = (tool: string) => {
    switch (tool) {
      case "search_logs":
        return "Application logs checked";
      case "query_metrics":
        return "Service metrics checked";
      case "search_deployments":
        return "Deployment history checked";
      case "search_knowledge":
        return "Knowledge base searched";
      default:
        return tool;
    }
  };

  const getInvestigationStatusText = (incidentId: string) => {
    if (investigating !== incidentId) {
      return null;
    }

    switch (investigationStatus) {
      case "collecting_evidence":
        return "Collecting evidence...";
      case "analyzing_evidence":
        return "Analyzing evidence...";
      case "completed":
        return "Completed";
      default:
        return "Starting investigation...";
    }
  };

  const toggleReport = (incidentId: string) => {
    setExpandedReports((current) => ({
      ...current,
      [incidentId]: !current[incidentId],
    }));
  };

  const investigateIncident = async (incident: Incident) => {
    const incidentId = incident.incident_id;

    setInvestigating(incidentId);
    setInvestigationStatus("Starting investigation...");
    setError(null);

    setReports((current) => {
      const next = { ...current };
      delete next[incidentId];
      return next;
    });

    setInvestigationTools((current) => ({
      ...current,
      [incidentId]: [],
    }));

    setExpandedReports((current) => ({
      ...current,
      [incidentId]: true,
    }));

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/investigations/${incidentId}/stream`,
        {
          method: "POST",
        }
      );

      if (!response.ok || !response.body) {
        throw new Error("Investigation failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }

          const event = JSON.parse(line);

          if (event.type === "status") {
            setInvestigationStatus(event.status);
          } else if (event.type === "tool") {
            setInvestigationTools((current) => ({
              ...current,
              [incidentId]: [
                ...(current[incidentId] ?? []),
                event.tool,
              ],
            }));
          } else if (event.type === "report") {
            setInvestigationStatus("completed");

            setReports((current) => ({
              ...current,
              [incidentId]: event.report,
            }));

            setExpandedReports((current) => ({
              ...current,
              [incidentId]: true,
            }));

            try {
              const historyResponse = await fetch(
                `${API_BASE_URL}/api/v1/investigations/${incidentId}/history`
              );

              if (historyResponse.ok) {
                const historyData = await historyResponse.json();
                setInvestigationHistory(historyData.investigations ?? []);
              }
            } catch (historyError) {
              console.error(
                "Failed to refresh investigation history:",
                historyError
              );
            }
          }
        }
      }
    } catch (error) {
      console.error("Investigation failed:", error);

      setError(
        "The investigation could not be completed. Please try again in a moment."
      );

      setInvestigationStatus(null);
    } finally {
      setInvestigating(null);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-6xl">
        <header className="mb-10">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
              <span className="text-lg font-bold">O</span>
            </div>

            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                OpsPilot
              </h1>

              <p className="text-sm text-slate-500">
                Agentic AI incident investigation platform
              </p>
            </div>
          </div>
        </header>

        {showStartupBanner && !error && investigating === null && (
          <div className="mb-5 flex items-center gap-3 rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-4">
            <span className="text-yellow-400">⚠</span>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-yellow-300">
                OpsPilot is starting up
              </p>
              <p className="mt-1 text-xs leading-5 text-yellow-200/60">
                The backend may take a few extra seconds to become available.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowStartupBanner(false)}
              className="text-sm text-yellow-200/50 transition hover:text-yellow-200"
              aria-label="Dismiss startup message"
            >
              ×
            </button>
          </div>
        )}

        <section>
          <div className="mb-5">
            <h2 className="text-xl font-semibold text-slate-100">
              Production Incidents
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Investigate production incidents using logs, metrics, deployments
              and operational knowledge.
            </p>
          </div>

          {error && investigating === null && (
            <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
              <span className="mt-0.5 text-red-400">✕</span>

              <p className="flex-1 text-sm text-red-400">{error}</p>
            </div>
          )}

          {initialLoading ? (
            <div className="flex min-h-[300px] items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-700 border-t-blue-400" />

                <p className="text-sm text-slate-500">
                  Loading incidents...
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {incidents.map((incident) => {
                const report = reports[incident.incident_id];

                const isInvestigating =
                  investigating === incident.incident_id;

                const hasReport = Boolean(report);

                const isExpanded =
                  expandedReports[incident.incident_id] ?? false;

                const tools =
                  investigationTools[incident.incident_id] ?? [];

                const history = investigationHistory.filter(
                  (item) => item.incident_id === incident.incident_id
                );

                return (
                  <article
                    key={incident.incident_id}
                    className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 shadow-lg shadow-black/10"
                  >
                    <div className="p-5">
                      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                        <div className="min-w-0">
                          <div className="mb-3 flex flex-wrap items-center gap-2">
                            <span className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300">
                              {incident.incident_id}
                            </span>

                            <span
                              className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getSeverityClasses(
                                incident.severity
                              )}`}
                            >
                              {incident.severity}
                            </span>

                            <span className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                              {incident.service}
                            </span>

                            <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                              {incident.resolved_at ? "Resolved" : "Open"}
                            </span>
                          </div>

                          <h3 className="text-base font-semibold text-slate-100">
                            {incident.title}
                          </h3>

                          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
                            {incident.description}
                          </p>

                          {incident.symptoms.length > 0 && (
                            <div className="mt-4">
                              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                                Symptoms
                              </p>

                              <div className="flex flex-wrap gap-2">
                                {incident.symptoms.map((symptom) => (
                                  <span
                                    key={symptom}
                                    className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-1.5 text-xs text-slate-400"
                                  >
                                    {symptom}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex shrink-0 items-center gap-2">
                          {hasReport && !isInvestigating && (
                            <button
                              type="button"
                              onClick={() =>
                                toggleReport(incident.incident_id)
                              }
                              className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white"
                            >
                              {isExpanded ? "Hide Report" : "View Report"}
                              <span className="ml-2">
                                {isExpanded ? "↑" : "↓"}
                              </span>
                            </button>
                          )}

                          <button
                            type="button"
                            disabled={isInvestigating}
                            onClick={() => investigateIncident(incident)}
                            className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {isInvestigating
                              ? "Investigating..."
                              : hasReport
                                ? "Investigate Again"
                                : "Investigate"}
                          </button>
                        </div>
                      </div>
                    </div>

                    {(isInvestigating || (hasReport && isExpanded)) && (
                      <div className="border-t border-slate-800 bg-slate-950/40 px-5 py-6">
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <h3 className="text-lg font-semibold text-slate-100">
                                Investigation Report
                              </h3>

                              <span className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                                {incident.incident_id}
                              </span>
                            </div>

                            <p className="mt-1 text-sm text-slate-500">
                              AI-generated incident investigation based on
                              collected evidence
                            </p>
                          </div>

                          <span
                            className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                              isInvestigating
                                ? "border border-blue-500/20 bg-blue-500/10 text-blue-400"
                                : "border border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                            }`}
                          >
                            {getInvestigationStatusText(
                              incident.incident_id
                            ) ?? "Completed"}
                          </span>
                        </div>

                        {(isInvestigating || tools.length > 0) && (
                          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
                            {isInvestigating && (
                              <div className="flex items-center gap-3">
                                <div className="h-2.5 w-2.5 animate-pulse rounded-full bg-blue-400" />

                                <p className="text-sm font-medium text-slate-300">
                                  {investigationStatus ===
                                  "collecting_evidence"
                                    ? "OpsPilot is collecting logs, metrics, deployments, and relevant knowledge..."
                                    : investigationStatus ===
                                        "analyzing_evidence"
                                      ? "OpsPilot is analyzing the collected evidence and determining the likely root cause..."
                                      : "OpsPilot is starting the investigation..."}
                                </p>
                              </div>
                            )}

                            {tools.length > 0 && (
                              <div
                                className={
                                  isInvestigating
                                    ? "mt-4 space-y-2"
                                    : "space-y-2"
                                }
                              >
                                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                                  Investigation Activity
                                </p>

                                {tools.map((tool, index) => (
                                  <div
                                    key={`${tool}-${index}`}
                                    className="flex items-center gap-2 text-sm text-slate-400"
                                  >
                                    <span className="text-emerald-400">
                                      ✓
                                    </span>

                                    <span>{getToolLabel(tool)}</span>
                                  </div>
                                ))}
                              </div>
                            )}

                            {isInvestigating && (
                              <p className="mt-3 text-xs leading-5 text-slate-500">
                                The report will appear here once the
                                investigation has collected enough evidence and
                                completed its analysis.
                              </p>
                            )}
                          </div>
                        )}

                        {report && (
                          <div className="mt-6 space-y-8">
                            <section>
                              <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                                Summary
                              </h4>

                              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
                                <p className="text-sm leading-7 text-slate-300">
                                  {report.summary}
                                </p>
                              </div>
                            </section>

                            <section>
                              <div className="mb-3 flex flex-wrap items-center gap-2">
                                <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                                  Root Cause
                                </h4>

                                <span
                                  className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getClaimLevelClasses(
                                    report.root_cause.claim_level
                                  )}`}
                                >
                                  {formatClaimLevel(
                                    report.root_cause.claim_level
                                  )}
                                </span>

                                <span className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300">
                                  {Math.round(
                                    report.root_cause.confidence * 100
                                  )}
                                  % confidence
                                </span>
                              </div>

                              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
                                <h5 className="text-sm font-semibold text-slate-200">
                                  {report.root_cause.hypothesis}
                                </h5>

                                <p className="mt-3 text-sm leading-7 text-slate-400">
                                  {report.root_cause.reasoning}
                                </p>
                              </div>
                            </section>

                            <section>
                              <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                                Evidence
                              </h4>

                              <div className="space-y-3">
                                {report.evidence.map((item, index) => (
                                  <div
                                    key={`${item.source}-${index}`}
                                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-5"
                                  >
                                    <div className="flex flex-wrap items-center justify-between gap-2">
                                      <div className="flex flex-wrap items-center gap-2">
                                        <span className="rounded-md bg-slate-800 px-2 py-1 text-xs font-medium text-slate-300">
                                          {item.source_type}
                                        </span>

                                        <span className="text-xs text-slate-500">
                                          {item.source}
                                        </span>
                                      </div>

                                      {item.timestamp && (
                                        <span className="text-xs text-slate-500">
                                          {item.timestamp}
                                        </span>
                                      )}
                                    </div>

                                    <div className="mt-3 flex flex-wrap gap-2">
                                      {item.service && (
                                        <span className="rounded-md border border-slate-700 bg-slate-950/60 px-2 py-1 text-xs text-slate-400">
                                          Service: {item.service}
                                        </span>
                                      )}

                                      {item.chunk_index !== null &&
                                        item.chunk_index !== undefined && (
                                          <span className="rounded-md border border-slate-700 bg-slate-950/60 px-2 py-1 text-xs text-slate-400">
                                            Knowledge chunk: {item.chunk_index}
                                          </span>
                                        )}
                                    </div>

                                    {item.observation && (
                                      <p className="mt-3 text-sm font-medium leading-6 text-slate-300">
                                        {item.observation}
                                      </p>
                                    )}

                                    <p className="mt-2 text-sm leading-6 text-slate-500">
                                      {item.description}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </section>

                            {report.timeline.length > 0 && (
                              <section>
                                <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                                  Timeline
                                </h4>

                                <div className="space-y-2">
                                  {report.timeline.map((event, index) => (
                                    <div
                                      key={`${event}-${index}`}
                                      className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3"
                                    >
                                      <p className="text-sm leading-6 text-slate-400">
                                        {event}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </section>
                            )}

                            {report.recommendations.length > 0 && (
                              <section>
                                <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                                  Recommendations
                                </h4>

                                <div className="space-y-2">
                                  {report.recommendations.map(
                                    (recommendation, index) => (
                                      <div
                                        key={`${recommendation}-${index}`}
                                        className="flex gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4"
                                      >
                                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-xs font-semibold text-blue-400">
                                          {index + 1}
                                        </span>

                                        <p className="text-sm leading-6 text-slate-400">
                                          {recommendation}
                                        </p>
                                      </div>
                                    )
                                  )}
                                </div>
                              </section>
                            )}

                            {report.uncertainties.length > 0 && (
                              <section>
                                <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                                  Uncertainties
                                </h4>

                                <div className="space-y-2">
                                  {report.uncertainties.map(
                                    (uncertainty, index) => (
                                      <div
                                        key={`${uncertainty}-${index}`}
                                        className="rounded-xl border border-yellow-500/10 bg-yellow-500/5 p-4"
                                      >
                                        <p className="text-sm leading-6 text-yellow-200/70">
                                          {uncertainty}
                                        </p>
                                      </div>
                                    )
                                  )}
                                </div>
                              </section>
                            )}

                            {history.length > 0 && (
                              <section>
                                <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                                  Investigation History
                                </h4>

                                <div className="space-y-3">
                                  {history.map((item) => (
                                    <div
                                      key={item.id}
                                      className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"
                                    >
                                      <div className="flex flex-wrap items-center justify-between gap-2">
                                        <div className="flex flex-wrap items-center gap-2">
                                          <span className="rounded-md bg-slate-800 px-2 py-1 text-xs font-medium text-slate-300">
                                            Investigation #{item.id}
                                          </span>

                                          <span
                                            className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getClaimLevelClasses(
                                              item.claim_level ?? ""
                                            )}`}
                                          >
                                            {item.claim_level
                                              ? formatClaimLevel(
                                                  item.claim_level
                                                )
                                              : "Unknown"}
                                          </span>

                                          {item.confidence !== null && (
                                            <span className="text-xs text-slate-500">
                                              {Math.round(
                                                item.confidence * 100
                                              )}
                                              % confidence
                                            </span>
                                          )}
                                        </div>

                                        <span className="text-xs text-slate-500">
                                          {new Date(
                                            item.started_at
                                          ).toLocaleString()}
                                        </span>
                                      </div>

                                      {item.summary && (
                                        <p className="mt-3 text-sm leading-6 text-slate-400">
                                          {item.summary}
                                        </p>
                                      )}

                                      <p className="mt-2 text-xs text-slate-600">
                                        {item.evidence.length} evidence item
                                        {item.evidence.length === 1 ? "" : "s"}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </section>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
