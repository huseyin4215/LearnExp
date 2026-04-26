import type { Article, RecommendationItem } from '../services/api';

type SourceItem = Article | RecommendationItem;

const getSourceName = (item: SourceItem) => {
  if ('api_source' in item) return item.api_source?.name || 'Unknown';
  return item.source || 'Unknown';
};

export const interleaveBySource = <T extends SourceItem>(items: T[]) => {
  const buckets = new Map<string, T[]>();

  items.forEach((item) => {
    const source = getSourceName(item);
    const bucket = buckets.get(source) || [];
    bucket.push(item);
    buckets.set(source, bucket);
  });

  const entries = Array.from(buckets.entries())
    .map(([source, sourceItems]) => ({
      source,
      items: [...sourceItems],
    }))
    .sort((left, right) => right.items.length - left.items.length);

  const interleaved: T[] = [];
  let added = true;

  while (added) {
    added = false;
    entries.forEach((entry) => {
      const next = entry.items.shift();
      if (next) {
        interleaved.push(next);
        added = true;
      }
    });
  }

  return interleaved;
};

export const formatMatchScore = (score?: number) => {
  if (score == null || Number.isNaN(score)) return null;
  const normalized = score <= 1 ? score * 100 : score;
  return Math.max(0, Math.min(100, Math.round(normalized)));
};
