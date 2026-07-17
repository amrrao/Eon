"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import { API_URL } from "@/lib/api"
import Navbar from "@/components/Navbar"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import BuyCreditsModal from "@/components/BuyCreditsModal"
import StartLifeModal from "@/components/StartLifeModal"

function formatCreatedAt(value: string) {
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}


export default function Profile() {
  const router = useRouter()
  const supabase = createClient()
  const [showStartLifeModal, setShowStartLifeModal] = useState(false)
  const [lives, setLives] = useState<any[]>([])
  const [showBuyModal, setShowBuyModal] = useState(false)


  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        router.push("/")
        return
      }
      const data = await fetch(`${API_URL}/lives/`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      })
      const json = await data.json()
      if (!json.lives) {
        router.push("/")
        return
      }
      setLives(json.lives)
    })
  }, [])

  async function handleSignOut() {
    await supabase.auth.signOut()
    router.push('/')
  }

  async function handleClick(life_id: string) {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    await fetch(`${API_URL}/lives/${life_id}/activate`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ decision: life_id })
    })
    router.push('/home')
  }

  async function handleDelete(e: React.MouseEvent, life_id: string) {
    e.stopPropagation()
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const res = await fetch(`${API_URL}/lives/${life_id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    })

    if (res.ok) {
      setLives(prev => prev.filter(life => life.id !== life_id))
    }
  }

  return (
    <div
      className="relative flex h-screen flex-col overflow-hidden bg-cover bg-center"
      style={{ backgroundImage: "url('/profile.png')" }}
    >
      <header className="relative z-10 px-6 pt-6 pb-4">
        <div className="mb-4 flex items-center justify-end gap-3">
          <Button
            className="bg-[#1F2937] border text-sm rounded-xl p-4 shadow-[0_8px_32px_rgba(0,0,0,0.3)]"
            onClick={() => setShowStartLifeModal(true)}
          >
            Start New Life
          </Button>
          <Button
            className="bg-[#1F2937] border text-sm rounded-xl p-4 shadow-[0_8px_32px_rgba(0,0,0,0.3)]"
            onClick={() => setShowBuyModal(true)}
          >
            Buy More Credits
          </Button>
          <Button variant="glass" onClick={handleSignOut}>
            Log Out
          </Button>
        </div>
        <div className="text-center text-2xl font-medium text-[#1F2937] [text-shadow:0_8px_32px_rgba(0,0,0,0.3)]">
          Your Lives
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-34 pb-28">
        <div className="flex flex-wrap justify-start gap-6">
          {lives.map((life, i) => (
            <div
              key={i}
              onClick={() => handleClick(life.id)}
              className={cn(
                buttonVariants({ variant: "glass" }),
                "h-auto w-52 aspect-[5/7] cursor-pointer flex-col justify-between whitespace-normal p-6",
                life.is_active && "border-white/50 bg-white/20"
              )}
            >
              <div className="flex flex-col items-center gap-3 text-center">
                {life.is_active && (
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-700">
                    Current
                  </span>
                )}
                <span className="text-lg font-medium capitalize">{life.gender}</span>
                <span className="text-5xl font-semibold leading-none">{life.age}</span>
                <span className="text-md font-bold text-slate-700">{formatCreatedAt(life.created_at)}</span>
              </div>
              <button
                onClick={(e) => handleDelete(e, life.id)}
                className="mx-auto w-1/2 rounded-lg bg-slate-200/80 px-2 py-1.5 text-xs text-slate-600 transition-colors hover:bg-slate-300/80 hover:text-slate-700"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>


      {showStartLifeModal && (
        <StartLifeModal onClose={() => setShowStartLifeModal(false)} />
      )}
      <BuyCreditsModal show={showBuyModal} onClose={() => setShowBuyModal(false)} />
      <Navbar />
    </div>
  )
}
