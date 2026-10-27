import { useLayoutEffect, useRef, type ReactNode } from 'react'

interface RefugeDialogProps {
  open: boolean
  title: string
  onClose: () => void
  footer?: ReactNode
  children: ReactNode
}

/**
 * Modal nativo: showModal da foco y Escape. El contenido se monta solo mientras
 * está abierto; así el mapa del selector se crea con el tamaño final del diálogo.
 */
export function RefugeDialog({ open, title, onClose, footer, children }: RefugeDialogProps) {
  const ref = useRef<HTMLDialogElement>(null)

  useLayoutEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      className="refuge-dialog"
      aria-labelledby="refuge-dialog-title"
      onClose={onClose}
      onClick={(event) => { if (event.target === event.currentTarget) onClose() }}
    >
      {open ? (
        <>
          <div className="refuge-dialog-head">
            <h2 id="refuge-dialog-title">{title}</h2>
            <button type="button" className="refuge-dialog-close" onClick={onClose} aria-label="Cerrar">×</button>
          </div>
          <div className="refuge-dialog-body">{children}</div>
          {footer ? <div className="refuge-dialog-foot">{footer}</div> : null}
        </>
      ) : null}
    </dialog>
  )
}
