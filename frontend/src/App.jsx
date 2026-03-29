import { useMemo, useState } from "react";

const defaultApiUrl =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1/analyze";

function formatValue(value) {
  if (value === null || value === undefined) return "N/A";
  if (Array.isArray(value)) return `[${value.join(", ")}]`;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(4);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function App() {
  const [apiUrl, setApiUrl] = useState(defaultApiUrl);
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState({ state: "idle", message: "" });
  const [result, setResult] = useState(null);

  const pillMeta = useMemo(() => {
    if (status.state === "loading") return { label: "Processing", color: "#bc7a00" };
    if (status.state === "success") return { label: "Success", color: "#207f4c" };
    if (status.state === "error") return { label: "Error", color: "#b23632" };
    return { label: "Idle", color: "#556170" };
  }, [status.state]);

  async function handleSubmit(event) {
    event.preventDefault();

    const endpoint = apiUrl.trim();
    if (!endpoint) {
      setStatus({ state: "error", message: "Provide an API endpoint." });
      return;
    }

    if (!file) {
      setStatus({ state: "error", message: "Choose an STL file first." });
      return;
    }

    setIsLoading(true);
    setStatus({ state: "loading", message: "Uploading and analyzing STL..." });

    try {
      const body = new FormData();
      body.append("file", file);

      const response = await fetch(endpoint, {
        method: "POST",
        body,
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = payload?.detail || `Request failed with status ${response.status}`;
        throw new Error(detail);
      }

      setResult(payload);
      setStatus({ state: "success", message: "Analysis complete." });
    } catch (error) {
      setStatus({
        state: "error",
        message: String(error?.message || "Unexpected error while analyzing file."),
      });
    } finally {
      setIsLoading(false);
    }
  }

  const geometry = result?.geometry || {};
  const validationIssues = result?.validation?.issues || [];

  const geometryEntries = [
    ["File", geometry.file_path],
    ["Faces", geometry.num_faces],
    ["Vertices", geometry.num_vertices],
    ["Surface Area", geometry.surface_area],
    ["Volume", geometry.volume],
    ["Watertight", geometry.is_watertight],
    ["Complexity", geometry.complexity_score],
    ["Bounding Min", geometry.bounding_box?.min],
    ["Bounding Max", geometry.bounding_box?.max],
  ];

  return (
    <>
      <div className="bg-orb orb-a" aria-hidden="true" />
      <div className="bg-orb orb-b" aria-hidden="true" />

      <main className="shell">
        <header className="hero reveal">
          <p className="kicker">React + Vite MVP</p>
          <h1>CAD Analysis Studio</h1>
          <p className="subtitle">
            Upload an STL file, send it to FastAPI, and inspect geometry plus validation insights.
          </p>
        </header>

        <section className="panel reveal" aria-label="Analyze form">
          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="field">
              <span>API Endpoint</span>
              <input
                type="url"
                value={apiUrl}
                onChange={(event) => setApiUrl(event.target.value)}
                autoComplete="off"
                required
              />
            </label>

            <label className="field file-field">
              <span>STL File</span>
              <input
                type="file"
                accept=".stl"
                required
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </label>

            <div className="actions">
              <button type="submit" disabled={isLoading}>
                {isLoading ? "Analyzing..." : "Analyze STL"}
              </button>
              <p id="status" role="status" aria-live="polite">
                {status.message}
              </p>
            </div>
          </form>
        </section>

        <section className="panel reveal" aria-label="Results">
          <div className="panel-head">
            <h2>Result</h2>
            <span className="pill" style={{ color: pillMeta.color }}>
              {pillMeta.label}
            </span>
          </div>

          {!result ? (
            <div className="empty-state">
              Submit a file to view parsed geometry and validation response.
            </div>
          ) : (
            <div className="result-root">
              <article className="result-card">
                <h3>Geometry</h3>
                <dl className="kv-list">
                  {geometryEntries.map(([key, value]) => (
                    <div key={key}>
                      <dt>{key}</dt>
                      <dd>{formatValue(value)}</dd>
                    </div>
                  ))}
                </dl>
              </article>

              <article className="result-card">
                <h3>Validation</h3>
                <ul className="issues-list">
                  {validationIssues.length === 0 ? (
                    <li>No issues reported.</li>
                  ) : (
                    validationIssues.map((issue, index) => (
                      <li key={`${issue.type}-${index}`}>
                        <span
                          className={`issue-tag issue-${String(issue.severity || "").toLowerCase()}`}
                        >
                          {issue.severity}
                        </span>
                        {`${issue.type}: ${issue.message}`}
                      </li>
                    ))
                  )}
                </ul>
              </article>

              <article className="result-card full-width">
                <h3>Raw API Response</h3>
                <pre className="json-block">{JSON.stringify(result, null, 2)}</pre>
              </article>
            </div>
          )}
        </section>
      </main>
    </>
  );
}
