/**
 * Skill Activation Prompt Hook — v2.0
 * UserPromptSubmit 훅에서 실행됨
 *
 * 개선 사항 (참조 프레임워크):
 *   - NeMo Guardrails: 자유문장 → Canonical Intent 변환 먼저
 *   - Superpowers (42k★): 관련 스킬만 선택적 레이지 로딩
 *   - Semantic Kernel: Handoff 대상 명시
 *
 * 처리 순서:
 *   1. Canonical Intent 변환 (자유문장 → 도메인 표준 의도)
 *   2. Vocabulary Register 매핑 (의도 → 에이전트/스킬)
 *   3. skill-rules.json 기반 스킬 레이지 로딩
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ── 1. Canonical Intent Map (NeMo Guardrails 패턴) ─────────────────────────
// 사용자 자유문장을 INTENT.md 어휘 레지스터의 표준 의도로 변환
const CANONICAL_INTENT_MAP = {
  '레짐 분석': {
    keywords: ['레짐', '경기', '사이클', '거시', '침체', '과열', 'goldilocks', 'overheating', 'stagflation', 'recession', '성장률', 'gdp', '인플레'],
    agent: 'macro-analyst',
    skill: 'skills/macro-economics/',
    output: 'outputs/context/regime_snapshot.json'
  },
  '시그널 분석': {
    keywords: ['시그널', 'signal', '기술적', '모멘텀', '추세', '과매수', '과매도', 'vix', 'hy oas', '스프레드', '수익률 곡선', 'yield curve'],
    agent: 'signal-interpreter',
    skill: 'skills/financial-signals/',
    output: 'outputs/context/signal_summary.json'
  },
  '리스크 평가': {
    keywords: ['리스크', 'risk', 'var', 'cvar', '손실', '꼬리', '변동성', '버블', '경보', '시나리오', '스트레스'],
    agent: 'risk-mgr',
    skill: 'skills/risk-assessment/',
    output: 'outputs/context/risk_assessment.json'
  },
  '포트폴리오 최적화': {
    keywords: ['포트폴리오', 'portfolio', '리밸런싱', 'hrp', 'mvo', '자산배분', '가중치', '분산투자', 'risk parity'],
    agent: 'quant-coder',
    skill: 'skills/portfolio-theory/',
    output: 'outputs/context/chart_paths.json'
  },
  '리서치': {
    keywords: ['뉴스', 'news', '공시', 'fomc', 'cpi', 'nfp', '보고서', '발표', '의사록', '10-k', '이벤트'],
    agent: 'researcher',
    skill: null,
    output: 'outputs/context/research_summary.json'
  },
  '온체인 분석': {
    keywords: ['온체인', 'onchain', '블록체인', 'ethereum', 'eth', 'bitcoin', 'btc', 'defi', 'web3', '크립토', 'nft'],
    agent: 'researcher',
    skill: 'skills/crypto-onchain/',
    output: 'outputs/context/research_summary.json'
  },
  '미시구조 분석': {
    keywords: ['미시구조', 'microstructure', '유동성', '호가', 'bid-ask', 'hft', '거래량', '시장조성', 'amihud'],
    agent: 'signal-interpreter',
    skill: 'skills/market-microstructure/',
    output: 'outputs/context/signal_summary.json'
  },
  '데이터 검증': {
    keywords: ['검증', '이상치', 'outlier', '결측', 'null', '데이터 품질', 'validation'],
    agent: 'data-validator',
    skill: 'skills/analysis-standards/',
    output: 'outputs/context/validation_result.json'
  }
};

function detectCanonicalIntents(prompt) {
  const lower = prompt.toLowerCase();
  const matched = [];
  for (const [intent, config] of Object.entries(CANONICAL_INTENT_MAP)) {
    if (config.keywords.some(kw => lower.includes(kw.toLowerCase()))) {
      matched.push({ intent, ...config });
    }
  }
  return matched;
}

// ── 메인 처리 ────────────────────────────────────────────────────────────────
try {
  const input = readFileSync(0, 'utf-8');
  const data = JSON.parse(input);
  const prompt = data.prompt || '';
  const promptLower = prompt.toLowerCase();

  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || join(__dirname, '..', '..');

  // Step 1: Canonical Intent 감지
  const canonicalIntents = detectCanonicalIntents(prompt);

  // Step 2: skill-rules.json 기반 스킬 매칭 (레이지 로딩)
  let matchedSkills = [];
  try {
    const rulesPath = join(pluginRoot, 'skills', 'skill-rules.json');
    const rules = JSON.parse(readFileSync(rulesPath, 'utf-8'));

    for (const [skillName, config] of Object.entries(rules.skills)) {
      const triggers = config.promptTriggers;
      if (!triggers) continue;

      let matched = false;
      if (triggers.keywords) {
        matched = triggers.keywords.some(kw => promptLower.includes(kw.toLowerCase()));
      }
      if (!matched && triggers.intentPatterns) {
        matched = triggers.intentPatterns.some(pattern => {
          try { return new RegExp(pattern, 'i').test(prompt); }
          catch { return false; }
        });
      }
      if (matched) matchedSkills.push({ name: skillName, config });
    }
  } catch {
    // skill-rules.json 없으면 canonical intent만 사용
  }

  // Step 3: 출력 (canonical intent + 스킬)
  if (canonicalIntents.length === 0 && matchedSkills.length === 0) {
    process.exit(0);
  }

  let output = '\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
  output += '🎯 INTENT & SKILL ACTIVATION\n';
  output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

  // Canonical Intent 섹션
  if (canonicalIntents.length > 0) {
    output += '📌 감지된 도메인 의도 (Canonical Intents):\n';
    for (const ci of canonicalIntents) {
      output += `  → [${ci.intent}]\n`;
      output += `     에이전트: ${ci.agent}\n`;
      if (ci.skill) output += `     스킬:     ${ci.skill}\n`;
      output += `     출력:     ${ci.output}\n`;
    }
    output += '\n';
  }

  // 스킬 섹션 (레이지 로딩)
  if (matchedSkills.length > 0) {
    const priorities = { critical: '⚠️  REQUIRED', high: '📚 RECOMMENDED', medium: '💡 SUGGESTED', low: '📌 OPTIONAL' };
    for (const [priority, label] of Object.entries(priorities)) {
      const skills = matchedSkills.filter(s => s.config.priority === priority);
      if (skills.length > 0) {
        output += `${label} SKILLS:\n`;
        skills.forEach(s => {
          const desc = s.config.description ? ` — ${s.config.description.split('\n')[0].slice(0, 60)}` : '';
          output += `  → ${s.name}${desc}\n`;
        });
        output += '\n';
      }
    }
  }

  output += 'ACTION: INTENT.md 어휘 레지스터 기준으로 해당 에이전트/스킬 우선 참조\n';
  output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
  process.stdout.write(output);
  process.exit(0);

} catch (err) {
  process.stderr.write(`[skill-activation v2] Error: ${err.message}\n`);
  process.exit(0);
}
