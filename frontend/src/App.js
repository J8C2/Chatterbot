import React, { useEffect, useState } from "react";

const App = () => {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");

  const sendMessage = () => {
    // Send data to the POST endpoint
    fetch("http://127.0.0.1:8000/api/message", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: "Hello from frontend!" }),
    })
      .then((response) => response.json())
      .then((data) => {
        setResponse(JSON.stringify(data));
      })
      .catch((error) => console.error("Error sending message:", error));
  };

  return (
    <div>
      <h1>FastAPI + React</h1>
      <p>Message from FastAPI: {message}</p>
      <button onClick={sendMessage}>Send Message to API</button>
      <p>API Response: {response}</p>
    </div>
  );
};

export default App;
