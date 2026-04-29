import PageWrapper from '../components/layout/PageWrapper'
import TopNav from '../components/layout/TopNav'

export default function DashboardPage() {
  return (
    <PageWrapper>
      <TopNav />
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="backdrop-blur-md bg-white/5 border border-purple-500/20 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-display font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent mb-2">
            Dashboard
          </h2>
          <p className="text-gray-500 text-sm">Coming in TIP-010</p>
        </div>
      </main>
    </PageWrapper>
  )
}
