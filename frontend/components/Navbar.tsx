"use client"

import { User, Home, MessageCircle, type LucideIcon } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const navItems: { href: string; icon: LucideIcon; label: string }[] = [
  { href: "/profile", icon: User, label: "Profile" },
  { href: "/home", icon: Home, label: "Home" },
  { href: "/messages", icon: MessageCircle, label: "Messages" },
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav
      className={cn(
        buttonVariants({ variant: "glass" }),
        "fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-1 rounded-full p-1.5 shadow-[0_8px_32px_rgba(0,0,0,0.18)]"
      )}
      aria-label="Main navigation"
    >
      {navItems.map(({ href, icon: Icon, label }) => {
        const isActive = pathname === href || pathname.startsWith(`${href}/`)

        return (
          <Link
            key={href}
            href={href}
            aria-label={label}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "rounded-full p-2.5 text-slate-800 outline-none select-none",
              "[-webkit-tap-highlight-color:transparent]",
              "focus-visible:outline-none focus-visible:ring-0"
            )}
          >
            <Icon size={22} strokeWidth={isActive ? 2.75 : 2} />
          </Link>
        )
      })}
    </nav>
  )
}
