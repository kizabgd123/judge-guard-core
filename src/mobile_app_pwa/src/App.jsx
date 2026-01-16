import { useEffect, useState } from "react";
import "./App.css";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";

function App() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Poll for config changes every 2 seconds (simple "live" reload)
    const fetchConfig = async () => {
      try {
        const res = await fetch("/app_config.json");
        const data = await res.json();
        setConfig(data);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch app config:", error);
      }
    };

    fetchConfig();
    const interval = setInterval(fetchConfig, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading Agent Config...</div>;
  if (!config) return <div>Error loading config.</div>;

  return (
    <>
      <div>
        <a href="https://vitejs.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>

      {/* Dynamic Content from Agent */}
      <h1>{config.title || "Antigravity Mobile"}</h1>

      <div className="card">
        <p style={{ fontSize: "1.2rem", fontWeight: "bold" }}>
          {config.content}
        </p>

        {/* Render dynamic components if any */}
        {config.components &&
          config.components.map((comp, idx) => (
            <div
              key={idx}
              className="dynamic-component"
              style={{
                margin: "10px",
                padding: "10px",
                border: "1px solid #ccc",
              }}
            >
              <h3>{comp.type}</h3>
              <p>{comp.payload}</p>
            </div>
          ))}
      </div>

      <p className="read-the-docs">Powered by Antigravity Agents</p>
    </>
  );
}

export default App;
