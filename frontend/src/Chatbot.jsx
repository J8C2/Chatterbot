import React, { useState } from "react";
import "./Chatbot.css";
import ReactMarkdown from 'react-markdown';

// Chatbot function for the bot
function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! How can I assist you today?", timestamp: new Date() },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  // Speech Recognition Setup
  const startListening = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = "en-US"; // Set language
    recognition.continuous = false; // Stop after one sentence
    recognition.interimResults = false; // Only return final result

    recognition.onstart = () => console.log("Listening...");
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript); // Set recognized text into input field
    };

    recognition.onerror = (event) => console.error("Speech recognition error:", event.error);
    recognition.start();
  };
  
  
  // Updated sendMessage function to hit backend API
  const sendMessage = async () => {
    if (!input.trim()) return;

    // Create a user message object
    const userMessage = {
      sender: "user",
      text: input,
      timestamp: new Date(),
    };
    setMessages([...messages, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      // Send message to Flask API
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: input }),
      });

      // Handle response from backend
      const data = await response.json();
      const botMessage = {
        sender: "bot",
        text: data.response || "I'm still learning, but I'm here to help!",
        timestamp: new Date(),
      };

      // Add bot message to chat
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "bot", text: "Error connecting to the server.", timestamp: new Date() },
      ]);
    }

    setIsTyping(false);
  };

  //New function for handling file uploads
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
  
    const formData = new FormData();
    formData.append("file", file);
  
    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: `Uploaded: ${file.name}`,
        timestamp: new Date(),
      },
    ]);
    setIsTyping(true);
  
    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
  
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: data.message || "Thanks for uploading!",
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error("Upload error:", error);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Upload failed. Please try again.",
          timestamp: new Date(),
        },
      ]);
    }
  
    setIsTyping(false);
  };

  return (
    <div className={`chatbot-container ${isOpen ? "open" : ""}`}>
      <button className="chatbot-toggle" onClick={() => setIsOpen(!isOpen)}> 💬 Chat </button>

      {isOpen && (
        <div className={`chat-window ${isOpen ? "open" : ""}`}>
          <div className="chat-header">
            <span>Moore Public Schools Chatbot</span>
            <button className="close-btn" onClick={() => setIsOpen(false)}>✖</button>
          </div>
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message-bubble ${msg.sender}`}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
                <span className="timestamp">{msg.timestamp.toLocaleTimeString()}</span>
              </div>
            ))}
            {isTyping && <p className="typing-indicator">Bot is typing...</p>}
          </div>
          <div className="chat-input-container">
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  sendMessage(); // Trigger sendMessage when Enter is pressed
                }
              }}
              placeholder="Type a message..."
            />
            <input
              type="file"
              className="file-input"
              onChange={handleFileUpload}
              style={{ display: "none" }}
              id="file-upload"
            />
            <label htmlFor="file-upload" className="file-upload-btn">📎</label>
            <button className="mic-btn" onClick={startListening}>🎤</button>
            <button className="send-btn" onClick={sendMessage}>➤</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Chatbot;