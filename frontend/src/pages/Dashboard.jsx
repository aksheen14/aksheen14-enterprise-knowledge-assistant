import FileUpload from '../components/FileUpload';

export default function Dashboard({ onNavigate }) {
  return (
    <div className="dashboard-page">
      <header>
        <h1>Dashboard</h1>
        <button onClick={() => onNavigate('chat')}>Go to Chat</button>
      </header>

      <section>
        <h2>Upload Documents</h2>
        <FileUpload />
      </section>

      <section>
        <h2>Admin Stats</h2>
        <p>Documents uploaded: 0</p>
        <p>Active users: 0</p>
      </section>

      <section>
        <h2>Recent Chat History</h2>
        <p>No history yet.</p>
      </section>
    </div>
  );
}
