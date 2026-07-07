"use client"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/client"
import StartLifeModal from "@/components/StartLifeModal"

export default function Welcome() {
  const [showAuth, setShowAuth] = useState(false)
  const [isLogin, setIsLogin] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [session, setSession] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showStartLifeModal, setShowStartLifeModal] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
      if (session) router.push("/home")
    })
  }, [])

  async function handleAuth() {
    setError("")
    if (isLogin) {
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) { setError(error.message); return }
      router.push("/home")
    } else {
      const { data, error } = await supabase.auth.signUp({ email, password })
      if (error) { setError(error.message); return }
      setShowAuth(false)
      setSession(data.session)
    }
  }

  return (
    <div
      className="relative min-h-screen bg-cover bg-center"
      style={{ backgroundImage: "url('/welcome.png')" }}
    >
      <div className="absolute top-[30vh] text-[#1F2937] text-bold left-1/2 -translate-x-1/2 -translate-y-1/2">
        <div className="text-6xl text-center [text-shadow:0_8px_32px_rgba(0,0,0,0.3)]">Welcome to Eon</div>

        <div className="flex justify-center mt-6">
          <Button className="bg-[#1F2937] border text-xl rounded-xl p-4 shadow-[0_8px_32px_rgba(0,0,0,0.3)]" onClick={() => {
            if (!session) {
              setShowAuth(true)
            } else {
              setShowStartLifeModal(true)
            }
          }}>
            Start Life
          </Button>
        </div>
      </div>

      {showStartLifeModal && <StartLifeModal onClose={() => setShowStartLifeModal(false)} />}

      {showAuth && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={() => setShowAuth(false)}>
          <div className="bg-white rounded-xl p-8 flex flex-col gap-4 w-80" onClick={e => e.stopPropagation()}>
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

      {!loading && (
        <div className="absolute top-6 right-8">
          {session ? (
            <Button variant="glass" onClick={async () => { await supabase.auth.signOut(); setSession(null) }}>
              Log Out
            </Button>
          ) : (
            <Button variant="glass" onClick={() => { setIsLogin(true); setShowAuth(true) }}>
              Sign In
            </Button>
          )}
        </div>
      )}
    </div>
  )
}