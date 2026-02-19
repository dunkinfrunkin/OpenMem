import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

const installSnippet = `pip install openmem-engine`;

const quickExample = `from openmem import MemoryEngine

engine = MemoryEngine("memories.db")

# Store
m1 = engine.add("JWT tokens expire after 24h", type="decision", entities=["JWT"])
m2 = engine.add("Auth uses refresh tokens in httpOnly cookies", type="fact")
engine.link(m1.id, m2.id, "supports")

# Recall
results = engine.recall("how does authentication work?")
for r in results:
    print(f"{r.score:.3f}  {r.memory.text}")
# 0.812  JWT tokens expire after 24h
# 0.604  Auth uses refresh tokens in httpOnly cookies`;

const claudeCodeSnippet = `uvx openmem-engine install

# That's it. Claude Code now has persistent memory.
# 7 MCP tools available automatically across sessions.`;

const pipeline = [
  { step: '1', name: 'BM25', detail: 'FTS5 lexical match against text, gist, entities' },
  { step: '2', name: 'Seed', detail: 'Normalize scores to [0, 1]' },
  { step: '3', name: 'Spread', detail: 'Traverse graph edges up to 2 hops with decay' },
  { step: '4', name: 'Compete', detail: 'Weighted sum: activation + recency + strength + confidence' },
  { step: '5', name: 'Resolve', detail: 'Detect contradictions, demote weaker memory' },
  { step: '6', name: 'Pack', detail: 'Sort by score, fit within token budget' },
];

const features = [
  {
    title: 'Deterministic retrieval',
    description: 'Same query, same results. BM25 + graph activation — no stochastic embedding drift. Fully inspectable score breakdowns.',
    code: 'r.components\n# {activation: 0.72, recency: 0.95, strength: 0.80, confidence: 0.90}',
  },
  {
    title: 'Zero dependencies',
    description: 'Pure Python + SQLite. No vector DB, no embedding model, no external services. Works everywhere Python runs.',
    code: 'engine = MemoryEngine()  # in-memory\nengine = MemoryEngine("prod.db")  # persistent',
  },
  {
    title: 'Human-inspired recall',
    description: 'Memories decay over time, get reinforced on access, compete for activation, and resolve conflicts — just like biological memory.',
    code: 'engine.reinforce(m.id)    # boost strength\nengine.supersede(old, new) # mark outdated\nengine.decay_all()        # natural forgetting',
  },
  {
    title: 'Token-budgeted output',
    description: 'Retrieval respects a token budget so you never blow your context window. Memories packed by score until the budget is hit.',
    code: 'engine.recall(query, top_k=10, token_budget=2000)\n# Returns highest-scoring memories that fit',
  },
  {
    title: 'Graph-linked context',
    description: 'Link related memories with typed edges. Spreading activation pulls in connected context that BM25 alone would miss.',
    code: 'engine.link(m1.id, m2.id, "supports", weight=0.8)\n# m2 activates when m1 is recalled',
  },
  {
    title: 'Web UI included',
    description: 'Browse, search, and inspect your memory store visually. One command to launch.',
    code: 'openmem-engine ui\n# Opens http://localhost:3333',
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={styles.hero}>
      <div className={styles.heroInner}>
        <div className={styles.heroText}>
          <Heading as="h1" className={styles.heroTitle}>
            {siteConfig.title}
          </Heading>
          <p className={styles.heroTagline}>
            Memory engine for AI agents. BM25 search, graph activation, competition scoring. No vectors, no embeddings — deterministic retrieval in pure Python + SQLite.
          </p>
          <div className={styles.heroInstall}>
            <code className={styles.installCode}>$ pip install openmem-engine</code>
          </div>
          <div className={styles.heroButtons}>
            <Link className={clsx('button button--primary button--lg', styles.heroButton)} to="/docs/quickstart">
              Get started
            </Link>
            <Link className={clsx('button button--outline button--lg', styles.heroButton)} to="https://github.com/dunkinfrunkin/OpenMem">
              GitHub
            </Link>
          </div>
        </div>
        <div className={styles.heroCode}>
          <CodeBlock language="python" title="quickstart.py">
            {quickExample}
          </CodeBlock>
        </div>
      </div>
    </header>
  );
}

function ClaudeCodeSection() {
  return (
    <section className={styles.claudeCode}>
      <div className="container">
        <div className={styles.claudeCodeInner}>
          <div className={styles.claudeCodeText}>
            <Heading as="h2">Works with Claude Code</Heading>
            <p>
              One command adds persistent memory to Claude Code via MCP.
              Seven tools — <code>store</code>, <code>recall</code>, <code>link</code>,
              {' '}<code>reinforce</code>, <code>supersede</code>, <code>contradict</code>,
              {' '}<code>stats</code> — available automatically across sessions.
            </p>
            <Link className={styles.claudeCodeLink} to="/docs/claude-code">
              Read the docs &rarr;
            </Link>
          </div>
          <div className={styles.claudeCodeSnippet}>
            <CodeBlock language="bash" title="terminal">
              {claudeCodeSnippet}
            </CodeBlock>
          </div>
        </div>
      </div>
    </section>
  );
}

function PipelineSection() {
  return (
    <section className={styles.pipeline}>
      <div className="container">
        <Heading as="h2" className={styles.sectionTitle}>Retrieval pipeline</Heading>
        <p className={styles.sectionSubtitle}>
          Every <code>recall()</code> call runs through six deterministic stages.
        </p>
        <div className={styles.pipelineSteps}>
          {pipeline.map((s, i) => (
            <div key={i} className={styles.pipelineStep}>
              <span className={styles.pipelineNum}>{s.step}</span>
              <div>
                <strong className={styles.pipelineName}>{s.name}</strong>
                <span className={styles.pipelineDetail}>{s.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Feature({title, description, code}: {title: string; description: string; code: string}) {
  return (
    <div className={styles.featureCard}>
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
        <Heading as="h2" className={styles.sectionTitle}>Built for agents</Heading>
        <div className={styles.featuresGrid}>
          {features.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout description="Deterministic memory engine for AI agents — BM25 search, graph activation, competition scoring. Pure Python + SQLite.">
      <HomepageHeader />
      <main>
        <PipelineSection />
        <FeaturesSection />
        <ClaudeCodeSection />
      </main>
    </Layout>
  );
}
