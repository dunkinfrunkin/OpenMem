import {type ReactNode, useState, useEffect, useRef} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

/* ── Inline SVG logos (16x16, transparent bg) ── */

const LogoPython = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path fill="#3776AB" d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09z"/>
    <path fill="#FFD43B" d="M21.1 6.11l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>
  </svg>
);

const LogoClaude = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="m3.127 10.604 3.135-1.76.053-.153-.053-.085H6.11l-.525-.032-1.791-.048-1.554-.065-1.505-.08-.38-.081L0 7.832l.036-.234.32-.214.455.04 1.009.069 1.513.105 1.097.064 1.626.17h.259l.036-.105-.089-.065-.068-.064-1.566-1.062-1.695-1.121-.887-.646-.48-.327-.243-.306-.104-.67.435-.48.585.04.15.04.593.456 1.267.981 1.654 1.218.242.202.097-.068.012-.049-.109-.181-.9-1.626-.96-1.655-.428-.686-.113-.411a2 2 0 0 1-.068-.484l.496-.674L4.446 0l.662.089.279.242.411.94.666 1.48 1.033 2.014.302.597.162.553.06.17h.105v-.097l.085-1.134.157-1.392.154-1.792.052-.504.25-.605.497-.327.387.186.319.456-.045.294-.19 1.23-.37 1.93-.243 1.29h.142l.161-.16.654-.868 1.097-1.372.484-.545.565-.601.363-.287h.686l.505.751-.226.775-.707.895-.585.759-.839 1.13-.524.904.048.072.125-.012 1.897-.403 1.024-.186 1.223-.21.553.258.06.263-.218.536-1.307.323-1.533.307-2.284.54-.028.02.032.04 1.029.098.44.024h1.077l2.005.15.525.346.315.424-.053.323-.807.411-3.631-.863-.872-.218h-.12v.073l.726.71 1.331 1.202 1.667 1.55.084.383-.214.302-.226-.032-1.464-1.101-.565-.497-1.28-1.077h-.084v.113l.295.432 1.557 2.34.08.718-.112.234-.404.141-.444-.08-.911-1.28-.94-1.44-.759-1.291-.093.053-.448 4.821-.21.246-.484.186-.403-.307-.214-.496.214-.98.258-1.28.21-1.016.19-1.263.112-.42-.008-.028-.092.012-.953 1.307-1.448 1.957-1.146 1.227-.274.109-.477-.247.045-.44.266-.39 1.586-2.018.956-1.25.617-.723-.004-.105h-.036l-4.212 2.736-.75.096-.324-.302.04-.496.154-.162 1.267-.871z"/>
  </svg>
);

const LogoCursor = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M11.503.131 1.891 5.678a.84.84 0 0 0-.42.726v11.188c0 .3.162.575.42.724l9.609 5.55a1 1 0 0 0 .998 0l9.61-5.55a.84.84 0 0 0 .42-.724V6.404a.84.84 0 0 0-.42-.726L12.497.131a1.01 1.01 0 0 0-.996 0M2.657 6.338h18.55c.263 0 .43.287.297.515L12.23 22.918c-.062.107-.229.064-.229-.06V12.335a.59.59 0 0 0-.295-.51l-9.11-5.257c-.109-.063-.064-.23.061-.23"/>
  </svg>
);

