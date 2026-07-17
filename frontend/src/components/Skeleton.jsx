const shimmer = `
  @keyframes shimmer {
    0%   { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
  }
`;

// Inject keyframes once
if (!document.getElementById("skeleton-styles")) {
  const style = document.createElement("style");
  style.id = "skeleton-styles";
  style.textContent = shimmer;
  document.head.appendChild(style);
}

export function SkeletonBlock({ width = "100%", height = "16px",
                          borderRadius = "4px", style = {} }) {
  return (
    <div style={{
      width,
      height,
      borderRadius,
      background: "linear-gradient(90deg, #F3F4F6 25%, #E5E7EB 50%, #F3F4F6 75%)",
      backgroundSize: "1000px 100%",
      animation: "shimmer 1.5s infinite linear",
      ...style,
    }} />
  );
}

export function SignalCardSkeleton() {
  return (
    <div style={cardStyle}>
      <div style={{ marginBottom: "20px" }}>
        <SkeletonBlock width="60%" height="24px"
                       style={{ marginBottom: "8px" }} />
        <SkeletonBlock width="40%" height="14px" />
      </div>
      <div style={{ textAlign: "center", marginBottom: "24px" }}>
        <SkeletonBlock width="120px" height="56px"
                       borderRadius="8px"
                       style={{ margin: "0 auto 12px" }} />
        <SkeletonBlock width="280px" height="8px"
                       borderRadius="4px"
                       style={{ margin: "0 auto" }} />
      </div>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} style={{ display: "flex", gap: "8px",
                               alignItems: "center",
                               marginBottom: "10px" }}>
          <SkeletonBlock width="16px"  height="16px" borderRadius="2px" />
          <SkeletonBlock width="160px" height="13px" />
          <SkeletonBlock height="6px" style={{ flex: 1 }} />
          <SkeletonBlock width="40px" height="11px" />
        </div>
      ))}
    </div>
  );
}

export function ExplanationSkeleton() {
  return (
    <div style={cardStyle}>
      <SkeletonBlock width="140px" height="18px"
                     style={{ marginBottom: "16px" }} />
      {[1, 2, 3, 4].map((i) => (
        <SkeletonBlock key={i}
          width       = {i === 4 ? "70%" : "100%"}
          height      = "14px"
          style       = {{ marginBottom: "8px" }}
        />
      ))}
    </div>
  );
}

export function OverviewSkeleton() {
  return (
    <div style={cardStyle}>
      <SkeletonBlock width="200px" height="18px"
                     style={{ marginBottom: "16px" }} />
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} style={{ display: "grid",
                               gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
                               gap: "8px", marginBottom: "12px" }}>
          {[1, 2, 3, 4, 5].map((j) => (
            <SkeletonBlock key={j} height="14px" />
          ))}
        </div>
      ))}
    </div>
  );
}

const cardStyle = {
  background  : "white",
  border      : "1px solid #E5E7EB",
  borderRadius: "12px",
  padding     : "24px",
};