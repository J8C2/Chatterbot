import React, { useState, useRef } from "react";
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
  const recognitionRef = useRef(null);
  const [chatSize, setChatSize] = useState("medium");
  // Speech Recognition Setup
  const startListening = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }  
    if (!recognitionRef.current) {
      recognitionRef.current = new window.webkitSpeechRecognition();
      recognitionRef.current.lang = "en-US";
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      //Lots of error checking as lots of issues are coming up. Used in console on chrome.
      //Different microhone allowed for text to be written out.
      //Maybe needs something around allowing more audio to come through users microphones through different webkit setings?
      recognitionRef.current.onstart = () => {
        console.log("Voice recognition started. Speak into the mic.");
      };
  
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Transcript received:", transcript);
        setInput(transcript);
      };
  
      recognitionRef.current.onspeechend = () => {
        console.log("Speech ended. Stopping recognition.");
        recognitionRef.current.stop();
      };
  
      recognitionRef.current.onend = () => {
        console.log("Recognition ended.");
      };
  
      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
      };
    }
  
      recognitionRef.current.start();
    };
  
    if (!recognitionRef.current) {
      recognitionRef.current = new window.webkitSpeechRecognition();
      recognitionRef.current.lang = "en-US";
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      //Lots of error checking as lots of issues are coming up. Used in console on chrome.
      //Different microhone allowed for text to be written out.
      //Maybe needs something around allowing more audio to come through users microphones through different webkit setings?
      recognitionRef.current.onstart = () => {
        console.log("Voice recognition started. Speak into the mic.");
      };
  
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Transcript received:", transcript);
        setInput(transcript);
      };
  
      recognitionRef.current.onspeechend = () => {
        console.log("Speech ended. Stopping recognition.");
        recognitionRef.current.stop();
      };
  
      recognitionRef.current.onend = () => {
        console.log("Recognition ended.");
      };
  
      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
      };
    }
  
      recognitionRef.current.start();
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
        query: input,
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

  //New function for handling file uploads
  const handleFileUpload = async (event) => {
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
/*
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
*/
    }
  
    setIsTyping(false);
  };
  // Handle feedback button clicks
  const handleFeedback = async (messageId, feedbackType, responseText, query) => {
    // Update local state
    setMessages((prevMessages) =>
      prevMessages.map((msg) =>
        msg.id === messageId ? { ...msg, feedback: feedbackType } : msg
      )
    );

    // Send feedback to backend
    try {
      const response = await fetch("http://localhost:8000/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query || "Unknown query",
          message_id: messageId,
          feedback: feedbackType,
          response_text: responseText,
        }),
      });
      const data = await response.json();
      console.log("Feedback response:", data);
    } catch (error) {
      console.error("Error sending feedback:", error);
    }
  };
  
  const cycleChatSize = () => {
    setChatSize((prev) =>
      prev === "small" ? "medium" :
      prev === "medium" ? "large" : "small"
    );
  };
  
  return (
    <div className={`chatbot-container ${isOpen ? "open" : ""}`}>
      <button className="chatbot-toggle" onClick={() => setIsOpen(!isOpen)}> 💬 Chat </button>

      {isOpen && (
        <div className={`chat-window ${isOpen ? "open" : ""} ${chatSize}`}>

          <div className="chat-header">
            <span>Moore Public Schools Chatbot</span>
            <div className="chat-header-buttons">
              <button className="resize-btn" onClick={cycleChatSize}>⛶</button>
              <button className="close-btn" onClick={() => setIsOpen(false)}>✖</button>
            </div>
          </div>
          <div className="chat-messages-background">
            {messages.map((msg, index) => (
              <div key={index} className={`message-bubble ${msg.sender}`}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
                {msg.sender === "bot" && !msg.feedback && (
                  <div className="feedback-buttons">
                    <button
                      className="feedback-btn good"
                      onClick={() => handleFeedback(msg.id, "good", msg.text, msg.query)}
                      title="Good Response"
                    >
                      👍
                    </button>
                    <button
                      className="feedback-btn bad"
                      onClick={() => handleFeedback(msg.id, "bad", msg.text, msg.query)}
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
