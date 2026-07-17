"use client"
import {useState, useEffect} from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import { API_URL } from "@/lib/api"
import Navbar from "@/components/Navbar"
import BuyCreditsModal from "@/components/BuyCreditsModal"



export default function messages() {
  const [selectedContact, setSelectedContact] = useState<string | null>(null)
  const [contacts, setContacts] = useState<any[]>([])
  const [texts, setTexts] = useState<any[]>([])
  const [message, setMessage] = useState("")
  const [life_id, setLifeID] = useState("")
  const [showBuyModal, setShowBuyModal] = useState(false)
  const [sending, setSending] = useState(false)
  const router = useRouter()
  const supabase = createClient()
  useEffect(() => {
    
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        router.push("/")
        return
      }
      const life = await fetch(`${API_URL}/lives/active`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      })
      const lifejson = await life.json()
      if (!lifejson.life_id) {
        router.push("/")
        return
      }
      const lifeId = lifejson["life_id"]
      setLifeID(lifeId)

      const data = await fetch(`${API_URL}/lives/${lifeId}/relationships`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      })
      const json = await data.json()
      setContacts(json.relationships || [])
      })
  }, [])

  async function handleSelect(life_id: string, relationship_id: string) {
    console.log("handleSelect called with:", life_id, relationship_id)
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const messages = await fetch(`${API_URL}/lives/${life_id}/relationships/${relationship_id}/messages`, {
      method: "GET",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }
    })

    const messageslist = await messages.json()
    setTexts(messageslist.messages || [])

    setSelectedContact(relationship_id)
    console.log("selectedContact:", selectedContact)


    await fetch(`${API_URL}/lives/${life_id}/relationships/${relationship_id}/messages`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    })
    

  }
  async function handleSend(relationship_id: string) {
    if (sending || !message.trim()) return
    const outgoing = message.trim()
    setMessage("")
    setSending(true)
    setTexts(prev => [...prev, { sent_by_whom: "player", message: outgoing }])

    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const res = await fetch(`${API_URL}/lives/${life_id}/relationships/${relationship_id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ message: outgoing })
    })

    if (res.status === 402) {
      setShowBuyModal(true)
      setSending(false)
      return
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      console.error("Send failed:", res.status, err)
      setSending(false)
      return
    }
    const data = await res.json()

    setTexts(prev => [...prev, { sent_by_whom: "other_person", message: data.response }])
    setContacts(contacts.map(c =>
      c.id === relationship_id
        ? {
            ...c,
            relationship_type: data.update_to_relationship_type || c.relationship_type,
            strength_number: c.strength_number + (data.update_to_relationship_strength || 0),
          }
        : c
    ))
    setSending(false)
  }

  return (
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div className="flex">
        <div className="w-1/3 h-screen overflow-y-auto bg-slate-400">
          {contacts.map((contact, i) => (
            <div key={i} onClick={() => handleSelect(life_id, contact.id)} className="p-4 border-b border-stone-600 cursor-pointer hover:bg-stone-100">
              <div className="font-medium">{contact.character_name}</div>
              <div className="text-xs text-stone-500">{contact.relationship_type}</div>
              <div className="mt-1.5 h-1.5 w-7/8 rounded-full bg-stone-300/70">
                <div
                  className="h-full rounded-full bg-slate-600"
                  style={{ width: `${Math.min(100, Math.max(0, contact.strength_number))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="w-2/3 border-l border-stone-600 h-screen flex flex-col">
          {selectedContact === null ? (
            <div className="flex-1 flex items-center justify-center text-stone-400">
              Select a contact
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
                {texts.map((text, i) => (
                  <div key={i} className={`flex ${text.sent_by_whom === "player" ? "justify-end" : "justify-start"}`}>
                    <div className={`rounded-xl px-4 py-2 text-sm max-w-xs ${text.sent_by_whom === "player" ? "bg-slate-600 text-white" : "bg-white text-stone-800"}`}>
                      {text.message}
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="rounded-xl bg-white px-4 py-2 text-sm text-stone-500">
                      ...
                    </div>
                  </div>
                )}
              </div>
              <div className="p-4 mb-20 shadow-[0_-4px_16px_rgba(0,0,0,0.08)]">
                <input
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  placeholder="Type a message..."
                  disabled={sending}
                  className="w-full rounded-lg bg-white px-3 py-2 text-sm outline-none focus:outline-none focus-visible:outline-none focus-visible:ring-0 disabled:opacity-60"
                  onKeyDown={e => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSend(selectedContact!)
                    }
                  }}
                />
              </div>
            </>
          )}
        </div>
      </div>
      <BuyCreditsModal show={showBuyModal} onClose={() => setShowBuyModal(false)} />
      <Navbar/>
    </div>
  )
}