import { useState, useEffect, useCallback } from 'react'
import { apostasAPI, jogosAPI } from '../services/api'
import { PainelPosJogoIndividual, PainelPosJogoGeral } from '../components/PosJogoPanel'

const FAIXA_LABEL = {
  quadra: { label: 'Quadra', color: 'bg-sky-100 text-sky-700' },
  quina: { label: 'Quina', color: 'bg-indigo-100 text-indigo-700' },
  sena: { label: 'Sena', color: 'bg-purple-100 text-purple-700' },
  quatorze: { label: 'Quatorze', color: 'bg-violet-100 text-violet-700' },
  'sena máxima': { label: 'Sena Máxima', color: 'bg-amber-100 text-amber-700' },
}

function BallTiny({ numero }) {
  return (
    <span className="w-7 h-7 rounded-full bg-purple-700 text-white text-xs font-bold flex items-center justify-center">
      {String(numero).padStart(2, '0')}
    </span>
  )
}

function BadgeFaixa({ faixa }) {
  const cfg = FAIXA_LABEL[faixa] ?? { label: faixa, color: 'bg-slate-100 text-slate-600' }
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}

function CardResumo({ resumo }) {
  if (!resumo) return null
  const stats = [
    { label: 'Total de apostas', value: resumo.total_apostas },
    { label: 'Conferidas', value: resumo.total_conferidas },
    { label: 'Premiadas', value: resumo.total_premiadas },
    {
      label: 'Melhor resultado',
      value: resumo.melhor_resultado != null ? `${resumo.melhor_resultado} acertos` : '—',
    },
  ]
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {stats.map(({ label, value }) => (
        <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4 text-center">
          <p className="text-2xl font-black text-purple-700">{value}</p>
          <p className="text-xs text-slate-400 mt-1">{label}</p>
        </div>
      ))}
    </div>
  )
}

