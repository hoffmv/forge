import React, { useEffect, useRef } from 'react'
import { Terminal as XTerm } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

export default function Terminal({ events }) {
  const containerRef = useRef(null)
  const termRef = useRef(null)
  const fitAddonRef = useRef(null)
  const eventCountRef = useRef(0)

  useEffect(() => {
    if (!containerRef.current) return

    const term = new XTerm({
      theme: {
        background: '#0e0e0e',
        foreground: '#f3f3f3',
        cursor: '#FF6E00',
        selectionBackground: '#FF6E0033',
        black: '#1C1C1C',
        red: '#f87171',
        green: '#4ade80',
        yellow: '#facc15',
        blue: '#60a5fa',
        magenta: '#c084fc',
        cyan: '#22d3ee',
        white: '#f3f3f3',
      },
      fontSize: 12,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      cursorBlink: false,
      disableStdin: true,
      convertEol: true,
      scrollback: 5000,
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(containerRef.current)

    try { fitAddon.fit() } catch (e) { /* ignore initial fit errors */ }

    term.writeln('\x1b[38;2;255;110;0m╔══════════════════════════════════╗\x1b[0m')
    term.writeln('\x1b[38;2;255;110;0m║         FORGE TERMINAL           ║\x1b[0m')
    term.writeln('\x1b[38;2;255;110;0m╚══════════════════════════════════╝\x1b[0m')
    term.writeln('')

    termRef.current = term
    fitAddonRef.current = fitAddon
    eventCountRef.current = 0

    const handleResize = () => {
      try { fitAddon.fit() } catch (e) { /* ignore */ }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      term.dispose()
      termRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!termRef.current || !events) return

    const newEvents = events.slice(eventCountRef.current)
    eventCountRef.current = events.length

    for (const evt of newEvents) {
      writeEvent(termRef.current, evt)
    }
  }, [events])

  return (
    <div ref={containerRef} className="h-full w-full bg-[#0e0e0e]" />
  )
}

function writeEvent(term, evt) {
  const time = evt.timestamp
    ? new Date(evt.timestamp).toLocaleTimeString()
    : new Date().toLocaleTimeString()

  const timeStr = `\x1b[38;2;102;102;102m[${time}]\x1b[0m `

  switch (evt.event) {
    case 'BUILD_STARTED':
      term.writeln(`${timeStr}\x1b[38;2;255;110;0m▶ BUILD STARTED\x1b[0m — ${evt.project || ''}`)
      break
    case 'FILE_CHANGED':
      term.writeln(`${timeStr}\x1b[38;2;96;165;250m✏ FILE_CHANGED\x1b[0m ${evt.file || ''} — ${evt.diff || ''}`)
      break
    case 'BUILD_ERROR':
      term.writeln(`${timeStr}\x1b[38;2;248;113;113m✖ BUILD_ERROR\x1b[0m [iter ${evt.iteration || '?'}]`)
      if (evt.error) {
        for (const line of evt.error.split('\n')) {
          term.writeln(`  \x1b[38;2;248;113;113m${line}\x1b[0m`)
        }
      }
      break
    case 'FIX_APPLIED':
      term.writeln(`${timeStr}\x1b[38;2;74;222;128m🔧 FIX_APPLIED\x1b[0m ${evt.file || ''} — ${evt.summary || ''}`)
      break
    case 'TESTS_RUNNING':
      term.writeln(`${timeStr}\x1b[38;2;250;204;21m🧪 TESTS_RUNNING\x1b[0m (${evt.framework || ''})`)
      break
    case 'TEST_FAILED':
      term.writeln(`${timeStr}\x1b[38;2;248;113;113m✖ TEST_FAILED\x1b[0m ${evt.test || ''}`)
      if (evt.error) {
        for (const line of evt.error.split('\n')) {
          term.writeln(`  \x1b[38;2;248;113;113m${line}\x1b[0m`)
        }
      }
      break
    case 'BUILD_COMPLETE':
      term.writeln(`${timeStr}\x1b[38;2;74;222;128m✔ BUILD COMPLETE\x1b[0m — ${evt.project || ''}`)
      break
    case 'BUILD_FAILED':
      term.writeln(`${timeStr}\x1b[38;2;248;113;113m✖ BUILD FAILED\x1b[0m — ${evt.reason || ''}`)
      break
    default:
      term.writeln(`${timeStr}\x1b[38;2;136;136;136m${evt.event || 'UNKNOWN'}\x1b[0m ${JSON.stringify(evt).slice(0, 200)}`)
  }
}
