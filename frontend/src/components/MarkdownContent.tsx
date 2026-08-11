import { memo, useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Expand, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import mermaid from 'mermaid'

type MarkdownContentProps = {
  content: string
  className?: string
}

const mermaidSvgCache = new Map<string, string>()

function isLikelyMermaid(code: string): boolean {
  const trimmed = code.trim()
  return /^(flowchart|graph)\s/i.test(trimmed)
}

let mermaidInitialized = false

function initMermaid() {
  if (mermaidInitialized) {
    return
  }
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'strict',
    suppressErrorRendering: true,
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: 'basis',
    },
  })
  mermaidInitialized = true
}

function styleRenderedSvg(container: HTMLElement, mode: 'thumb' | 'expanded') {
  const svg = container.querySelector('svg')
  if (!svg) {
    return
  }
  svg.style.display = 'block'
  svg.style.maxWidth = '100%'
  svg.style.width = '100%'
  svg.style.height = 'auto'
  svg.removeAttribute('height')

  if (mode === 'thumb') {
    svg.style.maxHeight = '110px'
    svg.style.minHeight = '0'
  } else {
    svg.style.maxHeight = 'none'
    svg.style.minHeight = '240px'
  }
}

function MermaidSvg({ svg, mode }: { svg: string; mode: 'thumb' | 'expanded' }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) {
      return
    }
    container.innerHTML = svg
    styleRenderedSvg(container, mode)
  }, [svg, mode])

  return <div ref={containerRef} className="mermaid-diagram-svg" />
}

type MermaidDiagramModalProps = {
  svg: string
  onClose: () => void
}

function MermaidDiagramModal({ svg, onClose }: MermaidDiagramModalProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  if (typeof document === 'undefined') {
    return null
  }

  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <button
        type="button"
        aria-label="Close diagram"
        className="fixed inset-0 animate-fade-in bg-slate-950/80 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative z-10 flex min-h-full items-center justify-center px-4 py-8">
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Expanded diagram"
          className="ui-card relative w-full max-w-5xl rounded-2xl border border-white/10 bg-slate-950/95 shadow-2xl"
        >
          <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
            <p className="text-sm font-medium text-slate-200">Diagram</p>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-white"
              aria-label="Close diagram"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="mermaid-diagram-expanded overflow-auto p-6 max-h-[80vh]">
            <MermaidSvg svg={svg} mode="expanded" />
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

const MermaidDiagram = memo(function MermaidDiagram({ code }: { code: string }) {
  const trimmedCode = code.trim()
  const cachedSvg = mermaidSvgCache.get(trimmedCode)
  const [svg, setSvg] = useState<string | null>(cachedSvg ?? null)
  const [renderState, setRenderState] = useState<'loading' | 'ok' | 'error'>(
    cachedSvg ? 'ok' : 'loading',
  )
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    let cancelled = false

    if (!isLikelyMermaid(trimmedCode)) {
      setRenderState('error')
      setSvg(null)
      return
    }

    const existing = mermaidSvgCache.get(trimmedCode)
    if (existing) {
      setSvg(existing)
      setRenderState('ok')
      return
    }

    setRenderState('loading')
    setSvg(null)
    initMermaid()

    const renderId = `mermaid-${Math.random().toString(36).slice(2)}`

    void mermaid
      .parse(trimmedCode)
      .then(() => mermaid.render(renderId, trimmedCode))
      .then(({ svg: renderedSvg }) => {
        if (!cancelled) {
          mermaidSvgCache.set(trimmedCode, renderedSvg)
          setSvg(renderedSvg)
          setRenderState('ok')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSvg(null)
          setRenderState('error')
        }
      })

    return () => {
      cancelled = true
    }
  }, [trimmedCode])

  if (renderState === 'error') {
    return (
      <div className="mermaid-diagram-error my-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
        <p className="mb-2 text-xs text-amber-200">
          Diagram could not be rendered (invalid Mermaid syntax).
        </p>
        <pre className="overflow-x-auto text-xs leading-relaxed text-slate-400">{trimmedCode}</pre>
      </div>
    )
  }

  if (renderState === 'loading' || !svg) {
    return (
      <div
        className="mermaid-diagram-thumb my-3 flex h-[140px] items-center justify-center rounded-lg border border-white/10 bg-black/30"
      >
        <p className="text-xs text-slate-500">Rendering diagram…</p>
      </div>
    )
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setExpanded(true)}
        className="mermaid-diagram-thumb group my-3 w-full rounded-lg border border-white/10 bg-black/30 p-3 text-left transition hover:border-indigo-400/40 hover:bg-black/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/50"
        aria-label="Expand diagram"
      >
        <div className="relative max-h-[120px] overflow-hidden">
          <MermaidSvg svg={svg} mode="thumb" />
          <div
            className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-slate-950/90 to-transparent"
          />
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400 group-hover:text-indigo-300">
          <Expand className="h-3.5 w-3.5" />
          <span>Click to expand diagram</span>
        </div>
      </button>

      {expanded ? <MermaidDiagramModal svg={svg} onClose={() => setExpanded(false)} /> : null}
    </>
  )
})

const markdownComponents = {
  pre({ children }: { children?: React.ReactNode }) {
    const child = children as { props?: { className?: string } } | undefined
    const className = child?.props?.className ?? ''
    if (className.includes('language-mermaid')) {
      return <>{children}</>
    }
    return <pre>{children}</pre>
  },
  code({
    className: codeClassName,
    children,
  }: {
    className?: string
    children?: React.ReactNode
  }) {
    const text = String(children).replace(/\n$/, '')
    if (codeClassName?.includes('language-mermaid')) {
      return <MermaidDiagram code={text} />
    }
    return <code className={codeClassName}>{children}</code>
  },
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={className}>
      <ReactMarkdown components={markdownComponents}>{content}</ReactMarkdown>
    </div>
  )
}
