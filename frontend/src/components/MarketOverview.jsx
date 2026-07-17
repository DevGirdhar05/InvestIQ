export default function MarketOverview({ data, loading, onSelect }) {
  if (loading) {
    return <div style={containerStyle}>Loading market overview...</div>;
  }

  if (!data || !data.stocks || data.stocks.length === 0) {
    return null;
  }

  return (
    <div style={containerStyle}>
      <h3 style={titleStyle}>Market Overview — {data.date}</h3>
      <div style={tableStyle}>
        <div style={headerRowStyle}>
          <span>Ticker</span>
          <span>Price</span>
          <span>RSI</span>
          <span>Momentum</span>
          <span>Trend</span>
        </div>
        {data.stocks.map((stock) => {
          const rsiColor = stock.rsi > 70 ? "#DC2626"
                         : stock.rsi < 30 ? "#16A34A"
                         : "#374151";
          const momentumUp = stock.macd_hist > 0;

          return (
            <div
              key     = {stock.ticker}
              style   = {rowStyle}
              onClick = {() => onSelect(stock.ticker)}
            >
              <span style={{ fontWeight: "500", color: "#1D4ED8",
                             cursor: "pointer" }}>
                {stock.ticker.replace(".NS", "")}
              </span>
              <span>₹{Number(stock.close).toLocaleString("en-IN",
                        { maximumFractionDigits: 2 })}</span>
              <span style={{ color: rsiColor, fontWeight: "500" }}>
                {Number(stock.rsi).toFixed(1)}
              </span>
              <span style={{ color: momentumUp ? "#16A34A" : "#DC2626" }}>
                {momentumUp ? "▲ Bullish" : "▼ Bearish"}
              </span>
              <span style={{
                fontSize     : "12px",
                padding      : "2px 8px",
                borderRadius : "10px",
                background   : stock.trend === "Above SMA50"
                                 ? "#DCFCE7" : "#FEE2E2",
                color        : stock.trend === "Above SMA50"
                                 ? "#16A34A" : "#DC2626",
              }}>
                {stock.trend}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const containerStyle = {
  background  : "white",
  border      : "1px solid #E5E7EB",
  borderRadius: "12px",
  padding     : "20px",
  marginBottom: "24px",
};
const titleStyle = {
  fontSize    : "15px",
  fontWeight  : "600",
  color       : "#111827",
  margin      : "0 0 16px",
};
const tableStyle  = { display: "flex", flexDirection: "column", gap: "1px" };
const headerRowStyle = {
  display      : "grid",
  gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
  padding      : "8px 0",
  fontSize     : "12px",
  fontWeight   : "500",
  color        : "#6B7280",
  borderBottom : "1px solid #F3F4F6",
};
const rowStyle = {
  display           : "grid",
  gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
  padding           : "10px 0",
  fontSize          : "13px",
  color             : "#374151",
  borderBottom      : "1px solid #F9FAFB",
  cursor            : "pointer",
  alignItems        : "center",
};