import { useUser, UserButton } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
import { Gavel, Briefcase, FileCheck, Clock, PlusCircle } from 'lucide-react'

export default function Dashboard() {
  const { isSignedIn, user, isLoaded } = useUser()

  if (!isLoaded) return <div className="min-h-screen flex items-center justify-center font-['Inter'] text-zinc-500">Loading...</div>
  if (!isSignedIn) return <Navigate to="/login" />

  return (
    <div className="min-h-screen bg-zinc-50 font-['Inter']">
      {/* Top Navbar */}
      <nav className="bg-white border-b border-zinc-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-50 p-2 rounded-xl">
            <Gavel className="w-6 h-6 text-indigo-600" />
          </div>
          <span className="text-xl font-bold text-zinc-900 tracking-tight">BharatLex</span>
        </div>
        <div className="flex items-center gap-4">
          <button className="hidden sm:flex items-center gap-2 text-sm font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 px-4 py-2 rounded-full transition-colors">
            <PlusCircle className="w-4 h-4" />
            New Case
          </button>
          <UserButton appearance={{ elements: { avatarBox: "w-10 h-10 shadow-sm" } }} />
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12 space-y-8">
        <header>
          <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">
            Welcome, {user.firstName || 'User'}
          </h1>
          <p className="text-zinc-500 font-medium mt-1">Here is the overview of your legal actions.</p>
        </header>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <div className="bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-zinc-100 flex flex-col gap-4 transition-transform hover:-translate-y-1 duration-300">
            <div className="flex items-center justify-between">
              <span className="text-zinc-500 font-semibold text-sm">Active Cases</span>
              <div className="bg-blue-50 p-2 rounded-lg">
                <Briefcase className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <div className="text-4xl font-bold text-zinc-900">3</div>
            <div className="text-xs font-medium text-emerald-600 bg-emerald-50 self-start px-2 py-1 rounded-md">
              +1 this week
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-zinc-100 flex flex-col gap-4 transition-transform hover:-translate-y-1 duration-300">
            <div className="flex items-center justify-between">
              <span className="text-zinc-500 font-semibold text-sm">Notices Sent</span>
              <div className="bg-violet-50 p-2 rounded-lg">
                <FileCheck className="w-5 h-5 text-violet-600" />
              </div>
            </div>
            <div className="text-4xl font-bold text-zinc-900">12</div>
            <div className="text-xs font-medium text-zinc-500">
              Across 4 categories
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-zinc-100 flex flex-col gap-4 transition-transform hover:-translate-y-1 duration-300">
            <div className="flex items-center justify-between">
              <span className="text-zinc-500 font-semibold text-sm">Pending Actions</span>
              <div className="bg-amber-50 p-2 rounded-lg">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
            </div>
            <div className="text-4xl font-bold text-zinc-900">2</div>
            <div className="text-xs font-medium text-amber-600 bg-amber-50 self-start px-2 py-1 rounded-md">
              Requires attention
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}
