import { useState, useEffect } from 'react'
import { sorteiosAPI, apostasAPI } from '../services/api'

function Ball({ numero }) {
  return (
    <span className="w-9 h-9 rounded-full bg-purple-700 text-white flex items-center justify-center text-xs font-bold shadow-sm flex-shrink-0">
      {String(numero).padStart(2, '0')}
    </span>
  )
}

function BallSelect({ numero, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
        selected
          ? 'bg-purple-700 text-white shadow-md scale-105'
          : 'bg-purple-50 text-purple-400 border-2 border-purple-200 hover:border-purple-400 hover:bg-purple-100'
      }`}
    >
      {String(numero).padStart(2, '0')}
    </button>
  )
}

function StatBadge({ label, value }) {
  return (
    <span className="inline-flex items-center gap-1.5 bg-purple-50 text-purple-800 border border-purple-200 rounded-full px-2.5 py-1 whitespace-nowrap">
      <span className="w-1.5 h-1.5 rounded-full bg-purple-600 flex-shrink-0" />
      <span style={{ fontSize: 11 }} className="font-medium">{label}:</span>
      <span style={{ fontSize: 11 }} className="font-black">{value}</span>
    </span>
  )
}

function CardProposta({ proposta, salvo }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-black text-purple-700 uppercase tracking-wide">
          Jogo #{proposta.jogo}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] bg-purple-50 text-purple-600 border border-purple-200 px-2 py-0.5 rounded-full font-semibold">
            {proposta.estrategia}
          </span>
          {salvo && (
            <span className="text-xs bg-emerald-100 text-emerald-700 font-semibold px-2 py-0.5 rounded-full">
              Salvo
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {proposta.dezenas.map((d) => (
          <Ball key={d} numero={d} />
        ))}
      </div>

      <div className="grid grid-cols-3 gap-1.5">
        <StatBadge label="Moldura" value={proposta.moldura} />
        <StatBadge label="Centro" value={proposta.centro} />
        <StatBadge label="Repetidas" value={proposta.repetidas_ultimo} />
        <StatBadge label="Paridade" value={`${proposta.impares}I / ${proposta.pares}P`} />
      </div>
    </div>
  )
}

function CardJogoAnalise({ analise }) {
  return (
    <div className="bg-white rounded-2xl border-2 border-purple-300 shadow-sm p-5 mt-6">
      <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
        <span className="text-xs font-black text-purple-700 uppercase tracking-wide">
          Seu jogo
        </span>
        {analise.aprovado ? (
          <span className="text-xs bg-emerald-100 text-emerald-700 font-semibold px-2.5 py-1 rounded-full border border-emerald-200">
            ✓ Aprovado nos 3 filtros
          </span>
        ) : (
          <div className="flex flex-wrap gap-1.5 justify-end">
            {analise.filtros_falhos.map((f, i) => (
              <span
                key={i}
                className="text-xs bg-red-50 text-red-600 font-semibold px-2.5 py-1 rounded-full border border-red-200 whitespace-nowrap"
              >
                ⚠ {f}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {analise.dezenas.map((d) => (
          <Ball key={d} numero={d} />
        ))}
      </div>

      <div className="grid grid-cols-3 gap-1.5">
        <StatBadge label="Moldura" value={analise.moldura} />
        <StatBadge label="Centro" value={analise.centro} />
        <StatBadge label="Repetidas" value={analise.repetidas_ultimo} />
        <StatBadge label="Paridade" value={`${analise.impares}I / ${analise.pares}P`} />
      </div>
    </div>
  )
}

export default function Propostas() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [salvos, setSalvos] = useState({})
  const [msg, setMsg] = useState(null)
  const [concursoAlvo, setConcursoAlvo] = useState('')

  const [showSelector, setShowSelector] = useState(false)
  const [selecionadas, setSelecionadas] = useState(new Set())
  const [analisando, setAnalisando] = useState(false)
  const [jogoAnalise, setJogoAnalise] = useState(null)

  async function carregar() {
    setLoading(true)
    setMsg(null)
    setSalvos({})
    try {
      const res = await sorteiosAPI.proposta()
      setDados(res.data)
    } catch {
      setMsg({ tipo: 'erro', texto: 'Erro ao gerar propostas. Verifique o backend.' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() }, [])

  async function salvarTodos() {
    if (!dados?.propostas?.length) return
    setSalvando(true)
    setMsg(null)
    const novosSalvos = {}
    for (let i = 0; i < dados.propostas.length; i++) {
      const p = dados.propostas[i]
      try {
        await apostasAPI.criar({
          nome: `Proposta-${String(p.jogo).padStart(2, '0')}`,
          dezenas: p.dezenas,
          numero_concurso_alvo: concursoAlvo ? parseInt(concursoAlvo) : null,
          origem: 'ia',
        })
        novosSalvos[i] = true
      } catch {
        novosSalvos[i] = false
      }
    }
    setSalvos(novosSalvos)
    const count = Object.values(novosSalvos).filter(Boolean).length
    setMsg({
      tipo: count === dados.propostas.length ? 'ok' : 'erro',
      texto: `${count} de ${dados.propostas.length} apostas salvas.`,
    })
    setSalvando(false)
  }

  function toggleBall(d) {
    setSelecionadas((prev) => {
      const next = new Set(prev)
      if (next.has(d)) {
        next.delete(d)
      } else if (next.size < 15) {
        next.add(d)
      }
      return next
    })
    setJogoAnalise(null)
  }

  function limparSelecao() {
    setSelecionadas(new Set())
    setJogoAnalise(null)
  }

  async function analisar() {
    if (selecionadas.size !== 15) return
    setAnalisando(true)
    try {
      const res = await sorteiosAPI.analisar([...selecionadas])
      setJogoAnalise(res.data)
    } catch {
      setMsg({ tipo: 'erro', texto: 'Erro ao analisar jogo.' })
    } finally {
      setAnalisando(false)
    }
  }

  const jaSalvou = Object.keys(salvos).length > 0

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-black text-slate-800">Propostas Estatísticas</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Jogos gerados pelo funil de 3 filtros combinado com o ciclo das 25 dezenas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSelector((s) => !s)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold rounded-xl shadow transition-all"
          >
            {showSelector ? 'Fechar seletor' : '+ Jogo próprio'}
          </button>
          <button
            onClick={carregar}
            disabled={loading}
            className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Gerando…' : 'Gerar novos'}
          </button>
        </div>
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

      {showSelector && (
        <div className="border-2 border-dashed border-purple-400 rounded-2xl p-5 mb-6 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-700">Monte seu jogo</h3>
            <div className="flex items-center gap-3">
              <span
                className={`text-sm font-semibold tabular-nums ${
                  selecionadas.size === 15 ? 'text-emerald-600' : 'text-purple-600'
                }`}
              >
                {selecionadas.size} de 15 selecionadas
              </span>
              <button
                onClick={limparSelecao}
                className="text-xs text-slate-400 hover:text-slate-600 underline underline-offset-2"
              >
                Limpar
              </button>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-2 mb-5">
            {Array.from({ length: 25 }, (_, i) => i + 1).map((d) => (
              <div key={d} className="flex justify-center">
                <BallSelect
                  numero={d}
                  selected={selecionadas.has(d)}
                  onClick={() => toggleBall(d)}
                />
              </div>
            ))}
          </div>

          <button
            onClick={analisar}
            disabled={selecionadas.size !== 15 || analisando}
            className="w-full py-2.5 bg-purple-700 hover:bg-purple-600 text-white font-bold rounded-xl shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed text-sm"
          >
            {analisando ? 'Analisando…' : 'Analisar jogo'}
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-400">
          <div className="inline-block w-8 h-8 border-4 border-purple-200 border-t-purple-700 rounded-full animate-spin mb-3" />
          <p className="text-sm">Aplicando funil de 3 filtros…</p>
        </div>
      ) : dados && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-3 mb-6 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600">
            <span>Ciclo <strong className="text-purple-700">#{dados.ciclo_atual}</strong></span>
            <span className="text-slate-300">|</span>
            <span><strong>{dados.concursos_no_ciclo}</strong> sorteio{dados.concursos_no_ciclo !== 1 ? 's' : ''} no ciclo</span>
            <span className="text-slate-300">|</span>
            <span>
              Dezenas fixas:{' '}
              {dados.dezenas_fixas.length > 0
                ? <strong className="text-purple-700">{dados.dezenas_fixas.map(d => String(d).padStart(2, '0')).join(', ')}</strong>
                : <span className="text-slate-400 font-medium">nenhuma</span>}
            </span>
          </div>

          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-700">
              {dados.propostas.length} jogo{dados.propostas.length !== 1 ? 's' : ''} aprovado{dados.propostas.length !== 1 ? 's' : ''} pelos filtros
            </h3>
            {dados.propostas.length > 0 && !jaSalvou && (
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={concursoAlvo}
                  onChange={(e) => setConcursoAlvo(e.target.value)}
                  placeholder="Concurso alvo"
                  className="w-36 px-3 py-1.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                />
                <button
                  onClick={salvarTodos}
                  disabled={salvando}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-50"
                >
                  {salvando ? 'Salvando…' : 'Salvar apostas'}
                </button>
              </div>
            )}
          </div>

          {dados.propostas.length === 0 ? (
            <div className="text-center py-12 text-slate-400 bg-white rounded-2xl border border-slate-100">
              <p className="text-sm">Nenhum jogo passou pelos 3 filtros nesta rodada.</p>
              <p className="text-xs mt-1">Clique em "Gerar novos" para tentar novamente.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {dados.propostas.map((p, i) => (
                <CardProposta key={p.jogo} proposta={p} salvo={salvos[i] === true} />
              ))}
            </div>
          )}

          {jogoAnalise && <CardJogoAnalise analise={jogoAnalise} />}
        </>
      )}
    </div>
  )
}
