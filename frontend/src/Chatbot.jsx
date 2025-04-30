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
      // Stores the speech recognition instance in a ref
      // This allows us to access the same instance across renders
      recognitionRef.current = new window.webkitSpeechRecognition();
      // Language can be set to others such as es-ES for Spanish, etc.
      // It can also be changed in a way to default as english and an additional dropdown can be added to 
      //    select a specific language if needed.
      recognitionRef.current.lang = "en-US";
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      //Lots of error checking as lots of issues are coming up. Used in console on chrome.
      //Different microhone allowed for text to be written out.
      //Maybe needs something around allowing more audio to come through users microphones through different webkit setings?
      
      // This line is mainly used for debugging on the developer console for the browser to notify when listning.
      recognitionRef.current.onstart = () => {
        console.log("Voice recognition started. Speak into the mic.");
      };
      // When speech is detected, this function is called and the spoken chat input is set to the input state.
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Transcript received:", transcript);
        setInput(transcript);
      };
      // Stopping speech recognition when the user stops speaking.
      recognitionRef.current.onspeechend = () => {
        console.log("Speech ended. Stopping recognition.");
        recognitionRef.current.stop();
      };
      // Another dev console log to show when the speech recognition has ended.
      recognitionRef.current.onend = () => {
        console.log("Recognition ended.");
      };
      // Error handling for speech recognition errors.
      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
      };
    }
      // Start the speech recognition process
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
      let response;
      if (file) {
        // If a file is present, use FormData to send the file and query
        const formData = new FormData();
        formData.append("file", file);
        formData.append("query", input);

        response = await fetch("http://localhost:8000/upload_and_query", {
          method: "POST",
          body: formData,
        });
      } else {
        // If no file, send the query to the default endpoint
        response = await fetch("http://localhost:8000/ask", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: input }),
        });
      }

      // Handle response from backend
      const data = await response.json();
      console.log(data);
      console.log(data.response);
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

  // New state to hold the file
  const [file, setFile] = useState(null);

  // Updated handleFileUpload function
  const handleFileUpload = (event) => {
    // Get the uploaded file from the input
    const uploadedFile = event.target.files[0];
    // Check if a file was selected
    if (uploadedFile) {
      // Save the file to state to be sent with the query
      setFile(uploadedFile);
      // Creating a chat message to show file uploaded 
      // Criteria below includes a unique ID, sender, text, timestamp, feedback, and fileUrl
      //     to allow for additional functionality in the future.
      const fileMessage = {
        id: Date.now(),
        sender: "user",
        text: `Uploaded: ${uploadedFile.name}`,
        timestamp: new Date(),
        feedback: null,
        fileUrl: URL.createObjectURL(uploadedFile),
      };
      setMessages([...messages, fileMessage]);
    }
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
