import { useState, useEffect, useMemo } from 'react'
import { analiseAPI, sorteiosAPI, apostasAPI } from '../services/api'

const DEZENAS = Array.from({ length: 25 }, (_, i) => i + 1)

function classeDezena(d, ultimoSorteio, pendentesNoCiclo, selecionadas, sugerida) {
  const noUltimo = ultimoSorteio?.includes(d)
  const pendente = pendentesNoCiclo?.includes(d)
  const sel = selecionadas.has(d)

  let base = ''
  if (noUltimo) {
    base = sel
      ? 'bg-purple-900 text-white ring-4 ring-purple-400 scale-110 shadow-lg'
      : sugerida
      ? 'bg-purple-900 text-white ring-4 ring-amber-400 shadow-lg animate-pulse'
      : 'bg-purple-900 text-white shadow'
  } else if (pendente) {
    base = sel
      ? 'bg-amber-500 text-white ring-4 ring-amber-300 scale-110 shadow-lg'
      : 'bg-amber-400 text-white shadow-sm'
  } else {
    base = sel
      ? 'bg-purple-300 text-purple-900 ring-4 ring-purple-500 scale-110 shadow-lg'
      : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
  }

  return `w-11 h-11 rounded-full flex items-center justify-center text-sm font-bold cursor-pointer transition-all select-none ${base}`
}

