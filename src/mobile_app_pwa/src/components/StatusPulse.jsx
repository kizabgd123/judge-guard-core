
export default function StatusPulse({ active }) {
  return (
    <div
      role="status"
      aria-label={`Connection Status: ${active ? "Live" : "Offline"}`}
      className={`fixed top-4 right-4 flex items-center gap-2`}
    >
      <div
        className={`w-3 h-3 rounded-full ${active ? "bg-green-500 motion-safe:animate-ping" : "bg-gray-500"}`}
      ></div>
      <span className="text-xs font-mono opacity-50">
        {active ? "LIVE" : "OFFLINE"}
      </span>
    </div>
  );
}
