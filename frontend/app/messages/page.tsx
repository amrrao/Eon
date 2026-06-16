"use client"
import {useState, useEffect} from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import Navbar from "@/components/Navbar"


export default function messages() {
  const [selectedContact, setSelectedContact] = useState<string | null>(null)
  const [contacts, setContacts] = useState<any[]>([])
  const [texts, setTexts] = useState<any[]>([])
  const [message, setMessage] = useState("")
  const [life_id, setLifeID] = useState("")
  const router = useRouter()
  const supabase = createClient()
  useEffect(() => {
    
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        router.push("/")
        return
      }
      const life = await fetch("http://localhost:8000/lives/active", {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      })
      const lifejson = await life.json()
      const lifeId = lifejson["life_id"]
      setLifeID(lifeId)

      const data = await fetch(`http://localhost:8000/lives/${lifeId}/relationships`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      })
      const json = await data.json()
      console.log("relationships response:", json)
      setContacts(json.relationships || [])
      })
  }, [])

  async function handleSelect(life_id: string, relationship_id: string) {
    console.log("handleSelect called with:", life_id, relationship_id)
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const messages = await fetch(`http://localhost:8000/lives/${life_id}/relationships/${relationship_id}/messages`, {
      method: "GET",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }
    })

    const messageslist = await messages.json()
    setTexts(messageslist.messages || [])

    setSelectedContact(relationship_id)
    console.log("selectedContact:", selectedContact)


    await fetch(`http://localhost:8000/lives/${life_id}/relationships/${relationship_id}/messages`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    })
    

  }
  async function handleSend(relationship_id: string) {
    console.log("handleSend called")
    const { data: { session } } = await supabase.auth.getSession()
    const token = session!.access_token

    const res = await fetch(`http://localhost:8000/lives/${life_id}/relationships/${relationship_id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ message: message })
    })
    const data = await res.json()
    console.log("data sent back:", data)
    
    setTexts(prev => [...prev, 
      { sent_by_whom: "player", message: message },
      { sent_by_whom: "other_person", message: data.response }
    ])
    setMessage("")
  }

  return (
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div className="flex">
        <div className="w-1/3 border-r border-stone-400 h-screen overflow-y-auto">
          {contacts.map((contact, i) => (
            <div key={i} onClick={() => handleSelect(life_id, contact.id)} className="p-4 border-b border-stone-300 cursor-pointer hover:bg-stone-100">
              <div className="font-medium">{contact.character_name}</div>
              <div className="text-xs text-stone-500">{contact.relationship_type}</div>
              <div className="text-xs text-stone-500">{contact.strength_number}/100</div>
            </div>
          ))}
        </div>
        <div className="w-2/3 h-screen flex flex-col">
          {selectedContact === null ? (
            <div className="flex-1 flex items-center justify-center text-stone-400">
              Select a contact
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
                {texts.map((text, i) => (
                  <div key={i} className={`flex ${text.sent_by_whom === "player" ? "justify-end" : "justify-start"}`}>
                    <div className={`rounded-xl px-4 py-2 text-sm max-w-xs ${text.sent_by_whom === "player" ? "bg-stone-400 text-white" : "bg-white text-stone-800"}`}>
                      {text.message}
                    </div>
                  </div>
                ))}
              </div>
              <div className="border border-gray-500 p-4 mb-20 flex gap-2">
                <input
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 border rounded-lg px-3 py-2 text-sm"
                  onKeyDown={e => e.key === "Enter" && handleSend(selectedContact!)}
                />
                <button
                  onClick={() => handleSend(selectedContact!)}
                  className="bg-stone-700 text-white rounded-lg px-4 py-2 text-sm"
                >
                  Send
                </button>
              </div>
            </>
          )}
        </div>
      </div>
      <Navbar/>
    </div>
  )
}