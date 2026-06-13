"use client"
import { User, Home, MessageCircle } from "lucide-react"
import Link from "next/link"

export default function Navbar() {
    return (
      <div className="fixed bottom-0 left-0 right-0 flex justify-around items-center h-16 border-t bg-[#c4956a]">
        <Link href="/profile"><button><User size={24} /></button></Link>
        <Link href="/"><button><Home size={24} /></button></Link>
        <Link href="/messages"><button><MessageCircle size={24} /></button></Link>
      </div>
    )
  }