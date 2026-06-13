"use client"
import {useState} from "react"
import { Button } from "@/components/ui/button"


export default function Welcome() {
  const [gender, setGender] = useState("")
  return (
    <div className="flex flex-col justify-center">

      <div className="text-xl text-center pt-12">
        Welcome to Eon
      </div>
      <div className="text-center">Choose your life's gender</div>
      <div className="flex justify-center gap-4 mt-4">
        <button
          onClick={() => setGender("male")}
          className={`rounded-lg px-8 py-3 border ${gender === "male" ? "bg-stone-700 text-white" : "bg-white text-stone-700 border-stone-400"}`}
        >
          Male
        </button>
        <button
          onClick={() => setGender("female")}
          className={`rounded-lg px-8 py-3 border ${gender === "female" ? "bg-stone-700 text-white" : "bg-white text-stone-700 border-stone-400"}`}
        >
          Female
        </button>
      </div>

      <div className="flex justify-center mt-4">
        <Button className="flex justify-center">Start Life</Button>
      </div>
    </div>    
    
  );
}