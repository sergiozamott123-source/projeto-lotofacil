import { useState } from 'react'
import { motorAPI } from '../services/api'

function BallSmall({ numero }) {
  return (
    <span className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm bg-purple-700 text-white">
      {String(numero).padStart(2, '0')}
    </span>
  )
}

function CampoNumero({ label, value, onChange, min = 0, max = 100 }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
        className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
      />
    </div>
  )
}

function CampoFaixa({ label, min, max, onChangeMin, onChangeMax }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          min={0}
          max={15}
          value={min}
          onChange={(e) => onChangeMin(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
          className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
        <span className="text-slate-400 text-sm">até</span>
        <input
          type="number"
          min={0}
          max={15}
          value={max}
          onChange={(e) => onChangeMax(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
          className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
      </div>
    </div>
  )
}

function Toggle({ label, ajuda, checked, onChange }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer select-none">
      <span
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`mt-0.5 w-10 h-6 rounded-full flex items-center px-0.5 transition-all shrink-0 ${
          checked ? 'bg-purple-700 justify-end' : 'bg-slate-200 justify-start'
        }`}
      >
        <span className="w-5 h-5 rounded-full bg-white shadow" />
      </span>
      <span>
        <span className="block text-sm font-semibold text-slate-700">{label}</span>
        {ajuda && <span className="block text-xs text-slate-400 mt-0.5">{ajuda}</span>}
      </span>
    </label>
  )
}

function CardJogo({ jogo, index, salvo }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-purple-500 uppercase tracking-wide">
          Jogo #{index + 1}
        </span>
        {salvo && (
          <span className="text-xs bg-emerald-100 text-emerald-700 font-semibold px-2 py-0.5 rounded-full">
            Salvo
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {jogo.dezenas.map((d) => (
          <BallSmall key={d} numero={d} />
        ))}
      </div>

      <div className="flex flex-wrap gap-1.5 text-xs">
        <span className="bg-slate-100 text-slate-600 font-medium px-2 py-1 rounded-lg">
          {jogo.pares}P / {jogo.impares}I
        </span>
        <span className="bg-slate-100 text-slate-600 font-medium px-2 py-1 rounded-lg">
          {jogo.repetidas_concurso_anterior} repetidas
        </span>
        <span className="bg-slate-100 text-slate-600 font-medium px-2 py-1 rounded-lg">
          moldura {jogo.moldura}
        </span>
        {jogo.ciclo_relaxado && (
          <span className="bg-amber-100 text-amber-700 font-medium px-2 py-1 rounded-lg">
            ciclo relaxado
          </span>
        )}
        {jogo.ja_sorteado_antes && (
          <span className="bg-red-100 text-red-700 font-medium px-2 py-1 rounded-lg">
            combinação já saiu antes
          </span>
        )}
      </div>

      {jogo.represadas_usadas?.length > 0 && (
        <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-100">
          Represadas usadas: {jogo.represadas_usadas.map((d) => String(d).padStart(2, '0')).join(', ')}
        </p>
      )}
    </div>
  )
}

const CRITERIOS_PADRAO = {
  nJogos: 6,
  paridadeMin: 6,
  paridadeMax: 9,
  repetidasMin: 8,
  repetidasMax: 10,
  usarCiclo: true,
  evitarJaSorteados: true,
}

export default function MotorFlexivel() {
  const [criterios, setCriterios] = useState(CRITERIOS_PADRAO)
  const [concursoAlvo, setConcursoAlvo] = useState('')
  const [jogos, setJogos] = useState([])
  const [salvos, setSalvos] = useState(false)
  const [loading, setLoading] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [msg, setMsg] = useState(null)

  function montarPayload(salvar) {
    return {
      n_jogos: criterios.nJogos || 1,
      paridade_min: criterios.paridadeMin,
      paridade_max: criterios.paridadeMax,
      repetidas_min: criterios.repetidasMin,
      repetidas_max: criterios.repetidasMax,
      usar_ciclo: criterios.usarCiclo,
      evitar_ja_sorteados: criterios.evitarJaSorteados,
      salvar,
      concurso_alvo: concursoAlvo ? parseInt(concursoAlvo, 10) : null,
    }
  }

  async function gerar() {
    setLoading(true)
    setMsg(null)
    setJogos([])
    setSalvos(false)
    try {
      const res = await motorAPI.gerar(montarPayload(false))
      setJogos(res.data)
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao gerar os jogos.' })
    } finally {
      setLoading(false)
    }
  }

  async function salvarTodos() {
    setSalvando(true)
    setMsg(null)
    try {
      const res = await motorAPI.gerar(montarPayload(true))
      setJogos(res.data)
      setSalvos(true)
      setMsg({ tipo: 'ok', texto: `${res.data.length} apostas salvas.` })
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao salvar as apostas.' })
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-black text-slate-800">Motor Estatístico</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Gere quantos jogos quiser, ajustando livremente cada critério — paridade, repetidas do
          concurso anterior e uso do ciclo das dezenas represadas.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          <CampoNumero
            label="Quantidade de jogos"
            value={criterios.nJogos}
            min={1}
            max={100}
            onChange={(v) => setCriterios((c) => ({ ...c, nJogos: v }))}
          />
          <CampoNumero
            label="Concurso alvo (opcional)"
            value={concursoAlvo}
            onChange={setConcursoAlvo}
          />
          <CampoFaixa
            label="Paridade (pares)"
            min={criterios.paridadeMin}
            max={criterios.paridadeMax}
            onChangeMin={(v) => setCriterios((c) => ({ ...c, paridadeMin: v }))}
            onChangeMax={(v) => setCriterios((c) => ({ ...c, paridadeMax: v }))}
          />
          <CampoFaixa
            label="Repetidas do concurso anterior"
            min={criterios.repetidasMin}
            max={criterios.repetidasMax}
            onChangeMin={(v) => setCriterios((c) => ({ ...c, repetidasMin: v }))}
            onChangeMax={(v) => setCriterios((c) => ({ ...c, repetidasMax: v }))}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6 pt-2 border-t border-slate-100">
          <div className="pt-4">
            <Toggle
              label="Usar dezenas represadas do ciclo"
              ajuda="Prioriza dezenas que ainda não saíram no ciclo atual"
              checked={criterios.usarCiclo}
              onChange={(v) => setCriterios((c) => ({ ...c, usarCiclo: v }))}
            />
          </div>
          <div className="pt-4">
            <Toggle
              label="Evitar combinações já sorteadas"
              ajuda="Não repete uma combinação de 15 dezenas que já saiu antes"
              checked={criterios.evitarJaSorteados}
              onChange={(v) => setCriterios((c) => ({ ...c, evitarJaSorteados: v }))}
            />
          </div>
        </div>

        <button
          onClick={gerar}
          disabled={loading}
          className="w-full py-3 bg-purple-700 hover:bg-purple-600 text-white font-bold rounded-xl shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Gerando…' : 'Gerar Jogos'}
        </button>
      </div>

      {msg && (
        <div
          className={`mb-4 px-4 py-3 rounded-xl text-sm font-medium ${
            msg.tipo === 'ok'
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {msg.text}
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-slate-400">
          <div className="inline-block w-8 h-8 border-4 border-purple-200 border-t-purple-700 rounded-full animate-spin mb-3" />
          <p className="text-sm">Calculando a melhor composição…</p>
        </div>
      )}

      {jogos.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-700">
              {jogos.length} jogo{jogos.length > 1 ? 's' : ''} gerado{jogos.length > 1 ? 's' : ''}
            </h3>
            {!salvos && (
              <button
                onClick={salvarTodos}
                disabled={salvando}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-50"
              >
                {salvando ? 'Salvando…' : 'Salvar Apostas'}
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {jogos.map((jogo, i) => (
              <CardJogo key={i} jogo={jogo} index={i} salvo={salvos} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
