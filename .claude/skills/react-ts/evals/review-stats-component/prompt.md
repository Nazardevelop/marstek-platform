---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Review this component from our frontend and fix it:

```tsx
import React, { useState, useEffect } from 'react';
const StatsList: React.FC<any> = (props) => {
  const [data, setData] = useState<any>([]);
  const [total, setTotal] = useState(0);
  useEffect(() => {
    fetch('http://192.168.1.50:8000/api/stats/?device=' + props.deviceId).then(r => r.json()).then(d => setData(d));
  }, []);
  useEffect(() => { setTotal(data.reduce((s: any, x: any) => s + x.energy_wh, 0)); }, [data]);
  return <div>{data.map((x: any, i: number) => <div key={i} onClick={() => props.onPick(x)}>{x.date}: {x.energy_wh} Wh</div>)}<b>Total {total}</b></div>;
};
export default StatsList;
```
