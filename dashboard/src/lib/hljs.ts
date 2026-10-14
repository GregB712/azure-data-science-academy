import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import ini from 'highlight.js/lib/languages/ini'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import plaintext from 'highlight.js/lib/languages/plaintext'
import powershell from 'highlight.js/lib/languages/powershell'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'

hljs.registerLanguage('bash', bash)
hljs.registerLanguage('ini', ini)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('plaintext', plaintext)
hljs.registerLanguage('powershell', powershell)
hljs.registerLanguage('python', python)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('yaml', yaml)

const ALIASES: Record<string, string> = {
  sh: 'bash', shell: 'bash', console: 'bash', zsh: 'bash',
  py: 'python', yml: 'yaml', ps1: 'powershell', azurepowershell: 'powershell', pwsh: 'powershell',
  ts: 'typescript', tsx: 'typescript', js: 'typescript', javascript: 'typescript',
  bicep: 'typescript', // no Bicep grammar in highlight.js; TypeScript colouring is close enough
  html: 'xml', text: 'plaintext', txt: 'plaintext', jsonc: 'json', md: 'markdown', example: 'ini', env: 'ini',
}

export function languageFor(langOrExt: string | undefined): string {
  const l = (langOrExt ?? '').toLowerCase()
  const name = ALIASES[l] ?? l
  return hljs.getLanguage(name) ? name : 'plaintext'
}

export function highlight(code: string, langOrExt?: string): { html: string; language: string } {
  const language = languageFor(langOrExt)
  return { html: hljs.highlight(code, { language, ignoreIllegals: true }).value, language }
}
