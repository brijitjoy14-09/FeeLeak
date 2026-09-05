import { useRef, useState } from 'react'
import { uploadDataset } from '../../services/api'
import { SOURCES } from '../../constants/reconciliation'

// Upload states: idle | uploading | success | error
function UploadPanel({ onUploaded }) {
  const [sourceType, setSourceType] = useState(SOURCES[0].id)
  const [file, setFile] = useState(null)
  const [phase, setPhase] = useState('idle')
  const [message, setMessage] = useState('')
  const [errorDetails, setErrorDetails] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const isCsv = (candidate) => candidate && candidate.name.toLowerCase().endsWith('.csv')

  function selectFile(candidate) {
    if (!candidate) return
    if (!isCsv(candidate)) {
      setFile(null)
      setPhase('error')
      setMessage('Only .csv files are supported.')
      setErrorDetails(null)
      return
    }
    setFile(candidate)
    setPhase('idle')
    setMessage('')
    setErrorDetails(null)
  }

  async function handleUpload() {
    if (!file) return
    setPhase('uploading')
    setMessage('Uploading and validating dataset…')
    setErrorDetails(null)
    try {
      const result = await uploadDataset(sourceType, file)
      setPhase('success')
      setMessage(result.message || `${result.record_count} records loaded.`)
      setFile(null)
      if (inputRef.current) inputRef.current.value = ''
      onUploaded?.(result)
    } catch (err) {
      setPhase('error')
      setMessage(err.message || 'Upload failed.')
      setErrorDetails(err.details ?? null)
    }
  }

  const missingColumns = errorDetails?.missing_columns
  const rowErrors = errorDetails?.errors

  return (
    <section className="panel upload-panel" aria-labelledby="upload-h">
      <div className="panel-head">
        <h2 id="upload-h" className="panel-title">
          Upload Financial Data
        </h2>
      </div>

      <div className="upload-controls">
        <div className="field">
          <label htmlFor="source-select">Source</label>
          <select
            id="source-select"
            value={sourceType}
            onChange={(event) => setSourceType(event.target.value)}
          >
            {SOURCES.map((source) => (
              <option key={source.id} value={source.id}>
                {source.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div
        className={`dropzone ${dragOver ? 'is-dragover' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragOver(false)
          selectFile(event.dataTransfer.files?.[0])
        }}
      >
        <p className="dropzone-text">
          {file ? file.name : 'Drop CSV file here'}
        </p>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => inputRef.current?.click()}
        >
          Browse Files
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          aria-label="Choose CSV file"
          onChange={(event) => selectFile(event.target.files?.[0])}
        />
      </div>

      <button
        type="button"
        className="btn btn-primary upload-submit"
        disabled={!file || phase === 'uploading'}
        onClick={handleUpload}
      >
        {phase === 'uploading' ? 'Uploading…' : 'Upload'}
      </button>

      {message && (
        <div className={`upload-message msg-${phase}`} role="status">
          <p>{message}</p>
          {missingColumns && (
            <p className="msg-detail">
              Missing required columns: {missingColumns.join(', ')}
            </p>
          )}
          {rowErrors && rowErrors.length > 0 && (
            <ul className="msg-detail msg-errors">
              {rowErrors.slice(0, 5).map((rowError, index) => (
                <li key={index}>
                  Row {rowError.row}: {rowError.message}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}

export default UploadPanel
