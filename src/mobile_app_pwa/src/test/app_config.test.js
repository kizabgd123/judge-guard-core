import { describe, it, expect } from 'vitest';
import appConfig from '../../public/app_config.json';

describe('app_config.json', () => {
  it('contains a title field', () => {
    expect(appConfig).toHaveProperty('title');
    expect(typeof appConfig.title).toBe('string');
  });

  it('contains a theme field', () => {
    expect(appConfig).toHaveProperty('theme');
    expect(typeof appConfig.theme).toBe('string');
  });

  it('contains a content field', () => {
    expect(appConfig).toHaveProperty('content');
    expect(typeof appConfig.content).toBe('string');
  });

  it('contains a components array', () => {
    expect(appConfig).toHaveProperty('components');
    expect(Array.isArray(appConfig.components)).toBe(true);
  });

  it('handles optional last_verdict from mobile bridge', () => {
    if ('last_verdict' in appConfig && appConfig.last_verdict !== null) {
      expect(typeof appConfig.last_verdict).toBe('object');
    }
  });

  it('has the correct title value', () => {
    expect(appConfig.title).toBe('Antigravity Mobile');
  });

  it('has all required base keys (title, theme, content, components)', () => {
    const keys = Object.keys(appConfig);
    expect(keys).toEqual(expect.arrayContaining(['title', 'theme', 'content', 'components']));
  });
});