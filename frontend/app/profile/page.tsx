import Image from "next/image";
import React from "react";
import Navbar from "@/components/Navbar"
import { Button } from "@/components/ui/button"

const choices = ["Say yes!", "Decline politely", "Ask for more time"]

const lives = [
  { label: "Date", value: "1/2/4", gender: "female"},
  { label: "Date", value: "1/4/2", gender: "male"},
  { label: "Date", value: "4/5/2", gender: "female"},
  { label: "Date", value: "4/5/3", gender: "male"},
]

export default function Profile() {
  return (
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div>
        Name
      </div>
      <div>
        <div className="pt-4 pb-2">Your Lives</div>
          {lives.map((life, i) => (
            <div key={i} className="flex items-center gap-3 border border-stone-400 rounded-md p-3 mb-2 hover:bg-stone-500">
              <span className="text-xs w-24">{life.label}</span>
              <span className="text-xs w-6 text-right">{life.value}</span>
              <span className="text-xs w-6 text-right">{life.gender}</span>
            </div>
          ))}
        <Button>
          Start new life
        </Button>
      </div>
      <div>
        <div>Credits</div>
        <Button>Buy More Credits</Button>
      </div>
      <div>
        <Button>Log Out</Button>
      </div>
      <Navbar/>
    </div>
  );
}