import { useState } from "react";
import { MessageCircle, Send } from "lucide-react";
import { api } from "../services/api";

export default function ExplanationPanel({
  explanation,
  loading,
  ticker
}) {
  const [question, setQuestion]   = useState("");
  const [answer, setAnswer]       = useState(null);
  const [asking, setAsking]       = useState(false);
  const [qaError, setQaError]     = useState(null);

  const handleAsk = async () => {
    if (!question.trim() || question.length < 5) return;
    setAsking(true);
    setAnswer(null);
    setQaError(null);

    try {
      const result = await api.ask(question, ticker);
      setAnswer(result);
    } catch (err) {
      setQaError(err.message);
    } finally {
      setAsking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div style={panelStyle}>
      <h3 style={titleStyle}>
        <MessageCircle size={16} style={{ marginRight: "6px" }} />
        AI Explanation
      </h3>

      {/* Prediction explanation */}
      {loading ? (
        <div style={loadingStyle}>Generating explanation...</div>
      ) : explanation ? (
        <p style={explanationStyle}>{explanation}</p>
      ) : (
        <p style={placeholderStyle}>
          Select a stock to see an AI-generated explanation.
        </p>
      )}

      {/* Divider */}
      <div style={dividerStyle} />

      {/* Q&A section */}
      <h4 style={subtitleStyle}>Ask about investing concepts</h4>
      <p style={hintStyle}>
        Try: "What does RSI mean?" or "Why does volume matter?"
      </p>

      <div style={inputRowStyle}>
        <input
          type        = "text"
          value       = {question}
          onChange    = {(e) => setQuestion(e.target.value)}
          onKeyDown   = {handleKeyDown}
          placeholder = "Ask anything about stocks or signals..."
          style       = {inputStyle}
          disabled    = {asking}
        />
        <button
          onClick  = {handleAsk}
          disabled = {asking || question.length < 5}
          style    = {buttonStyle(asking || question.length < 5)}
        >
          <Send size={14} />
        </button>
      </div>

      {/* Answer */}
      {asking && (
        <div style={loadingStyle}>Searching knowledge base...</div>
      )}
      {qaError && (
        <div style={errorStyle}>{qaError}</div>
      )}
      {answer && (
        <div style={answerStyle}>
          <p style={{ margin: "0 0 8px", fontSize: "14px",
                      color: "#111827", lineHeight: "1.6" }}>
            {answer.answer}
          </p>
          {answer.sources.length > 0 && (
            <p style={{ margin: 0, fontSize: "11px", color: "#9CA3AF" }}>
              Sources: {answer.sources.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Styles
const panelStyle = {
  background  : "white",
  border      : "1px solid #E5E7EB",
  borderRadius: "12px",
  padding     : "24px",
};
const titleStyle = {
  display    : "flex",
  alignItems : "center",
  fontSize   : "15px",
  fontWeight : "600",
  color      : "#111827",
  margin     : "0 0 12px",
};
const subtitleStyle = {
  fontSize  : "13px",
  fontWeight: "500",
  color     : "#374151",
  margin    : "0 0 4px",
};
const hintStyle = {
  fontSize: "12px",
  color   : "#9CA3AF",
  margin  : "0 0 10px",
};
const explanationStyle = {
  fontSize  : "14px",
  color     : "#374151",
  lineHeight: "1.7",
  margin    : 0,
};
const placeholderStyle = {
  fontSize: "13px",
  color   : "#9CA3AF",
  margin  : 0,
};
const loadingStyle = {
  fontSize : "13px",
  color    : "#6B7280",
  padding  : "8px 0",
};
const dividerStyle = {
  height    : "1px",
  background: "#F3F4F6",
  margin    : "20px 0",
};
const inputRowStyle = {
  display: "flex",
  gap    : "8px",
};
const inputStyle = {
  flex        : 1,
  padding     : "8px 12px",
  border      : "1px solid #E5E7EB",
  borderRadius: "8px",
  fontSize    : "13px",
  outline     : "none",
};
const buttonStyle = (disabled) => ({
  padding        : "8px 12px",
  background     : disabled ? "#F3F4F6" : "#1D4ED8",
  color          : disabled ? "#9CA3AF" : "white",
  border         : "none",
  borderRadius   : "8px",
  cursor         : disabled ? "not-allowed" : "pointer",
  display        : "flex",
  alignItems     : "center",
});
const answerStyle = {
  marginTop   : "12px",
  padding     : "12px",
  background  : "#F9FAFB",
  borderRadius: "8px",
  border      : "1px solid #E5E7EB",
};
const errorStyle = {
  marginTop : "8px",
  fontSize  : "12px",
  color     : "#DC2626",
};