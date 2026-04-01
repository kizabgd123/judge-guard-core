
export default function StatusPulse({ active }) {
  return (
    <div
      role="status"
      aria-label={`Connection Status: ${active ? "Live" : "Offline"}`}
      className={`fixed top-4 right-4 flex items-center gap-3 px-4 py-2 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full shadow-lg min-h-[44px] min-w-[120px] justify-center transition-all duration-300`}
    >
      <div
        className={`w-3 h-3 rounded-full ${active ? "bg-green-500 motion-safe:animate-ping" : "bg-gray-400"}`}
      ></div>
      <span className="text-sm font-bold tracking-widest font-sans">
        {active ? "LIVE" : "OFFLINE"}
      </span>
    </div>
  );
}
