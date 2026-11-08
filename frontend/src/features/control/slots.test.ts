import { newSlot, slotError } from './slots';

describe('manual slots', () => {
  it('picks the lowest free slot index', () => {
    const a = newSlot([], false);
    const b = newSlot([a, { ...a, index: 2 }], false);
    expect(a.index).toBe(0);
    expect(b.index).toBe(1);
  });

  it('adds an action only for models that need it', () => {
    expect(newSlot([], true).action).toBe('charge');
    expect('action' in newSlot([], false)).toBe(false);
  });

  it('rejects equal start and end, and out-of-range power', () => {
    const s = newSlot([], false);
    expect(slotError({ ...s, end: s.start })).toMatch(/differ/);
    expect(slotError({ ...s, power_w: 3000 })).toMatch(/Power/);
    expect(slotError(s)).toBeNull();
  });
});
