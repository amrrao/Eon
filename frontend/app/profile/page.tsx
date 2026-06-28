"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import Navbar from "@/components/Navbar"
import { Button } from "@/components/ui/button"
import BuyCreditsModal from "@/components/BuyCreditsModal"
import StartLifeModal from "@/components/StartLifeModal"


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
      const data = await fetch("http://localhost:8000/lives/", {
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

  async function handleSignOut(){
    await supabase.auth.signOut()
    router.push('/')
  }

  async function handleClick(life_id: string) {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const patchRes = await fetch(`http://localhost:8000/lives/${life_id}/activate`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ decision: life_id })
    })
    router.push('/home')
  }

  async function handleDelete(e: React.MouseEvent, life_id: string) {
    e.stopPropagation() // prevent the parent div's onClick from also firing
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token
  
    const res = await fetch(`http://localhost:8000/lives/${life_id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    })
  
    if (res.ok) {
      setLives(prev => prev.filter(life => life.id !== life_id))
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div>
        Name
      </div>
      <div>
        <div className="pt-4 pb-2">Your Lives</div>
        {lives.map((life, i) => (
          <div key={i} onClick={() => handleClick(life.id)} className={`flex items-center justify-between gap-3 border rounded-md p-3 mb-2 hover:bg-stone-500 ${life.is_active ? "border-stone-700 bg-stone-300" : "border-stone-400"}`}>
            <div className="flex items-center gap-3">
              {life.is_active && <span className="text-xs font-medium text-stone-700">Current</span>}
              <span className="text-xs w-24">{life.gender}</span>
              <span className="text-xs w-6 text-right">{life.age}</span>
              <span className="text-xs w-6 text-right">{life.created_at}</span>
            </div>
            <button
              onClick={(e) => handleDelete(e, life.id)}
              className="text-xs text-red-600 border border-red-300 rounded px-2 py-1 hover:bg-red-50"
            >
              Delete
            </button>
          </div>
        ))}
        <Button onClick={() => setShowStartLifeModal(true)}>Start New Life</Button>
        {showStartLifeModal && <StartLifeModal onClose={() => setShowStartLifeModal(false)} />}
      </div>
      <div>
        <div>Credits</div>
        <Button onClick={() => setShowBuyModal(true)}>Buy More Credits</Button>

        <BuyCreditsModal show={showBuyModal} onClose={() => setShowBuyModal(false)} />
      </div>
      <div>
        <button className="border border-gray-600 rounded-lg p-1" onClick={handleSignOut}>
              Log Out
        </button>
            
      </div>
      <Navbar/>
    </div>
  );
}