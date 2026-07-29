import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { Filter, FilterConverter, Rule } from '@adguard/dnr-converter';
import { OPTION_NAMES } from '../node_modules/@adguard/dnr-converter/dist/rule/option-names.js';

const supportedModifiers = new Set([...Object.values(OPTION_NAMES), 'reason']);
const sanitization = { droppedRules: 0, unsupportedModifiers: {} };

const sanitizeFilter = (text) => text.split('\n').map((rawLine) => {
  const line = rawLine.endsWith(String.fromCharCode(13)) ? rawLine.slice(0, -1) : rawLine;
  if (!line || line.startsWith('!')) return line;
  try {
    const rules = Rule.createFromText(0, 0, line);
    const unsupported = new Set();
    for (const rule of rules) {
      for (const modifier of rule.node.modifiers?.children || []) {
        const name = modifier.name.value;
        if (!supportedModifiers.has(name)) unsupported.add(name);
      }
    }
    if (unsupported.size === 0) return line;
    sanitization.droppedRules += 1;
    for (const name of unsupported) {
      sanitization.unsupportedModifiers[name] = (sanitization.unsupportedModifiers[name] || 0) + 1;
    }
    return `! Dropped unsafe unsupported modifiers: ${[...unsupported].join(', ')}`;
  } catch {
    return line;
  }
}).join('\n');

const isUnsafeCatchAllBlock = (rule) => {
  const condition = rule.condition || {};
  const catchAll = (condition.urlFilter === undefined || condition.urlFilter === '*') &&
    condition.regexFilter === undefined;
  const positivelyScoped = Boolean(condition.requestDomains?.length || condition.initiatorDomains?.length);
  return rule.action?.type === 'block' && catchAll && !positivelyScoped;
};

const [filtersDir, outputDir] = process.argv.slice(2);
if (!filtersDir || !outputDir) {
  throw new Error('Usage: node scripts/convert_filters.mjs <filters-dir> <output-dir>');
}
const resolvedFiltersDir = path.resolve(filtersDir);
const resolvedOutputDir = path.resolve(outputDir);
const outputRelativeToProject = path.relative(process.cwd(), resolvedOutputDir);
if (!outputRelativeToProject || outputRelativeToProject === '..' ||
    outputRelativeToProject.startsWith(`..${path.sep}`) || path.isAbsolute(outputRelativeToProject)) {
  throw new Error('Output directory must be a child of the current project directory');
}

const metadata = JSON.parse(await readFile(path.join(resolvedFiltersDir, 'filters.json'), 'utf8'));
const filters = await Promise.all(metadata.map(async ({ filterId }) => {
  const text = await readFile(path.join(resolvedFiltersDir, `filter_${filterId}.txt`), 'utf8');
  return new Filter(filterId, sanitizeFilter(text));
}));

await rm(resolvedOutputDir, { recursive: true, force: true });
await mkdir(resolvedOutputDir, { recursive: true });

// ponytail: omit resourcesPath because CLI turns Windows paths into invalid extension URLs.
// Redirect rules without bundled resources are skipped; regular DNR rules still compile.
const results = await new FilterConverter().convert(filters);
const report = {
  rulesets: [], conversionErrors: {}, limitations: {}, sanitization,
  unsafeDeclarativeRulesDropped: 0,
};

for (const { ruleset, errors, limitations } of results) {
  const id = ruleset.getId();
  const rules = ruleset.getDeclarativeRules();
  const safeRules = rules.filter((rule) => !isUnsafeCatchAllBlock(rule));
  const unsafeDropped = rules.length - safeRules.length;
  report.unsafeDeclarativeRulesDropped += unsafeDropped;
  const folder = path.join(resolvedOutputDir, id);
  await mkdir(folder, { recursive: true });
  await writeFile(path.join(folder, `${id}.json`), JSON.stringify(safeRules));
  report.rulesets.push({ id, rules: safeRules.length, unsafeDropped });

  for (const error of errors) {
    const name = error?.constructor?.name || 'Error';
    report.conversionErrors[name] = (report.conversionErrors[name] || 0) + 1;
  }
  for (const limitation of limitations) {
    const name = limitation?.constructor?.name || 'Limitation';
    report.limitations[name] = (report.limitations[name] || 0) + 1;
  }
}

await writeFile(
  path.join(resolvedOutputDir, 'conversion-report.json'),
  `${JSON.stringify(report, null, 2)}\n`,
);
console.log(JSON.stringify(report));
