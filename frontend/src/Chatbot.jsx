import React, { useState } from "react";
import "./Chatbot.css";
import ReactMarkdown from 'react-markdown';

// Chatbot function for the bot
function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: Date.now(),
      sender: "bot",
      text: "Hello! How can I assist you today?",
      timestamp: new Date(),
      feedback: null,
    },
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
      id: Date.now(),
      sender: "user",
      text: input,
      timestamp: new Date(),
      feedback: null,
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
        id: Date.now() + 1, // Ensure unique ID
        sender: "bot",
        text: data.response || "I'm still learning, but I'm here to help!",
        timestamp: new Date(),
        feedback: null,
      };

      // Add bot message to chat
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          id: Date.now(),
          sender: "bot",
          text: "Error connecting to the server.",
          timestamp: new Date(),
          feedback: null,
        },
      ]);
    }

    setIsTyping(false);
  };

  // Function to handle file uploads
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const fileMessage = {
        id: Date.now(),
        sender: "user",
        text: `Uploaded: ${file.name}`,
        timestamp: new Date(),
        feedback: null,
        fileUrl: URL.createObjectURL(file),
      };
      setMessages([...messages, fileMessage]);

      // Simulate bot response to file upload
      setIsTyping(true);
      setTimeout(() => {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: Date.now() + 1,
            sender: "bot",
            text: "Thanks for uploading the file!",
            timestamp: new Date(),
            feedback: null,
          },
        ]);
        setIsTyping(false);
      }, 1200);
    }
  };

  // Handle feedback button clicks
  const handleFeedback = async (messageId, feedbackType, responseText) => {
    // Update local state
    setMessages((prevMessages) =>
      prevMessages.map((msg) =>
        msg.id === messageId ? { ...msg, feedback: feedbackType } : msg
      )
    );

    // Send feedback to backend
    try {
      await fetch("http://localhost:8000/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message_id: messageId,
          feedback: feedbackType,
          response_text: responseText,
        }),
      });
    } catch (error) {
      console.error("Error sending feedback:", error);
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
            {messages.map((msg) => (
              <div key={msg.id} className={`message-bubble ${msg.sender}`}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
                {msg.sender === "bot" && !msg.feedback && (
                  <div className="feedback-buttons">
                    <button
                      className="feedback-btn good"
                      onClick={() => handleFeedback(msg.id, "good", msg.text)}
                      title="Good Response"
                    >
                      👍
                    </button>
                    <button
                      className="feedback-btn bad"
                      onClick={() => handleFeedback(msg.id, "bad", msg.text)}
                      title="Bad Response"
                    >
                      👎
                    </button>
                  </div>
                )}
                {msg.feedback && (
                  <div className="feedback-status">
                    Feedback: {msg.feedback === "good" ? "👍 Good" : "👎 Bad"}
                  </div>
                )}
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
