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
    <div className="flex flex-col justify-center">
      <div className="text-xl text-center pt-12">Welcome to Eon</div>

      <div className="flex justify-center mt-4">
        <Button onClick={() => {
          if (!session) {
            setShowAuth(true)
          } else {
            setShowStartLifeModal(true)
          }
        }}>
          Start Life
        </Button>
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
            <button onClick={async () => { await supabase.auth.signOut(); setSession(null) }}>
              Log Out
            </button>
          ) : (
            <button onClick={() => { setIsLogin(true); setShowAuth(true) }}>
              Sign In
            </button>
          )}
        </div>
      )}
    </div>
  )
}