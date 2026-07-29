const UNIVERSAL_PUNCTUATION_FILTERS = new Set([':', '://', '//', '.']);
const URL_SAFETY_SAMPLES = [
  ['http://a.invalid/', 'http://example.org/path', 'http://127.0.0.1:8080/q?x=1', 'http://localhost/'],
  ['https://b.invalid/', 'https://sample.net/deep/file.js', 'https://192.0.2.1:8443/q?y=2', 'https://localhost/'],
  ['ws://c.invalid/socket', 'ws://example.org/live', 'ws://198.51.100.1:8080/feed', 'ws://localhost/channel'],
  ['wss://d.invalid/socket', 'wss://sample.net/live', 'wss://203.0.113.1:8443/feed', 'wss://localhost/channel'],
];

const escapeRegex = (char) => char.replace(/[\\^$.*+?()[\]{}|]/g, '\\$&');

const matchesUrlFilter = (urlFilter, url, caseSensitive) => {
  let pattern = urlFilter;
  const leftAnchored = pattern.startsWith('|');
  if (leftAnchored) pattern = pattern.slice(1);
  const rightAnchored = pattern.endsWith('|');
  if (rightAnchored) pattern = pattern.slice(0, -1);
  let source = '';
  for (const char of pattern) {
    if (char === '*') source += '.*';
    else if (char === '^') source += '(?:[^a-z0-9_\\-.%]|$)';
    else source += escapeRegex(char);
  }
  const expression = `${leftAnchored ? '^' : ''}${source}${rightAnchored ? '$' : ''}`;
  return new RegExp(expression, caseSensitive ? '' : 'i').test(url);
};

export const isUnsafeUnscopedBlock = (rule) => {
  if (rule.action?.type !== 'block') return false;
  const condition = rule.condition || {};
  if (condition.requestDomains?.length || condition.initiatorDomains?.length) return false;
  // ponytail: unscoped regex blocks fail closed; proving every RE2 pattern narrow is not worth the risk.
  if (condition.regexFilter !== undefined) return true;
  const urlFilter = condition.urlFilter;
  if (typeof urlFilter !== 'string') return true;
  const literal = urlFilter.replace(/[|*^]/g, '');
  if (literal === '' || UNIVERSAL_PUNCTUATION_FILTERS.has(literal)) return true;
  if (urlFilter.startsWith('||')) return false;
  return URL_SAFETY_SAMPLES.some((urls) =>
    urls.every((url) => matchesUrlFilter(urlFilter, url, condition.isUrlFilterCaseSensitive)),
  );
};
