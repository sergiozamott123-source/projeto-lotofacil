import { Outlet, NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/gerar-ia', label: 'Gerar com IA' },
  { to: '/jogar-manual', label: 'Minha Aposta' },
  { to: '/apostas', label: 'Minhas Apostas' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-purple-900 text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-400/30 flex items-center justify-center text-lg font-black">
              L
            </div>
            <h1 className="text-lg font-bold tracking-wide">Lotofácil IA</h1>
          </div>
          <nav className="flex gap-1">
            {navItems.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `text-sm font-medium px-4 py-2 rounded-lg transition-all ${
                    isActive
                      ? 'bg-white text-purple-900 shadow'
                      : 'text-purple-200 hover:bg-purple-800 hover:text-white'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 text-center text-xs text-slate-400 py-3 bg-white">
        Lotofácil IA — análise estatística e apostas com Anthropic Claude
      </footer>
    </div>
  )
}
