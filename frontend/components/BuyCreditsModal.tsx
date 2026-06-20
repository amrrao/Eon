// components/BuyCreditsModal.tsx
"use client"
import { useState } from "react"
import { createClient } from "@/lib/client"

export default function BuyCreditsModal({ show, onClose }: { show: boolean, onClose: () => void }) {
  const [customCredits, setCustomCredits] = useState("")
  const supabase = createClient()

  async function handleBuy(credits: number) {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const res = await fetch("http://localhost:8000/credits/purchase", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ credits })
    })
    const data = await res.json()
    window.location.href = data.checkout_url
  }

  if (!show) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={onClose}>
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
  )
}