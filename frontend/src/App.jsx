import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Apostas from './pages/Apostas'
import GerarIA from './pages/GerarIA'
import JogarManual from './pages/JogarManual'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="gerar-ia" element={<GerarIA />} />
        <Route path="jogar-manual" element={<JogarManual />} />
        <Route path="apostas" element={<Apostas />} />
      </Route>
    </Routes>
  )
}
