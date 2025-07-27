import React from 'react';
import FileUpload from './components/FileUpload';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Text Extraction from Images</h1>
        <p>Upload an image to extract text using OCR</p>
      </header>
      <main>
        <FileUpload />
      </main>
    </div>
  );
}

export default App;
