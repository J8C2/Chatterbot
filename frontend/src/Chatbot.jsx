import React, { useState } from "react";
import "./Chatbot.css";

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false); // Controls chatbot visibility

  return (
    <div className="chatbot-container">
      {/* Chatbot Toggle Button */}
      <button className="chatbot-toggle" onClick={() => setIsOpen(!isOpen)}>
        💬 Chat
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <span>Chatbot</span>
            <button className="close-btn" onClick={() => setIsOpen(false)}>✖</button>
          </div>
          <div className="chat-messages">
            <p className="bot-message">Hello! How can I assist you?</p>
          </div>
          <input type="text" className="chat-input" placeholder="Type a message..." />
        </div>
      )}
    </div>
  );
}

export default Chatbot;
