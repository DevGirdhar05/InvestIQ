export default function SentimentBadge({ data, loading }) {
  if (loading || !data) return null;

  const score = data.sentiment_3d || 0;
  const color = score > 0.1  ? "#16A34A"
              : score < -0.1 ? "#DC2626"
              : "#D97706";

  const barWidth = Math.abs(score) * 100;
  const barSide  = score >= 0 ? "left" : "right";

  return (
    <div style={containerStyle}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: "10px" }}>
        <h4 style={{ margin: 0, fontSize: "13px", fontWeight: "500",
                     color: "#374151" }}>
          News Sentiment
        </h4>
        <span style={{
          fontSize     : "12px",
          fontWeight   : "500",
          color        : color,
          padding      : "2px 8px",
          background   : color + "20",
          borderRadius : "10px",
        }}>
          {data.sentiment_label}
        </span>
      </div>

      {/* Sentiment bar */}
      <div style={{ position: "relative", height: "6px",
                    background: "#F3F4F6", borderRadius: "3px",
                    marginBottom: "8px" }}>
        <div style={{
          position    : "absolute",
          top         : 0,
          height      : "100%",
          width       : `${barWidth}%`,
          [barSide]   : "50%",
          background  : color,
          borderRadius: "3px",
        }} />
        <div style={{
          position  : "absolute",
          left      : "50%",
          top       : "-3px",
          width     : "2px",
          height    : "12px",
          background: "#D1D5DB",
        }} />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between",
                    fontSize: "11px", color: "#9CA3AF" }}>
        <span>Negative</span>
        <span>Neutral</span>
        <span>Positive</span>
      </div>

      <div style={{ marginTop: "12px", display: "grid",
                    gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
        {[
          ["1-day",   data.sentiment_1d],
          ["3-day",   data.sentiment_3d],
          ["7-day",   data.sentiment_7d],
          ["Momentum",data.sentiment_momentum],
        ].map(([label, val]) => (
          <div key={label} style={{ fontSize: "12px" }}>
            <span style={{ color: "#6B7280" }}>{label}: </span>
            <span style={{
              fontWeight: "500",
              color: val > 0.05 ? "#16A34A" : val < -0.05 ? "#DC2626" : "#374151"
            }}>
              {val >= 0 ? "+" : ""}{Number(val).toFixed(3)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

const containerStyle = {
  background  : "white",
  border      : "1px solid #E5E7EB",
  borderRadius: "12px",
  padding     : "16px",
};