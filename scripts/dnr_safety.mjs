const PROTOCOL_ONLY_FILTERS = new Set(['http', 'https', 'http:', 'https:', 'http://', 'https://']);
const UNIVERSAL_PUNCTUATION_FILTERS = new Set([':', '://', '//', '.']);

export const isUnsafeUnscopedBlock = (rule) => {
  if (rule.action?.type !== 'block') return false;
  const condition = rule.condition || {};
  if (condition.requestDomains?.length || condition.initiatorDomains?.length) return false;
  // ponytail: unscoped regex blocks fail closed; proving every RE2 pattern narrow is not worth the risk.
  if (condition.regexFilter !== undefined) return true;
  const urlFilter = condition.urlFilter;
  if (typeof urlFilter !== 'string') return true;
  const literal = urlFilter.replace(/[|*^]/g, '');
  return literal === '' || UNIVERSAL_PUNCTUATION_FILTERS.has(literal) || PROTOCOL_ONLY_FILTERS.has(literal.toLowerCase());
};
