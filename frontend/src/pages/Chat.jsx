import { useState } from 'react';
import ChatWindow from '../components/ChatWindow';
import SourceCard from '../components/SourceCard';

const mockSources = [
  { title: 'Quarterly Report', excerpt: 'Customer churn decreased by 12%.', source: 'report.pdf' },
];

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Ask me anything about your enterprise knowledge base.' },
  ]);
  const [question, setQuestion] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!question.trim()) return;
    setMessages((prev) => [...prev, { role: 'user', text: question }, { role: 'assistant', text: 'Processing...' }]);
    setQuestion('');
  };

  return (
    <div className="chat-page">
      <header>
        <h1>Knowledge Assistant</h1>
      </header>

      <ChatWindow messages={messages} />

      <form onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question..."
        />
        <button type="submit">Send</button>
      </form>

      <aside>
        <h2>Source</h2>
        {mockSources.map((source, index) => (
          <SourceCard key={index} {...source} />
        ))}
      </aside>
    </div>
  );
}
