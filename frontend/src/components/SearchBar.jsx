import { useState } from "react";
import { Search } from "lucide-react";

const WATCHLIST = [
  { ticker: "RELIANCE.NS", name: "Reliance Industries" },
  { ticker: "TCS.NS",      name: "Tata Consultancy Services" },
  { ticker: "INFY.NS",     name: "Infosys" },
  { ticker: "HDFCBANK.NS", name: "HDFC Bank" },
  { ticker: "WIPRO.NS",    name: "Wipro" },
];

export default function SearchBar({ onSelect, selectedTicker }) {
  const [query, setQuery] = useState("");

  const filtered = WATCHLIST.filter(
    (s) =>
      s.ticker.toLowerCase().includes(query.toLowerCase()) ||
      s.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div style={{ marginBottom: "24px" }}>
      <div style={{ position: "relative", marginBottom: "12px" }}>
        <Search
          size={18}
          style={{
            position : "absolute",
            left     : "12px",
            top      : "50%",
            transform: "translateY(-50%)",
            color    : "#6B7280",
          }}
        />
        <input
          type        = "text"
          placeholder = "Search ticker or company..."
          value       = {query}
          onChange    = {(e) => setQuery(e.target.value)}
          style={{
            width        : "100%",
            padding      : "10px 12px 10px 40px",
            border       : "1px solid #E5E7EB",
            borderRadius : "8px",
            fontSize     : "14px",
            outline      : "none",
            boxSizing    : "border-box",
          }}
        />
      </div>

      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        {filtered.map((stock) => (
          <button
            key     = {stock.ticker}
            onClick = {() => onSelect(stock.ticker)}
            style={{
              padding         : "6px 14px",
              borderRadius    : "20px",
              border          : "1px solid",
              borderColor     : selectedTicker === stock.ticker
                                  ? "#1D4ED8" : "#E5E7EB",
              background      : selectedTicker === stock.ticker
                                  ? "#EFF6FF" : "white",
              color           : selectedTicker === stock.ticker
                                  ? "#1D4ED8" : "#374151",
              fontSize        : "13px",
              cursor          : "pointer",
              fontWeight      : selectedTicker === stock.ticker
                                  ? "500" : "400",
            }}
          >
            {stock.ticker.replace(".NS", "")}
          </button>
        ))}
      </div>
    </div>
  );
}