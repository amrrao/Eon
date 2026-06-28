"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"

export default function StartLifeModal({ onClose }: { onClose: () => void }) {
  const [gender, setGender] = useState("")
  const router = useRouter()
  const supabase = createClient()

  async function handleStart() {
    if (!gender) return
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    await fetch("http://localhost:8000/lives/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ gender })
    })
    router.push("/home")
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded-xl p-8 flex flex-col gap-4 w-80" onClick={e => e.stopPropagation()}>
        <div className="text-xl font-medium">Choose your life's gender</div>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => setGender("male")}
            className={`rounded-lg px-6 py-3 border ${gender === "male" ? "bg-stone-700 text-white" : "bg-white text-stone-700 border-stone-400"}`}
          >
            Male
          </button>
          <button
            onClick={() => setGender("female")}
            className={`rounded-lg px-6 py-3 border ${gender === "female" ? "bg-stone-700 text-white" : "bg-white text-stone-700 border-stone-400"}`}
          >
            Female
          </button>
        </div>
        <button onClick={handleStart} className="bg-stone-700 text-white rounded-lg py-3">
          Start Life
        </button>
      </div>
    </div>
  )
}