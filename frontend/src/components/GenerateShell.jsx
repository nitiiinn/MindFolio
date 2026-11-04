import { DownloadIcon, RefreshIcon, SparkIcon } from './Icons.jsx'

// Shared layout for the Notes / Quiz / Flashcards views: header, empty state
// with a Generate button, loading state, and toolbar once content exists.
export default function GenerateShell({ title, subtitle, Icon, includes, cta, data, loading, onGenerate, downloadUrl, children }) {
  return (
    <div className="gen">
      <div className="gen-header">
        <div className="gen-title"><Icon size={20} /><h2>{title}</h2></div>
        <p className="muted">{subtitle}</p>
        {data && (
          <div className="gen-toolbar">
            {data.model_label && <span className="muted small">Generated with {data.model_label}</span>}
            <div className="row">
              <button className="btn btn-ghost" onClick={onGenerate} disabled={loading}>
                <RefreshIcon size={15} /> {loading ? 'Regenerating…' : 'Regenerate'}
              </button>
              <a className="btn btn-primary" href={downloadUrl} download>
                <DownloadIcon size={15} /> Download PDF
              </a>
            </div>
          </div>
        )}
      </div>

      {!data && !loading && (
        <div className="gen-empty">
          <div className="gen-empty-icon"><Icon size={28} /></div>
          <p>{cta.text}</p>
          <button className="btn btn-primary btn-lg" onClick={onGenerate}><SparkIcon size={16} /> {cta.label}</button>
          <p className="muted small">{includes}</p>
        </div>
      )}

      {!data && loading && (
        <div className="gen-empty">
          <span className="spinner spinner-lg" />
          <p>AI is reading your documents…</p>
          <p className="muted small">This usually takes 20–60 seconds.</p>
        </div>
      )}

      {data && <div className={`gen-body ${loading ? 'stale' : ''}`}>{children}</div>}
    </div>
  )
}
