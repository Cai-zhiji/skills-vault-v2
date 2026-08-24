import { CircleHelp } from "lucide-react"
import { Link } from "react-router-dom"

export function HelpHint({ text }: { text: string }) {
  return <Link className="help-hint" to="/help" aria-label={text} title={text}><CircleHelp /></Link>
}
