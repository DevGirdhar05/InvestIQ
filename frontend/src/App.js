import { useState, useEffect, useCallback } from "react";
import SearchBar        from "./components/SearchBar";
import SignalCard       from "./components/SignalCard";
import ExplanationPanel from "./components/ExplanationPanel";
import MarketOverview   from "./components/MarketOverview";
import SentimentBadge  from "./components/SentimentBadge";
import { api }          from "./services/api";
import { TrendingUp }   from "lucide-react";

export default function App() {
  const [ticker,      setTicker]      = useState(null);
  const [analysis,    setAnalysis]    = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [sentiment,   setSentiment]   = useState(null);
  const [overview,    setOverview]    = useState(null);

  const [loadingAnalysis,    setLoadingAnalysis]    = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [loadingSentiment,   setLoadingSentiment]   = useState(false);
  const [loadingOverview,    setLoadingOverview]    = useState(true);

  const [error, setError] = useState(null);

  // Add at the top of App component
const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

useEffect(() => {
  const handler = () => setIsMobile(window.innerWidth < 768);
  window.addEventListener("resize", handler);
  return () => window.removeEventListener("resize", handler);
}, []);

  // Load market overview on mount
  useEffect(() => {
    api.overview()
      .then(setOverview)
      .catch(console.error)
      .finally(() => setLoadingOverview(false));
  }, []);

  // Load all data when ticker changes
  const loadTicker = useCallback(async (newTicker) => {
    if (!newTicker) return;

    setTicker(newTicker);
    setAnalysis(null);
    setExplanation(null);
    setSentiment(null);
    setError(null);

    // Step 1: Load analysis (fast — cached after first call)
    setLoadingAnalysis(true);
    let analysisData = null;
    try {
      analysisData = await api.analyze(newTicker);
      setAnalysis(analysisData);
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      setLoadingAnalysis(false);
      return;
    } finally {
      setLoadingAnalysis(false);
    }

    // Step 2: Load sentiment (parallel with explanation)
    setLoadingSentiment(true);
    api.sentiment(newTicker)
      .then(setSentiment)
      .catch(console.error)
      .finally(() => setLoadingSentiment(false));

    // Step 3: Load explanation (slowest — calls Gemini)
    setLoadingExplanation(true);
    api.explain(newTicker)
      .then((data) => setExplanation(data.explanation))
      .catch(console.error)
      .finally(() => setLoadingExplanation(false));

  }, []);
    const gridStyle = {
    display: "grid",
    gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr",
    gap: "20px",
    alignItems: "start",
  };

  return (
    <div style={appStyle}>
      {/* Header */}
      <header style={headerStyle}>
        <div style={headerInnerStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <TrendingUp size={24} color="#1D4ED8" />
            <h1 style={logoStyle}>InvestIQ</h1>
          </div>
          <span style={taglineStyle}>
            AI-powered stock signals for beginner investors
          </span>
        </div>
      </header>

      {/* Main content */}
      <main style={mainStyle}>

        {/* Search */}
        <SearchBar onSelect={loadTicker} selectedTicker={ticker} />

        {/* Error */}
        {error && (
          <div style={errorStyle}>{error}</div>
        )}

        {/* Market overview — shown when no ticker selected */}
        {!ticker && (
          <MarketOverview
            data    = {overview}
            loading = {loadingOverview}
            onSelect= {loadTicker}
          />
        )}

        {/* Ticker analysis — shown when ticker selected */}
        {ticker && (
          <div style={gridStyle}>
            {/* Left column */}
            <div style={{ display: "flex", flexDirection: "column",
                          gap: "16px" }}>
              <SignalCard
                data    = {analysis}
                loading = {loadingAnalysis}
              />
              <SentimentBadge
                data    = {sentiment}
                loading = {loadingSentiment}
              />
            </div>

            {/* Right column */}
            <ExplanationPanel
              explanation = {explanation}
              loading     = {loadingExplanation}
              ticker      = {ticker}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={footerStyle}>
        <p style={{ margin: 0, fontSize: "12px", color: "#9CA3AF" }}>
          InvestIQ · For educational purposes only ·
          Not financial advice · Predictions are probabilistic
        </p>
      </footer>
    </div>
  );
}

// Styles
const appStyle = {
  minHeight  : "100vh",
  background : "#F9FAFB",
  fontFamily : "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
};
const headerStyle = {
  background   : "white",
  borderBottom : "1px solid #E5E7EB",
  padding      : "0 24px",
  position     : "sticky",
  top          : 0,
  zIndex       : 10,
};
const headerInnerStyle = {
  maxWidth       : "1200px",
  margin         : "0 auto",
  height         : "60px",
  display        : "flex",
  alignItems     : "center",
  justifyContent : "space-between",
};
const logoStyle = {
  margin    : 0,
  fontSize  : "20px",
  fontWeight: "700",
  color     : "#111827",
};
const taglineStyle = {
  fontSize: "13px",
  color   : "#6B7280",
};
const mainStyle = {
  maxWidth : "1200px",
  margin   : "0 auto",
  padding  : "32px 24px",
};


const errorStyle = {
  padding     : "12px 16px",
  background  : "#FEF2F2",
  border      : "1px solid #FECACA",
  borderRadius: "8px",
  color       : "#DC2626",
  fontSize    : "14px",
  marginBottom: "16px",
};
const footerStyle = {
  borderTop : "1px solid #E5E7EB",
  padding   : "16px 24px",
  textAlign : "center",
  marginTop : "40px",
};