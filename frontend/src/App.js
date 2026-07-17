import { useState, useEffect, useCallback } from "react";
import SearchBar         from "./components/SearchBar";
import SignalCard        from "./components/SignalCard";
import ExplanationPanel  from "./components/ExplanationPanel";
import MarketOverview    from "./components/MarketOverview";
import SentimentBadge   from "./components/SentimentBadge";
import PriceChart        from "./components/PriceChart";
import {
  SignalCardSkeleton,
  ExplanationSkeleton,
  OverviewSkeleton
} from "./components/Skeleton";
import { api }           from "./services/api";
import { TrendingUp, RefreshCw, AlertCircle } from "lucide-react";

export default function App() {
  const [ticker,      setTicker]      = useState(null);
  const [analysis,    setAnalysis]    = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [sentiment,   setSentiment]   = useState(null);
  const [overview,    setOverview]    = useState(null);
  const [apiHealth,   setApiHealth]   = useState(null);

  const [loadingAnalysis,    setLoadingAnalysis]    = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [loadingSentiment,   setLoadingSentiment]   = useState(false);
  const [loadingOverview,    setLoadingOverview]    = useState(true);

  const [error,    setError]    = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Responsive handler
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  // Check API health and load overview on mount
  useEffect(() => {
    api.health()
      .then(setApiHealth)
      .catch(() => setApiHealth({ status: "error" }));

    api.overview()
      .then(setOverview)
      .catch(console.error)
      .finally(() => setLoadingOverview(false));
  }, []);

  const loadTicker = useCallback(async (newTicker) => {
    if (!newTicker) return;

    setTicker(newTicker);
    setAnalysis(null);
    setExplanation(null);
    setSentiment(null);
    setError(null);

    // Analysis first
    setLoadingAnalysis(true);
    try {
      const data = await api.analyze(newTicker);
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
      setLoadingAnalysis(false);
      return;
    } finally {
      setLoadingAnalysis(false);
    }

    // Sentiment and explanation in parallel
    setLoadingSentiment(true);
    api.sentiment(newTicker)
      .then(setSentiment)
      .catch(console.error)
      .finally(() => setLoadingSentiment(false));

    setLoadingExplanation(true);
    api.explain(newTicker)
      .then((d) => setExplanation(d.explanation))
      .catch(console.error)
      .finally(() => setLoadingExplanation(false));

  }, []);

  const handleRefresh = () => {
    if (ticker) loadTicker(ticker);
  };

  return (
    <div style={appStyle}>

      {/* Header */}
      <header style={headerStyle}>
        <div style={headerInnerStyle}>
          <div style={{ display: "flex", alignItems: "center",
                        gap: "10px" }}>
            <div style={logoIconStyle}>
              <TrendingUp size={18} color="white" />
            </div>
            <div>
              <h1 style={logoStyle}>InvestIQ</h1>
              <p style={taglineStyle}>
                AI stock signals for beginner investors
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center",
                        gap: "12px" }}>
            {/* API status indicator */}
            {apiHealth && (
              <div style={{ display: "flex", alignItems: "center",
                            gap: "6px", fontSize: "12px",
                            color: apiHealth.status === "ok"
                                   ? "#16A34A" : "#DC2626" }}>
                <div style={{
                  width       : "7px",
                  height      : "7px",
                  borderRadius: "50%",
                  background  : apiHealth.status === "ok"
                                  ? "#16A34A" : "#DC2626",
                }} />
                {apiHealth.status === "ok" ? "Live" : "Offline"}
              </div>
            )}

            {/* Refresh button */}
            {ticker && (
              <button onClick={handleRefresh} style={refreshBtnStyle}
                      title="Refresh data">
                <RefreshCw size={14} />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main */}
      <main style={{ ...mainStyle,
                     padding: isMobile ? "20px 16px" : "32px 24px" }}>

        {/* Search */}
        <SearchBar onSelect={loadTicker} selectedTicker={ticker} />

        {/* Error banner */}
        {error && (
          <div style={errorBannerStyle}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* No ticker selected — show overview */}
        {!ticker && (
          <>
            {loadingOverview
              ? <OverviewSkeleton />
              : <MarketOverview
                  data    = {overview}
                  loading = {false}
                  onSelect= {loadTicker}
                />
            }
            <EmptyState onSelect={loadTicker} />
          </>
        )}

        {/* Ticker selected */}
        {ticker && (
          <div style={{
            display             : "grid",
            gridTemplateColumns : isMobile ? "1fr" : "1fr 1fr",
            gap                 : "20px",
            alignItems          : "start",
          }}>
            {/* Left column */}
            <div style={{ display: "flex", flexDirection: "column",
                          gap: "16px" }}>
              {loadingAnalysis
                ? <SignalCardSkeleton />
                : <SignalCard data={analysis} loading={false} />
              }
              <PriceChart ticker={ticker} />
              <SentimentBadge
                data    = {sentiment}
                loading = {loadingSentiment}
              />
            </div>

            {/* Right column */}
            <div style={{ display: "flex", flexDirection: "column",
                          gap: "16px" }}>
              {loadingExplanation && !explanation
                ? <ExplanationSkeleton />
                : <ExplanationPanel
                    explanation = {explanation}
                    loading     = {loadingExplanation}
                    ticker      = {ticker}
                  />
              }
              <DisclaimerCard />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={footerStyle}>
        <p style={{ margin: 0, fontSize: "12px", color: "#9CA3AF" }}>
          InvestIQ · Educational purposes only ·
          Not financial advice · Predictions are probabilistic ·
          Built with XGBoost + FinBERT + Gemini
        </p>
      </footer>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────

function EmptyState({ onSelect }) {
  const suggestions = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"];
  return (
    <div style={emptyStateStyle}>
      <TrendingUp size={40} color="#D1D5DB"
                  style={{ margin: "0 auto 16px",
                           display: "block" }} />
      <h3 style={{ margin: "0 0 8px", fontSize: "16px",
                   fontWeight: "600", color: "#374151" }}>
        Select a stock to get started
      </h3>
      <p style={{ margin: "0 0 20px", fontSize: "14px",
                  color: "#6B7280" }}>
        Get AI-powered predictions, signal explanations,
        and news sentiment for NIFTY50 stocks.
      </p>
      <div style={{ display: "flex", gap: "8px",
                    justifyContent: "center", flexWrap: "wrap" }}>
        {suggestions.map((t) => (
          <button key={t} onClick={() => onSelect(t)}
                  style={suggestionBtnStyle}>
            Try {t.replace(".NS", "")}
          </button>
        ))}
      </div>
    </div>
  );
}

function DisclaimerCard() {
  return (
    <div style={disclaimerStyle}>
      <h4 style={{ margin: "0 0 8px", fontSize: "13px",
                   fontWeight: "600", color: "#374151" }}>
        Important Disclaimer
      </h4>
      <ul style={{ margin: 0, paddingLeft: "16px",
                   fontSize: "12px", color: "#6B7280",
                   lineHeight: "1.8" }}>
        <li>Predictions are probabilistic, not guarantees</li>
        <li>Past performance does not predict future results</li>
        <li>This is not financial advice</li>
        <li>Always do your own research before investing</li>
        <li>Model trained on 2 years of historical data</li>
      </ul>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────

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
  boxShadow    : "0 1px 3px rgba(0,0,0,0.05)",
};
const headerInnerStyle = {
  maxWidth      : "1200px",
  margin        : "0 auto",
  height        : "64px",
  display       : "flex",
  alignItems    : "center",
  justifyContent: "space-between",
};
const logoIconStyle = {
  width       : "36px",
  height      : "36px",
  background  : "#1D4ED8",
  borderRadius: "8px",
  display     : "flex",
  alignItems  : "center",
  justifyContent: "center",
};
const logoStyle    = { margin: 0, fontSize: "18px",
                        fontWeight: "700", color: "#111827" };
const taglineStyle = { margin: 0, fontSize: "11px", color: "#9CA3AF" };
const mainStyle    = { maxWidth: "1200px", margin: "0 auto" };
const footerStyle  = {
  borderTop : "1px solid #E5E7EB",
  padding   : "16px 24px",
  textAlign : "center",
  marginTop : "40px",
  background: "white",
};
const errorBannerStyle = {
  display     : "flex",
  alignItems  : "center",
  gap         : "8px",
  padding     : "10px 14px",
  background  : "#FEF2F2",
  border      : "1px solid #FECACA",
  borderRadius: "8px",
  color       : "#DC2626",
  fontSize    : "13px",
  marginBottom: "16px",
};
const refreshBtnStyle = {
  padding        : "6px",
  background     : "transparent",
  border         : "1px solid #E5E7EB",
  borderRadius   : "6px",
  cursor         : "pointer",
  display        : "flex",
  alignItems     : "center",
  color          : "#6B7280",
};
const emptyStateStyle = {
  textAlign   : "center",
  padding     : "60px 24px",
  background  : "white",
  borderRadius: "12px",
  border      : "1px solid #E5E7EB",
};
const suggestionBtnStyle = {
  padding     : "8px 16px",
  background  : "#EFF6FF",
  color       : "#1D4ED8",
  border      : "1px solid #BFDBFE",
  borderRadius: "8px",
  cursor      : "pointer",
  fontSize    : "13px",
  fontWeight  : "500",
};
const disclaimerStyle = {
  background  : "#FFFBEB",
  border      : "1px solid #FDE68A",
  borderRadius: "12px",
  padding     : "16px",
};