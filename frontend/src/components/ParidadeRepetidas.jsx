// Situação de paridade (pares/ímpares) e de dezenas repetidas do último
// sorteio, comparada às faixas já validadas no histórico, mais um quadro
// com os últimos 5 sorteios. É uma leitura descritiva do que já saiu,
// não uma previsão. Usado no Dashboard (card Último Sorteio) e no Jogo
// Manual (card Sorteio Anterior).
//
// `historico` deve vir ordenado do mais recente para o mais antigo. Para
// calcular as repetidas do 5º sorteio é preciso o 6º, então passe pelo
// menos 6 sorteios.

const FAIXA_PARES = { min: 6, max: 9 }
const FAIXA_REPETIDAS = { min: 8, max: 10 }
const QTD_HISTORICO = 5

function contarPares(dezenas) {
  return dezenas.filter((d) => d % 2 === 0).length
}

function situacaoParidade(pares, total) {
  // As faixas foram calibradas para jogos/sorteios de 15 dezenas.
  if (total !== 15) return null
  if (pares === 7 || pares === 8) return 'comum'
  if (pares >= FAIXA_PARES.min && pares <= FAIXA_PARES.max) return 'faixa'
  return 'fora'
}

function situacaoRepetidas(repetidas) {
  if (repetidas == null) return null
  return repetidas >= FAIXA_REPETIDAS.min && repetidas <= FAIXA_REPETIDAS.max ? 'faixa' : 'fora'
}

export function montarHistoricoParidadeRepetidas(historico, quantidade = QTD_HISTORICO) {
  if (!historico || historico.length === 0) return []
  return historico.slice(0, quantidade).map((sorteio, idx) => {
    const anterior = historico[idx + 1] ?? null
    const pares = contarPares(sorteio.dezenas)
    const repetidas = anterior
      ? sorteio.dezenas.filter((d) => anterior.dezenas.includes(d)).length
      : null
    return {
      numero: sorteio.numero_concurso,
      pares,
      impares: sorteio.dezenas.length - pares,
      repetidas,
      numeroAnterior: anterior?.numero_concurso ?? null,
      sitParidade: situacaoParidade(pares, sorteio.dezenas.length),
      sitRepetidas: situacaoRepetidas(repetidas),
    }
  })
}

// Selo discreto: só verde quando está dentro da faixa; fora dela fica neutro.
function Selo({ situacao, textoFaixa }) {
  if (!situacao) return null
  const dentro = situacao !== 'fora'
  const texto =
    situacao === 'comum'
      ? 'Composição mais comum'
      : situacao === 'faixa'
      ? `Dentro da faixa (${textoFaixa})`
      : `Fora da faixa (${textoFaixa})`
  return (
    <span
      className={`text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${
        dentro ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
      }`}
    >
      {texto}
    </span>
  )
}

function Ponto({ situacao }) {
  if (!situacao) return <span className="inline-block w-2 h-2" />
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${
        situacao === 'fora' ? 'bg-slate-300' : 'bg-emerald-500'
      }`}
      aria-label={situacao === 'fora' ? 'fora da faixa' : 'dentro da faixa'}
    />
  )
}

export default function ParidadeRepetidas({ historico }) {
  const linhas = montarHistoricoParidadeRepetidas(historico)
  if (linhas.length === 0) return null
  const atual = linhas[0]

  const comRepetidas = linhas.filter((l) => l.repetidas != null)
  const paridadeOk = linhas.filter((l) => l.sitParidade && l.sitParidade !== 'fora').length
  const repetidasOk = comRepetidas.filter((l) => l.sitRepetidas === 'faixa').length

  return (
    <div className="mt-4 pt-4 border-t border-slate-100">
      {/* Situação do último sorteio */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div>
            <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold">Paridade</p>
            <p className="text-sm font-bold text-slate-700">
              {atual.pares} pares / {atual.impares} ímpares
            </p>
          </div>
          <Selo situacao={atual.sitParidade} textoFaixa="6 a 9 pares" />
        </div>
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div>
            <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold">Repetidas</p>
            <p className="text-sm font-bold text-slate-700">
              {atual.repetidas != null
                ? `${atual.repetidas} do #${atual.numeroAnterior}`
                : 'sem sorteio anterior'}
            </p>
          </div>
          <Selo situacao={atual.sitRepetidas} textoFaixa="8 a 10" />
        </div>
      </div>

      {/* Histórico dos últimos sorteios */}
      {linhas.length > 1 && (
        <div className="mt-4">
          <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold mb-1.5">
            Últimos {linhas.length} sorteios
          </p>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left font-semibold py-1">Concurso</th>
                <th className="text-left font-semibold py-1">Pares / Ímpares</th>
                <th className="text-left font-semibold py-1">Repetidas</th>
              </tr>
            </thead>
            <tbody>
              {linhas.map((l, idx) => (
                <tr key={l.numero} className="border-t border-slate-100">
                  <td className={`py-1.5 ${idx === 0 ? 'font-bold text-slate-700' : 'text-slate-600'}`}>
                    #{l.numero}
                  </td>
                  <td className="py-1.5">
                    <span className="inline-flex items-center gap-1.5 text-slate-700">
                      <Ponto situacao={l.sitParidade} />
                      {l.pares}P / {l.impares}I
                    </span>
                  </td>
                  <td className="py-1.5">
                    <span className="inline-flex items-center gap-1.5 text-slate-700">
                      <Ponto situacao={l.sitRepetidas} />
                      {l.repetidas ?? '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-[11px] text-slate-500 mt-2">
            Paridade na faixa em <strong>{paridadeOk} de {linhas.length}</strong>
            {comRepetidas.length > 0 && (
              <>
                {' · '}repetidas na faixa em <strong>{repetidasOk} de {comRepetidas.length}</strong>
              </>
            )}
          </p>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5 flex-wrap">
            <span className="inline-flex items-center gap-1"><Ponto situacao="faixa" /> na faixa</span>
            <span className="inline-flex items-center gap-1"><Ponto situacao="fora" /> fora da faixa</span>
            <span>· leitura do que já saiu, não previsão</span>
          </p>
        </div>
      )}
    </div>
  )
}
