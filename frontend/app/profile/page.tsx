"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import Navbar from "@/components/Navbar"
import { Button } from "@/components/ui/button"
import BuyCreditsModal from "@/components/BuyCreditsModal"


export default function Profile() {
  const router = useRouter()
  const supabase = createClient()
  const [lives, setLives] = useState<any[]>([])
  const [showBuyModal, setShowBuyModal] = useState(false)
  const [customCredits, setCustomCredits] = useState("")
  


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


  return (
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div>
        Name
      </div>
      <div>
        <div className="pt-4 pb-2">Your Lives</div>
          {lives.map((life, i) => (
            <div key={i} onClick={()=>handleClick(life.id)} className="flex items-center gap-3 border border-stone-400 rounded-md p-3 mb-2 hover:bg-stone-500">
              <span className="text-xs w-24">{life.gender}</span>
              <span className="text-xs w-6 text-right">{life.age}</span>
              <span className="text-xs w-6 text-right">{life.created_at}</span>
            </div>
          ))}
        <Button>
          Start new life
        </Button>
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