"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import Navbar from "@/components/Navbar"
import { Button } from "@/components/ui/button"

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

  async function handleBuy(credits: number) {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const res = await fetch("http://localhost:8000/credits/purchase",{
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}`},
      body: JSON.stringify({ credits })
    })
    const data = await res.json()
    window.location.href = data.checkout_url

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

        {showBuyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={() => setShowBuyModal(false)}>
          <div className="bg-white rounded-xl p-8 flex flex-col gap-4 w-80" onClick={e => e.stopPropagation()}>
            <div className="text-xl font-medium">Buy Credits</div>
            <button onClick={() => handleBuy(100)} className="border rounded-lg p-3">100 Credits - $2.99</button>
            <button onClick={() => handleBuy(500)} className="border rounded-lg p-3">500 Credits - $9.99</button>
            <input
              type="number"
              value={customCredits}
              onChange={e => setCustomCredits(e.target.value)}
              placeholder="Custom amount"
              className="border rounded-lg p-3 text-sm"
            />
            <button onClick={() => handleBuy(Number(customCredits))} className="border rounded-lg p-3">
              Buy Custom Amount
            </button>
          </div>
        </div>
      )}
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