import React, { useState, useRef } from 'react';
import axios from 'axios';
import './FileUpload.css';

const languageOptions = [
  { value: 'auto', label: 'Auto (Detect Multiple)' },
  { value: 'eng', label: 'English' },
  { value: 'hin', label: 'Hindi' },
  { value: 'tel', label: 'Telugu' },
  { value: 'tam', label: 'Tamil' },
  { value: 'ben', label: 'Bengali' },
  { value: 'chi_sim', label: 'Chinese (Simplified)' },
  { value: 'jpn', label: 'Japanese' },
  { value: 'ara', label: 'Arabic' },
  { value: 'rus', label: 'Russian' },
  { value: 'deu', label: 'German' },
  { value: 'spa', label: 'Spanish' },
  { value: 'fra', label: 'French' },
  { value: 'ita', label: 'Italian' },
  { value: 'por', label: 'Portuguese' },
];

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copySuccess, setCopySuccess] = useState('');
  const [spellCheck, setSpellCheck] = useState(true);
  const [punctuation, setPunctuation] = useState(true);
  const [preprocessing, setPreprocessing] = useState(true);
  const [segmentation, setSegmentation] = useState(true);
  const [language, setLanguage] = useState('auto');
  const textContentRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
      setAnalysis(null);
      setCopySuccess('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');
    setCopySuccess('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('spell_check', spellCheck);
    formData.append('punctuation', punctuation);
    formData.append('preprocessing', preprocessing);
    formData.append('segmentation', segmentation);
    formData.append('language', language);

    try {
      const response = await axios.post('http://localhost:5000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setAnalysis(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred while processing the file');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopySuccess('Copied!');
        setTimeout(() => setCopySuccess(''), 2000);
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
        setCopySuccess('Failed to copy');
        setTimeout(() => setCopySuccess(''), 2000);
      });
  };

  const renderEntity = (entity) => {
    const colors = {
      'PERSON': '#ff6b6b',
      'ORG': '#4dabf7',
      'GPE': '#51cf66',
      'DATE': '#ffd43b',
      'MONEY': '#cc5de8',
      'PERCENT': '#ff922b',
      'TIME': '#20c997',
      'QUANTITY': '#fd7e14',
      'ORDINAL': '#e64980',
      'CARDINAL': '#868e96'
    };

    return (
      <span
        key={`${entity.start}-${entity.end}`}
        style={{
          backgroundColor: colors[entity.label] || '#adb5bd',
          color: 'white',
          padding: '2px 4px',
          borderRadius: '3px',
          margin: '0 2px',
          fontSize: '0.9em'
        }}
        title={entity.label}
      >
        {entity.text}
      </span>
    );
  };

  return (
    <div className="file-upload-container">
      <div className="upload-box">
        <input
          type="file"
          id="file-input"
          onChange={handleFileChange}
          accept=".png,.jpg,.jpeg"
          className="file-input"
        />
        <label htmlFor="file-input" className="file-label">
          <div className="upload-content">
            <svg
              className="upload-icon"
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p>Drag and drop your file here or click to browse</p>
            {file && <p className="selected-file">Selected: {file.name}</p>}
          </div>
        </label>
      </div>

      <div style={{ margin: '1rem 0', textAlign: 'left' }}>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={spellCheck}
            onChange={() => setSpellCheck(!spellCheck)}
          />
          Enable Spell Check
        </label>
        <br />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={punctuation}
            onChange={() => setPunctuation(!punctuation)}
          />
          Enable Punctuation Correction
        </label>
        <br />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={preprocessing}
            onChange={() => setPreprocessing(!preprocessing)}
          />
          Enable Preprocessing
        </label>
        <br />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={segmentation}
            onChange={() => setSegmentation(!segmentation)}
          />
          Enable Segmentation (Tesseract PSM)
        </label>
        <br />
        <label className="checkbox-label">
          Language:&nbsp;
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            style={{ fontSize: '0.95rem', color: '#111', marginLeft: 4 }}
          >
            {languageOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
        <div style={{ fontSize: '0.92rem', color: '#444', marginTop: 4 }}>
          For best accuracy, select the language of the text in your image. Use 'Auto' only for mixed-language images.
        </div>
      </div>

      <button
        className="upload-button"
        onClick={handleUpload}
        disabled={!file || loading}
      >
        {loading ? 'Processing...' : 'Extract Text'}
      </button>

      {error && <p className="error-message">{error}</p>}

      {analysis && (
        <div className="analysis-container">
          <div className="section">
            <h3>Extracted Text with Entities:</h3>
            <div className="text-content" ref={textContentRef}>
              {analysis.entities.map(renderEntity)}
            </div>
          </div>

          <div className="section">
            <h3>Corrected Text:</h3>
            <div className="corrected-text">
              <pre>{analysis.corrected_text}</pre>
              <button onClick={() => handleCopy(analysis.corrected_text)} className="copy-button">
                Copy
              </button>
              {copySuccess && <span className="copy-success-message">{copySuccess}</span>}
            </div>
          </div>
          <div className="section">
            <h4>Detected Language: {analysis.detected_language}</h4>
            <h4>Detected Scripts: {analysis.detected_scripts && analysis.detected_scripts.join(', ')}</h4>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload; 
