import { useState } from 'react';

export default function FileUpload() {
  const [filename, setFilename] = useState('');

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) setFilename(file.name);
  };

  return (
    <div className="file-upload">
      <label>
        Upload PDF
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
      </label>
      {filename && <p>Selected file: {filename}</p>}
    </div>
  );
}
