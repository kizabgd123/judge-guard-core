import axios from "axios";
import { useEffect, useState, useRef, useCallback } from "react";
import StatusPulse from "./components/StatusPulse";
import VerdictCard from "./components/VerdictCard";

function App() {
  const [config, setConfig] = useState(null);
  const [lastVerdict, setLastVerdict] = useState(null);
  const [connected, setConnected] = useState(false);
  const prevDataRef = useRef(null);

  const fetchData = useCallback(async () => {
    // ⚡ Bolt: Skip fetching when tab is hidden to save battery and network.
    // Extremely defensive guards for CI environments like browser-workers.
    try {
      if (typeof document !== 'undefined' && document !== null) {
        if (typeof document.visibilityState === 'string' && document.visibilityState !== "visible") {
          return;
        }
      }
    } catch (e) {
      // If document access throws, we assume we are in a non-browser environment
      // and continue with the fetch as visibility doesn't apply.
    }

    try {
      const timestamp = new Date().getTime();
      const response = await axios.get(`/app_config.json?t=${timestamp}`);
      const newData = response.data;
      const newDataStr = JSON.stringify(newData);

      // ⚡ Bolt: Only update state if data has actually changed
      if (newDataStr !== prevDataRef.current) {
        setConfig(newData);
        if (newData.last_verdict) {
          setLastVerdict(newData.last_verdict);
        }
        setConnected(true);
        prevDataRef.current = newDataStr;
      } else if (!connected) {
        // Recovery of connection without data change
        setConnected(true);
      }
    } catch (error) {
      if (connected) {
        console.error("Connection lost", error);
        setConnected(false);
        prevDataRef.current = null;
      }
    }
  }, [connected]);

  useEffect(() => {
    // Poll every 500ms for "Real-time" feel
    const interval = setInterval(fetchData, 500);

    // ⚡ Bolt: Fetch immediately on visibility change (coming back to tab)
    const handleVisibilityChange = () => {
      try {
        if (typeof document !== 'undefined' && document !== null && document.visibilityState === "visible") {
          fetchData();
        }
      } catch (e) {
        // Ignore visibility errors in weird environments
      }
    };

    // Extremely robust guard for environments with throwing proxies or incomplete implementations
    let hasAddEventListener = false;
    try {
      hasAddEventListener = typeof document !== 'undefined' &&
                            document !== null &&
                            typeof document.addEventListener === 'function';

      if (hasAddEventListener) {
        document.addEventListener("visibilitychange", handleVisibilityChange);
      }
    } catch (e) {
      console.warn("Could not setup visibilitychange listener", e);
    }

    // Initial fetch - ⚡ Bolt: wrap in async to avoid lint error
    const initialFetch = async () => {
      await fetchData();
    };
    initialFetch();

    return () => {
      clearInterval(interval);
      try {
        if (hasAddEventListener && typeof document.removeEventListener === 'function') {
          document.removeEventListener("visibilitychange", handleVisibilityChange);
        }
      } catch (e) {
        // Ignore cleanup errors
      }
    };
  }, [fetchData]);

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
