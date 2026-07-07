"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import Navbar from "@/components/Navbar"
import BuyCreditsModal from "@/components/BuyCreditsModal"
import StartLifeModal from "@/components/StartLifeModal"


export default function Home() {
  const [game, setGame] = useState<any>(null)
  const router = useRouter()
  const supabase = createClient()
  const [choosing, setChoosing] = useState(false)
  const [showBuyModal, setShowBuyModal] = useState(false)
  const [hasNoLife, setHasNoLife] = useState(false)

  async function loadActiveLife(token: string) {
    const res = await fetch("http://localhost:8000/lives/active", {
      headers: { "Authorization": `Bearer ${token}` }
    })
    const data = await res.json()
    if (!data.life_id) {
      setHasNoLife(true)
      return
    }

    setHasNoLife(false)

    if (data.decided_choice !== null) {
      const eventRes = await fetch(`http://localhost:8000/lives/${data.life_id}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      })

      if (eventRes.status === 402) {
        setShowBuyModal(true)
        return
      }

      const newEvent = await eventRes.json()
      setGame({
        ...data,
        scenario: newEvent.scenario,
        possible_choices: newEvent.choices,
        event_id: newEvent.event_id,
      })
    } else {
      setGame({
        ...data,
        possible_choices: JSON.parse(data.possible_choices)
      })
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        router.push("/")
        return
      }
      await loadActiveLife(session.access_token)
    })
  }, [])

  if (hasNoLife) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <StartLifeModal onClose={() => {}} />
      </div>
    )
  }

  if (!game) return <div className="flex items-center justify-center min-h-screen">Loading...</div>

  async function handleChoice(choice: string) {
    setChoosing(true)
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const patchRes = await fetch(`http://localhost:8000/lives/${game.life_id}/events/${game.event_id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ decision: choice })
    })
    const updatedStats = await patchRes.json()

    if (patchRes.status === 402) {
      setShowBuyModal(true)
      setChoosing(false)
      return
    }

    const res = await fetch(`http://localhost:8000/lives/${game.life_id}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    })

    const newEvent = await res.json()
    
    setGame({
      ...game,
      money: updatedStats.money,
      happiness: updatedStats.happiness,
      intelligence: updatedStats.intelligence,
      reputation: updatedStats.reputation,
      age: updatedStats.age,
      scenario: newEvent.scenario,
      possible_choices: newEvent.choices,
      event_id: newEvent.event_id,
    })
    setChoosing(false)


  }

return (
  <div className="flex flex-col min-h-screen bg-stone-200">
    <div className="pt-8 pl-8 text-xl">
      Age: {game.age}
    </div>
    <div className="justify-center text-center pt-12 text-lg pr-20 pl-20">
      {game.scenario}
    </div>
    {choosing ? (
      <div className="text-center text-stone-500 mt-6">Your life unfolds...</div>
    ) : (
      <div className="flex flex-col gap-3 mt-6 ml-20 mr-20 text-center">
        {game.possible_choices?.map((choice: string, index: number) => (
          <div key={index} onClick={() => handleChoice(choice)} className="border border-gray-400 rounded-xl p-4 hover:bg-gray-100 cursor-pointer">
            {choice}
          </div>
        ))}
      </div>
    )}
    <div className="mt-auto pb-28 bg-stone-100 pr-8 pl-8">
      <div className="pt-4 pb-2">Life Stats</div>
      {[
        { label: "Money", value: game.money, color: "#c4956a" },
        { label: "Happiness", value: game.happiness, color: "#a67c52" },
        { label: "Intelligence", value: game.intelligence, color: "#8b6240" },
        { label: "Reputation", value: game.reputation, color: "#d4a87a" },
      ].map((stat, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs w-24">{stat.label}</span>
          <div className="flex-1 h-1.5 bg-[#e8e0d0] rounded-full">
            <div className="h-full rounded-full" style={{ width: `${stat.value}%`, background: stat.color }} />
          </div>
          <span className="text-xs w-6 text-right">{stat.value}</span>
        </div>
      ))}
    </div>
    <BuyCreditsModal show={showBuyModal} onClose={() => setShowBuyModal(false)} />
    <Navbar/>
  </div>
)}