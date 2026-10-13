// Distribuição das dezenas sorteadas pelas 5 zonas fixas do volante
// (5 dezenas cada). Mostra o último sorteio como ilustração, o histórico
// dos últimos 5 sorteios e, se houver dezenas marcadas no Jogo Manual,
// quantas o jogo do usuário tem em cada zona. Leitura descritiva do que
// já saiu, não previsão.
//
// `historico` deve vir ordenado do mais recente para o mais antigo.

export const ZONAS = [
  { nome: 'Abertura', inicio: 1, fim: 5 },
  { nome: 'Início central', inicio: 6, fim: 10 },
  { nome: 'Centro', inicio: 11, fim: 15 },
  { nome: 'Centro final', inicio: 16, fim: 20 },
  { nome: 'Encerra\u00admento', inicio: 21, fim: 25 }, // \u00ad = hífen opcional (quebra só se faltar espaço)
]

// 15 de 25 dezenas saem por concurso (60%), então cada zona de 5 dezenas
// recebe em média 3 dezenas por sorteio.
const MEDIA_ESPERADA = 3
const QTD_HISTORICO = 5

const pad = (n) => String(n).padStart(2, '0')

export function contarPorZona(dezenas) {
  return ZONAS.map((z) => dezenas.filter((d) => d >= z.inicio && d <= z.fim).length)
}

function Slots({ quantidade }) {
  // Pilha de 5 casinhas, preenchidas de baixo para cima.
  return (
    <div className="flex flex-col-reverse gap-1 items-center">
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`w-6 h-2.5 rounded-sm ${i < quantidade ? 'bg-purple-900' : 'bg-slate-100'}`}
        />
      ))}
    </div>
  )
}

export default function ZonasSorteio({ historico, selecionadas }) {
  if (!historico || historico.length === 0) return null
  const ultimo = historico[0]
  const contagemUltimo = contarPorZona(ultimo.dezenas)
  const linhas = historico.slice(0, QTD_HISTORICO).map((s) => ({
    numero: s.numero_concurso,
    contagem: contarPorZona(s.dezenas),
  }))
  const medias = ZONAS.map(
    (_, i) => linhas.reduce((acc, l) => acc + l.contagem[i], 0) / linhas.length
  )
  const jogo = selecionadas && selecionadas.size > 0 ? contarPorZona([...selecionadas]) : null

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-700">Zonas do Sorteio</h3>
        <span className="text-xs text-slate-400">#{ultimo.numero_concurso}</span>
      </div>

      {/* Ilustração do último sorteio */}
      <div className="grid grid-cols-5 gap-1.5 text-center">
        {ZONAS.map((z, i) => (
          <div key={z.nome} className="flex flex-col items-center">
            <span className="text-xl font-black text-purple-800 leading-none mb-2">
              {contagemUltimo[i]}
            </span>
            <Slots quantidade={contagemUltimo[i]} />
            <span className="mt-2 px-0.5 w-full text-[10px] font-semibold text-slate-600 leading-tight min-h-[2.2em] hyphens-manual break-words">
              {z.nome}
            </span>
            <span className="text-[10px] text-slate-400">
              {pad(z.inicio)}–{pad(z.fim)}
            </span>
            {jogo && (
              <span className="mt-1 text-[10px] text-slate-500">
                seu jogo: <strong className="text-slate-700">{jogo[i]}</strong>
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Histórico dos últimos sorteios */}
      {linhas.length > 1 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold mb-1.5">
            Últimos {linhas.length} sorteios
          </p>
          <table className="w-full text-xs table-fixed">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left font-semibold py-1 w-[4.5rem]">Concurso</th>
                {ZONAS.map((z) => (
                  <th key={z.nome} className="font-semibold py-1 text-center" title={z.nome}>
                    {pad(z.inicio)}–{pad(z.fim)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {linhas.map((l, idx) => (
                <tr key={l.numero} className="border-t border-slate-100">
                  <td className={`py-1.5 ${idx === 0 ? 'font-bold text-slate-700' : 'text-slate-600'}`}>
                    #{l.numero}
                  </td>
                  {l.contagem.map((c, i) => (
                    <td key={i} className="py-1.5 text-center text-slate-700">
                      {c}
                    </td>
                  ))}
                </tr>
              ))}
              <tr className="border-t border-slate-200">
                <td className="py-1.5 font-semibold text-slate-500">Média</td>
                {medias.map((m, i) => (
                  <td key={i} className="py-1.5 text-center font-semibold text-slate-700">
                    {m.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
          <p className="text-[11px] text-slate-400 mt-2">
            Referência: em média saem {MEDIA_ESPERADA} dezenas por zona (15 de 25 sorteadas). Leitura do que já
            saiu, não previsão.
          </p>
        </div>
      )}
    </div>
  )
}
