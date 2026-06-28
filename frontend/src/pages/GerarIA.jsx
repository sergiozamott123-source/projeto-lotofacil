import { useState } from 'react'
import { iaAPI, apostasAPI } from '../services/api'

function BallSmall({ numero, selected }) {
  return (
    <span
      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm ${
        selected ? 'bg-purple-700 text-white' : 'bg-purple-100 text-purple-700'
      }`}
    >
      {String(numero).padStart(2, '0')}
    </span>
  )
}

function Selector({ label, options, value, onChange }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      <div className="flex gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold border transition-all ${
              value === opt.value
                ? 'bg-purple-700 text-white border-purple-700 shadow'
                : 'bg-white text-slate-600 border-slate-200 hover:border-purple-300'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function CardJogo({ jogo, index, salvando, salvo }) {
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
        {salvando && (
          <span className="text-xs text-slate-400">Salvando…</span>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {jogo.dezenas.map((d) => (
          <BallSmall key={d} numero={d} selected />
        ))}
      </div>
      {jogo.justificativa && (
        <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-3">
          {jogo.justificativa}
        </p>
      )}
    </div>
  )
}

export default function GerarIA() {
  const [quantidade, setQuantidade] = useState(3)
  const [repetidas, setRepetidas] = useState(9)
  const [paridade, setParidade] = useState('auto')
  const [jogos, setJogos] = useState([])
  const [loading, setLoading] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [salvos, setSalvos] = useState({})
  const [msg, setMsg] = useState(null)
  const [concursoAlvo, setConcursoAlvo] = useState('')

  async function gerar() {
    setLoading(true)
    setMsg(null)
    setJogos([])
    setSalvos({})
    try {
      const res = await iaAPI.gerarJogos({ quantidade, repetidas, paridade, salvar: false })
      setJogos(res.data)
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao gerar jogos com IA.' })
    } finally {
      setLoading(false)
    }
  }

  async function salvarTodos() {
    if (!jogos.length) return
    setSalvando(true)
    setMsg(null)
    const novosSalvos = {}
    for (let i = 0; i < jogos.length; i++) {
      try {
        await apostasAPI.criar({
          nome: `IA-${repetidas}R/${paridade}-${String(i + 1).padStart(2, '0')}`,
          dezenas: jogos[i].dezenas,
          numero_concurso_alvo: concursoAlvo ? parseInt(concursoAlvo) : null,
          origem: 'ia',
        })
        novosSalvos[i] = true
      } catch {
        novosSalvos[i] = false
      }
    }
    setSalvos(novosSalvos)
    const salvosCount = Object.values(novosSalvos).filter(Boolean).length
    setMsg({
      tipo: salvosCount === jogos.length ? 'ok' : 'erro',
      texto: `${salvosCount} de ${jogos.length} apostas salvas.`,
    })
    setSalvando(false)
  }

  const jaSalvou = Object.keys(salvos).length > 0

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-black text-slate-800">Gerar Jogos com IA</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          O Claude analisa o histórico e gera apostas estratégicas
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          <Selector
            label="Quantidade de jogos"
            options={[1, 2, 3, 5, 10].map((v) => ({ value: v, label: String(v) }))}
            value={quantidade}
            onChange={setQuantidade}
          />
          <Selector
            label="Repetidas esperadas"
            options={[
              { value: 8, label: '8' },
              { value: 9, label: '9' },
              { value: 10, label: '10' },
            ]}
            value={repetidas}
            onChange={setRepetidas}
          />
          <Selector
            label="Paridade (Pares/Ímpares)"
            options={[
              { value: '6P9I', label: '6P / 9I' },
              { value: '7P8I', label: '7P / 8I' },
              { value: 'auto', label: 'Auto' },
            ]}
            value={paridade}
            onChange={setParidade}
          />
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
              Concurso alvo (opcional)
            </label>
            <input
              type="number"
              value={concursoAlvo}
              onChange={(e) => setConcursoAlvo(e.target.value)}
              placeholder="Ex: 3200"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>
        </div>

        <button
          onClick={gerar}
          disabled={loading}
          className="w-full py-3 bg-purple-700 hover:bg-purple-600 text-white font-bold rounded-xl shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Gerando com IA…' : 'Gerar com IA'}
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
          {msg.texto}
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-slate-400">
          <div className="inline-block w-8 h-8 border-4 border-purple-200 border-t-purple-700 rounded-full animate-spin mb-3" />
          <p className="text-sm">O Claude está analisando o histórico…</p>
        </div>
      )}

      {jogos.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-700">{jogos.length} jogo{jogos.length > 1 ? 's' : ''} gerado{jogos.length > 1 ? 's' : ''}</h3>
            {!jaSalvou && (
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
              <CardJogo
                key={i}
                jogo={jogo}
                index={i}
                salvando={salvando}
                salvo={salvos[i] === true}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
