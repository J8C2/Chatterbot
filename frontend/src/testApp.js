import React, { useState } from "react";

const App = () => {
  const [query, setQuery] = useState(""); // User input
  const [response, setResponse] = useState(""); // Response from API
  const [loading, setLoading] = useState(false); // Loading state
  const [error, setError] = useState(null); // Error handling

  const sendQuery = async () => {
    if (!query.trim()) {
      setError("Please enter a query.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        throw new Error("Failed to fetch response from API.");
      }

      const data = await res.json();
      setResponse(data.response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h1>Ask Your AI Assistant</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Type your question..."
        style={{
          width: "60%",
          padding: "10px",
          fontSize: "16px",
          marginBottom: "10px",
        }}
      />
      <br />
      <button
        onClick={sendQuery}
        disabled={loading}
        style={{
          padding: "10px 15px",
          fontSize: "16px",
          backgroundColor: "#007BFF",
          color: "#fff",
          border: "none",
          cursor: "pointer",
        }}
      >
        {loading ? "Thinking..." : "Ask"}
      </button>

      {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}

      {response && (
        <div style={{ marginTop: "20px", textAlign: "left", maxWidth: "80%", margin: "auto" }}>
          <h3>Response:</h3>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
};

export default App;
