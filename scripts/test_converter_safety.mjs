import assert from 'node:assert/strict';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { isUnsafeUnscopedBlock } from './dnr_safety.mjs';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const base = path.join(projectRoot, '.build', 'converter-safety-test');
const filters = path.join(base, 'filters');
const output = path.join(base, 'output');

await rm(base, { recursive: true, force: true });
await mkdir(filters, { recursive: true });
await writeFile(path.join(filters, 'filters.json'), '[{"filterId":1}]\r\n');
await writeFile(
  path.join(filters, 'filter_1.txt'),
  [
    '! CRLF safety fixture',
    '||ads.example^',
    '*$doc,ipaddress=203.0.113.7',
    '||app-only.example^$app=com.example.app',
    '||referrer.example^$referrerpolicy=no-referrer',
    '|*$doc,app=com.example.app',
    '|*$doc',
    '*|$doc',
    '|*|$doc',
    '$ping,third-party',
    '',
  ].join('\r\n'),
);

const result = spawnSync(
  process.execPath,
  ['scripts/convert_filters.mjs', filters, output],
  { cwd: projectRoot, encoding: 'utf8' },
);
assert.equal(result.status, 0, result.stderr || result.stdout);

const report = JSON.parse(await readFile(path.join(output, 'conversion-report.json'), 'utf8'));
const rules = JSON.parse(await readFile(path.join(output, 'ruleset_1', 'ruleset_1.json'), 'utf8'));
assert.equal(report.sanitization.droppedRules, 4);
assert.equal(report.sanitization.unsupportedModifiers.ipaddress, 1);
assert.equal(report.sanitization.unsupportedModifiers.app, 2);
assert.equal(report.sanitization.unsupportedModifiers.referrerpolicy, 1);
assert.equal(report.unsafeDeclarativeRulesDropped, 4);
assert.equal(rules.length, 1);
assert.equal(rules[0].condition.urlFilter, '||ads.example^');

const unsafeConditions = ['', '*', '|*', '*|', '|*|', 'http', 'https://', '*http*', '|https*'].map((urlFilter) => ({
  action: { type: 'block' }, condition: { urlFilter, resourceTypes: ['main_frame'] },
}));
unsafeConditions.push({ action: { type: 'block' }, condition: { regexFilter: '.*', resourceTypes: ['main_frame'] } });
assert(unsafeConditions.every(isUnsafeUnscopedBlock));
assert(!isUnsafeUnscopedBlock({ action: { type: 'block' }, condition: { urlFilter: '||example.test^' } }));
assert(!isUnsafeUnscopedBlock({ action: { type: 'block' }, condition: { urlFilter: '|*', requestDomains: ['example.test'] } }));
assert(!isUnsafeUnscopedBlock({ action: { type: 'allow' }, condition: { urlFilter: '|*' } }));

const pythonSafety = spawnSync(
  'python',
  [
    '-c',
    [
      'import build_extension as b',
      'unsafe = [{"action":{"type":"block"},"condition":{"urlFilter":value,"resourceTypes":["main_frame"]}} for value in ("", "*", "|*", "*|", "|*|", "http", "https://", "*http*", "|https*")] + [{"action":{"type":"block"},"condition":{"regexFilter":".*","resourceTypes":["main_frame"]}}]',
      'safe = [{"action":{"type":"block"},"condition":{"urlFilter":"||example.test^"}}, {"action":{"type":"block"},"condition":{"urlFilter":"|*","requestDomains":["example.test"]}}, {"action":{"type":"allow"},"condition":{"urlFilter":"|*"}}]',
      'assert all(b.is_unsafe_unscoped_block(rule) for rule in unsafe)',
      'assert not any(b.is_unsafe_unscoped_block(rule) for rule in safe)',
    ].join('; '),
  ],
  { cwd: projectRoot, encoding: 'utf8' },
);
assert.equal(pythonSafety.status, 0, pythonSafety.stderr || pythonSafety.stdout);

await rm(base, { recursive: true, force: true });
console.log('Converter safety regression: PASS');
