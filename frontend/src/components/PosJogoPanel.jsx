import { useState, useEffect } from 'react'
import { apostasAPI } from '../services/api'

// Painéis "Pós-Jogo": o par, olhando pra trás, do relatório de situação
// das dezenas (pré-jogo). Individual (uma aposta já conferida) e Geral
// (todas as apostas conferidas de um concurso) — ambos com painel na tela
// e opção de exportar o mesmo conteúdo em PDF.

const TENDENCIA_LABEL = {
  acima: { label: 'Acima do esperado', color: 'text-emerald-600' },
  abaixo: { label: 'Abaixo do esperado', color: 'text-red-500' },
  equilibrada: { label: 'Equilibrada', color: 'text-slate-500' },
}

function Bola({ numero, acertou }) {
  return (
    <span
      className={`w-8 h-8 rounded-full text-white text-xs font-bold flex items-center justify-center ${
        acertou ? 'bg-emerald-500' : 'bg-slate-300'
      }`}
    >
      {String(numero).padStart(2, '0')}
    </span>
  )
}

function Overlay({ titulo, subtitulo, onFechar, onExportarPdf, exportando, carregando, erro, children }) {
  return (
    <div
      className="fixed inset-0 bg-slate-900/50 flex items-start justify-center p-4 z-50 overflow-y-auto"
      onClick={onFechar}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-3xl my-8"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 p-5 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-black text-purple-700">{titulo}</h3>
            {subtitulo && <p className="text-xs text-slate-400 mt-0.5">{subtitulo}</p>}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {onExportarPdf && (
              <button
                onClick={onExportarPdf}
                disabled={exportando || carregando}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg shadow transition-all disabled:opacity-40"
              >
                {exportando ? 'Gerando…' : 'Exportar PDF'}
              </button>
            )}
            <button
              onClick={onFechar}
              className="text-slate-300 hover:text-red-400 text-xl leading-none transition-colors"
              title="Fechar"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-5">
          {carregando ? (
            <div className="text-center py-12 text-slate-400 text-sm">Carregando análise…</div>
          ) : erro ? (
            <div className="text-center py-12 text-slate-400">
              <p className="font-semibold text-slate-500">{erro}</p>
            </div>
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  )
}

function TabelaEtapas({ etapas, comAposta }) {
  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-purple-50 text-purple-700">
            <th className="text-left px-2 py-2 font-semibold rounded-l-lg">Etapa</th>
            <th className="text-left px-2 py-2 font-semibold">Faixa</th>
            {comAposta && <th className="text-left px-2 py-2 font-semibold">Apostadas</th>}
            <th className="text-left px-2 py-2 font-semibold">Sorteadas</th>
            {comAposta && <th className="text-left px-2 py-2 font-semibold">Acertadas</th>}
            <th className="text-left px-2 py-2 font-semibold rounded-r-lg">Tendência antes</th>
          </tr>
        </thead>
        <tbody>
          {etapas.map((e, i) => {
            const tend = TENDENCIA_LABEL[e.tendencia_recente] ?? TENDENCIA_LABEL.equilibrada
            return (
              <tr key={e.etapa} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                <td className="px-2 py-2 font-semibold text-slate-700 whitespace-nowrap">
                  {e.etapa} — {e.nome}
                </td>
                <td className="px-2 py-2 text-slate-500 whitespace-nowrap">
                  {String(e.inicio).padStart(2, '0')}–{String(e.fim).padStart(2, '0')}
                </td>
                {comAposta && (
                  <td className="px-2 py-2 text-slate-600">
                    {e.qtd_apostada}: {e.dezenas_apostadas.length ? e.dezenas_apostadas.map((d) => String(d).padStart(2, '0')).join(', ') : '—'}
                  </td>
                )}
                <td className="px-2 py-2 text-slate-600">
                  {e.qtd_sorteada}: {e.dezenas_sorteadas.length ? e.dezenas_sorteadas.map((d) => String(d).padStart(2, '0')).join(', ') : '—'}
                </td>
                {comAposta && (
                  <td className="px-2 py-2 text-slate-600">
                    {e.qtd_acertada}: {e.dezenas_acertadas.length ? e.dezenas_acertadas.map((d) => String(d).padStart(2, '0')).join(', ') : '—'}
                  </td>
                )}
                <td className={`px-2 py-2 font-medium ${tend.color}`}>{tend.label}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

const Disclaimer = ({ texto }) => (
  <p className="text-xs text-slate-400 mt-4 pt-4 border-t border-slate-100">
    <span className="font-semibold text-slate-500">Leitura crítica, não causal: </span>
    {texto}
  </p>
)

export function PainelPosJogoIndividual({ apostaId, onFechar }) {
  const [dados, setDados] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)
  const [exportando, setExportando] = useState(false)

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    setErro(null)
    apostasAPI
      .posJogo(apostaId)
      .then((res) => { if (ativo) setDados(res.data) })
      .catch((err) => {
        if (ativo) setErro(err.response?.data?.detail ?? 'Erro ao carregar a análise pós-jogo.')
      })
      .finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [apostaId])

  async function exportarPdf() {
    setExportando(true)
    try {
      const res = await apostasAPI.posJogoPdf(apostaId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `lotofacil-pos-jogo-aposta-${apostaId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      setErro('Erro ao gerar o PDF.')
    } finally {
      setExportando(false)
    }
  }

  const subtitulo = dados
    ? `${dados.nome_aposta} · Concurso #${dados.numero_concurso_alvo}`
    : undefined

  return (
    <Overlay
      titulo="Análise Pós-Jogo"
      subtitulo={subtitulo}
      onFechar={onFechar}
      onExportarPdf={dados ? exportarPdf : null}
      exportando={exportando}
      carregando={carregando}
      erro={erro}
    >
      {dados && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-slate-700">
              {dados.total_acertos} acertos
              {dados.premiado ? (
                <span className="ml-2 text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                  {dados.faixa_premio}
                </span>
              ) : (
                <span className="ml-2 text-xs text-slate-400">Não premiado</span>
              )}
            </h4>
          </div>

          <div className="flex flex-wrap gap-1.5 mb-4">
            {dados.dezenas_aposta.map((d) => (
              <Bola key={d} numero={d} acertou={dados.dezenas_acertadas.includes(d)} />
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4 text-xs">
            <div className="bg-slate-50 rounded-xl p-3">
              <p className="text-slate-400 mb-1">Paridade</p>
              <p className="text-slate-700 font-semibold">
                Aposta: {dados.paridade_aposta.pares}P/{dados.paridade_aposta.impares}I — Concurso: {dados.paridade_real.pares}P/{dados.paridade_real.impares}I
              </p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3">
              <p className="text-slate-400 mb-1">Repetidas do concurso anterior</p>
              <p className="text-slate-700 font-semibold">
                Aposta trazia: {dados.repetidas_previstas ?? '—'} — Concurso repetiu de fato: {dados.repetidas_reais_concurso ?? '—'}
              </p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3">
              <p className="text-slate-400 mb-1">Dezenas "quentes" na aposta</p>
              <p className="text-slate-700 font-semibold">
                {dados.quentes_na_aposta.length} na aposta, {dados.quentes_na_aposta_que_sairam.length} saíram
              </p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3">
              <p className="text-slate-400 mb-1">Dezenas "em chama" na aposta</p>
              <p className="text-slate-700 font-semibold">
                {dados.chama_na_aposta.length} na aposta, {dados.chama_na_aposta_que_sairam.length} saíram
              </p>
            </div>
          </div>

          <h4 className="font-semibold text-slate-700 mb-2 text-sm">Panorama por etapas</h4>
          <TabelaEtapas etapas={dados.etapas} comAposta />

          <Disclaimer texto='este relatório descreve o que aconteceu com esta aposta em relação aos sinais estatísticos disponíveis antes do sorteio — não é evidência de que a estratégia "funcionou" ou "falhou": só o histórico agregado valida ou derruba um critério.' />
        </div>
      )}
    </Overlay>
  )
}

export function PainelPosJogoGeral({ numeroConcurso, onFechar }) {
  const [dados, setDados] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)
  const [exportando, setExportando] = useState(false)

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    setErro(null)
    apostasAPI
      .posJogoGeral(numeroConcurso)
      .then((res) => { if (ativo) setDados(res.data) })
      .catch((err) => {
        if (ativo) setErro(err.response?.data?.detail ?? 'Erro ao carregar a análise pós-jogo do concurso.')
      })
      .finally(() => { if (ativo) setCarregando(false) })
    return () => { ativo = false }
  }, [numeroConcurso])

  async function exportarPdf() {
    setExportando(true)
    try {
      const res = await apostasAPI.posJogoGeralPdf(numeroConcurso)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `lotofacil-pos-jogo-concurso-${numeroConcurso}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      setErro('Erro ao gerar o PDF.')
    } finally {
      setExportando(false)
    }
  }

  return (
    <Overlay
      titulo="Análise Pós-Jogo do Concurso"
      subtitulo={dados ? `Concurso #${dados.numero_concurso} · ${dados.total_apostas} aposta(s) conferida(s)` : undefined}
      onFechar={onFechar}
      onExportarPdf={dados ? exportarPdf : null}
      exportando={exportando}
      carregando={carregando}
      erro={erro}
    >
      {dados && (
        <div>
          <div className="bg-slate-50 rounded-xl p-3 mb-4 text-xs text-slate-600">
            O concurso saiu com <span className="font-semibold">{dados.paridade_real.pares}P/{dados.paridade_real.impares}I</span> e{' '}
            <span className="font-semibold">{dados.repetidas_reais_concurso ?? '—'}</span> dezenas repetidas em relação ao concurso anterior:{' '}
            {dados.dezenas_sorteadas.map((d) => String(d).padStart(2, '0')).join(', ')}.
          </div>

          {dados.total_apostas === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              Nenhuma aposta conferida para este concurso ainda.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                {[
                  { label: 'Apostas conferidas', value: dados.total_apostas },
                  { label: 'Premiadas', value: dados.total_premiadas },
                  { label: 'Melhor resultado', value: `${dados.melhor_resultado} acertos` },
                  { label: 'Média de acertos', value: dados.media_acertos },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-white rounded-xl border border-slate-100 shadow-sm p-3 text-center">
                    <p className="text-lg font-black text-purple-700">{value}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{label}</p>
                  </div>
                ))}
              </div>

              <div className="overflow-x-auto -mx-1 mb-4">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-purple-50 text-purple-700">
                      <th className="text-left px-2 py-2 font-semibold rounded-l-lg">Aposta</th>
                      <th className="text-left px-2 py-2 font-semibold">Acertos</th>
                      <th className="text-left px-2 py-2 font-semibold rounded-r-lg">Resultado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.apostas.map((a, i) => (
                      <tr key={a.aposta_id} className={a.premiado ? 'bg-amber-50' : i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                        <td className="px-2 py-2 font-semibold text-slate-700">{a.nome_aposta}</td>
                        <td className="px-2 py-2 text-slate-600">{a.total_acertos}</td>
                        <td className="px-2 py-2 text-slate-600">{a.premiado ? a.faixa_premio : 'Não premiado'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <h4 className="font-semibold text-slate-700 mb-2 text-sm">Panorama por etapas deste concurso</h4>
          <TabelaEtapas etapas={dados.etapas} comAposta={false} />

          <Disclaimer texto="este relatório descreve o que aconteceu neste concurso em relação às apostas feitas e aos sinais estatísticos disponíveis antes do sorteio — não é validação de estratégia: só o histórico agregado valida ou derruba um critério." />
        </div>
      )}
    </Overlay>
  )
}