const LogoCodex = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M14.949 6.547a3.94 3.94 0 0 0-.348-3.273 4.11 4.11 0 0 0-4.4-1.934 4.1 4.1 0 0 0-1.778-.214 4.15 4.15 0 0 0-2.118-.086 4.1 4.1 0 0 0-1.891.948 4.04 4.04 0 0 0-1.158 1.753 4.1 4.1 0 0 0-1.563.679 4 4 0 0 0-.932 1.253 3.99 3.99 0 0 0 .502 4.731 3.94 3.94 0 0 0 .346 3.274 4.11 4.11 0 0 0 4.402 1.933c.382.425.852.764 1.377.995.526.231 1.095.35 1.67.346 1.78.002 3.358-1.132 3.901-2.804a4.1 4.1 0 0 0 1.563-.68 4 4 0 0 0 1.14-1.253 3.99 3.99 0 0 0-.506-4.716m-6.097 8.406a3.05 3.05 0 0 1-1.945-.694l.096-.054 3.23-1.838a.53.53 0 0 0 .265-.455v-4.49l1.366.778q.02.011.025.035v3.722c-.003 1.653-1.361 2.992-3.037 2.996m-6.53-2.75a2.95 2.95 0 0 1-.36-2.01l.095.057L5.29 12.09a.53.53 0 0 0 .527 0l3.949-2.246v1.555a.05.05 0 0 1-.022.041L6.473 13.3c-1.454.826-3.311.335-4.15-1.098m-.85-6.94A3.02 3.02 0 0 1 3.07 3.949v3.785a.51.51 0 0 0 .262.451l3.93 2.237-1.366.779a.05.05 0 0 1-.048 0L2.585 9.342a2.98 2.98 0 0 1-1.113-4.094zm11.216 2.571L8.747 5.576l1.362-.776a.05.05 0 0 1 .048 0l3.265 1.86a3 3 0 0 1 1.173 1.207 2.96 2.96 0 0 1-.27 3.2 3.05 3.05 0 0 1-1.36.997V8.279a.52.52 0 0 0-.276-.445m1.36-2.015-.097-.057-3.226-1.855a.53.53 0 0 0-.53 0L6.249 6.153V4.598a.04.04 0 0 1 .019-.04L9.533 2.7a3.07 3.07 0 0 1 3.257.139c.474.325.843.778 1.066 1.303.223.526.289 1.103.191 1.664zM5.503 8.575 4.139 7.8a.05.05 0 0 1-.026-.037V4.049c0-.57.166-1.127.476-1.607s.752-.864 1.275-1.105a3.08 3.08 0 0 1 3.234.41l-.096.054-3.23 1.838a.53.53 0 0 0-.265.455zm.742-1.577 1.758-1 1.762 1v2l-1.755 1-1.762-1z"/>
  </svg>
);

const tabLogos: Record<string, ReactNode> = {
  agentic: <LogoPython />,
  claude: <LogoClaude />,
  cursor: <LogoCursor />,
  codex: <LogoCodex />,
};

/* ── Tab data ── */

const heroTabs = [
  {
    id: 'agentic',
    label: 'Agentic',
    language: 'python',
    title: 'agent.py',
    code: [
      'from openmem import MemoryEngine',
      '',
      'engine = MemoryEngine("memories.db")',
      '',
      '# Store',
      'm1 = engine.add("JWT tokens expire after 24h",',
      '    type="decision", entities=["JWT"])',
      'm2 = engine.add("Auth uses refresh tokens",',
      '    type="fact", entities=["auth"])',
      'engine.link(m1.id, m2.id, "supports")',
      '',
      '# Recall',
      'results = engine.recall("how does auth work?")',
      'for r in results:',
      '    print(f"{r.score:.3f}  {r.memory.text}")',
    ].join('\n'),
  },
  {
    id: 'claude',
    label: 'Claude Code',
    language: 'bash',
    title: 'terminal',
    code: [
      '# One command to install',
      'uvx openmem-engine install',
      '',
      '# Claude Code now has persistent memory.',
      '# 7 MCP tools available across sessions:',
      '#   memory_store    memory_recall',
      '#   memory_link     memory_reinforce',
      '#   memory_supersede',
      '#   memory_contradict',
      '#   memory_stats',
      '',
      '# Browse your memories',
      'openmem-engine ui',
      '',
      '# Memories persist in ~/.openmem/memories.db',
    ].join('\n'),
  },
  {
    id: 'cursor',
    label: 'Cursor',
    language: 'bash',
    title: 'terminal',
    code: [
      '# Coming soon — Cursor MCP integration',
      '',
      'uvx openmem-engine install --cursor',
      '',
      '# Persistent memory across Cursor sessions.',
      '# Same engine, same database, same recall.',
      '',
      '# All 7 memory tools work the same way:',
      '#   store, recall, link, reinforce,',
      '#   supersede, contradict, stats',
      '',
      '# Browse your memories',
      'openmem-engine ui',
      '',
      '',
    ].join('\n'),
  },
  {
    id: 'codex',
    label: 'Codex',
    language: 'bash',
    title: 'terminal',
    code: [
      '# Coming soon — Codex integration',
      '',
      'uvx openmem-engine install --codex',
      '',
      '# Persistent memory across Codex sessions.',
      '# Same engine, same database, same recall.',
      '',
      '# All 7 memory tools work the same way:',
      '#   store, recall, link, reinforce,',
      '#   supersede, contradict, stats',
      '',
      '# Browse your memories',
      'openmem-engine ui',
      '',
      '',
    ].join('\n'),
  },
];

