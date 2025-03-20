import React, { useState } from "react";
import "./Chatbot.css";

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
  
  
  // Function to handle sending a message
  const sendMessage = () => {
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

    // Simulate bot delay before response
    setTimeout(() => {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "bot", text: "I'm still learning, but I'm here to help!", timestamp: new Date() },
      ]);
      setIsTyping(false);
    }, 1200);
  };
  // Function to handle file uploads
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const fileMessage = {
        sender: "user",
        text: `Uploaded: ${file.name}`,
        timestamp: new Date(),
        fileUrl: URL.createObjectURL(file), // Create a temporary URL for the file
      };
      setMessages([...messages, fileMessage]);

      // Simulate bot response to file upload
      setIsTyping(true);
      setTimeout(() => {
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: "bot", text: "Thanks for uploading the file!", timestamp: new Date() },
        ]);
        setIsTyping(false);
      }, 1200);
    }
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
                <p>{msg.text}</p>
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
