import { useState } from 'react'

// Cores dos gráficos (validadas para daltonismo): roxo = gasto / abaixo da
// meta, verde = ganho / meta atingida. Os textos usam sempre tons de cinza.
const COR_GASTO = '#7e22ce'
const COR_GANHO = '#059669'
const COR_ABAIXO = '#d8b4fe'

const brl = (v) => (v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const pct = (v) => `${((v ?? 0) * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`

function CardBase({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5">
      <h3 className="font-semibold text-slate-700">{title}</h3>
      {subtitle && <p className="text-xs text-slate-400 mt-0.5 mb-4">{subtitle}</p>}
      {children}
    </div>
  )
}

function Vazio() {
  return <p className="text-sm text-slate-400">Ainda não há apostas conferidas para mostrar.</p>
}

/* ---------- Meu desempenho ---------- */

function GraficoMeta({ concursos, meta }) {
  const [hover, setHover] = useState(null)
  const W = 480, H = 220, padL = 30, padR = 8, padT = 22, padB = 30
  const n = concursos.length
  const passo = (W - padL - padR) / n
  const larg = Math.max(4, Math.min(22, passo - 2))
  const y = (v) => padT + (H - padT - padB) * (1 - v / 15)
  const sel = hover != null ? concursos[hover] : null

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img"
        aria-label="Melhor acerto em cada concurso, com a linha da meta de 11 acertos"
        onMouseLeave={() => setHover(null)}>
        {[0, 5, 10, 15].map((v) => (
          <g key={v}>
            <line x1={padL} x2={W - padR} y1={y(v)} y2={y(v)} stroke="#f1f5f9" />
            <text x={padL - 6} y={y(v) + 4} textAnchor="end" fontSize="12" fill="#94a3b8">{v}</text>
          </g>
        ))}
        {concursos.map((c, i) => {
          const x = padL + i * passo + (passo - larg) / 2
          const atingiu = c.melhor_acerto >= meta
          const topo = y(c.melhor_acerto)
          const base = y(0)
          const r = Math.min(4, larg / 2)
          return (
            <g key={c.numero_concurso} onMouseEnter={() => setHover(i)} onClick={() => setHover(i)} style={{ cursor: 'pointer' }}>
              <rect x={padL + i * passo} y={padT} width={passo} height={H - padT - padB} fill="transparent" />
              <path
                d={`M${x},${base} V${topo + r} Q${x},${topo} ${x + r},${topo} H${x + larg - r} Q${x + larg},${topo} ${x + larg},${topo + r} V${base} Z`}
                fill={atingiu ? COR_GANHO : COR_ABAIXO}
                opacity={hover == null || hover === i ? 1 : 0.45}
              />
            </g>
          )
        })}
        <line x1={padL} x2={W - padR} y1={y(meta)} y2={y(meta)} stroke="#334155" strokeDasharray="4 4" strokeWidth="1.5" />
        <text x={W - padR} y={y(meta) - 6} textAnchor="end" fontSize="12" fontWeight="600" fill="#334155">meta: {meta} acertos</text>
        {n > 0 && (
          <>
            <text x={padL} y={H - 8} fontSize="12" fill="#94a3b8">#{concursos[0].numero_concurso}</text>
            <text x={W - padR} y={H - 8} textAnchor="end" fontSize="12" fill="#94a3b8">#{concursos[n - 1].numero_concurso}</text>
          </>
        )}
      </svg>
      <div className="min-h-[2.5rem] text-xs text-slate-500 mt-1">
        {sel ? (
          <>
            <span className="font-semibold text-slate-700">Concurso #{sel.numero_concurso}</span> · {sel.apostas} aposta{sel.apostas !== 1 && 's'} ·
            melhor: <span className="font-semibold text-slate-700">{sel.melhor_acerto} acertos</span> ·
            {' '}{sel.na_meta} na meta · gasto {brl(sel.gasto)} · ganho {brl(sel.ganho)}
          </>
        ) : (
          <span className="text-slate-400">Toque ou passe o mouse numa barra para ver o concurso. Cada barra mostra o seu melhor acerto naquele concurso.</span>
        )}
      </div>
    </div>
  )
}

function Distribuicao({ dist, meta }) {
  const max = Math.max(...dist.map((d) => d.apostas), 1)
  return (
    <div className="space-y-1">
      {dist.map((d) => (
        <div key={d.acertos} className="flex items-center gap-2 text-xs">
          <span className="w-16 text-slate-500 text-right">{d.acertos} acertos</span>
          <div className="flex-1 bg-slate-50 rounded h-3.5">
            <div className="h-3.5 rounded" style={{ width: `${(d.apostas / max) * 100}%`, background: d.acertos >= meta ? COR_GANHO : COR_ABAIXO }} />
          </div>
          <span className="w-8 text-slate-700 font-semibold">{d.apostas}</span>
        </div>
      ))}
    </div>
  )
}

