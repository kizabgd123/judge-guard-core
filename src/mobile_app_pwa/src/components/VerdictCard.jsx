import { Activity, ShieldAlert, ShieldCheck } from "lucide-react";

export default function VerdictCard({ verdict }) {
  if (!verdict) return null;

  const { status, action, reason, timestamp } = verdict;
  const isPassed = status === "PASSED";
  const isPending = status === "PENDING";

  if (isPending) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 bg-gray-900 text-blue-400 animate-pulse">
        <Activity size={64} className="mb-4" />
        <h2 className="text-2xl font-bold">JUDGE IS THINKING</h2>
        <p className="mt-2 text-center text-gray-400">{action}</p>
        <p className="mt-4 text-sm text-gray-500">{reason}</p>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center justify-center h-full p-8 transition-colors duration-500 ${isPassed ? "bg-green-900 text-green-100" : "bg-red-900 text-red-100"}`}
    >
      {isPassed ? <ShieldCheck size={96} /> : <ShieldAlert size={96} />}

      <h1 className="mt-6 text-4xl font-black uppercase tracking-widest">
        {status}
      </h1>

      <div className="mt-8 text-center">
        <p className="text-lg font-medium opacity-80 uppercase text-xs tracking-wider mb-2">
          Action
        </p>
        <p className="text-xl font-bold">{action}</p>
      </div>

      <div className="mt-8 text-center bg-black/20 p-4 rounded-lg backdrop-blur-sm w-full">
        <p className="font-mono text-sm opacity-90">{reason}</p>
      </div>

      <p className="mt-8 text-xs opacity-50 font-mono">{timestamp}</p>
    </div>
  );
}
