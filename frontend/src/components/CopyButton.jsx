import { useState } from 'react'
import { CopyIcon, CheckIcon } from './Icons.jsx'

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text)
  }
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
}

export default function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const onClick = async () => {
    try {
      await copyText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch { /* ignore */ }
  }
  return (
    <button className="icon-btn" onClick={onClick} title={copied ? 'Copied' : 'Copy'} aria-label="Copy message">
      {copied ? <CheckIcon size={15} /> : <CopyIcon size={15} />}
    </button>
  )
}