export function CardDesempenho({ dados }) {
  if (!dados) return null
  if (!dados.apostas_conferidas) return <CardBase title="Meu desempenho"><Vazio /></CardBase>
  const { taxa_meta, chance_meta_acaso, apostas_na_meta, apostas_conferidas, meta_acertos, melhor_acerto } = dados
  const acima = taxa_meta >= chance_meta_acaso
  return (
    <CardBase title="Meu desempenho" subtitle={`Meta: pelo menos ${meta_acertos} acertos (o mínimo premiado) · só apostas simples de 15 dezenas`}>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-2 mb-4">
        <div>
          <div className="text-3xl font-bold text-slate-800">{pct(taxa_meta)}</div>
          <div className="text-xs text-slate-500">{apostas_na_meta} de {apostas_conferidas} apostas atingiram a meta</div>
        </div>
        <div>
          <div className="text-xl font-semibold text-slate-700">{melhor_acerto}</div>
          <div className="text-xs text-slate-500">melhor acerto até hoje</div>
        </div>
      </div>
      <p className="text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2 mb-4">
        Régua honesta: uma aposta feita totalmente ao acaso atinge a meta em <strong>{pct(chance_meta_acaso)}</strong> das vezes
        (cerca de 1 em {Math.round(1 / chance_meta_acaso)}). Você está {acima ? 'acima' : 'abaixo'} dessa média
        {apostas_conferidas < 200 && ' — mas com poucas apostas ainda, a diferença pode ser só sorte ou azar'}.
      </p>
      <GraficoMeta concursos={dados.concursos} meta={meta_acertos} />
      <div className="mt-4">
        <div className="text-xs font-semibold text-slate-600 mb-2">Quantas apostas fizeram cada número de acertos</div>
        <Distribuicao dist={dados.distribuicao_acertos} meta={meta_acertos} />
      </div>
    </CardBase>
  )
}

/* ---------- Balanço financeiro ---------- */

function GraficoAcumulado({ concursos }) {
  const [hover, setHover] = useState(null)
  const W = 480, H = 210, padL = 58, padR = 52, padT = 14, padB = 30
  const n = concursos.length
  const bruto = Math.max(...concursos.map((c) => Math.max(c.gasto_acumulado, c.ganho_acumulado)), 1)
  const degrau = bruto > 1000 ? 500 : bruto > 200 ? 100 : 50
  const max = Math.ceil(bruto / degrau) * degrau
  const x = (i) => padL + (n === 1 ? (W - padL - padR) / 2 : (i * (W - padL - padR)) / (n - 1))
  const y = (v) => padT + (H - padT - padB) * (1 - v / max)
  const linha = (k) => concursos.map((c, i) => `${i ? 'L' : 'M'}${x(i)},${y(c[k])}`).join(' ')
  const ult = concursos[n - 1]
  const sel = hover != null ? concursos[hover] : null
  const ticks = [0, max / 2, max]

  function mover(e) {
    const r = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - r.left) / r.width) * W
    const i = Math.round(((px - padL) / (W - padL - padR)) * (n - 1))
    setHover(Math.max(0, Math.min(n - 1, i)))
  }

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img"
        aria-label="Gasto acumulado e ganho acumulado ao longo dos concursos"
        onMouseMove={mover} onClick={mover} onMouseLeave={() => setHover(null)}>
        {ticks.map((v, i) => (
          <g key={i}>
            <line x1={padL} x2={W - padR} y1={y(v)} y2={y(v)} stroke="#f1f5f9" />
            <text x={padL - 6} y={y(v) + 4} textAnchor="end" fontSize="12" fill="#94a3b8">{`R$ ${Math.round(v).toLocaleString('pt-BR')}`}</text>
          </g>
        ))}
        <path d={linha('gasto_acumulado')} fill="none" stroke={COR_GASTO} strokeWidth="2" strokeLinejoin="round" />
        <path d={linha('ganho_acumulado')} fill="none" stroke={COR_GANHO} strokeWidth="2" strokeLinejoin="round" />
        {sel && (
          <>
            <line x1={x(hover)} x2={x(hover)} y1={padT} y2={H - padB} stroke="#cbd5e1" />
            <circle cx={x(hover)} cy={y(sel.gasto_acumulado)} r="4" fill={COR_GASTO} stroke="#fff" strokeWidth="2" />
            <circle cx={x(hover)} cy={y(sel.ganho_acumulado)} r="4" fill={COR_GANHO} stroke="#fff" strokeWidth="2" />
          </>
        )}
        <text x={x(n - 1) + 6} y={y(ult.gasto_acumulado) + 4} fontSize="12" fontWeight="600" fill="#334155">Gasto</text>
        <text x={x(n - 1) + 6} y={y(ult.ganho_acumulado) + 4} fontSize="12" fontWeight="600" fill="#334155">Ganho</text>
        <text x={padL} y={H - 6} fontSize="12" fill="#94a3b8">#{concursos[0].numero_concurso}</text>
        <text x={W - padR} y={H - 6} textAnchor="end" fontSize="12" fill="#94a3b8">#{ult.numero_concurso}</text>
      </svg>
      <div className="flex flex-wrap gap-4 text-xs text-slate-500 mt-1 min-h-[1.25rem]">
        <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block" style={{ background: COR_GASTO }} /> Gasto acumulado</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block" style={{ background: COR_GANHO }} /> Ganho acumulado</span>
        {sel && (
          <span className="text-slate-600">
            Até o #{sel.numero_concurso}: gastou <strong>{brl(sel.gasto_acumulado)}</strong>, ganhou <strong>{brl(sel.ganho_acumulado)}</strong>
          </span>
        )}
      </div>
    </div>
  )
}

