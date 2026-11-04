import GenerateShell from './GenerateShell.jsx'
import Markdown from './Markdown.jsx'
import CopyButton from './CopyButton.jsx'
import { NotesIcon } from './Icons.jsx'

export default function NotesView(props) {
  const { data } = props
  return (
    <GenerateShell
      {...props}
      title="Study Notes"
      subtitle="Key concepts, definitions and summaries extracted from your PDFs."
      Icon={NotesIcon}
      cta={{ label: 'Generate study notes', text: 'Turn your documents into organised, revision-ready notes.' }}
      includes="Key concepts · Definitions · Summary points · Important formulas"
    >
      {data && (
        <article className="notes">
          <div className="notes-copy"><CopyButton text={data.markdown} /></div>
          <Markdown>{data.markdown}</Markdown>
        </article>
      )}
    </GenerateShell>
  )
}
