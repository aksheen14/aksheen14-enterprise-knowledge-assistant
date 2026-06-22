export default function SourceCard({ title, excerpt, source }) {
  return (
    <div className="source-card">
      <h3>{title}</h3>
      <p>{excerpt}</p>
      <small>{source}</small>
    </div>
  );
}
