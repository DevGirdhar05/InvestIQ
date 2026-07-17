export default function SignalCard({ data, loading }) {
  if (loading) {
    return (
      <div style={cardStyle}>
        <div style={loadingStyle}>Analysing signals...</div>
      </div>
    );
  }

  if (!data) return null;

  const prob       = Math.round(data.probability_up * 100);
  const isPositive = prob > 50;
  const probColor  = prob > 65 ? "#16A34A"
                   : prob > 50 ? "#65A30D"
                   : prob > 35 ? "#DC2626"
                   : "#B91C1C";

  const confidenceColor = {
    high  : "#16A34A",
    medium: "#D97706",
    low   : "#DC2626",
  }[data.confidence] || "#6B7280";

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between",
                      alignItems: "flex-start" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "600",
                         color: "#111827" }}>
              {data.company_name}
            </h2>
            <p style={{ margin: "2px 0 0", fontSize: "13px",
                        color: "#6B7280" }}>
              {data.ticker} · {data.date} · {data.horizon_days}-day outlook
            </p>
          </div>
          <span style={{
            padding      : "4px 10px",
            borderRadius : "12px",
            fontSize     : "12px",
            fontWeight   : "500",
            background   : confidenceColor + "20",
            color        : confidenceColor,
            textTransform: "uppercase",
          }}>
            {data.confidence} confidence
          </span>
        </div>
      </div>

      {/* Probability gauge */}
      <div style={{ textAlign: "center", marginBottom: "24px" }}>
        <div style={{ fontSize: "56px", fontWeight: "700",
                      color: probColor, lineHeight: 1 }}>
          {prob}%
        </div>
        <div style={{ fontSize: "14px", color: "#6B7280", marginTop: "4px" }}>
          probability of rising in {data.horizon_days} trading days
        </div>

        {/* Progress bar */}
        <div style={{
          height      : "8px",
          background  : "#F3F4F6",
          borderRadius: "4px",
          margin      : "12px auto",
          maxWidth    : "280px",
          overflow    : "hidden",
        }}>
          <div style={{
            height      : "100%",
            width       : `${prob}%`,
            background  : probColor,
            borderRadius: "4px",
            transition  : "width 0.5s ease",
          }} />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between",
                      maxWidth: "280px", margin: "0 auto",
                      fontSize: "12px", color: "#9CA3AF" }}>
          <span>0% (Strong sell)</span>
          <span>100% (Strong buy)</span>
        </div>
      </div>

      {/* SHAP features */}
      <div>
        <h3 style={{ fontSize: "14px", fontWeight: "500",
                     color: "#374151", marginBottom: "12px" }}>
          Key signals driving this prediction
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {data.top_features.slice(0, 5).map((feature, i) => (
            <FeatureRow key={i} feature={feature} />
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <p style={{ fontSize: "11px", color: "#9CA3AF",
                  marginTop: "16px", marginBottom: 0 }}>
        Based on {data.training_samples} training samples.
        Predictions are probabilistic — not financial advice.
      </p>
    </div>
  );
}

function FeatureRow({ feature }) {
  const isBullish  = feature.direction === "bullish";
  const barColor   = isBullish ? "#16A34A" : "#DC2626";
  const barWidth   = Math.min(Math.abs(feature.shap_value) * 300, 100);

  const LABELS = {
    sma_50          : "50-day Moving Average",
    sma_20          : "20-day Moving Average",
    macd_hist       : "MACD Momentum",
    macd_signal     : "MACD Signal",
    macd            : "MACD Trend",
    price_vs_sma50  : "Price vs SMA50",
    price_vs_sma20  : "Price vs SMA20",
    rsi             : "RSI Momentum",
    rsi_normalized  : "RSI Momentum",
    bb_pct          : "Bollinger %B",
    bb_width        : "Bollinger Width",
    volume_ratio    : "Volume Ratio",
    ema_20          : "EMA 20",
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      <span style={{
        fontSize     : "11px",
        fontWeight   : "500",
        color        : isBullish ? "#16A34A" : "#DC2626",
        width        : "16px",
        textAlign    : "center",
      }}>
        {isBullish ? "▲" : "▼"}
      </span>
      <span style={{ fontSize: "13px", color: "#374151",
                     width: "170px", flexShrink: 0 }}>
        {LABELS[feature.feature] || feature.feature}
      </span>
      <div style={{ flex: 1, height: "6px", background: "#F3F4F6",
                    borderRadius: "3px", overflow: "hidden" }}>
        <div style={{
          height      : "100%",
          width       : `${barWidth}%`,
          background  : barColor,
          borderRadius: "3px",
        }} />
      </div>
      <span style={{ fontSize: "11px", color: "#9CA3AF",
                     width: "40px", textAlign: "right" }}>
        {feature.shap_value > 0 ? "+" : ""}{feature.shap_value.toFixed(3)}
      </span>
    </div>
  );
}

const cardStyle = {
  background  : "white",
  border      : "1px solid #E5E7EB",
  borderRadius: "12px",
  padding     : "24px",
};

const loadingStyle = {
  textAlign : "center",
  color     : "#6B7280",
  padding   : "40px",
  fontSize  : "14px",
};