import axios from "axios";
import { useEffect, useState } from "react";
import StatusPulse from "./components/StatusPulse";
import VerdictCard from "./components/VerdictCard";

function App() {
  const [config, setConfig] = useState(null);
  const [lastVerdict, setLastVerdict] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch from the public file written by Python
        const response = await axios.get("/app_config.json?t=" + list_time()); // bust cache
        setConfig(response.data);
        if (response.data.last_verdict) {
          setLastVerdict(response.data.last_verdict);
        }
        setConnected(true);
      } catch (error) {
        console.error("Connection lost", error);
        setConnected(false);
      }
    };

    const list_time = () => new Date().getTime();

    // Poll every 500ms for "Real-time" feel
    const interval = setInterval(fetchData, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen w-screen bg-black text-white overflow-hidden font-sans select-none">
      <StatusPulse active={connected} />

      {lastVerdict ? (
        <VerdictCard verdict={lastVerdict} />
      ) : (
        <div className="flex flex-col items-center justify-center h-full opacity-30">
          <h1 className="text-2xl font-bold tracking-widest">JUDGE GUARD</h1>
          <p className="mt-2 text-sm">WAITING FOR ACTION...</p>
        </div>
      )}

      {/* Debug/Info Footer */}
      <div className="fixed bottom-4 w-full text-center text-xs opacity-20 font-mono pointer-events-none">
        ANTIGRAVITY BRIDGE v2.0 • {config?.title || "Disconnect"}
      </div>
    </div>
  );
}

export default App;
