import { useState, useEffect, useCallback } from 'react'
import { analiseAPI, sorteiosAPI } from '../services/api'

function Ball({ numero, variant = 'default', size = 'md' }) {
  const sizeClass = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm'
  const variants = {
    default: 'bg-slate-100 text-slate-500',
    pendente: 'bg-purple-900 text-white',
    sorteada: 'bg-emerald-500 text-white',
    destaque: 'bg-purple-600 text-white',
  }
  return (
    <div className={`${sizeClass} ${variants[variant]} rounded-full flex items-center justify-center font-bold shadow-sm`}>
      {String(numero).padStart(2, '0')}
    </div>
  )
}

function Card({ title, children, action }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-700">{title}</h3>
        {action}
      </div>
      {children}
    </div>
  )
}

function Skeleton({ className = '' }) {
  return <div className={`animate-pulse bg-slate-100 rounded-lg ${className}`} />
}

function CardCiclo({ ciclo }) {
  if (!ciclo) return <Skeleton className="h-64" />
  const { dezenas_pendentes, dezenas_sorteadas, numero_ciclo_atual, concursos_no_ciclo } = ciclo
  return (
    <Card title="Ciclo das 25 Dezenas">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-xs bg-purple-100 text-purple-700 font-semibold px-2 py-1 rounded-full">
          Ciclo #{numero_ciclo_atual}
        </span>
        <span className="text-xs text-slate-400">
          {concursos_no_ciclo.length} sorteio{concursos_no_ciclo.length !== 1 ? 's' : ''} no ciclo
        </span>
      </div>
      <div className="grid grid-cols-5 gap-1.5">
        {Array.from({ length: 25 }, (_, i) => i + 1).map((d) => (
          <div key={d} className="flex justify-center">
            <Ball
              numero={d}
              variant={dezenas_pendentes.includes(d) ? 'pendente' : 'sorteada'}
              size="sm"
            />
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-purple-900 inline-block" />
          Pendentes ({dezenas_pendentes.length})
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
          Saíram ({dezenas_sorteadas.length})
        </span>
      </div>
    </Card>
  )
}

function CardParidade({ paridade }) {
  if (!paridade) return <Skeleton className="h-64" />
  const top6 = [...paridade]
    .sort((a, b) => b.total_ocorrencias - a.total_ocorrencias)
    .slice(0, 6)
  const max = Math.max(...top6.map((p) => p.percentual), 1)

  return (
    <Card title="Atraso de Paridade (P/I)">
      <div className="space-y-3">
        {top6.map((p) => (
          <div key={p.composicao}>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">{p.composicao}</span>
              <div className="flex gap-2 text-slate-400">
                <span>{p.percentual}%</span>
                <span
                  className={`font-medium ${p.atraso_atual === 0 ? 'text-emerald-600' : p.atraso_atual > 5 ? 'text-red-500' : 'text-amber-500'}`}
                >
                  {p.atraso_atual === 0 ? 'Último' : `−${p.atraso_atual}`}
                </span>
              </div>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 rounded-full transition-all"
                style={{ width: `${(p.percentual / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

function CardRepetidas({ repetidas }) {
  if (!repetidas) return <Skeleton className="h-64" />
  return (
    <Card title="Dezenas Repetidas Consecutivas">
      <div className="space-y-2">
        {repetidas.map((r) => (
          <div
            key={r.quantidade_repetidas}
            className={`flex items-center justify-between p-3 rounded-xl border ${
              r.is_ouro
                ? 'border-amber-200 bg-amber-50'
                : 'border-slate-100 bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`text-lg font-black ${r.is_ouro ? 'text-amber-500' : 'text-slate-400'}`}
              >
                {r.quantidade_repetidas}
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  repetidas{' '}
                  {r.is_ouro && (
                    <span className="text-xs bg-amber-400 text-white px-1.5 py-0.5 rounded-full ml-1">
                      Ouro
                    </span>
                  )}
                </p>
                <p className="text-xs text-slate-400">{r.percentual}% dos sorteios</p>
              </div>
            </div>
            <div className="text-right">
              <p
                className={`text-sm font-bold ${
                  r.atraso_atual === 0
                    ? 'text-emerald-600'
                    : r.atraso_atual > 5
                    ? 'text-red-500'
                    : 'text-amber-500'
                }`}
              >
                {r.atraso_atual === 0 ? 'Hoje' : `−${r.atraso_atual}`}
              </p>
              <p className="text-xs text-slate-400">atraso</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

// Uma dezena é "quente" quando vem saindo em concursos seguidos, sem
// falhar nenhum, contando a partir do sorteio mais recente. `historico`
// deve vir ordenado do mais recente para o mais antigo.
function calcularDezenasQuentes(historico, minStreak = 3) {
  const quentes = new Set()
  if (!historico || historico.length === 0) return quentes
  const ultimo = historico[0]
  for (const d of ultimo.dezenas) {
    let streak = 0
    for (const sorteio of historico) {
      if (sorteio.dezenas.includes(d)) streak++
      else break
    }
    if (streak >= minStreak) quentes.add(d)
  }
  return quentes
}

function CardDinamicaDezenas({ historico }) {
  if (!historico || historico.length === 0) {
    return (
      <div className="md:col-span-2">
        <Skeleton className="h-64" />
      </div>
    )
  }
  const ultimoDezenas = historico[0].dezenas
  const quentes = calcularDezenasQuentes(historico)

  return (
    <div className="md:col-span-2">
      <Card
        title="Dinâmica das Dezenas"
        action={
          <span className="text-xs text-slate-400">
            <span className="font-semibold text-purple-700">{ultimoDezenas.length}</span> saíram no último
            {' · '}
            <span className="font-semibold text-orange-600">{quentes.size}</span> em sequência
          </span>
        }
      >
        <div className="grid grid-cols-5 gap-2">
          {Array.from({ length: 25 }, (_, i) => i + 1).map((d) => {
            const saiu = ultimoDezenas.includes(d)
            const quente = quentes.has(d)
            let classe = 'bg-slate-100 text-slate-400'
            if (saiu && quente) classe = 'bg-orange-500 text-white shadow'
            else if (saiu) classe = 'bg-purple-900 text-white shadow'
            return (
              <div key={d} className="flex justify-center">
                <div className="relative">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${classe}`}
                  >
                    {String(d).padStart(2, '0')}
                  </div>
                  {saiu && quente && (
                    <span className="absolute -top-1 -right-1 text-[11px] leading-none pointer-events-none">
                      🔥
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        <div className="flex flex-wrap gap-4 mt-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-slate-100 border border-slate-200 inline-block" />
            Não saiu no último
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-purple-900 inline-block" />
            Saiu no último
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-orange-500 inline-block" />
            🔥 Saiu e está em sequência (3+ concursos seguidos sem falhar)
          </span>
        </div>
      </Card>
    </div>
  )
}

function CardUltimoSorteio({ sorteio }) {
  if (!sorteio) return <Skeleton className="h-48" />
  const data = new Date(sorteio.data_sorteio).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
  return (
    <Card title="Último Sorteio">
      <div className="mb-3">
        <span className="text-2xl font-black text-purple-700">#{sorteio.numero_concurso}</span>
        <p className="text-xs text-slate-400 mt-0.5">{data}</p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {[...sorteio.dezenas].sort((a, b) => a - b).map((d) => (
          <Ball key={d} numero={d} variant="destaque" size="sm" />
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5 text-xs text-slate-500">
        <span>{sorteio.total_pares}P / {sorteio.total_impares}I</span>
        <span>•</span>
        <span>
          {sorteio.dezenas_repetidas?.length ?? 0} repetidas do #{sorteio.numero_concurso_anterior ?? '?'}:{' '}
          {sorteio.dezenas_repetidas?.length > 0
            ? sorteio.dezenas_repetidas.map((d) => String(d).padStart(2, '0')).join(', ')
            : '—'}
        </span>
      </div>
    </Card>
  )
}

export default function Dashboard() {
  const [radar, setRadar] = useState(null)
  const [ultimoSorteio, setUltimoSorteio] = useState(null)
  const [historicoSorteios, setHistoricoSorteios] = useState(null)
  const [loading, setLoading] = useState(true)
  const [atualizando, setAtualizando] = useState(false)
  const [msg, setMsg] = useState(null)
  const [mostrarManual, setMostrarManual] = useState(false)
  const [concursoManual, setConcursoManual] = useState('')
  const [dataManual, setDataManual] = useState('')
  const [dezenasManual, setDezenasManual] = useState(new Set())
  const [salvandoManual, setSalvandoManual] = useState(false)

  const carregar = useCallback(async () => {
    try {
      const [radarRes, ultimoRes, historicoRes] = await Promise.all([
        analiseAPI.radar(),
        sorteiosAPI.ultimo(),
        sorteiosAPI.listar(0, 15),
      ])
      setRadar(radarRes.data)
      setUltimoSorteio(ultimoRes.data ?? null)
      setHistoricoSorteios(historicoRes.data ?? [])
    } catch {
      setMsg({ tipo: 'erro', texto: 'Erro ao carregar dados. Verifique o backend.' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { carregar() }, [carregar])

  async function atualizar() {
    setAtualizando(true)
    setMsg(null)
    try {
      const res = await sorteiosAPI.atualizar()
      setMsg({ tipo: 'ok', texto: res.data.mensagem ?? 'Base atualizada!' })
      await carregar()
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao atualizar.' })
    } finally {
      setAtualizando(false)
    }
  }

  function toggleDezenaManual(d) {
    setDezenasManual((prev) => {
      const next = new Set(prev)
      if (next.has(d)) {
        next.delete(d)
      } else if (next.size < 15) {
        next.add(d)
      }
      return next
    })
  }

  async function registrarManual() {
    const dezenasArr = [...dezenasManual].sort((a, b) => a - b)
    if (dezenasArr.length !== 15) {
      setMsg({ tipo: 'erro', texto: 'Selecione exatamente 15 dezenas.' })
      return
    }
    if (!concursoManual || !dataManual) {
      setMsg({ tipo: 'erro', texto: 'Informe o número do concurso e a data do sorteio.' })
      return
    }
    setSalvandoManual(true)
    setMsg(null)
    try {
      const res = await sorteiosAPI.registrarManual({
        numero_concurso: parseInt(concursoManual),
        data_sorteio: dataManual,
        dezenas: dezenasArr,
      })
      const conferidas = res.data.apostas_conferidas_automaticamente ?? 0
      setMsg({
        tipo: res.data.status === 'ja_existe' ? 'erro' : 'ok',
        texto:
          res.data.status === 'ja_existe'
            ? `O concurso ${concursoManual} já estava cadastrado.`
            : `Concurso ${concursoManual} cadastrado! ${conferidas} aposta${conferidas !== 1 ? 's' : ''} conferida${conferidas !== 1 ? 's' : ''} automaticamente.`,
      })
      setConcursoManual('')
      setDataManual('')
      setDezenasManual(new Set())
      setMostrarManual(false)
      await carregar()
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao cadastrar o sorteio.' })
    } finally {
      setSalvandoManual(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-black text-slate-800">Radar Estratégico</h2>
          <p className="text-sm text-slate-400 mt-0.5">Análise do histórico para apostar com inteligência</p>
        </div>
        <button
          onClick={atualizar}
          disabled={atualizando}
          className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {atualizando ? 'Atualizando…' : 'Atualizar Base'}
        </button>
      </div>

      <div className="mb-4">
        <button
          onClick={() => setMostrarManual((v) => !v)}
          className="text-xs text-slate-400 hover:text-slate-600 underline-offset-2 hover:underline"
        >
          {mostrarManual
            ? 'Cancelar cadastro manual'
            : 'A Caixa já divulgou um resultado novo e o sistema não pegou? Cadastre manualmente'}
        </button>

        {mostrarManual && (
          <div className="mt-3 bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
            <h3 className="font-semibold text-slate-700 mb-1">Cadastrar resultado manualmente</h3>
            <p className="text-xs text-slate-400 mb-4">
              Use quando "Atualizar Base" não conseguir buscar sozinho. Confira os números no site oficial da Caixa antes de salvar.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                  Número do concurso
                </label>
                <input
                  type="number"
                  value={concursoManual}
                  onChange={(e) => setConcursoManual(e.target.value)}
                  placeholder="Ex: 3780"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                  Data do sorteio
                </label>
                <input
                  type="date"
                  value={dataManual}
                  onChange={(e) => setDataManual(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                />
              </div>
            </div>

            <label className="block text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">
              Dezenas sorteadas ({dezenasManual.size}/15)
            </label>
            <div className="grid grid-cols-5 sm:grid-cols-8 gap-2 mb-4">
              {Array.from({ length: 25 }, (_, i) => i + 1).map((d) => (
                <button
                  key={d}
                  onClick={() => toggleDezenaManual(d)}
                  className={`w-10 h-10 rounded-full text-sm font-bold transition-all ${
                    dezenasManual.has(d)
                      ? 'bg-purple-700 text-white ring-2 ring-purple-400 scale-105'
                      : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                  }`}
                >
                  {String(d).padStart(2, '0')}
                </button>
              ))}
            </div>

            <button
              onClick={registrarManual}
              disabled={salvandoManual || dezenasManual.size !== 15}
              className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {salvandoManual ? 'Salvando…' : 'Salvar resultado'}
            </button>
          </div>
        )}
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

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-64" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardCiclo ciclo={radar?.ciclo} />
          <CardUltimoSorteio sorteio={ultimoSorteio} />
          <CardParidade paridade={radar?.paridade} />
          <CardRepetidas repetidas={radar?.repetidas} />
          <CardDinamicaDezenas historico={historicoSorteios} />
        </div>
      )}
    </div>
  )
}
