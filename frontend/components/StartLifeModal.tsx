"use client"
import { useState } from "react"
import { createClient } from "@/lib/client"
import { API_URL } from "@/lib/api"

export default function StartLifeModal({ onClose }: { onClose: () => void }) {
  const [gender, setGender] = useState("")
  const [loading, setLoading] = useState(false)
  const supabase = createClient()

  async function handleStart() {
    if (!gender || loading) return
    setLoading(true)

    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const res = await fetch(`${API_URL}/lives/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ gender })
    })

    if (res.ok) {
      window.location.href = "/home"
      return
    }

    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded-xl p-8 flex flex-col gap-4 w-80" onClick={e => e.stopPropagation()}>
        <div className="text-xl font-medium">Choose your life's gender</div>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => setGender("male")}
            disabled={loading}
            className={`rounded-lg px-6 py-3 border disabled:opacity-50 ${gender === "male" ? "bg-stone-700 text-white" : "bg-white text-stone-700 border-stone-400"}`}
          >
            Male
          </button>
          <button
            onClick={() => setGender("female")}
            disabled={loading}
            className={`rounded-lg px-6 py-3 border disabled:opacity-50 ${gender === "female" ? "bg-stone-700 text-white" : "bg-white text-stone-700 border-stone-400"}`}
          >
            Female
          </button>
        </div>
        <button
          onClick={handleStart}
          disabled={loading || !gender}
          className="bg-stone-700 text-white rounded-lg py-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Starting..." : "Start Life"}
        </button>
      </div>
    </div>
  )
}
