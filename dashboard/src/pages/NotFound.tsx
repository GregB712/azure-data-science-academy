export default function NotFound({ what }: { what: string }) {
  return (
    <div className="page">
      <h1>Not found</h1>
      <p>
        Nothing in the academy matches <code>{what || '(empty)'}</code>. It may be a planned item that has not been written yet,
        or a file the dashboard does not load (it loads Markdown under <code>docs/</code>, <code>labs/</code>, <code>projects/</code>,{' '}
        <code>diagrams/</code>, <code>references/</code>, the root, plus code and scripts).
      </p>
      <p>
        <a href="#/">Back to the home page</a> · <a href="#/catalog">Browse the catalog</a> · <a href={`#/search?q=${encodeURIComponent(what)}`}>Search for it</a>
      </p>
    </div>
  )
}