export default function JogarManual() {
  const [selecionadas, setSelecionadas] = useState(new Set())
  const [nome, setNome] = useState('')
  const [concursoAlvo, setConcursoAlvo] = useState('')
  const [ultimoDezenas, setUltimoDezenas] = useState(null)
  const [pendentes, setPendentes] = useState(null)
  const [salvando, setSalvando] = useState(false)
  const [msg, setMsg] = useState(null)
  const [metaRepetidas, setMetaRepetidas] = useState(null)

  useEffect(() => {
    Promise.all([sorteiosAPI.listar(0, 1), analiseAPI.ciclo()])
      .then(([s, c]) => {
        setUltimoDezenas(s.data[0]?.dezenas ?? [])
        setPendentes(c.data.dezenas_pendentes ?? [])
      })
      .catch(() => {})
  }, [])

  function toggle(d) {
    setSelecionadas((prev) => {
      const next = new Set(prev)
      if (next.has(d)) {
        next.delete(d)
      } else if (next.size < 20) {
        next.add(d)
      }
      return next
    })
  }

  const dezenasSorted = useMemo(() => [...selecionadas].sort((a, b) => a - b), [selecionadas])

  const pares = dezenasSorted.filter((d) => d % 2 === 0).length
  const impares = dezenasSorted.length - pares
  const repetidas = useMemo(
    () => (ultimoDezenas ? dezenasSorted.filter((d) => ultimoDezenas.includes(d)).length : 0),
    [dezenasSorted, ultimoDezenas]
  )
  const faixaParidadeOk = pares >= 6 && pares <= 9
  const faixaRepetidasOk = repetidas >= 8 && repetidas <= 10

  async function salvar() {
    if (dezenasSorted.length < 15) {
      setMsg({ tipo: 'erro', texto: 'Selecione pelo menos 15 dezenas.' })
      return
    }
    if (!nome.trim()) {
      setMsg({ tipo: 'erro', texto: 'Informe um nome para a aposta.' })
      return
    }
    setSalvando(true)
    setMsg(null)
    try {
      await apostasAPI.criar({
        nome: nome.trim(),
        dezenas: dezenasSorted,
        numero_concurso_alvo: concursoAlvo ? parseInt(concursoAlvo) : null,
        origem: 'manual',
      })
      setMsg({ tipo: 'ok', texto: 'Aposta salva com sucesso!' })
      setSelecionadas(new Set())
      setNome('')
      setConcursoAlvo('')
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao salvar aposta.' })
    } finally {
      setSalvando(false)
    }
  }

  const progresso = selecionadas.size

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-black text-slate-800">Jogo Manual</h2>
        <p className="text-sm text-slate-400 mt-0.5">Selecione de 15 a 20 dezenas para montar seu jogo (apostas com mais de 15 são apostas especiais)</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex gap-3 text-sm">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-purple-900" />
                <span className="text-slate-500">Último sorteio</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-amber-400" />
                <span className="text-slate-500">Pendente no ciclo</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-purple-100 border border-purple-300" />
                <span className="text-slate-500">Disponível</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-2">
            {DEZENAS.map((d) => {
              const sugerida =
                metaRepetidas != null &&
                repetidas < metaRepetidas &&
                ultimoDezenas?.includes(d) &&
                !selecionadas.has(d)
              return (
                <div key={d} className="flex justify-center">
                  <button
                    onClick={() => toggle(d)}
                    className={classeDezena(d, ultimoDezenas, pendentes, selecionadas, sugerida)}
                  >
                    {String(d).padStart(2, '0')}
                  </button>
                </div>
              )
            })}
          </div>

          <div className="mt-5 pt-4 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <div className="flex gap-4 text-sm">
                <span>
                  <span className="font-bold text-purple-700">{pares}</span>{' '}
                  <span className="text-slate-400">pares</span>
                </span>
                <span>
                  <span className="font-bold text-purple-700">{impares}</span>{' '}
                  <span className="text-slate-400">ímpares</span>
                </span>
              </div>
              <span
                className={`text-sm font-bold ${progresso >= 15 ? 'text-emerald-600' : 'text-slate-400'}`}
              >
                {progresso}/20 selecionadas {progresso >= 15 ? '' : `(mín. 15)`}
              </span>
            </div>
            <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${progresso >= 15 ? 'bg-emerald-500' : 'bg-purple-500'}`}
                style={{ width: `${(progresso / 20) * 100}%` }}
              />
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-100">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Painel de Estratégia</h3>

            <div className="flex items-center justify-between gap-2 mb-3">
              <div>
                <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold">Paridade</p>
                <p className="text-sm font-bold text-slate-700">{pares}P / {impares}I</p>
              </div>
              <span
                className={`text-xs font-semibold px-2.5 py-1 rounded-full text-right ${
                  faixaParidadeOk ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {faixaParidadeOk ? 'Dentro da faixa ideal (6-9)' : 'Faixa ideal: 6 a 9 pares'}
              </span>
            </div>

            <div className="flex items-center justify-between gap-2 mb-3">
              <div>
                <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold">Repetidas do último sorteio</p>
                <p className="text-sm font-bold text-slate-700">
                  {repetidas} dezena{repetidas !== 1 ? 's' : ''}
                </p>
              </div>
              <span
                className={`text-xs font-semibold px-2.5 py-1 rounded-full text-right ${
                  faixaRepetidasOk ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {faixaRepetidasOk ? 'Dentro da faixa ideal (8-10)' : 'Faixa ideal: 8 a 10 repetidas'}
              </span>
            </div>

            {progresso !== 15 && (
              <p className="text-[11px] text-slate-400 mb-3 -mt-1.5">
                Faixas calibradas para jogos de 15 dezenas — em apostas especiais, use como referência.
              </p>
            )}

            <div>
              <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold mb-1.5">
                Meta de repetidas
              </p>
              <div className="flex gap-1.5">
                {[8, 9, 10].map((n) => (
                  <button
                    key={n}
                    onClick={() => setMetaRepetidas((prev) => (prev === n ? null : n))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      metaRepetidas === n
                        ? 'bg-purple-700 text-white shadow'
                        : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                    }`}
                  >
                    {n}
                  </button>
                ))}
                <button
                  onClick={() => setMetaRepetidas(null)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    metaRepetidas === null
                      ? 'bg-purple-700 text-white shadow'
                      : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                  }`}
                >
                  Livre
                </button>
              </div>
              {metaRepetidas != null && (
                <p className="text-xs mt-2 text-purple-600 font-medium">
                  {repetidas >= metaRepetidas
                    ? 'Meta atingida! O anel piscando ainda mostra outras dezenas do último sorteio disponíveis, se quiser trocar alguma.'
                    : `Faltam ${metaRepetidas - repetidas} — as dezenas com anel piscando no último sorteio ainda estão livres pra completar a meta.`}
                </p>
              )}
            </div>
          </div>

          {dezenasSorted.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {dezenasSorted.map((d) => (
                <span
                  key={d}
                  className="w-8 h-8 rounded-full bg-purple-700 text-white text-xs font-bold flex items-center justify-center"
                >
                  {String(d).padStart(2, '0')}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
            <h3 className="font-semibold text-slate-700 mb-4">Detalhes da Aposta</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                  Nome da aposta
                </label>
                <input
                  type="text"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Ex: Aposta Sorte Grande"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                  Concurso alvo
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

            {msg && (
              <div
                className={`mt-3 px-3 py-2 rounded-xl text-sm font-medium ${
                  msg.tipo === 'ok'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}
              >
                {msg.texto}
              </div>
            )}

            <button
              onClick={salvar}
              disabled={salvando || progresso < 15}
              className="mt-4 w-full py-3 bg-purple-700 hover:bg-purple-600 text-white font-bold rounded-xl shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {salvando ? 'Salvando…' : 'Salvar Aposta'}
            </button>
          </div>

          <div className="bg-purple-50 rounded-2xl border border-purple-100 p-4 text-xs text-purple-700 space-y-1">
            <p className="font-semibold mb-2">Legenda das cores:</p>
            <p>🟣 <strong>Roxo escuro</strong> — saiu no último sorteio</p>
            <p>🟠 <strong>Laranja</strong> — pendente no ciclo de 25</p>
            <p>🔵 <strong>Roxo claro</strong> — não saiu no último</p>
            <p>✨ <strong>Anel piscando</strong> — sugestão pra completar sua meta de repetidas</p>
          </div>
        </div>
      </div>
    </div>
  )
}