const pipeline = [
  { step: '01', name: 'BM25', detail: 'FTS5 lexical match against text, gist, entities' },
  { step: '02', name: 'Seed', detail: 'Normalize BM25 scores to [0, 1]' },
  { step: '03', name: 'Spread', detail: 'Traverse graph edges up to 2 hops with decay' },
  { step: '04', name: 'Compete', detail: 'Weighted: activation + recency + strength + confidence' },
  { step: '05', name: 'Resolve', detail: 'Detect contradictions, demote weaker memory' },
  { step: '06', name: 'Pack', detail: 'Sort by score, fit within token budget' },
];

/* ── Feature icons (inline SVGs) ── */

const FeatureIcons: Record<string, ReactNode> = {
  deterministic: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M9 12l2 2 4-4"/>
    </svg>
  ),
  zero: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
    </svg>
  ),
  biological: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    </svg>
  ),
  token: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 7V5a4 4 0 00-8 0v2"/><circle cx="12" cy="14" r="1"/>
    </svg>
  ),
  graph: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98"/>
    </svg>
  ),
  webui: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><path d="M8 21h8M12 17v4"/>
    </svg>
  ),
};

const features = [
  {
    key: 'deterministic',
    title: 'Deterministic',
    description: 'Same query, same results. No stochastic embedding drift. Every score is inspectable.',
    code: 'r.components\n# {activation: 0.72, recency: 0.95,\n#  strength: 0.80, confidence: 0.90}',
  },
  {
    key: 'zero',
    title: 'Zero dependencies',
    description: 'Pure Python + SQLite. No vector DB, no embedding model, no external services.',
    code: 'engine = MemoryEngine()       # in-memory\nengine = MemoryEngine("p.db") # persistent',
  },
  {
    key: 'biological',
    title: 'Biological recall',
    description: 'Memories decay, get reinforced, compete for activation, and resolve conflicts.',
    code: 'engine.reinforce(m.id)     # boost\nengine.supersede(old, new)  # outdated\nengine.decay_all()          # forget',
  },
  {
    key: 'token',
    title: 'Token-budgeted',
    description: 'Retrieval respects a token budget. Never blow your context window.',
    code: 'engine.recall(\n  query, top_k=10, token_budget=2000\n) # packs by score until budget hit',
  },
  {
    key: 'graph',
    title: 'Graph-linked',
    description: 'Spreading activation pulls in connected context that BM25 alone would miss.',
    code: 'engine.link(\n  m1.id, m2.id, "supports", weight=0.8\n) # m2 activates when m1 is recalled',
  },
  {
    key: 'webui',
    title: 'Web UI',
    description: 'Browse, search, and inspect your memory store. One command.',
    code: 'openmem-engine ui\n# Opens http://localhost:3333',
  },
];

/* ── Comparison data ── */

type CellValue = true | false | 'partial' | string;

const compProducts = ['OpenMem', 'Mem0', 'Zep', 'Letta', 'File-based'] as const;
const compDescriptions: Record<string, string> = {
  'OpenMem': 'BM25 + graph',
  'Mem0': 'Vector, managed cloud',
  'Zep': 'KG + vector',
  'Letta': 'Agent runtime',
  'File-based': 'CLAUDE.md, etc.',
};

interface CompFeature {
  name: string;
  values: Record<string, CellValue>;
}

