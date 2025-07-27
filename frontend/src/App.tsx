import { useState } from 'react';
import './App.css';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [selectedTicker, setSelectedTicker] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          ticker: selectedTicker || undefined
        }),
      });

      const data = await response.json();
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="App">
      <header>
        <h1>Finance Chatbot</h1>
      </header>
      
      <main>
        <div className="chat-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
        </div>
        
        <form onSubmit={handleSubmit}>
          <select 
            value={selectedTicker} 
            onChange={(e) => setSelectedTicker(e.target.value)}
          >
            <option value="">Select Ticker</option>
            <option value="RELIANCE">RELIANCE</option>
            <option value="TCS">TCS</option>
          </select>
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
          />
          <button type="submit">Send</button>
        </form>
      </main>
    </div>
  );
}

export default App; 