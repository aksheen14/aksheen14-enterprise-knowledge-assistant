export default function ChatWindow({ messages }) {
  return (
    <div className="chat-window">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.role}`}>
          <strong>{message.role === 'user' ? 'You' : 'Assistant'}:</strong>
          <p>{message.text}</p>
        </div>
      ))}
    </div>
  );
}
