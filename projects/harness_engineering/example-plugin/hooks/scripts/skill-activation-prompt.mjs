/**
 * Skill Activation Prompt Hook
 * UserPromptSubmit 훅에서 실행됨 — 프롬프트 키워드/의도 패턴과 skill-rules.json을 매칭하여
 * 관련 스킬을 Claude 컨텍스트에 주입한다.
 *
 * 원본: chacha95/advanced-harness-window
 * 수정: 플러그인 구조에 맞게 skill-rules.json 경로 조정
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

try {
    const input = readFileSync(0, 'utf-8');
    const data = JSON.parse(input);
    const prompt = data.prompt.toLowerCase();

    // 플러그인 루트에서 skill-rules.json 로드
    // 훅 스크립트 위치: hooks/scripts/ → 루트는 ../..
    const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT
        || join(__dirname, '..', '..');

    const rulesPath = join(pluginRoot, 'skills', 'skill-rules.json');
    const rules = JSON.parse(readFileSync(rulesPath, 'utf-8'));

    const matchedSkills = [];

    for (const [skillName, config] of Object.entries(rules.skills)) {
        const triggers = config.promptTriggers;
        if (!triggers) continue;

        // 키워드 매칭
        if (triggers.keywords) {
            const keywordMatch = triggers.keywords.some(kw =>
                prompt.includes(kw.toLowerCase())
            );
            if (keywordMatch) {
                matchedSkills.push({ name: skillName, matchType: 'keyword', config });
                continue;
            }
        }

        // 의도 패턴 매칭 (정규식)
        if (triggers.intentPatterns) {
            const intentMatch = triggers.intentPatterns.some(pattern => {
                try {
                    return new RegExp(pattern, 'i').test(prompt);
                } catch {
                    return false;
                }
            });
            if (intentMatch) {
                matchedSkills.push({ name: skillName, matchType: 'intent', config });
            }
        }
    }

    if (matchedSkills.length > 0) {
        const groups = {
            critical: '⚠️  CRITICAL SKILLS (REQUIRED)',
            high:     '📚 RECOMMENDED SKILLS',
            medium:   '💡 SUGGESTED SKILLS',
            low:      '📌 OPTIONAL SKILLS'
        };

        let output = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
        output += '🎯 SKILL ACTIVATION CHECK\n';
        output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

        for (const [priority, label] of Object.entries(groups)) {
            const skills = matchedSkills.filter(s => s.config.priority === priority);
            if (skills.length > 0) {
                output += `${label}:\n`;
                skills.forEach(s => {
                    const desc = s.config.description
                        ? ` — ${s.config.description.split('\n')[0].slice(0, 60)}`
                        : '';
                    output += `  → ${s.name}${desc}\n`;
                });
                output += '\n';
            }
        }

        output += 'ACTION: Use Skill tool BEFORE responding\n';
        output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
        process.stdout.write(output);
    }

    process.exit(0);
} catch (err) {
    // 훅 실패해도 프롬프트 처리는 계속
    process.stderr.write(`[skill-activation] Error: ${err.message}\n`);
    process.exit(0);
}
