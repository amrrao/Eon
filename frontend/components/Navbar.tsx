import { User, Home, MessageCircle } from "lucide-react"
export default function Navbar() {
    return (
      <div className="fixed bottom-0 left-0 right-0 flex justify-around items-center h-16 border-t bg-[#c4956a]">
        <button><User size={24} /></button>
        <button><Home size={24} /></button>
        <button><MessageCircle size={24} /></button>
      </div>
    )
  }