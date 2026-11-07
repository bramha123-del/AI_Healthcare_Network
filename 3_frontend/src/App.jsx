import { useState } from "react";

const FIELDS = [
  { name: "age", label: "Age", def: 50 },
  { name: "sex", label: "Sex (1 = male, 0 = female)", def: 1 },
  { name: "cp", label: "Chest pain type (0-3)", def: 0 },
  { name: "trestbps", label: "Resting blood pressure", def: 130 },
  { name: "chol", label: "Cholesterol", def: 240 },
  { name: "fbs", label: "Fasting sugar > 120 (1 = yes, 0 = no)", def: 0 },
  { name: "restecg", label: "Resting ECG (0-2)", def: 1 },
  { name: "thalach", label: "Max heart rate", def: 150 },
  { name: "exang", label: "Exercise chest pain (1 = yes, 0 = no)", def: 0 },
  { name: "oldpeak", label: "ST depression (oldpeak)", def: 1.0 },
  { name: "slope", label: "ST slope (0-2)", def: 1 },
  { name: "ca", label: "Major vessels (0-4)", def: 0 },
  { name: "thal", label: "Thal (0-3)", def: 2 },
];

const COLORS = {
  LOW: "bg-green-100 text-green-800 border-green-400",
  MEDIUM: "bg-yellow-100 text-yellow-800 border-yellow-400",
  HIGH: "bg-red-100 text-red-800 border-red-400",
};

export default function App() {
  const [form, setForm] = useState(
    Object.fromEntries(FIELDS.map((f) => [f.name, f.def]))
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const body = Object.fromEntries(
        Object.entries(form).map(([k, v]) => [k, Number(v)])
      );
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("Server error");
      setResult(await res.json());
    } catch (err) {
      setError("Could not get result. Is the backend running?");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-blue-700 text-center">
          AI Healthcare Network
        </h1>
        <p className="text-center text-gray-600 mb-6">
          Heart Risk Screening (demo, dummy data only)
        </p>

        <div className="bg-white rounded-xl shadow p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FIELDS.map((f) => (
            <label key={f.name} className="flex flex-col text-sm text-gray-700">
              {f.label}
              <input
                type="number"
                step="any"
                name={f.name}
                value={form[f.name]}
                onChange={handleChange}
                className="mt-1 border rounded-lg p-2"
              />
            </label>
          ))}
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full mt-4 bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Checking..." : "Check Risk"}
        </button>

        {error && <p className="mt-4 text-red-600 text-center">{error}</p>}

        {result && (
          <div className={`mt-6 border-2 rounded-xl p-5 ${COLORS[result.risk_level]}`}>
            <h2 className="text-2xl font-bold">
              {result.risk_level} RISK ({result.risk_percent}%)
            </h2>
            <p className="mt-3 whitespace-pre-line">{result.explanation}</p>
            <p className="mt-4 text-sm font-semibold">{result.disclaimer}</p>
          </div>
        )}
      </div>
    </div>
  );
}