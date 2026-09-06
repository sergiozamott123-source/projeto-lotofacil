import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Apostas from './pages/Apostas'
import GerarIA from './pages/GerarIA'
import JogarManual from './pages/JogarManual'
import Propostas from './pages/Propostas'
import MotorFlexivel from './pages/MotorFlexivel'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="propostas" element={<Propostas />} />
        <Route path="gerar-ia" element={<GerarIA />} />
        <Route path="motor" element={<MotorFlexivel />} />
        <Route path="jogar-manual" element={<JogarManual />} />
        <Route path="apostas" element={<Apostas />} />
      </Route>
    </Routes>
  )
}
