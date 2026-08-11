import { useCallback, useRef, useState, type ReactNode } from 'react'

type ResizableColumnsProps = {
  left: ReactNode
  right: ReactNode | null
  defaultLeftRatio?: number
  minLeftRatio?: number
  maxLeftRatio?: number
  className?: string
  align?: 'end' | 'stretch' | 'center'
  embedded?: boolean
}

export function ResizableColumns({
  left,
  right,
  defaultLeftRatio = 0.48,
  minLeftRatio = 0.28,
  maxLeftRatio = 0.72,
  className = '',
  align = 'end',
  embedded = false,
}: ResizableColumnsProps) {
  const [leftRatio, setLeftRatio] = useState(defaultLeftRatio)
  const containerRef = useRef<HTMLDivElement>(null)

  const onMouseDown = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      event.preventDefault()
      const container = containerRef.current
      if (!container) return

      const startX = event.clientX
      const startRatio = leftRatio
      const width = container.getBoundingClientRect().width

      function onMouseMove(moveEvent: MouseEvent) {
        const delta = moveEvent.clientX - startX
        const newRatio = startRatio + delta / width
        setLeftRatio(Math.min(maxLeftRatio, Math.max(minLeftRatio, newRatio)))
      }

      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove)
        document.removeEventListener('mouseup', onMouseUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }

      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', onMouseMove)
      document.addEventListener('mouseup', onMouseUp)
    },
    [leftRatio, minLeftRatio, maxLeftRatio],
  )

  if (!right) {
    return <div className={className}>{left}</div>
  }

  const alignClass =
    align === 'stretch' ? 'items-stretch' : align === 'center' ? 'items-center' : 'items-end'

  return (
    <div ref={containerRef} className={`flex gap-0 ${alignClass} ${className}`}>
      <div
        className={`min-w-0 shrink-0 ${embedded ? '' : 'pr-1'}`}
        style={{ width: `${leftRatio * 100}%` }}
      >
        {left}
      </div>
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize columns"
        onMouseDown={onMouseDown}
        className={`chat-col-resize-handle shrink-0 self-stretch ${
          embedded ? 'chat-col-resize-handle-inline' : ''
        }`}
      />
      <div className={`min-w-0 flex-1 ${embedded ? '' : 'pl-1'}`}>{right}</div>
    </div>
  )
}