export function CardBalanco({ dados }) {
  if (!dados) return null
  if (!dados.gasto_total) return <CardBase title="Balanço financeiro"><Vazio /></CardBase>
  const { gasto_total, ganho_total, saldo, retorno_por_real, apostas_pendentes, gasto_pendente, premios_a_confirmar, gasto_por_mes } = dados
  const mesAtual = gasto_por_mes[gasto_por_mes.length - 1]
  const mesAnterior = gasto_por_mes[gasto_por_mes.length - 2]
  const nomeMes = (m) => {
    const [a, mm] = m.split('-')
    return new Date(Number(a), Number(mm) - 1, 1).toLocaleDateString('pt-BR', { month: 'long' })
  }
  return (
    <CardBase title="Balanço financeiro" subtitle={`Aposta simples a ${brl(dados.preco_aposta)} · prêmios fixos: 11 = R$ 7, 12 = R$ 14, 13 = R$ 35`}>
      <div className="grid grid-cols-3 gap-1.5 sm:gap-2 mb-4">
        <div className="bg-slate-50 rounded-xl p-2.5 sm:p-3">
          <div className="text-xs text-slate-500">Gastei</div>
          <div className="text-sm sm:text-lg font-bold text-slate-800 whitespace-nowrap">{brl(gasto_total)}</div>
        </div>
        <div className="bg-slate-50 rounded-xl p-2.5 sm:p-3">
          <div className="text-xs text-slate-500">Ganhei</div>
          <div className="text-sm sm:text-lg font-bold text-slate-800 whitespace-nowrap">{brl(ganho_total)}</div>
        </div>
        <div className={`rounded-xl p-2.5 sm:p-3 ${saldo < 0 ? 'bg-red-50' : 'bg-emerald-50'}`}>
          <div className="text-xs text-slate-500">Saldo</div>
          <div className="text-sm sm:text-lg font-bold text-slate-800 whitespace-nowrap">{saldo > 0 ? '+' : ''}{brl(saldo).replace('-', '−')}</div>
        </div>
      </div>
      <p className="text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2 mb-4">
        A cada <strong>R$ 1,00</strong> apostado voltaram <strong>{brl(retorno_por_real)}</strong>.
        {mesAtual && <> Em {nomeMes(mesAtual.mes)} você já gastou <strong>{brl(mesAtual.gasto)}</strong>{mesAnterior && <> (em {nomeMes(mesAnterior.mes)}: {brl(mesAnterior.gasto)})</>}.</>}
        {apostas_pendentes > 0 && <> Há {apostas_pendentes} aposta{apostas_pendentes !== 1 && 's'} aguardando sorteio ({brl(gasto_pendente)}, já incluído no gasto).</>}
        {premios_a_confirmar > 0 && <> {premios_a_confirmar} prêmio(s) de 14/15 acertos ainda não somado(s): o valor varia por concurso — confira no site da Caixa.</>}
      </p>
      {dados.concursos.length > 0 && <GraficoAcumulado concursos={dados.concursos} />}
    </CardBase>
  )
}