const compFeatures: CompFeature[] = [
  { name: 'Deterministic retrieval', values: { OpenMem: true, Mem0: false, Zep: false, Letta: false, 'File-based': true } },
  { name: 'Graph relationships', values: { OpenMem: true, Mem0: 'partial', Zep: true, Letta: false, 'File-based': false } },
  { name: 'Memory decay & reinforcement', values: { OpenMem: true, Mem0: false, Zep: false, Letta: false, 'File-based': false } },
  { name: 'Conflict resolution', values: { OpenMem: true, Mem0: 'partial', Zep: false, Letta: false, 'File-based': false } },
  { name: 'Token-budgeted output', values: { OpenMem: true, Mem0: false, Zep: false, Letta: true, 'File-based': false } },
  { name: 'No embedding model needed', values: { OpenMem: true, Mem0: false, Zep: false, Letta: false, 'File-based': true } },
  { name: 'Local-first, no cloud', values: { OpenMem: true, Mem0: 'partial', Zep: 'partial', Letta: true, 'File-based': true } },
  { name: 'Inspectable scoring', values: { OpenMem: true, Mem0: false, Zep: false, Letta: false, 'File-based': 'N/A' } },
  { name: 'Zero external dependencies', values: { OpenMem: true, Mem0: false, Zep: false, Letta: false, 'File-based': true } },
  { name: 'Open source', values: { OpenMem: true, Mem0: 'partial', Zep: 'partial', Letta: true, 'File-based': true } },
];

/* ── Components ── */

function Caret({className}: {className?: string}) {
  return <span className={clsx(styles.caret, className)}>&gt;</span>;
}

