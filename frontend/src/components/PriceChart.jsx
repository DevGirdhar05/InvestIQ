import { useState, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from "recharts";
import { SkeletonBlock } from "./Skeleton";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Custom tooltip shown on hover
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div style={{
      background  : "white",
      border      : "1px solid #E5E7EB",
      borderRadius: "8px",
      padding     : "10px 14px",
      fontSize    : "12px",
      boxShadow   : "0 2px 8px rgba(0,0,0,0.08)"
    }}>
      <p style={{ margin: "0 0 6px", fontWeight: "500",
                  color: "#374151" }}>{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ margin: "2px 0",
                                      color: entry.color }}>
          {entry.name}: ₹{Number(entry.value).toFixed(2)}
        </p>
      ))}
    </div>
  );
}

export default function PriceChart({ ticker }) {
  const [chartData, setChartData] = useState([]);
  const [loading,   setLoading]   = useState(false);

    useEffect(() => {
        if (!ticker) return;
        setLoading(true);
        setChartData([]);

        fetch(`${BASE_URL}/prices/${ticker}?days=90`)
            .then(r => r.json())
            .then(data => {
            if (data.data) setChartData(data.data);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [ticker]);

  if (!ticker) return null;

  if (loading) {
    return (
      <div style={containerStyle}>
        <SkeletonBlock height="200px" borderRadius="8px" />
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h3 style={titleStyle}>
        Price Chart — {ticker.replace(".NS", "")}
      </h3>
      <p style={subtitleStyle}>
        Illustrative trend with SMA20 and SMA50 overlays
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData}
                   margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
          <XAxis
            dataKey  = "date"
            tick     = {{ fontSize: 10, fill: "#9CA3AF" }}
            interval = {9}
          />
          <YAxis
            tick       = {{ fontSize: 10, fill: "#9CA3AF" }}
            tickFormatter= {(v) => `₹${v.toLocaleString("en-IN")}`}
            width      = {70}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType  = "line"
            iconSize  = {12}
            wrapperStyle={{ fontSize: "12px" }}
          />
          <Line type="monotone" dataKey="Price"
                stroke="#1D4ED8" strokeWidth={2}
                dot={false} />
          <Line type="monotone" dataKey="SMA20"
                stroke="#F59E0B" strokeWidth={1.5}
                strokeDasharray="4 2" dot={false} />
          <Line type="monotone" dataKey="SMA50"
                stroke="#EF4444" strokeWidth={1.5}
                strokeDasharray="4 2" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

const containerStyle = {
  background  : "white",
  border      : "1px solid #E5E7EB",
  borderRadius: "12px",
  padding     : "20px",
};
const titleStyle = {
  margin    : "0 0 2px",
  fontSize  : "15px",
  fontWeight: "600",
  color     : "#111827",
};
const subtitleStyle = {
  margin    : "0 0 16px",
  fontSize  : "12px",
  color     : "#9CA3AF",
};