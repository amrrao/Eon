"use client"
import {useState} from "react"
import Image from "next/image";
import React from "react";
import Navbar from "@/components/Navbar"

const texts = [
  {from:"them", message: "hey"},
  {from:"you", message: "hi"},
  {from:"them", message: "what's up"},
  {from:"you", message: "nothing much"},

]

const contacts = [
  {name:"Stacy", relationship_type: "Mother", relationship_strength: "80"},
  {name:"Braden", relationship_type: "Father", relationship_strength: "80"},
  {name:"Jordan", relationship_type: "Brother", relationship_strength: "60"},
  {name:"Adriana", relationship_type: "Sister", relationship_strength: "70"},

]
export default function messages() {
  const [selectedContact, setSelectedContact] = useState<number | null>(null)

  return (
    
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div className="flex">
        <div className="w-1/3 border-r border-stone-400 h-screen overflow-y-auto">
          {contacts.map((contact, i) => (
            <div key={i} onClick={() => setSelectedContact(i)} className="p-4 border-b border-stone-300 cursor-pointer hover:bg-stone-100">
              <div className="font-medium">{contact.name}</div>
              <div className="text-xs text-stone-500">{contact.relationship_type}</div>
              <div className="text-xs text-stone-500">{contact.relationship_strength}/100</div>
            </div>
          ))}
        </div>
        <div className="w-2/3 h-screen flex flex-col">
        {selectedContact === null ? (
          <div className="flex-1 flex items-center justify-center text-stone-400">
            Select a contact
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
            {texts.map((text, i) => (
              <div key={i} className={`flex ${text.from === "you" ? "justify-end" : "justify-start"}`}>
                <div className={`rounded-xl px-4 py-2 text-sm max-w-xs ${text.from === "you" ? "bg-stone-400 text-white" : "bg-white text-stone-800"}`}>
                  {text.message}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      </div>
      <Navbar/>
    </div>
  );
}