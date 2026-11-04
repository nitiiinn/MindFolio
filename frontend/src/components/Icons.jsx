const base = { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' }

const make = (paths) => function Icon({ size = 18, ...props }) {
  return <svg {...base} width={size} height={size} aria-hidden="true" {...props}>{paths}</svg>
}

export const ChatIcon = make(<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />)
export const NotesIcon = make(<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" /></>)
export const QuizIcon = make(<><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" /></>)
export const CardsIcon = make(<><rect x="2" y="6" width="16" height="14" rx="2" /><path d="M6 2h14a2 2 0 0 1 2 2v12" /></>)
export const UploadIcon = make(<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="M17 8l-5-5-5 5M12 3v12" /></>)
export const FileIcon = make(<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /></>)
export const CopyIcon = make(<><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></>)
export const CheckIcon = make(<path d="M20 6L9 17l-5-5" />)
export const XIcon = make(<path d="M18 6L6 18M6 6l12 12" />)
export const SendIcon = make(<path d="M12 19V5M5 12l7-7 7 7" />)
export const DownloadIcon = make(<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="M7 10l5 5 5-5M12 15V3" /></>)
export const RefreshIcon = make(<><path d="M23 4v6h-6M1 20v-6h6" /><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" /></>)
export const TrashIcon = make(<><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" /></>)
export const GlobeIcon = make(<><circle cx="12" cy="12" r="10" /><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></>)
export const MenuIcon = make(<path d="M3 12h18M3 6h18M3 18h18" />)
export const ChevronLeft = make(<path d="M15 18l-6-6 6-6" />)
export const ChevronRight = make(<path d="M9 18l6-6-6-6" />)
export const ShuffleIcon = make(<><path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5" /></>)
export const SparkIcon = make(<path d="M12 3l1.9 5.8L20 10l-6.1 1.2L12 17l-1.9-5.8L4 10l6.1-1.2z" />)
export const PlusIcon = make(<path d="M12 5v14M5 12h14" />)