function CardAposta({ aposta, jogo, onDeletar, onConferir, conferindo, onVerPosJogo }) {
  const [expandido, setExpandido] = useState(false)

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <h4 className="font-semibold text-slate-800">{aposta.nome}</h4>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                aposta.origem === 'ia'
                  ? 'bg-violet-100 text-violet-700'
                  : 'bg-slate-100 text-slate-500'
              }`}
            >
              {aposta.origem === 'ia' ? 'IA' : 'Manual'}
            </span>
            {aposta.numero_concurso_alvo && (
              <span className="text-xs text-slate-400">Concurso #{aposta.numero_concurso_alvo}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {jogo ? (
            <div className="text-right">
              <p className="text-sm font-bold text-slate-700">{jogo.total_acertos} acertos</p>
              {jogo.faixa_premio ? (
                <BadgeFaixa faixa={jogo.faixa_premio} />
              ) : (
                <span className="text-xs text-slate-400">Não premiado</span>
              )}
            </div>
          ) : (
            <button
              onClick={() => onConferir(aposta.id)}
              disabled={conferindo}
              className="text-xs px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-700 font-semibold rounded-lg transition-all disabled:opacity-40"
            >
              {conferindo ? '…' : 'Conferir'}
            </button>
          )}
          <button
            onClick={() => onDeletar(aposta.id)}
            className="text-slate-300 hover:text-red-400 text-lg leading-none transition-colors"
            title="Excluir aposta"
          >
            ×
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => setExpandido((v) => !v)}
          className="text-xs text-slate-400 hover:text-slate-600 underline-offset-2 hover:underline"
        >
          {expandido ? 'Ocultar dezenas' : 'Ver dezenas'}
        </button>
        {jogo && (
          <button
            onClick={() => onVerPosJogo(aposta.id)}
            className="text-xs text-purple-600 hover:text-purple-800 font-medium underline-offset-2 hover:underline"
          >
            Ver Análise Pós-Jogo
          </button>
        )}
      </div>

      {expandido && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <div className="flex flex-wrap gap-1">
            {[...aposta.dezenas].sort((a, b) => a - b).map((d) => (
              <BallTiny key={d} numero={d} />
            ))}
          </div>
          {jogo && jogo.dezenas_acertadas?.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-slate-400 mb-1">Acertadas:</p>
              <div className="flex flex-wrap gap-1">
                {jogo.dezenas_acertadas.map((d) => (
                  <span
                    key={d}
                    className="w-7 h-7 rounded-full bg-emerald-500 text-white text-xs font-bold flex items-center justify-center"
                  >
                    {String(d).padStart(2, '0')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Apostas() {
  const [apostas, setApostas] = useState([])
  const [jogos, setJogos] = useState([])
  const [resumo, setResumo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [conferindoId, setConferindoId] = useState(null)
  const [conferindoTodas, setConferindoTodas] = useState(false)
  const [msg, setMsg] = useState(null)
  const [filtroConcurso, setFiltroConcurso] = useState('')
  const [exportando, setExportando] = useState(false)
  const [posJogoApostaId, setPosJogoApostaId] = useState(null)
  const [posJogoGeralConcurso, setPosJogoGeralConcurso] = useState(null)

  const carregar = useCallback(async () => {
    try {
      const [apostasRes, jogosRes, resumoRes] = await Promise.all([
        apostasAPI.listar(),
        jogosAPI.listar(),
        apostasAPI.resumo(),
      ])
      setApostas(apostasRes.data)
      setJogos(jogosRes.data)
      setResumo(resumoRes.data)
    } catch {
      setMsg({ tipo: 'erro', texto: 'Erro ao carregar apostas.' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { carregar() }, [carregar])

  const jogosPorAposta = Object.fromEntries(jogos.map((j) => [j.aposta_id, j]))

  async function conferir(id) {
    setConferindoId(id)
    setMsg(null)
    try {
      await apostasAPI.conferir(id)
      await carregar()
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao conferir.' })
    } finally {
      setConferindoId(null)
    }
  }

  async function conferirTodas() {
    setConferindoTodas(true)
    setMsg(null)
    try {
      const res = await apostasAPI.conferirTodas()
      const { total_conferidas } = res.data
      setMsg({
        tipo: 'ok',
        texto: `${total_conferidas} aposta${total_conferidas !== 1 ? 's' : ''} conferida${total_conferidas !== 1 ? 's' : ''}.`,
      })
      await carregar()
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err.response?.data?.detail ?? 'Erro ao conferir.' })
    } finally {
      setConferindoTodas(false)
    }
  }

  async function deletar(id) {
    if (!confirm('Excluir esta aposta?')) return
    try {
      await apostasAPI.deletar(id)
      setApostas((prev) => prev.filter((a) => a.id !== id))
      await carregar()
    } catch {
      setMsg({ tipo: 'erro', texto: 'Erro ao excluir.' })
    }
  }

  async function exportarPdf() {
    setExportando(true)
    setMsg(null)
    try {
      const res = await apostasAPI.exportarPdf(filtroConcurso || null)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const nomeArquivo = filtroConcurso
        ? `lotofacil-jogos-concurso-${filtroConcurso}.pdf`
        : 'lotofacil-meus-jogos.pdf'
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', nomeArquivo)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setMsg({
        tipo: 'erro',
        texto:
          err.response?.status === 404
            ? 'Nenhuma aposta encontrada para esse filtro.'
            : 'Erro ao gerar o PDF.',
      })
    } finally {
      setExportando(false)
    }
  }

  const pendentes = apostas.filter((a) => !jogosPorAposta[a.id])
  const apostasFiltradas = filtroConcurso
    ? apostas.filter((a) => String(a.numero_concurso_alvo) === filtroConcurso)
    : apostas

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-black text-slate-800">Minhas Apostas</h2>
          <p className="text-sm text-slate-400 mt-0.5">Acompanhe e confira seus jogos</p>
        </div>
        {pendentes.length > 0 && (
          <button
            onClick={conferirTodas}
            disabled={conferindoTodas}
            className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-50"
          >
            {conferindoTodas ? 'Conferindo…' : `Conferir Todas (${pendentes.length})`}
          </button>
        )}
      </div>

      <CardResumo resumo={resumo} />

      <div className="flex flex-wrap items-center gap-2 mb-4 bg-white rounded-2xl border border-slate-100 shadow-sm p-3">
        <input
          type="number"
          value={filtroConcurso}
          onChange={(e) => setFiltroConcurso(e.target.value)}
          placeholder="Filtrar por concurso (opcional)"
          className="flex-1 min-w-[180px] px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
        <button
          onClick={exportarPdf}
          disabled={exportando || apostas.length === 0}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-40"
        >
          {exportando ? 'Gerando PDF…' : 'Exportar PDF'}
        </button>
        <button
          onClick={() => setPosJogoGeralConcurso(parseInt(filtroConcurso))}
          disabled={!filtroConcurso}
          title={!filtroConcurso ? 'Informe o número do concurso acima para ver a análise pós-jogo geral' : undefined}
          className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold rounded-xl shadow transition-all disabled:opacity-40"
        >
          Análise Pós-Jogo do Concurso
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

      {loading ? (
        <div className="text-center py-16 text-slate-400 text-sm">Carregando apostas…</div>
      ) : apostas.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <p className="text-4xl mb-3">🎯</p>
          <p className="font-semibold">Nenhuma aposta cadastrada ainda.</p>
          <p className="text-sm mt-1">Use "Jogo Manual" ou "Gerar com IA" para começar.</p>
        </div>
      ) : apostasFiltradas.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <p className="text-4xl mb-3">🔍</p>
          <p className="font-semibold">Nenhuma aposta para o concurso {filtroConcurso}.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {apostasFiltradas.map((aposta) => (
            <CardAposta
              key={aposta.id}
              aposta={aposta}
              jogo={jogosPorAposta[aposta.id] ?? null}
              onDeletar={deletar}
              onConferir={conferir}
              conferindo={conferindoId === aposta.id}
              onVerPosJogo={setPosJogoApostaId}
            />
          ))}
        </div>
      )}

      {posJogoApostaId != null && (
        <PainelPosJogoIndividual apostaId={posJogoApostaId} onFechar={() => setPosJogoApostaId(null)} />
      )}
      {posJogoGeralConcurso != null && !Number.isNaN(posJogoGeralConcurso) && (
        <PainelPosJogoGeral numeroConcurso={posJogoGeralConcurso} onFechar={() => setPosJogoGeralConcurso(null)} />
      )}
    </div>
  )
}
