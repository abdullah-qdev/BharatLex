import { SignInButton, SignedOut, useUser } from '@clerk/clerk-react'
import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { LogIn, Scale, FileText, Shield, Gavel } from 'lucide-react'

export default function Login() {
  const { isSignedIn } = useUser()
  const navigate = useNavigate()

  useEffect(() => {
    if (isSignedIn) navigate('/dashboard')
  }, [isSignedIn, navigate])

  return (
    <div className="min-h-screen flex w-full font-['Inter']">
      {/* Left Half - Branding & Copy */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-900 p-12 text-white relative overflow-hidden">
        {/* Subtle animated background grid */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsIDI1NSwgMjU1LCAwLjA1KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-50"></div>
        
        {/* Floating Icons */}
        <Scale className="absolute top-1/4 left-1/4 text-white/10 w-32 h-32 -rotate-12 animate-pulse" />
        <Shield className="absolute bottom-1/3 right-1/4 text-white/10 w-24 h-24 rotate-12" />
        <FileText className="absolute top-1/3 right-1/4 text-white/10 w-16 h-16 rotate-45" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="bg-white/10 p-2 rounded-xl backdrop-blur-md">
            <Gavel className="w-8 h-8 text-indigo-300" />
          </div>
          <span className="text-3xl font-bold tracking-tight">BharatLex</span>
        </div>

        <div className="relative z-10 mb-20 space-y-6 max-w-xl">
          <h1 className="text-5xl font-extrabold leading-tight tracking-tight">
            Your Legal Action Engine
          </h1>
          <p className="text-xl text-indigo-100/80 leading-relaxed font-medium">
            Empowering India with AI-driven legal intelligence. Understand your consumer rights, draft legal notices instantly, and take decisive action with confidence.
          </p>
        </div>
        
        <div className="relative z-10 text-sm text-indigo-200/60">
          © {new Date().getFullYear()} BharatLex. All rights reserved.
        </div>
      </div>

      {/* Right Half - Login Card */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-zinc-50 p-6 lg:p-12">
        <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-zinc-100 flex flex-col items-center space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold text-zinc-900 tracking-tight">Welcome back</h2>
            <p className="text-zinc-500 font-medium">Sign in to your account to continue</p>
          </div>

          <div className="w-full pt-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="w-full flex items-center justify-center gap-3 bg-zinc-900 hover:bg-zinc-800 text-white py-3.5 px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 font-semibold text-sm">
                  <LogIn className="w-5 h-5" />
                  Continue with Clerk
                </button>
              </SignInButton>
            </SignedOut>
          </div>
          
          <div className="text-center text-xs text-zinc-400 max-w-xs mx-auto">
            By clicking continue, you agree to our Terms of Service and Privacy Policy.
          </div>
        </div>
      </div>
    </div>
  )
}
