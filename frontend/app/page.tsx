"use client"
import {useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {useRouter} from "next/navigation"
import { createClient } from "@/lib/client"



export default function Welcome() {
  const [gender, setGender] = useState("")
  const [showAuth, setShowAuth] = useState(false)
  const [isLogin, setIsLogin] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [startinglife, setStartingLife] = useState(true)
  const [session, setSession] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
      //change
      if (session) router.push("/home")
    })
  }, [])
  

  async function handleStartLife() {
    if (!gender) return 
    const { data: { session } } = await supabase.auth.getSession()
    if (session) {
      await createLife(session.access_token)
    } else {
      setShowAuth(true)
    }
  }

  async function handleAuth() {
    setError("")
    if (isLogin) {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) { setError(error.message); return }
      if (startinglife) {
        await createLife(data.session!.access_token)
      } else {
        router.push("/home")
      }
    } else {
      const { data, error } = await supabase.auth.signUp({ email, password })
      if (error) { setError(error.message); return }
      if (startinglife) {
        await createLife(data.session!.access_token)
      } else {
        setShowAuth(false)
        setSession(data.session)
      }
    }
  }
  async function createLife(token: string) {
    const res = await fetch("http://localhost:8000/lives/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ gender })
    })
    const data = await res.json()
    router.push("/home")
  }
  
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
        <Button onClick={handleStartLife} className="flex justify-center">Start Life</Button>
      </div>
      {showAuth && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center"
          onClick={() => setShowAuth(false)}
        >
          <div 
            className="bg-white rounded-xl p-8 flex flex-col gap-4 w-80"
            onClick={e => e.stopPropagation()}
          >
            <div className="text-xl font-medium">{isLogin ? "Log In" : "Sign Up"}</div>
            <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="border rounded-lg p-3" />
            <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} className="border rounded-lg p-3" />
            {error && <div className="text-red-500 text-sm">{error}</div>}
            <button onClick={handleAuth} className="bg-stone-700 text-white rounded-lg py-3">
              {isLogin ? "Log In" : "Sign Up"}
            </button>
            <button onClick={() => setIsLogin(!isLogin)} className="text-stone-500 text-sm">
              {isLogin ? "Need an account? Sign up" : "Already have an account? Log in"}
            </button>
          </div>
        </div>
      )}
      {!loading && (<div className="absolute top-6 right-8">
        {session ? (
          <button onClick={async () => {
            await supabase.auth.signOut()
            setSession(null)
          }}>
            Log Out
          </button>
        ) : (
          <button onClick={() => { setIsLogin(true); setShowAuth(true); setStartingLife(false) }}>
            Sign In
          </button>
        )}
      </div>
      )}

    </div>    
    
  );
}