import Image from "next/image";
import React from "react";
import Navbar from "@/components/Navbar"

const choices = ["Say yes!", "Decline politely", "Ask for more time"]
const stats = [
  { label: "Money", value: 42, color: "#c4956a" },
  { label: "Happiness", value: 68, color: "#a67c52" },
  { label: "Intelligence", value: 75, color: "#8b6240" },
  { label: "Reputation", value: 55, color: "#d4a87a" },
]

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-stone-200">
      <div className="pt-8 pl-8 text-xl">
        Age 19
      </div>
      <div className="justify-center text-center pt-12 text-lg">
        Your classmate Sydney just asks you to be friends. What do you do?
      </div>
      <div className="flex flex-col gap-3 mt-6 ml-20 mr-20 text-center">
        {choices.map((choice, index) => (
          <div key={index} className="border border-gray-400 rounded-xl p-4 hover:bg-gray-100">
            {choice}
          </div>
        ))}
      </div>
      <div className="mt-auto pb-20 bg-stone-100 pr-8 pl-8">
      <div className="pt-4 pb-2">Life Stats</div>
        {stats.map((stat, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-xs w-24">{stat.label}</span>
            <div className="flex-1 h-1.5 bg-[#e8e0d0] rounded-full">
              <div className="h-full rounded-full" style={{ width: `${stat.value}%`, background: stat.color }} />
            </div>
            <span className="text-xs w-6 text-right">{stat.value}</span>
          </div>
        ))}
      </div>
      <Navbar/>
    </div>
    
    
  );
}