import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { Filter, FilterConverter } from '@adguard/dnr-converter';

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
const filters = await Promise.all(metadata.map(async ({ filterId }) => (
  new Filter(filterId, await readFile(path.join(resolvedFiltersDir, `filter_${filterId}.txt`), 'utf8'))
)));

await rm(resolvedOutputDir, { recursive: true, force: true });
await mkdir(resolvedOutputDir, { recursive: true });

// ponytail: omit resourcesPath because CLI turns Windows paths into invalid extension URLs.
// Redirect rules without bundled resources are skipped; regular DNR rules still compile.
const results = await new FilterConverter().convert(filters);
const report = { rulesets: [], conversionErrors: {}, limitations: {} };

for (const { ruleset, errors, limitations } of results) {
  const id = ruleset.getId();
  const rules = ruleset.getDeclarativeRules();
  const folder = path.join(resolvedOutputDir, id);
  await mkdir(folder, { recursive: true });
  await writeFile(path.join(folder, `${id}.json`), JSON.stringify(rules));
  report.rulesets.push({ id, rules: rules.length });

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