function HomepageHeader() {
  const [activeTab, setActiveTab] = useState('agentic');

  return (
    <header className={styles.hero}>
      <div className={styles.heroGlow} />
      <div className={styles.heroInner}>
        <div className={styles.heroText}>
          <p className={styles.heroBadge}><Caret /> open source &middot; MIT licensed</p>
          <Heading as="h1" className={styles.heroTitle}>
            Your agent forgets<br />everything.{' '}
            <span className={styles.heroGradient}>Fix that.</span>
          </Heading>
          <p className={styles.heroTagline}>
            openmem is a deterministic memory engine for AI agents.
            BM25 search, graph activation, competition scoring.
            No vectors. No embeddings. No cloud. Just a SQLite file.
          </p>
          <div className={styles.heroInstall}>
            <div className={styles.installBox}>
              <span className={styles.installPrompt}>$</span>
              <code className={styles.installCode}>pip install openmem-engine</code>
            </div>
          </div>
          <div className={styles.heroButtons}>
            <Link className={clsx('button button--lg', styles.heroPrimary)} to="/docs/quickstart">
              Get started
            </Link>
            <Link className={clsx('button button--lg', styles.heroSecondary)} to="https://github.com/dunkinfrunkin/OpenMem">
              GitHub
            </Link>
          </div>
        </div>
        <div className={styles.heroCode}>
          <div className={styles.heroTabs}>
            {heroTabs.map((t) => (
              <button
                key={t.id}
                className={clsx(styles.heroTab, activeTab === t.id && styles.heroTabActive)}
                onClick={() => setActiveTab(t.id)}
              >
                <span className={styles.heroTabLogo}>{tabLogos[t.id]}</span>
                {t.label}
              </button>
            ))}
          </div>
          <div className={styles.heroCodePanels}>
            {heroTabs.map((t) => (
              <div
                key={t.id}
                className={clsx(styles.heroCodePanel, activeTab !== t.id && styles.heroCodePanelHidden)}
              >
                <CodeBlock language={t.language} title={t.title}>
                  {t.code}
                </CodeBlock>
              </div>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}

function CompCell({value}: {value: CellValue}) {
  if (value === true) {
    return (
      <span className={styles.cellYes}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="10" fill="currentColor" opacity="0.12"/><path d="M6 10.5l2.5 2.5L14 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
      </span>
    );
  }
  if (value === false) {
    return <span className={styles.cellNo}>&mdash;</span>;
  }
  if (value === 'partial') {
    return <span className={styles.cellPartial}>~</span>;
  }
  return <span className={styles.cellText}>{value}</span>;
}

function ComparisonSection() {
  return (
    <section className={styles.comparison}>
      <div className="container">
        <Caret className={styles.sectionCaret} />
        <Heading as="h2" className={styles.sectionTitle}>How we compare</Heading>
        <p className={styles.sectionSubtitle}>
          Other memory systems rely on embeddings and hosted infrastructure.<br />
          We think agent memory should be deterministic, local, and inspectable.
        </p>
        <div className={styles.compGrid}>
          <div className={styles.compHeader}>
            <div className={styles.compFeatureLabel} />
            {compProducts.map((p) => (
              <div key={p} className={clsx(styles.compProductCol, p === 'OpenMem' && styles.compProductHighlight)}>
                <span className={styles.compProductName}>{p === 'OpenMem' ? '> openmem' : p}</span>
                <span className={styles.compProductDesc}>{compDescriptions[p]}</span>
              </div>
            ))}
          </div>
          {compFeatures.map((f, i) => (
            <div key={i} className={styles.compRow}>
              <div className={styles.compFeatureLabel}>{f.name}</div>
              {compProducts.map((p) => (
                <div key={p} className={clsx(styles.compCell, p === 'OpenMem' && styles.compCellHighlight)}>
                  <CompCell value={f.values[p]} />
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PipelineSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState(-1);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setPhase(0);
          observer.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // 0 = typing, 1-6 = stages, 7 = output
  useEffect(() => {
    if (phase < 0 || phase > 7) return;
    const delay = phase === 0 ? 2000 : 320;
    const timer = setTimeout(() => setPhase((p) => p + 1), delay);
    return () => clearTimeout(timer);
  }, [phase]);

  return (
    <section className={styles.pipeline} ref={sectionRef}>
      <div className="container">
        <Caret className={styles.sectionCaret} />
        <Heading as="h2" className={styles.sectionTitle}>Six-stage retrieval</Heading>
        <p className={styles.sectionSubtitle}>
          Every <code>recall()</code> runs a deterministic pipeline. No magic. No black boxes.
        </p>

        <div className={styles.pipelineFlow}>
          {/* ── Top-left: input + vertical arrow ── */}
          <div className={styles.pipelineInputGroup}>
            <div className={clsx(styles.pipelineTerminal, phase >= 0 && styles.pipelineShow)}>
              <div className={styles.pipelineTerminalIcon}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M5 3l6 5-6 5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </div>
              <div>
                <span className={styles.pipelineTerminalLabel}>input</span>
                <div className={styles.pipelineTypingWrap}>
                  <code className={clsx(
                    styles.pipelineTypingCode,
                    phase >= 0 && styles.pipelineTypingActive,
                    phase >= 1 && styles.pipelineTypingDone,
                  )}>recall("how does auth work?")</code>
                </div>
              </div>
            </div>
            <svg className={clsx(styles.pipelineVert, phase >= 1 && styles.pipelineVertShow)} viewBox="0 0 20 36" aria-hidden>
              <line className={styles.pipelineVertLine} x1="10" y1="0" x2="10" y2="28" />
              <path className={styles.pipelineVertHead} d="M5 25 L10 34 L15 25" />
            </svg>
          </div>

          {/* ── Horizontal graph: nodes + drawn edges ── */}
          <div className={styles.pipelineGraph}>
            {pipeline.flatMap((s, i) => {
              const items = [];
              if (i > 0) {
                items.push(
                  <svg
                    key={`e${i}`}
                    className={clsx(styles.pipelineEdge, phase >= i + 1 && styles.pipelineEdgeShow)}
                    viewBox="0 0 48 20"
                    aria-hidden
                  >
                    <line className={styles.pipelineEdgeLine} x1="2" y1="10" x2="36" y2="10" />
                    <path className={styles.pipelineEdgeHead} d="M33 4.5 L43 10 L33 15.5" />
                  </svg>,
                );
              }
              items.push(
                <div
                  key={`n${i}`}
                  className={clsx(
                    styles.pipelineNode,
                    phase >= i + 1 && styles.pipelineNodeShow,
                    phase === i + 1 && styles.pipelineNodeFlash,
                  )}
                >
                  <span className={styles.pipelineNodeNum}>{s.step}</span>
                  <strong className={styles.pipelineNodeName}>{s.name}</strong>
                  <span className={styles.pipelineNodeDetail}>{s.detail}</span>
                </div>,
              );
              return items;
            })}
          </div>

          {/* ── Bottom-right: vertical arrow + output ── */}
          <div className={styles.pipelineOutputGroup}>
            <svg className={clsx(styles.pipelineVert, phase >= 7 && styles.pipelineVertShow)} viewBox="0 0 20 36" aria-hidden>
              <line className={styles.pipelineVertLine} x1="10" y1="0" x2="10" y2="28" />
              <path className={styles.pipelineVertHead} d="M5 25 L10 34 L15 25" />
            </svg>
            <div className={clsx(styles.pipelineTerminal, styles.pipelineTerminalOutput, phase >= 7 && styles.pipelineShow)}>
              <div className={styles.pipelineTerminalIcon}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h8M2 12h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              </div>
              <div>
                <span className={styles.pipelineTerminalLabel}>output</span>
                <div className={styles.pipelineOutputScores}>
                  <code className={clsx(styles.pipelineScoreItem, phase >= 7 && styles.pipelineScoreShow)} style={{transitionDelay: '0.1s'}}>
                    <span className={styles.pipelineScoreNum}>0.92</span>{' '}"Auth uses refresh tokens"
                  </code>
                  <code className={clsx(styles.pipelineScoreItem, phase >= 7 && styles.pipelineScoreShow)} style={{transitionDelay: '0.3s'}}>
                    <span className={styles.pipelineScoreNum}>0.87</span>{' '}"JWT tokens expire after 24h"
                  </code>
                  <code className={clsx(styles.pipelineScoreItem, phase >= 7 && styles.pipelineScoreShow)} style={{transitionDelay: '0.5s'}}>
                    <span className={styles.pipelineScoreDim}>0.41</span>{' '}"Session store uses Redis"
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Feature({featureKey, title, description, code}: {featureKey: string; title: string; description: string; code: string}) {
  return (
    <div className={styles.featureCard}>
      <div className={styles.featureIcon}>{FeatureIcons[featureKey]}</div>
      <Heading as="h3" className={styles.featureTitle}>{title}</Heading>
      <p className={styles.featureDesc}>{description}</p>
      <pre className={styles.featureCode}><code>{code}</code></pre>
    </div>
  );
}

function FeaturesSection() {
  return (
    <section className={styles.features}>
      <div className="container">
        <Caret className={styles.sectionCaret} />
        <Heading as="h2" className={styles.sectionTitle}>Built for agents</Heading>
        <p className={styles.sectionSubtitle}>
          Everything your agent needs to remember, recall, and reason over time.
        </p>
        <div className={styles.featuresGrid}>
          {features.map((f) => (
            <Feature key={f.key} featureKey={f.key} title={f.title} description={f.description} code={f.code} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ClaudeCodeSection() {
  return (
    <section className={styles.claudeCode}>
      <div className="container">
        <div className={styles.claudeCodeInner}>
          <div className={styles.claudeCodeText}>
            <div className={styles.claudeCodeHeader}>
              <div className={styles.claudeCodeLogo}>
                <svg width="28" height="28" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="m3.127 10.604 3.135-1.76.053-.153-.053-.085H6.11l-.525-.032-1.791-.048-1.554-.065-1.505-.08-.38-.081L0 7.832l.036-.234.32-.214.455.04 1.009.069 1.513.105 1.097.064 1.626.17h.259l.036-.105-.089-.065-.068-.064-1.566-1.062-1.695-1.121-.887-.646-.48-.327-.243-.306-.104-.67.435-.48.585.04.15.04.593.456 1.267.981 1.654 1.218.242.202.097-.068.012-.049-.109-.181-.9-1.626-.96-1.655-.428-.686-.113-.411a2 2 0 0 1-.068-.484l.496-.674L4.446 0l.662.089.279.242.411.94.666 1.48 1.033 2.014.302.597.162.553.06.17h.105v-.097l.085-1.134.157-1.392.154-1.792.052-.504.25-.605.497-.327.387.186.319.456-.045.294-.19 1.23-.37 1.93-.243 1.29h.142l.161-.16.654-.868 1.097-1.372.484-.545.565-.601.363-.287h.686l.505.751-.226.775-.707.895-.585.759-.839 1.13-.524.904.048.072.125-.012 1.897-.403 1.024-.186 1.223-.21.553.258.06.263-.218.536-1.307.323-1.533.307-2.284.54-.028.02.032.04 1.029.098.44.024h1.077l2.005.15.525.346.315.424-.053.323-.807.411-3.631-.863-.872-.218h-.12v.073l.726.71 1.331 1.202 1.667 1.55.084.383-.214.302-.226-.032-1.464-1.101-.565-.497-1.28-1.077h-.084v.113l.295.432 1.557 2.34.08.718-.112.234-.404.141-.444-.08-.911-1.28-.94-1.44-.759-1.291-.093.053-.448 4.821-.21.246-.484.186-.403-.307-.214-.496.214-.98.258-1.28.21-1.016.19-1.263.112-.42-.008-.028-.092.012-.953 1.307-1.448 1.957-1.146 1.227-.274.109-.477-.247.045-.44.266-.39 1.586-2.018.956-1.25.617-.723-.004-.105h-.036l-4.212 2.736-.75.096-.324-.302.04-.496.154-.162 1.267-.871z"/>
                </svg>
              </div>
              <div>
                <div className={styles.claudeCodeBadge}>
                  <span>MCP Integration</span>
                </div>
                <Heading as="h2" className={styles.claudeCodeTitle}>Drop into Claude Code</Heading>
              </div>
            </div>
            <p className={styles.claudeCodeDesc}>
              One command installs 7 MCP tools that give Claude persistent memory across every session.
              Your agent remembers what it learned yesterday.
            </p>
            <div className={styles.toolGrid}>
              {[
                {name: 'store', desc: 'save a memory'},
                {name: 'recall', desc: 'search & retrieve'},
                {name: 'link', desc: 'connect memories'},
                {name: 'reinforce', desc: 'boost strength'},
                {name: 'supersede', desc: 'replace outdated'},
                {name: 'contradict', desc: 'flag conflicts'},
                {name: 'stats', desc: 'store overview'},
              ].map((t) => (
                <div key={t.name} className={styles.toolTag}>
                  <code className={styles.toolTagName}>{t.name}</code>
                  <span className={styles.toolTagDesc}>{t.desc}</span>
                </div>
              ))}
            </div>
            <Link className={clsx('button button--lg', styles.heroPrimary, styles.claudeCodeBtn)} to="/docs/claude-code">
              Read the docs &rarr;
            </Link>
          </div>
          <div className={styles.claudeCodeSnippet}>
            <CodeBlock language="bash" title="terminal">
              {`$ uvx openmem-engine install\n\nAdding OpenMem to Claude Code...\nDone! OpenMem is now available.\n\n$ openmem-engine status\nMemories: 142\n  Active: 130\nEdges:    87\nAvg strength: 0.84`}
            </CodeBlock>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className={styles.cta}>
      <div className="container">
        <div className={styles.ctaInner}>
          <Heading as="h2" className={styles.ctaTitle}>
            <span className={styles.heroGradient}>Stop losing context.</span>
          </Heading>
          <p className={styles.ctaSubtitle}>
            Give your agent a memory that decays, reinforces, and competes — just like yours.
          </p>
          <div className={styles.ctaButtons}>
            <Link className={clsx('button button--lg', styles.heroPrimary)} to="/docs/quickstart">
              Get started
            </Link>
            <Link className={clsx('button button--lg', styles.heroSecondary)} to="https://github.com/dunkinfrunkin/OpenMem">
              Star on GitHub
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout description="Deterministic memory engine for AI agents. BM25 search, graph activation, competition scoring. Pure Python + SQLite.">
      <HomepageHeader />
      <main>
        <ComparisonSection />
        <PipelineSection />
        <FeaturesSection />
        <ClaudeCodeSection />
        <CTASection />
      </main>
    </Layout>
  );
}
