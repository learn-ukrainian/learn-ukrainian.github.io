/* Read-only operator home. Requests only the explicit existing endpoints below. */
(function (root) {
  const REFRESH_MS = 30000;
  const STALE_MS = 120000;
  const STATES = ["working", "idle", "stuck", "dead", "paused", "off"];
  const STATE_ORDER = { dead: 0, stuck: 1, working: 2, idle: 3, paused: 4, off: 5 };
  const KIND_LABEL = {
    dead_driver: "Dead driver",
    stuck_driver: "Stuck driver",
    red_foundation: "Red foundation",
    unqueued_pr: "Green PR not queued",
    alert: "Alert",
    usage: "Usage near limit",
  };
  const STATUS_RANK = { ok: 0, stale: 1, unavailable: 2, not_configured: 3 };

  function esc(value) {
    return String(value ?? "").replace(/[&<>"]/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
    }[ch]));
  }

  function identifierHref(prefix, id) {
    try {
      return prefix + encodeURIComponent(id);
    } catch (error) {
      if (error instanceof URIError) return null;
      throw error;
    }
  }

  function identifierLink(prefix, id, label, attrs = '') {
    const href = identifierHref(prefix, id);
    return href === null ? esc(label) : `<a${attrs} href="${esc(href)}">${esc(label)}</a>`;
  }

  function isFleetPath(path) {
    if (typeof path !== "string") return false;
    if (path.includes("://") || path.includes("\\") || path.includes("..")) return false;
    if (!path.startsWith("/api/fleet/v1")) return false;
    const rest = path.slice("/api/fleet/v1".length);
    if (["/now", "/epics", "/agents", "/prs", "/alerts", "/backups", "/downloads", "/stats", "/links"].includes(rest)) return true;
    const epic = /^\/epics\/([^/]+)$/.exec(rest);
    if (epic) return epic[1].length > 0 && !/%2f/i.test(epic[1]);
    const agent = /^\/agents\/([^/]+)$/.exec(rest);
    if (agent) return agent[1].length > 0 && !/%2f/i.test(agent[1]);
    return false;
  }

  const READS = {
    registry: '/api/epics/v1',
    work: '/api/work/v1/projection',
    hosts: '/api/occupancy',
    workers: '/api/fleet/workers/v1',
    tasks: '/api/delegate/tasks?limit=100',
    slots: '/api/ops/v1/test-slots',
    accounts: '/api/state/routing-budget',
    proposals: '/api/consultation/queue',
    messages: '/api/fleet/messages?limit=50',
    prs: '/api/fleet/v1/prs',
    alerts: '/api/fleet/v1/alerts',
    backups: '/api/fleet/v1/backups',
    downloads: '/api/fleet/v1/downloads',
    stats: '/api/fleet/v1/stats',
    links: '/api/fleet/v1/links',
  };
  const record = (v) => !!v && typeof v === 'object' && !Array.isArray(v);
  const number = (v) => typeof v === 'number' && Number.isFinite(v) && v >= 0;
  const text = (v) => typeof v === 'string' && v.length > 0;

  function validRead(key, b) {
    if (!record(b)) return false;
    if (key === 'registry')
      return Array.isArray(b.streams) && b.streams.every((r) => record(r) && text(r.stream_id));
    if (key === 'work')
      return (
        Array.isArray(b.items) &&
        Array.isArray(b.sources) &&
        b.items.every(
          (r) => record(r) && text(r.work_id) && text(r.resource_kind) && record(r.projections),
        )
      );
    if (key === 'hosts') return record(b.hosts) && Object.values(b.hosts).every(record);
    if (key === 'workers')
      return (
        Array.isArray(b.hosts) &&
        record(b.counts) &&
        b.hosts.every(
          (h) =>
            record(h) &&
            text(h.host_id) &&
            Array.isArray(h.workers) &&
            h.workers.every((w) => record(w) && text(w.id) && text(w.state)),
        )
      );
    if (key === 'tasks')
      return (
        Array.isArray(b.tasks) && b.tasks.every((t) => record(t) && text(t.task_id) && text(t.status))
      );
    if (key === 'slots')
      return (
        b.schema === 'test-slots.status.v1' &&
        (typeof b.enabled === 'boolean' || (b.enabled === null && record(b.error))) &&
        'error' in b &&
        (b.error !== null ||
          ['pool_size', 'slots_in_use', 'slots_free', 'queue_depth'].every((k) => number(b[k])))
      );
    if (key === 'accounts') return record(b.claude_accounts);
    if (key === 'proposals')
      return Array.isArray(b.pending) && number(b.count) && b.pending.every(record);
    if (key === 'messages') return Array.isArray(b.messages) && text(b.availability);
    if (!Array.isArray(b.sources) || !record(b.data) || b.schema !== 'fleet.v1.' + key) return false;
    if (key === 'backups') return ['age_h', 'last_result', 'restore_test'].every((k) => k in b.data);
    if (key === 'stats')
      return (
        Array.isArray(b.data.stats) && Array.isArray(b.data.by_repo) && Array.isArray(b.data.by_lane)
      );
    const rows = b.data[key === 'downloads' ? 'items' : key];
    if (!Array.isArray(rows)) return false;
    if (key === 'prs')
      return rows.every(
        (r) =>
          record(r) && text(r.repo) && Number.isInteger(r.number) && r.number > 0 && text(r.head_sha),
      );
    return rows.every(record);
  }

  function readResult(key, body, error, previous, at) {
    let omitted = 0;
    if (!error && record(body)) {
      const validators = {
        registry: ['streams', (r) => record(r) && text(r.stream_id)],
        work: [
          'items',
          (r) => record(r) && text(r.work_id) && text(r.resource_kind) && record(r.projections),
        ],
        tasks: ['tasks', (r) => record(r) && text(r.task_id) && text(r.status)],
        workers: [
          'hosts',
          (h) =>
            record(h) &&
            text(h.host_id) &&
            Array.isArray(h.workers) &&
            h.workers.every((w) => record(w) && text(w.id) && text(w.state)),
        ],
        proposals: ['pending', record],
        messages: ['messages', record],
      };
      const field = key === 'downloads' ? 'items' : key;
      const collection =
        validators[key] ||
        (record(body.data) && Array.isArray(body.data[field])
          ? [
              field,
              key === 'prs'
                ? (r) =>
                    record(r) &&
                    text(r.repo) &&
                    Number.isInteger(r.number) &&
                    r.number > 0 &&
                    text(r.head_sha)
                : record,
            ]
          : null);
      const container = validators[key] ? body : body.data;
      if (collection && Array.isArray(container?.[collection[0]])) {
        const [name, valid] = collection;
        const input = container[name],
          kept = input.filter(valid);
        omitted = input.length - kept.length;
        if (omitted && !kept.length) error = 'Malformed success response';
        else if (omitted)
          body = validators[key]
            ? Object.assign({}, body, { [name]: kept })
            : Object.assign({}, body, { data: Object.assign({}, body.data, { [name]: kept }) });
      }
    }
    if (!error && !validRead(key, body)) error = 'Malformed success response';
    if (error)
      return {
        body: previous?.body || null,
        fetchedAt: previous?.fetchedAt || null,
        error,
        pending: false,
      };
    return { body, fetchedAt: at, error: '', pending: false, omitted };
  }

  function elapsedSeconds(at, now) {
    const parsed = typeof at === 'string' ? Date.parse(at) : NaN;
    return Number.isFinite(parsed) && parsed <= now ? (now - parsed) / 1000 : null;
  }

  function ageText(seconds) {
    return number(seconds) ? metricText(seconds, ' s') : 'unknown';
  }

  function advancedAge(age, fetchedAt, now) {
    return number(age) && number(fetchedAt) && now >= fetchedAt
      ? age + (now - fetchedAt) / 1000
      : null;
  }

  function valueText(v) {
    return typeof v === 'boolean'
      ? String(v)
      : typeof v === 'number'
        ? metricText(v)
        : text(v)
          ? esc(v)
          : 'unknown';
  }

  function table(caption, headers, rows) {
    if (!rows.length) return '<p class="fb-empty">No rows returned; coverage/age unknown.</p>';
    return `<div class="fb-table-wrap"><table class="fb-table"><caption>${esc(caption)}</caption><thead><tr>${headers.map((h) => `<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell, i) => `<td data-l="${esc(headers[i])}">${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }

  function sourceNotes(entry, now, focusKey) {
    if (!entry?.body) return '';
    const b = entry.body;
    const rows = [];
    for (const s of Array.isArray(b.sources) ? b.sources : []) {
      if (!record(s)) continue;
      const name = s.name || s.source_id || s.id || 'source';
      rows.push(
        `<li>${esc(name)}: ${valueText(s.status)}; read/cache age ${ageText(advancedAge(s.age_s, entry.fetchedAt, now))}</li>`,
      );
      for (const [name, section] of Object.entries(s.sections || {})) {
        if (!record(section)) continue;
        rows.push(
          `<li>${esc(name)} section: ${valueText(section.status)}; coverage ${valueText(section.count)} returned rows; observation age ${ageText(advancedAge(section.age_s, entry.fetchedAt, now))}; omissions ${valueText(section.reason)}</li>`,
        );
      }
    }
    if (number(b.cache_age_s))
      rows.push(
        `<li>Projection cache age ${ageText(advancedAge(b.cache_age_s, entry.fetchedAt, now))}; source age remains independent.</li>`,
      );
    return rows.length
      ? `<details class="fb-provenance"><summary data-focus-key="${esc(focusKey)}">Source qualifications</summary><ul>${rows.join('')}</ul></details>`
      : '';
  }

  function readPanel(key, title, entries, now, render, extra) {
    const e = entries[key];
    const b = e?.body;
    const reports = sourcesOf(b);
    let status = 'Unknown';
    if (!e || (e.pending && !b)) status = 'Loading';
    else if (e.error) status = 'Error: ' + e.error + (b ? '; retained historical observation' : '');
    else if (
      reports.some((s) =>
        ['unavailable', 'timeout', 'degraded', 'permission_denied'].includes(s.status),
      )
    )
      status = 'Partial / unavailable source';
    else if (reports.length && reports.every((s) => s.status === 'not_configured'))
      status = 'Not installed';
    else if (reports.some((s) => s.status === 'not_configured'))
      status = 'Partial / not installed source';
    else if (
      reports.some((s) => s.status === 'stale') ||
      (e.fetchedAt && now - e.fetchedAt > STALE_MS)
    )
      status = 'Stale';
    else if (reports.length && reports.every((s) => s.status === 'ok'))
      status = 'Observed; upstream sample age/coverage unknown';
    if (key === 'slots' && b?.error) status = 'Unavailable: governor read failed';
    if (key === 'messages' && b && b.availability !== 'available')
      status = 'Unavailable: ' + b.availability;
    if (e?.omitted) status = 'Partial: ' + e.omitted + ' malformed rows omitted';
    const busy = !e || e.pending ? 'true' : 'false';
    const fetchAge = e?.fetchedAt ? ageText((now - e.fetchedAt) / 1000) + ' ago' : 'none';
    return `<section class="fb-panel" data-read="${key}" aria-busy="${busy}"><h3>${esc(title)}</h3><p class="fb-read-state">${esc(status)}</p>
        ${b ? render(b, e) : '<p>No values available.</p>'}${extra || ''}
        <p class="fb-src">Source age unknown unless qualified below. Last successful fetch: ${esc(fetchAge)}. Read: ${esc(READS[key])}</p>
        ${sourceNotes(e, now, "source:" + key + ":" + title)}<button type="button" class="fb-btn" data-focus-key="${esc(key + ":" + title)}" data-retry="${key}">Retry ${esc(title)}</button></section>`;
  }

  function gap(id, owner, reason) {
    return `<p class="fb-gap">${esc(id)} unmet: ${esc(reason)} Owner: ${esc(owner)}.</p>`;
  }

  function registryRows(b, entries, now) {
    const optional = entries.epics?.body?.data?.epics || [];
    return (
      `<p>${b.streams.length} streams known to the session store, including ${b.streams.filter((s) => s.registered === true).length} registered.</p>` +
      table(
        'Lanes and recorded driver observations',
        [
          'Stream',
          'Registry',
          'Lease holder / task',
          'Lease / heartbeat',
          'Model',
          'Last recorded state / decision',
        ],
        b.streams.map((s) => {
          const lease = s.lease || {},
            holder = lease.holder || {};
          const match = optional.find(
            (o) => o.epic === s.stream_name && o.driver?.agent_id === holder.agent,
          );
          const model = match?.driver?.model;
          const events =
            [s.last_state, s.last_decision]
              .filter(record)
              .map(
                (v) =>
                  `${esc(v.body || 'recorded event')} (event age ${ageText(elapsedSeconds(v.created_at, now))})`,
              )
              .join('<br>') || 'unknown';
          return [
            `${identifierLink('/epics.html#', s.stream_id, s.title || s.stream_name || s.stream_id)} ${identifierLink('#/epic/', s.stream_name || s.stream_id, 'Board detail')}`,
            s.registered === true ? 'registered' : 'unregistered',
            `${valueText(holder.agent)} / ${valueText(holder.task_id)}<br>Harness ${valueText(holder.harness)}`,
            `${valueText(lease.state)} / heartbeat age ${ageText(elapsedSeconds(lease.heartbeat_at, now))}; expires ${valueText(lease.expires_at)}`,
            model
              ? `${esc(model)} (optional board observation, currentness unknown)`
              : 'unknown (D11-RO/HA)',
            events,
          ];
        }),
      )
    );
  }

  function workerBuckets(b) {
    const counts = { fresh: 0, stale: 0, unknown: 0, unreported: 0, live: 0, rows: 0 };
    const rows = [];
    b.hosts.forEach((h) => {
      const bucket =
        h.workers_status !== 'reported'
          ? 'unreported'
          : h.host_id === 'unattributed'
            ? 'unknown'
            : ['fresh', 'stale'].includes(h.freshness)
              ? h.freshness
              : 'unknown';
      counts[bucket]++;
      h.workers.forEach((w) => {
        if (!record(w)) return;
        counts.rows++;
        if (bucket === 'fresh' && w.state === 'live') counts.live++;
        rows.push({ host: h, worker: w, bucket });
      });
    });
    return { counts, rows };
  }

  function workersRows(b, e, now) {
    const { counts: c, rows } = workerBuckets(b);
    return (
      `<p>${c.live} observed live workers on fresh reporting hosts. Host coverage: ${c.fresh} fresh, ${c.stale} stale, ${c.unknown} unknown/unattributed, ${c.unreported} unreported; ${b.hosts.length} returned hosts. ${c.rows} loaded worker rows; reported total ${valueText(b.counts.workers_total)}; skipped ${valueText(b.counts.skipped)}. Feeds overlap; totals are not added.</p>` +
      table(
        'Workers by final host freshness',
        ['Worker', 'Host / report age', 'Observation', 'Activity age', 'Task / epic'],
        rows.map(({ host: h, worker: w, bucket }) => [
          `${valueText(w.agent)} / ${valueText(w.harness)}<br>${valueText(w.id)} (${valueText(w.kind)})`,
          `${esc(h.host_id)} / ${ageText(advancedAge(h.age_s, e.fetchedAt, now))}`,
          `${esc(bucket === 'stale' ? 'last observed' : bucket)}: ${valueText(w.state)}`,
          ageText(advancedAge(w.age_s, e.fetchedAt, now)),
          valueText(w.epic),
        ]),
      )
    );
  }

  function hostRows(b, e, now) {
    return table(
      'Host load observations',
      ['Host', 'Status / source age', 'Load / CPUs', 'Memory', 'Disk'],
      Object.entries(b.hosts).map(([id, h]) => {
        const usable =
          ['fresh', 'stale'].includes(h.status) && elapsedSeconds(h.observed_at, now) !== null;
        const age = usable ? elapsedSeconds(h.observed_at, now) : null;
        const metric = (v) =>
          !usable
            ? 'unknown'
            : Array.isArray(v)
              ? v.map(valueText).join(' / ')
              : record(v)
                ? Object.entries(v)
                    .filter(([, v]) => typeof v === 'number')
                    .map(([k, v]) => `${esc(k)} ${valueText(v)}`)
                    .join('; ') || 'unknown'
                : valueText(v);
        return [
          esc(id),
          `${valueText(h.status)} / ${ageText(age)}${h.status === 'stale' ? ' (historical)' : ''}`,
          `${metric(h.loadavg)} / ${metric(h.cpu_count)}`,
          metric(h.mem),
          metric(h.disk),
        ];
      }),
    );
  }

  function slotsRows(b) {
    if (b.error) return '<p>Unavailable: governor read failed. Counts unknown.</p>';
    if (!b.enabled)
      return '<p>Governor disabled. Governed occupancy, free slots and queue are unknown.</p>';
    if (b.pool_exists !== true) return '<p>Pool observation unknown. Occupied, free and queued counts unknown.</p>';
    return `<p>Pool ${b.pool_size}; occupied ${b.slots_in_use}; free ${b.slots_free}; queued ${b.queue_depth}. Source observation time is not supplied.</p>`;
  }

  function accountRows(b, e, now) {
    return (
      table(
        'Account windows, separate from provider meters',
        ['Account alias', 'State / source age', 'Window', 'Left', 'Reset', 'Pace / delta / leftover'],
        ['claude:a', 'claude:b'].flatMap((alias) => {
          const a = b.claude_accounts[alias] || {};
          const usable =
            ['ok', 'stale'].includes(a.status) &&
            !['account_ambiguous', 'not_probed'].includes(a.reason);
          return ['session5h', 'weekly'].map((window) => {
            const w = usable && record(a[window]) ? a[window] : {};
            return [
              esc(alias),
              `${valueText(a.stale === true ? "stale" : a.status)} / ${ageText(elapsedSeconds(a.updated, now))}; ${valueText(a.reason)}`,
              window,
              number(w.left_pct) && w.left_pct <= 100 ? valueText(w.left_pct) + '%' : 'unknown',
              valueText(w.resets_at),
              `${valueText(w.pace)} / ${valueText(w.pace_delta_pct)} / ${valueText(w.leftover_pct)}`,
            ];
          });
        }),
      ) +
      '<p>Other provider meters are not verified account equivalents. Preference is a display hint, never routing authorization.</p>' + providerRows(b,e,now)
    );
  }

  function providerRows(b, e, now) {
    const rows = [];
    for (const lane of ['claude', 'codex', 'agy', 'grok', 'cursor', 'kimi']) {
      const agent = b.agents?.[lane] || {};
      const cb = agent.codexbar || {};
      const named = record(agent.provider_windows) ? agent.provider_windows : cb.provider_windows;
      const windows = record(named) ? Object.entries(named) : record(cb.windows)
        ? ['primary','secondary','tertiary'].filter(k => record(cb.windows[k])).map(k => [k,cb.windows[k]]) : [];
      if (!windows.length) windows.push(['weekly', {used_pct:cb.weekly_used_pct,remaining_pct:cb.weekly_remaining_pct,resets_at:cb.weekly_resets_at}]);
      for (const [name,win] of windows) {
        const usable = record(win) && ['fresh','stale','stale_last_good'].includes(cb.freshness) && cb.status !== 'unavailable' && cb.probe_state !== 'NEED_PROBE';
        const pct = v => usable && number(v) && v <= 100 ? valueText(v) + '%' : 'unknown';
        rows.push([esc(lane),esc(name), `${valueText(cb.stale === true ? 'stale' : cb.freshness)} / report age ${ageText(advancedAge(cb.age_s,e.fetchedAt,now))}`,
          pct(win?.used_pct),pct(win?.remaining_pct),valueText(usable ? win?.resets_at : null)]);
      }
    }
    return table('Provider meters; account attribution and shared-meter parity unverified', ['Lane alias','Window','Source state / age','Used','Remaining','Reset'],rows) + '<p>Grok/Cursor meters may overlap. They are never summed or counted as separate accounts. Cost/burn fallback is excluded.</p>';
  }

  function workQualifications(item, e, now) {
    return (
      (Array.isArray(item.authority) ? item.authority.filter(record) : [])
        .map(
          (a) =>
            `${valueText(a.domain)}; observation age ${ageText(advancedAge(a.age_s, e.fetchedAt, now))}; stale ${valueText(a.stale)}`,
        )
        .join('<br>') +
      (Array.isArray(item.omissions) && item.omissions.length ? '<br>Item omissions present' : '')
    );
  }

  function pipelineRows(entries, now, params) {
    const work = entries.work?.body;
    const fleet = entries.prs?.body;
    const selected = params?.get('pr');
    const workRows = (work?.items || []).filter((r) => r.resource_kind === 'pr');
    const optional = fleet?.data?.prs || [];
    const samePR = (item, f) => f.repo === item.repository_id && String(f.number) === String(item.remote_id);
    const duplicate = (repo, id) =>
      workRows.filter(i => i.repository_id === repo && String(i.remote_id) === String(id)).length > 1 ||
      optional.filter(f => f.repo === repo && String(f.number) === String(id)).length > 1;
    const observed = (e) => !e?.error && !e?.omitted && number(e?.fetchedAt) &&
      now >= e.fetchedAt && now - e.fetchedAt <= STALE_MS;
    const qualified = (name) => {
      const reports = sourcesOf(fleet).filter(s => s.name === name);
      return observed(entries.prs) && reports.length > 0 &&
        reports.every(s => s.status === 'ok' && s.error === null && number(s.age_s));
    };
    const rows = workRows.map((item) => {
      const p = item.projections || {},
        v = p.verification || {};
      const f = optional.find(
        (f) => samePR(item, f) && !duplicate(f.repo, f.number),
      );
      return { item, f, v, p };
    });
    optional
      .filter((f) => !rows.some((r) => r.f === f))
      .forEach((f) => rows.push({ f, item: null, p: {}, v: {} }));
    const gh = qualified('github');
    const mq = qualified('mq_state');
    const activity = sourcesOf(fleet).filter(s => s.name === 'stale_prs');
    const activityUsable = activity.every(s => !s.error &&
      (s.status === 'not_configured' || s.status === 'ok' && number(s.age_s)));
    const shown = rows.filter(
      (r) => !selected || String(r.item?.remote_id || r.f?.number) === selected,
    );
    return (
      `${selected ? `<p>Selected PR #${esc(selected)}. <a href="#/prs">Clear selection</a></p>` : ''}` +
      table(
        'Observed PR pipeline; no merge eligibility is granted here',
        [
          'PR / head',
          'Accountable owner',
          'Stream',
          'Derived/recorded lane',
          'Review',
          'CI',
          'Gate',
          'Queue / hold',
          'Idle / blockers / flags',
          'Source qualification',
        ],
        shown.map(({ item: i, f, p, v }) => {
          const ambiguous = duplicate(i?.repository_id || f?.repo, i?.remote_id || f?.number);
          const authority = (Array.isArray(i?.authority) ? i.authority : []).filter(a => a?.domain === 'github');
          const usable =
            i?.flags?.source_ok === true &&
            observed(entries.work) && !ambiguous && text(v.head_sha) &&
            sourcesOf(work).every(s => ['ok', 'truncated'].includes(s.sections?.prs?.status || s.status)) &&
            authority.length > 0 &&
            authority.every(
              (a) =>
                record(a) &&
                a.domain === 'github' &&
                a.stale === false &&
                elapsedSeconds(a.observed_at, now) !== null,
            );
          const disagreement = i && f && text(v.head_sha) && text(f.head_sha) && f.head_sha !== v.head_sha;
          const headMatch = !f || (text(v.head_sha) && text(f.head_sha) && f.head_sha === v.head_sha);
          const fleetUsable = !!f && gh && !ambiguous && !(usable && disagreement);
          const workUsable = usable && headMatch;
          const queueUsable = !!f && mq && !ambiguous && !(usable && disagreement);
          const currentCF = fleetUsable && f?.cf?.at_head === true;
          const id = i?.remote_id || f?.number;
          const title = i?.title || f?.title;
          const blocker =
            fleetUsable && f?.blocker?.kind && f.blocker.kind !== 'none'
              ? valueText(f.blocker.kind) +
                (Array.isArray(f.blocker.checks) ? ': ' + f.blocker.checks.map(esc).join(', ') : '')
              : 'unknown; Work PR flags carry no blocker evidence';
          return [
            `${identifierLink('#/prs?pr=', id, '#' + id + ' ' + (title || ''), ` data-focus-key="pr:${esc(i?.repository_id || f?.repo)}:${esc(id)}"`)}<br>${valueText(i?.repository_id || f?.repo)}<br>Head ${valueText(usable ? v.head_sha : f?.head_sha || v.head_sha)}<br>${valueText(workUsable ? i.lifecycle : fleetUsable && f ? (f.draft === true ? 'draft' : 'open observation') : null)}`,
            'unknown (D04; canonical PR association unavailable)',
            'unknown (D04; canonical PR membership unavailable)',
            `${valueText(f?.owner_lane)}; provenance unverified`,
            currentCF
              ? `CF ${valueText(f.cf.verdict)} at observed head`
              : `CF unknown; Work review ${valueText(usable ? p.review?.review_decision : null)} is not exact-head approval`,
            fleetUsable && f ? valueText(f.ci) : valueText(workUsable ? v.ci_state : null),
            fleetUsable ? valueText(f?.gate) : 'unknown',
            queueUsable
              ? `${valueText(f?.mq)} / hold ${valueText(f?.keeper?.hold)} ${valueText(f?.keeper?.reason)}`
              : 'unknown',
            `Idle ${valueText(fleetUsable && activityUsable ? f?.hours_idle : null)} h (activity clock); ${blocker}<br>Draft ${valueText(fleetUsable ? f?.draft : workUsable ? i?.flags?.is_draft : null)}; stale green ${valueText(fleetUsable && queueUsable ? f?.stale_green : null)}; stacked ${valueText(fleetUsable ? f?.stacked_base?.state : null)}; flake ${valueText(queueUsable ? f?.flake_grant?.decision : null)}`,
            `${ambiguous ? 'Duplicate PR observations; current attributes unknown.<br>' : ''}${disagreement ? `Head disagreement: Work ${esc(v.head_sha)} / Fleet ${esc(f.head_sha)}.<br>` : ''}${f ? `Fleet github: ${valueText(sourceStatus(sourcesOf(fleet), 'github'))}; mq_state: ${valueText(sourceStatus(sourcesOf(fleet), 'mq_state'))}; source ages in qualifications, separate from activity.<br>` : ''}` + (i
              ? workQualifications(i, entries.work, now)
              : 'Optional Fleet observation; Work association unknown'),
          ];
        }),
      ) +
      gap(
        'D04 / D11-GH/MQ/SP',
        'codex-monitor and existing source custodians',
        'Merged history, canonical PR ownership/stream association and missing current-head evidence remain required; disappearance is not a merge.',
      )
    );
  }

  function attentionPanels(entries, now) {
    return (
      `<h2>Needs attention</h2><div class="fb-gap"><h3>Posted blockers</h3><p>Unknown: safe typed projection unavailable (D05). Source age unknown; last successful fetch: none.</p><h3>Confirmed operator decisions</h3><p>Unknown: safe typed projection unavailable (D05). Source age unknown; last successful fetch: none.</p></div>${gap('D05', 'codex-monitor and existing Fleet/decision custodians', 'Posted blockers and confirmed operator decisions require a safe typed projection. Neither Work impediments, proposals nor recorded decisions proves those obligations.')}` +
      readPanel('work', 'Derived impediments', entries, now, (b) =>
        table(
          'Derived Work attention, not posted blocker reports',
          ['Work', 'Lifecycle / action'],
          b.items
            .filter(
              (i) =>
                i.resource_kind !== 'pr' &&
                (i.flags?.has_blocker ||
                  (i.safe_next_action?.code && i.safe_next_action.code !== 'NONE')),
            )
            .map((i) => [
              esc(i.title || i.work_id),
              `${valueText(i.lifecycle)} / ${valueText(i.safe_next_action?.code)}`,
            ]),
        ),
      ) +
      readPanel(
        'messages',
        'Posted blocker / decision metadata',
        entries,
        now,
        (b) =>
          `<p>Availability ${valueText(b.availability)}; ${b.messages.length} loaded messages of ${valueText(b.total)}. Source age and classification coverage unknown. <a href="/fleet.html">Fleet metadata</a></p>`,
      ) +
      readPanel('proposals', 'Proposals', entries, now, (b) =>
        table(
          'Queued proposals, not confirmed operator decisions',
          ['Proposal', 'Summary', 'Queued event age'],
          b.pending.map((p) => [
            `<a href="/consultation.html">${esc(p.source_module || 'Proposal')}</a>`,
            valueText(p.root_cause_summary),
            ageText(elapsedSeconds(p.queued_at, now)),
          ]),
        ),
      ) +
      readPanel(
        'alerts',
        'Alerts',
        entries,
        now,
        (b) =>
          table(
            'Returned alerts',
            ['Name', 'Severity / state', 'Summary', 'Started event age'],
            b.data.alerts
              .filter(record)
              .map((a) => [
                valueText(a.name),
                `${valueText(a.severity)} / ${valueText(a.state)}`,
                valueText(a.summary),
                ageText(elapsedSeconds(a.starts_at, now)),
              ]),
          ),
        gap(
          'D11-AL',
          'existing observability custodian and codex-monitor',
          'Unavailable alert source cannot prove no alerts.',
        ),
      )
    );
  }

  function opsPanels(entries, now) {
    return (
      `<h2>Ops</h2>` +
      readPanel(
        'backups',
        'Backup and restore',
        entries,
        now,
        (b, e) => {
          const d = b.data;
          return `<p>Backup result ${valueText(d.last_result?.status)}; backup event age ${ageText(elapsedSeconds(d.last_result?.at, now))}. Restore test ${valueText(d.restore_test?.ok)}; restore event age ${ageText(elapsedSeconds(d.restore_test?.at, now))}. Upstream stale ${valueText(d.stale)}.</p><a href="/admin.html#backups">Backup detail</a>`;
        },
        gap(
          'D11-BA',
          'existing backup custodian and codex-monitor',
          'Missing backup or restore evidence remains unknown.',
        ),
      ) +
      readPanel(
        'downloads',
        'Downloads',
        entries,
        now,
        (b) =>
          table(
            'Download observations; unidentified rows are never merged',
            ['Alias', 'State', 'Progress', 'Last progress event age', 'Stalled'],
            b.data.items
              .filter(record)
              .map((d) => [
                d.source === 'unlisted' ? 'Unidentified download (D12)' : valueText(d.source),
                valueText(d.state),
                number(d.total) && d.total > 0
                  ? `${valueText(d.done)} / ${d.total} (${valueText(d.pct)}%)`
                  : `${valueText(d.done)} / unknown total`,
                ageText(elapsedSeconds(d.last_progress_at, now)),
                valueText(d.stalled),
              ]),
          ),
        gap(
          'D11-DL / D12',
          'existing download custodian, DevOps/operator and codex-monitor',
          'Producer binding and approved recognizable public aliases are required.',
        ),
      ) +
      readPanel(
        'stats',
        'Statistics and PR throughput',
        entries,
        now,
        (b) => {
          const stats = table(
            'Returned monitoring statistics',
            ['Metric', 'Value', 'Status'],
            b.data.stats
              .filter(record)
              .map((s) => [
                valueText(s.name),
                s.status === 'ok' ? valueText(s.value) : 'unknown',
                valueText(s.status),
              ]),
          );
          const eventOK = sourceStatus(b.sources, 'stale_prs') === 'ok';
          return (
            stats +
            (eventOK
              ? table(
                  'PR event history; not per-PR merge proof',
                  ['Repository', 'Backlog', 'Daily opened / merged'],
                  b.data.by_repo
                    .filter(record)
                    .map((r) => [
                      valueText(r.repo),
                      valueText(r.backlog),
                      (Array.isArray(r.days) ? r.days.filter(record) : [])
                        .map(
                          (d) =>
                            `${valueText(d.date)}: ${valueText(d.opened)} / ${valueText(d.merged)}`,
                        )
                        .join('<br>'),
                    ]),
                )
              : '<p>PR throughput unknown: event source unavailable. Default zero aggregates are not measurements.</p>')
          );
        },
        gap(
          'D11-ST/SP',
          'existing statistics custodian and codex-monitor',
          'Missing global statistics and PR event history remain required.',
        ),
      ) +
      readPanel(
        'links',
        'Monitoring destinations',
        entries,
        now,
        (b) =>
          table(
            'Approved monitoring names',
            ['Name', 'Destination'],
            b.data.links
              .filter(record)
              .map((l) => [
                valueText(l.name),
                'Destination unavailable: boundary approval unknown (D13)',
              ]),
          ),
        gap(
          'D11-LI / D13 / RETAIN-02',
          'DevOps/operator and codex-monitor',
          'Named destinations need existing-boundary approval; link construction does not prove destination health.',
        ),
      )
    );
  }

  function renderOperator(entries, route, now) {
    const p = (k, t, render, extra) => readPanel(k, t, entries, now, render, extra);
    const workers = () =>
      `<h2>Workers</h2>${p('workers', 'Worker observations', (b, e) => workersRows(b, e, now))}${p(
        'tasks',
        'Task results',
        (b) =>
          `<p>${b.tasks.length} loaded tasks of ${valueText(b.total)} returned total. Statuses remain distinct.</p>` +
          table(
            'Delegate task observations',
            ['Task', 'Status', 'Detail'],
            b.tasks.map((t) => [
              esc(t.task_id),
              esc(t.status),
              `<a data-focus-key="task:${esc(t.task_id)}" href="/delegate.html">Select task in Delegate</a>`,
            ]),
          ),
      )}`;
    const capacity = () =>
      `<h2>Host and test capacity</h2>${p('hosts', 'Host load', (b, e) => hostRows(b, e, now))}${p('slots', 'Governed test slots', slotsRows)}<h2>Account capacity</h2>${p('accounts', 'Account windows', (b, e) => accountRows(b, e, now), gap('D02', 'codex-monitor; external tool custodian and account bindings under operator authority', 'Muse, OpenAI/Sol, AGY Claude/GPT, Gemini and shared Grok/Cursor windows and coherent lu-capacity parity remain required.'))}<a href="/routing.html">Routing details</a>`;
    const pipeline = () =>
      `<h2>PR pipeline</h2>${p('work', 'Public PR observations', () => pipelineRows(entries, now, route.params))}${p('prs', 'Optional current-head pipeline', () => (entries.work?.body ? '<p>Matched by repository and PR identity in the table above. Field qualifications stay separate.</p>' : pipelineRows(entries, now, route.params)))}`;
    if (route.view === 'prs') return pipeline();
    if (route.view === 'workers') return workers();
    if (route.view === 'capacity') return capacity();
    if (route.view === 'attention') return attentionPanels(entries, now);
    if (route.view === 'ops') return opsPanels(entries, now);
    return (
      attentionPanels(entries, now) +
      `<h2>Lanes and drivers</h2>${p('registry', 'Session-store streams', (b) => registryRows(b, entries, now), gap('D03 / D11-RO/HA', 'codex-monitor and existing registry/roster custodians', 'Lease activity is not current work. Registry has no model field or universal current-activity classifier.'))}` +
      workers() +
      capacity() +
      pipeline() +
      opsPanels(entries, now)
    );
  }
  function parseRoute(hash) {
    const fragment = hash || "#/home";
    const raw = fragment.charAt(0) === "#" ? fragment.slice(1) : fragment;
    const splitAt = raw.indexOf("?");
    const path = splitAt === -1 ? raw : raw.slice(0, splitAt);
    const query = splitAt === -1 ? "" : raw.slice(splitAt + 1);
    const parts = path.split("/").filter(Boolean);
    let epicId = "";
    if (parts[0] === "epic" && parts[1]) {
      try {
        epicId = decodeURIComponent(parts[1]);
      } catch (error) {
        epicId = parts[1];
      }
    }
    return {
      view: parts[0] || "home",
      parts,
      params: new URLSearchParams(query),
      epicId,
    };
  }

  function withParams(hash, updates) {
    const route = parseRoute(hash || "#/home");
    const params = new URLSearchParams(route.params);
    Object.keys(updates).forEach((key) => {
      const value = updates[key];
      if (value) params.set(key, value);
      else params.delete(key);
    });
    const path = route.parts.length ? route.parts.join("/") : "home";
    const query = params.toString();
    return "#/" + path + (query ? "?" + query : "");
  }

  function stateClass(state) {
    return STATES.indexOf(state) === -1 ? "off" : state;
  }

  function statePill(state) {
    const known = STATES.indexOf(state) !== -1;
    return `<span class="fb-state is-${stateClass(state)}">${esc(known ? state : "unknown")}</span>`;
  }

  function sinceLabel(value) {
    if (!value) return "unknown";
    const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}):\d{2}Z$/.exec(String(value));
    if (!match) return String(value);
    return match[2] + " UTC";
  }

  function taskText(task) {
    if (!task || (task.kind !== "pr" && task.kind !== "issue")) return "current task unknown";
    const label = task.kind === "pr" ? "PR" : "Issue";
    const number = Number.isInteger(task.number) ? " #" + task.number : "";
    const title = task.title ? " · " + task.title : "";
    return label + number + title;
  }

  function subtitle(epic) {
    const parts = [epic.epic || "no epic id"];
    if (epic.focus) parts.push(epic.focus);
    if (epic.parent) parts.push("parent " + epic.parent);
    parts.push(epic.layer == null ? "layer unknown" : "layer " + epic.layer);
    parts.push("intended " + (epic.intended || "unknown"));
    return parts.join(" · ");
  }

  function haystack(epic) {
    const driver = epic.driver || {};
    const task = epic.task || {};
    const workers = Array.isArray(epic.workers) ? epic.workers : [];
    const parts = [
      epic.epic, epic.title, epic.focus, epic.parent, epic.state, epic.state_reason,
      driver.cli, driver.model, driver.harness, driver.agent_id,
      task.kind, task.number, task.title,
    ];
    workers.forEach((worker) => {
      if (!worker) return;
      parts.push(worker.agent_id, worker.cli, worker.model, worker.state);
      if (typeof worker.task === "string") {
        parts.push(worker.task);
      } else if (worker.task && typeof worker.task === "object" && !Array.isArray(worker.task)) {
        parts.push(worker.task.kind, worker.task.number, worker.task.title);
      }
    });
    return parts.filter((part) => (typeof part === "string" && part !== "") ||
      (typeof part === "number" && Number.isFinite(part))).join(" ").toLowerCase();
  }

  function titleOf(epic) {
    return String((epic && (epic.title || epic.epic)) || "");
  }

  function compareEpics(a, b, sort) {
    if (sort === "name") return titleOf(a).localeCompare(titleOf(b));
    if (sort === "layer") {
      const layer = (a.layer ?? 99) - (b.layer ?? 99);
      return layer || titleOf(a).localeCompare(titleOf(b));
    }
    const rank = (STATE_ORDER[a.state] ?? 9) - (STATE_ORDER[b.state] ?? 9);
    return rank || titleOf(a).localeCompare(titleOf(b));
  }

  function filterEpics(epics, params) {
    const query = params instanceof URLSearchParams ? params : new URLSearchParams(params || "");
    const layer = query.get("layer") || "";
    const state = query.get("state") || "";
    const harness = query.get("harness") || "";
    const q = (query.get("q") || "").trim().toLowerCase();
    const sort = query.get("sort") || "attention";
    const rows = (Array.isArray(epics) ? epics : []).filter((epic) => {
      if (!epic) return false;
      if (layer && String(epic.layer ?? "") !== layer) return false;
      if (state && epic.state !== state) return false;
      const epicHarness = (epic.driver && epic.driver.harness) || "";
      if (harness && epicHarness !== harness) return false;
      if (q && haystack(epic).indexOf(q) === -1) return false;
      return true;
    });
    return rows.slice().sort((a, b) => compareEpics(a, b, sort));
  }

  function metricText(value, suffix) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "?";
    const shown = Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
    return suffix ? shown + suffix : shown;
  }

  function contextClass(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    if (value >= 85) return "is-bad";
    if (value >= 70) return "is-warn";
    return "";
  }

  function idleClass(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    return value >= 30 ? "is-bad" : "";
  }

  function stopsClass(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    return value > 0 ? "is-warn" : "";
  }

  function healthOf(epic) {
    const health = epic && epic.health;
    if (!health || typeof health !== "object") return null;
    return health;
  }

  function tile(metric, label, value, cls) {
    const extra = cls ? " " + cls : "";
    return `<div class="fb-tile${extra}" data-metric="${metric}"><span>${label}</span><b>${esc(value)}</b></div>`;
  }

  function harnessTiles(health) {
    const row = health || {};
    const current = row.status === "ok";
    function value(key, suffix) {
      if (row.status === "stale") return "stale";
      if (!current || typeof row[key] !== "number" || !Number.isFinite(row[key])) return "unknown";
      return metricText(row[key], suffix);
    }
    return `<div class="fb-tiles">
      ${tile("context", "context", value("context_pct", "%"), current ? contextClass(row.context_pct) : "")}
      ${tile("compactions", "compactions", value("compactions", ""), "")}
      ${tile("stops", "stops", value("stop_count", ""), current ? stopsClass(row.stop_count) : "")}
      ${tile("asks", "asks", value("ask_count", ""), current ? stopsClass(row.ask_count) : "")}
      ${tile("idle", "idle", value("idle_min", " m"), current ? idleClass(row.idle_min) : "")}
    </div>`;
  }

  function workerSummary(workers) {
    if (!Array.isArray(workers) || workers.length === 0) return "worker coverage unknown";
    const bits = workers.map((worker) => {
      const model = (worker && worker.model) || "unknown model";
      const state = worker && STATES.indexOf(worker.state) !== -1 ? worker.state : "unknown";
      return model + " (" + state + ")";
    });
    const noun = workers.length === 1 ? "worker" : "workers";
    return workers.length + " " + noun + ": " + bits.join(", ");
  }

  function attentionHref(item) {
    const target = item && item.target;
    if (!target || typeof target.id !== "string" || !target.id) return "#/home";
    if (target.type === "epic") return identifierHref("#/epic/", target.id);
    if (target.type === "pr") return identifierHref("#/prs?pr=", target.id);
    return "#/home";
  }

  function kindLabel(kind) {
    return KIND_LABEL[kind] || "Needs attention";
  }

  function attentionItem(item) {
    const severity = item && item.severity === "bad" ? "bad" : "warn";
    const title = item && item.title ? item.title : "Needs attention";
    const summary = item && item.summary ? item.summary : "";
    const href = attentionHref(item);
    return `<a class="fb-attn-item ${severity}"${href === null ? '' : ` href="${esc(href)}"`}>
      <div class="fb-k">${esc(kindLabel(item && item.kind))}</div>
      <div class="fb-t">${esc(title)}</div>
      <div class="fb-s">${esc(summary)}</div>
    </a>`;
  }

  function cardHtml(epic) {
    const state = stateClass(epic.state);
    const id = String(epic.epic || "");
    const href = identifierHref("#/epic/", id);
    const driver = epic.driver;
    const driverLine = driver
      ? `<p class="fb-sub">driver: <b>${esc(driver.cli || "unknown cli")}</b> · ${esc(driver.model || "unknown model")}</p>`
      : `<p class="fb-sub">driver unknown</p>`;
    return `<a class="fb-card is-${state}" data-focus-key="board:${esc(id)}"${href === null ? '' : ` href="${esc(href)}"`}>
      <div class="fb-card-top"><div><h3>${esc(epic.title || id || "Untitled")}</h3>
        <p class="fb-sub">${esc(subtitle(epic))}</p></div>${statePill(epic.state)}</div>
      <p class="fb-reason">${esc(epic.state_reason || "unknown reason")} <span class="fb-sub">since ${esc(sinceLabel(epic.since))}</span></p>
      ${driverLine}
      <div class="fb-task">${esc(taskText(epic.task))}</div>
      ${harnessTiles(healthOf(epic))}
      <p class="fb-workers">${esc(workerSummary(epic.workers))}</p>
    </a>`;
  }

  function selectOptions(values, current, allLabel) {
    const items = values.slice();
    if (current && items.indexOf(current) === -1) items.push(current);
    let html = `<option value="">${esc(allLabel)}</option>`;
    items.forEach((value) => {
      const selected = value === current ? " selected" : "";
      html += `<option value="${esc(value)}"${selected}>${esc(value)}</option>`;
    });
    return html;
  }

  function sortOptions(current) {
    const items = [["attention", "Sort: attention"], ["layer", "Sort: layer"], ["name", "Sort: name"]];
    return items.map(([value, label]) => {
      const selected = value === current ? " selected" : "";
      return `<option value="${value}"${selected}>${label}</option>`;
    }).join("");
  }

  function toolbar(epics, query) {
    const layers = [];
    const harnesses = [];
    epics.forEach((epic) => {
      if (epic.layer != null && layers.indexOf(String(epic.layer)) === -1) layers.push(String(epic.layer));
      const harness = epic.driver && epic.driver.harness;
      if (harness && harnesses.indexOf(harness) === -1) harnesses.push(harness);
    });
    layers.sort((a, b) => Number(a) - Number(b));
    harnesses.sort();
    const q = query.get("q") || "";
    return `<div class="fb-toolbar">
      <input id="fb-search" type="search" aria-label="Search epic, model, task, or PR" placeholder="Search epic, model, task, PR" value="${esc(q)}">
      <select data-filter="layer" aria-label="Layer">${selectOptions(layers, query.get("layer") || "", "All layers")}</select>
      <select data-filter="state" aria-label="State">${selectOptions(STATES, query.get("state") || "", "All states")}</select>
      <select data-filter="harness" aria-label="Harness">${selectOptions(harnesses, query.get("harness") || "", "All harnesses")}</select>
      <select data-filter="sort" aria-label="Sort">${sortOptions(query.get("sort") || "attention")}</select>
    </div>`;
  }

  function sourceStatus(sources, name) {
    let status = "";
    let best = -1;
    (sources || []).forEach((row) => {
      if (!row || row.name !== name) return;
      const score = STATUS_RANK[row.status];
      if (score == null || score <= best) return;
      best = score;
      status = row.status;
    });
    return status;
  }

  function sourceLabel(status) {
    if (status === "not_configured") return "not installed";
    if (status === "unavailable") return "unavailable";
    if (status === "stale") return "stale";
    if (status === "ok") return "ok";
    return "unknown";
  }

  function harnessCaption(sources) {
    if (sourceLabel(sourceStatus(sources, "harness_snapshot")) !== "not installed") return "";
    return `<p class="fb-src">Harness health: not installed</p>`;
  }

  function sourcesOf(envelope) {
    const rows = envelope && envelope.sources;
    return Array.isArray(rows) ? rows.filter(record) : [];
  }

  function mergeSources() {
    const out = [];
    for (let i = 0; i < arguments.length; i += 1) {
      sourcesOf(arguments[i]).forEach((row) => out.push(row));
    }
    return out;
  }

  function notableSources(sources) {
    const byName = Object.create(null);
    (sources || []).forEach((row) => {
      if (!row || !row.name) return;
      const prev = byName[row.name];
      if (!prev || (STATUS_RANK[row.status] || 0) > (STATUS_RANK[prev.status] || 0)) byName[row.name] = row;
    });
    return Object.keys(byName).map((name) => byName[name]).filter((row) => row.status && row.status !== "ok");
  }

  function sourceList(sources) {
    const rows = notableSources(sources);
    if (!rows.length) return "";
    const items = rows.map((row) => {
      const name = String(row.name).replace(/_/g, " ");
      return `<li><span>${esc(name)}</span> <b>${esc(sourceLabel(row.status))}</b></li>`;
    });
    return `<ul class="fb-source-list">${items.join("")}</ul>`;
  }

  function staleState(sources, ageMs, refreshFailed) {
    const sourceStale = (sources || []).some((row) => row && row.status === "stale");
    const ageStale = typeof ageMs === "number" && ageMs > STALE_MS;
    const failed = !!refreshFailed;
    return { sourceStale, ageStale, refreshFailed: failed, stale: sourceStale || ageStale || failed };
  }

  function staleMessage(state) {
    const parts = [];
    if (state.ageStale) parts.push("The last successful refresh was over 2 minutes ago.");
    if (state.sourceStale) parts.push("A source is stale.");
    if (state.refreshFailed) parts.push("The last refresh failed; values below are from an earlier refresh.");
    if (!parts.length) return "";
    return parts.join(" ") + " Values below may be out of date.";
  }

  function staleBanner(state) {
    const hidden = state.stale ? "" : " hidden";
    return `<p id="fb-stale" class="fb-stale" role="status"${hidden}>${esc(staleMessage(state))}</p>`;
  }

  function homeModel(nowEnvelope, epicsEnvelope) {
    const nowData = (nowEnvelope && nowEnvelope.data) || {};
    const epicData = (epicsEnvelope && epicsEnvelope.data) || {};
    const fromEpics = Array.isArray(epicData.epics) ? epicData.epics : null;
    const fromNow = Array.isArray(nowData.epics) ? nowData.epics : [];
    return {
      attention: Array.isArray(nowData.attention) ? nowData.attention : [],
      epics: fromEpics || fromNow,
      sources: mergeSources(nowEnvelope, epicsEnvelope),
    };
  }

  function ageOption(options) {
    if (!options || !Object.prototype.hasOwnProperty.call(options, "ageMs")) return null;
    return options.ageMs;
  }

  function optionFlag(options, key) {
    return !!(options && options[key]);
  }

  function renderHome(model, params, options) {
    const query = params instanceof URLSearchParams ? params : new URLSearchParams(params || "");
    const epics = Array.isArray(model.epics) ? model.epics : [];
    const attention = Array.isArray(model.attention) ? model.attention : [];
    const sources = model.sources || [];
    return `${staleBanner(staleState(sources, ageOption(options), optionFlag(options, "failed")))}
      <section><h2>Derived Fleet attention</h2><div class="fb-attn">${attention.map(attentionItem).join("") || '<p>No derived attention rows returned; coverage unknown.</p>'}</div></section>
      <section><h2>Optional Fleet board observations</h2>${toolbar(epics, query)}${harnessCaption(sources)}<div class="fb-grid">${filterEpics(epics, query).map(cardHtml).join("") || '<p>No epics match these filters; source coverage unknown.</p>'}</div></section>${sourceList(sources)}`;
  }

  function liveness(driver) {
    if (!driver || driver.pid_alive == null) return "liveness unknown";
    return driver.pid_alive ? "process alive" : "process is not alive";
  }

  function driverBlock(epic, sources) {
    const driver = epic.driver;
    const source = `<p class="fb-src">source: /api/fleet/v1/epics/${esc(epic.epic || "")} · /api/fleet/v1/agents</p>`;
    if (!driver) {
      return `<section class="fb-panel"><h3>Driver</h3><p class="fb-sub">Driver unknown.</p>
        <h3 class="fb-subhead">Harness health</h3>${harnessTiles(null)}${harnessCaption(sources)}${source}</section>`;
    }
    return `<section class="fb-panel"><h3>Driver</h3>
      <dl class="fb-kv">
        <dt>CLI / harness</dt><dd>${esc(driver.cli || "unknown")} / ${esc(driver.harness || "unknown")}</dd>
        <dt>Model</dt><dd>${esc(driver.model || "unknown")}</dd>
        <dt>Liveness</dt><dd>${esc(liveness(driver))}</dd>
        <dt>Current task</dt><dd>${esc(taskText(epic.task))}</dd>
      </dl>
      <h3 class="fb-subhead">Harness health</h3>
      ${harnessTiles(healthOf(epic))}
      ${harnessCaption(sources)}
      ${source}
    </section>`;
  }

  function workersTable(workers) {
    const rows = Array.isArray(workers) ? workers : [];
    if (!rows.length) {
      return `<section class="fb-panel"><h3>Workers</h3><p class="fb-sub">No worker rows returned; coverage unknown.</p>
        <p class="fb-src">source: /api/fleet/v1/agents</p></section>`;
    }
    const body = rows.map((worker) => `<tr>
      <td data-l="Agent"><button type="button" class="fb-link" data-agent="${esc(worker.agent_id || "")}">${esc(worker.agent_id || "unknown")}</button></td>
      <td data-l="Model">${esc(worker.model || "unknown")}</td>
      <td data-l="Task">${esc(worker.task || "none")}</td>
      <td data-l="State">${statePill(worker.state)}</td>
      <td data-l="Since">${esc(sinceLabel(worker.since || worker.last_seen))}</td>
    </tr>`).join("");
    return `<section class="fb-panel"><h3>Workers <span class="fb-sub">${rows.length}</span></h3>
      <table class="fb-table"><thead><tr><th>Agent</th><th>Model</th><th>Task</th><th>State</th><th>Since</th></tr></thead>
      <tbody>${body}</tbody></table>
      <p class="fb-src">source: /api/fleet/v1/agents</p></section>`;
  }

  function phaseActions() {
    return `<div class="fb-actions"><span class="fb-ph2">Phase 2</span>
      <button type="button" class="fb-btn" disabled>Pause epic</button>
      <button type="button" class="fb-btn" disabled>Nudge driver</button>
      <button type="button" class="fb-btn" disabled>Restart driver</button>
    </div>`;
  }

  function epicHeader(epic) {
    return `<p class="fb-crumbs"><a href="#/home">Home</a> <span aria-hidden="true">›</span> epic</p>
      <div class="fb-title"><h2>${esc(epic.title || epic.epic || "Epic")}</h2>${statePill(epic.state)}
        <p class="fb-sub">${esc(subtitle(epic))}</p></div>
      <p class="fb-reason">${esc(epic.state_reason || "unknown reason")} <span class="fb-sub">since ${esc(sinceLabel(epic.since))}</span></p>
      ${phaseActions()}`;
  }

  function agentsCurrent(epicEnvelope, agentsEnvelope, options) {
    if (optionFlag(options, "agentsFailed")) return false;
    const agentsAt = Date.parse(agentsEnvelope && agentsEnvelope.generated_at);
    if (Number.isNaN(agentsAt)) return false;
    const epicAt = Date.parse(epicEnvelope && epicEnvelope.generated_at);
    if (Number.isNaN(epicAt)) return true;
    return agentsAt >= epicAt;
  }

  function renderEpic(epicEnvelope, agentsEnvelope, options) {
    const sources = mergeSources(epicEnvelope, agentsEnvelope);
    const banner = staleBanner(staleState(sources, ageOption(options), optionFlag(options, "failed")));
    const epic = epicEnvelope && epicEnvelope.data;
    if (!epic || typeof epic !== "object") {
      return `${banner}<p class="fb-empty">This epic is not on the board.</p>${sourceList(sources)}`;
    }
    const agentsData = agentsEnvelope && agentsEnvelope.data;
    const agents = agentsData && Array.isArray(agentsData.agents) && agentsCurrent(epicEnvelope, agentsEnvelope, options)
      ? agentsData.agents
      : null;
    const workers = agents
      ? agents.filter((agent) => agent && agent.epic === epic.epic && agent.role === "worker")
      : (Array.isArray(epic.workers) ? epic.workers : []);
    const prs = '<section class="fb-panel"><h3>PR observations</h3><p>Canonical PR membership unknown (D04). <a href="#/prs">Open PR pipeline</a></p></section>';
    const deps = '<section class="fb-panel"><h3>Registry and dependencies</h3><p>Board snapshot does not establish registry coverage. <a href="/epics.html">Registry detail</a> · <a href="/epics-map.html">Epics Map</a></p></section>';
    return `${banner}
      ${epicHeader(epic)}
      <div class="fb-cols"><div>${driverBlock(epic, sources)}${workersTable(workers)}${prs}</div><div>${deps}</div></div>
      ${sourceList(sources)}`;
  }

  function renderPrs(params, entries, options) {
    return renderOperator(entries || {}, { view: 'prs', params: params instanceof URLSearchParams ? params : new URLSearchParams(params || '') }, options?.now || Date.now());
  }

  function renderAgent(agent) {
    const close = `<button type="button" class="fb-btn" data-action="close">Close</button>`;
    if (!agent) return `${close}<p class="fb-empty">This agent is not on the board.</p>`;
    const epic = agent.epic
      ? identifierLink('#/epic/', agent.epic, agent.epic)
      : "none";
    return `${close}
      <p class="fb-crumbs">Agent</p>
      <h2>${esc(agent.agent_id || "Agent")}</h2>
      <dl class="fb-kv">
        <dt>Role</dt><dd>${esc(agent.role || "unknown")}</dd>
        <dt>Epic</dt><dd>${epic}</dd>
        <dt>CLI</dt><dd>${esc(agent.cli || "unknown")}</dd>
        <dt>Model</dt><dd>${esc(agent.model || "unknown")}</dd>
        <dt>Task</dt><dd>${esc(typeof agent.task === "string" ? agent.task : taskText(agent.task))}</dd>
        <dt>State</dt><dd>${statePill(agent.state)}</dd>
        <dt>Reason</dt><dd>${esc(agent.state_reason || "unknown")}</dd>
        <dt>Last seen</dt><dd>${esc(sinceLabel(agent.last_seen || agent.since))}</dd>
      </dl>
      <div class="fb-actions"><span class="fb-ph2">Phase 2</span>
        <button type="button" class="fb-btn" disabled>Cancel task</button></div>
      <p class="fb-src">source: /api/fleet/v1/agents</p>`;
  }

  function agoLabel(ms) {
    const seconds = Math.max(0, Math.floor(ms / 1000));
    if (seconds < 60) return seconds + " s ago";
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return minutes + " min " + rest + " s ago";
  }

  function updatedLabel(age) {
    if (age == null) return "waiting";
    return agoLabel(age);
  }

  function routeSlots(route) {
    return route && route.view === "epic" ? ["epic", "agents"] : ["now", "epics"];
  }

  function routeFailed(failures, route) {
    return routeSlots(route).some((slot) => !!(failures && failures[slot]));
  }

  function routeKey(route) {
    const view = route && route.view ? route.view : "home";
    if (view === "epic") return "epic:" + (route.epicId || "");
    return view;
  }

  function responseCurrent(ticket, generation, route) {
    return !!ticket && ticket.generation === generation && ticket.key === routeKey(route);
  }

  function rosterUnavailable(body) {
    return sourcesOf(body).some((row) => row && row.name === "roster_snapshot" && row.status === "unavailable");
  }

  function payloadUsable(slot, body) {
    const data = body && body.data;
    if (!data || typeof data !== "object") return false;
    if (slot === "now") {
      const attention = Array.isArray(data.attention) ? data.attention.length : 0;
      const epics = Array.isArray(data.epics) ? data.epics.length : 0;
      return attention + epics > 0;
    }
    if (slot === "epics") return Array.isArray(data.epics) && data.epics.length > 0;
    if (slot === "epic") return typeof data.epic === "string" && data.epic.length > 0;
    if (slot === "agents") return Array.isArray(data.agents) && data.agents.length > 0;
    return false;
  }

  function adoptPayload(slot, previous, incoming) {
    if (!incoming) return { body: previous || null, fresh: false };
    if (rosterUnavailable(incoming) && !payloadUsable(slot, incoming) && payloadUsable(slot, previous)) {
      const sources = sourcesOf(incoming);
      return {
        body: {
          schema: previous.schema,
          generated_at: previous.generated_at,
          sources: sources.length ? sources : sourcesOf(previous),
          data: previous.data,
        },
        fresh: false,
      };
    }
    return { body: incoming, fresh: true };
  }

  function displayedAge(stamps, route, now) {
    const keys = route && route.view === "epic" ? ["epic", "agents"] : ["now", "epics"];
    let oldest = null;
    keys.forEach((key) => {
      const at = stamps && stamps[key];
      if (typeof at !== "number" || at <= 0) return;
      const age = now - at;
      if (oldest == null || age > oldest) oldest = age;
    });
    return oldest;
  }

  function commitBoard(state, ticket, incoming, now) {
    if (!responseCurrent(ticket, state.generation, state.route)) return state;
    const nextSnapshot = Object.assign({}, state.snapshot);
    const freshAt = Object.assign({}, state.freshAt);
    const failures = Object.assign({}, state.failures);
    routeSlots(state.route).forEach((slot) => {
      const prior = slot === "epic" && nextSnapshot.epicId !== state.route.epicId ? null : nextSnapshot[slot];
      const body = incoming ? incoming[slot] : null;
      const adopted = adoptPayload(slot, prior, body);
      nextSnapshot[slot] = adopted.body;
      failures[slot] = !body;
      if (adopted.fresh) freshAt[slot] = now;
    });
    if (state.route && state.route.view === "epic") nextSnapshot.epicId = state.route.epicId;
    return { generation: state.generation, route: state.route, snapshot: nextSnapshot, freshAt, failures };
  }

  const api = {
    preserveFocusedRow, READS, validRead, readResult, elapsedSeconds, advancedAge, workerBuckets, renderOperator,
    REFRESH_MS,
    STALE_MS,
    esc,
    isFleetPath,
    parseRoute,
    withParams,
    filterEpics,
    metricText,
    harnessTiles,
    stateClass,
    statePill,
    attentionHref,
    sourceLabel,
    staleState,
    staleMessage,
    homeModel,
    routeKey,
    responseCurrent,
    routeSlots,
    routeFailed,
    adoptPayload,
    displayedAge,
    commitBoard,
    renderHome,
    renderEpic,
    renderPrs,
    renderAgent,
    cardHtml,
  };
  root.FleetBoard = api;

  if (typeof document === "undefined" || !document.getElementById) return;

  const reads = {};
  const readGeneration = {};
  let pendingRefresh = false;
  let refreshRunning = false;
  let returnFocus = null;

  const snapshot = { now: null, epics: null, epic: null, epicId: "", agents: null };
  const freshAt = { now: 0, epics: 0, epic: 0, agents: 0 };
  const failures = { now: false, epics: false, epic: false, agents: false };
  let refreshGen = 0;
  let appliedKey = "";
  let openAgentId = null;
  let searchTimer = 0;
  let searchVersion = 0;
  let paintQueued = false;
  let failed = false;
  let chord = false;

  function ageMs() {
    return displayedAge(freshAt, parseRoute(location.hash || "#/home"), Date.now());
  }

  function viewSources(route) {
    if (route.view === "epic") return mergeSources(snapshot.epic, snapshot.agents);
    return mergeSources(snapshot.now, snapshot.epics);
  }

  function findAgent(id) {
    const agents = snapshot.agents && snapshot.agents.data && snapshot.agents.data.agents;
    if (Array.isArray(agents)) {
      const found = agents.find((agent) => agent && agent.agent_id === id);
      if (found) return found;
    }
    const epics = [];
    const listed = snapshot.epics && snapshot.epics.data && snapshot.epics.data.epics;
    const nowEpics = snapshot.now && snapshot.now.data && snapshot.now.data.epics;
    if (Array.isArray(listed)) listed.forEach((epic) => epics.push(epic));
    else if (Array.isArray(nowEpics)) nowEpics.forEach((epic) => epics.push(epic));
    if (snapshot.epic && snapshot.epic.data) epics.push(snapshot.epic.data);
    for (let i = 0; i < epics.length; i += 1) {
      const epic = epics[i];
      if (!epic) continue;
      if (epic.driver && epic.driver.agent_id === id) {
        return {
          agent_id: id,
          role: "driver",
          epic: epic.epic,
          cli: epic.driver.cli,
          model: epic.driver.model,
          task: taskText(epic.task),
          state: epic.state,
          state_reason: epic.state_reason,
          last_seen: epic.since,
        };
      }
      const workers = Array.isArray(epic.workers) ? epic.workers : [];
      for (let j = 0; j < workers.length; j += 1) {
        if (workers[j] && workers[j].agent_id === id) {
          return Object.assign({ role: "worker", epic: epic.epic }, workers[j]);
        }
      }
    }
    return null;
  }

  function fillDrawer(id) {
    const drawer = document.getElementById("fb-drawer");
    if (!drawer) return;
    drawer.hidden = false;
    document.getElementById("fb-app").inert = true;
    const top = document.querySelector("header");
    if (top) top.inert = true;
    drawer.classList.add("is-open");
    drawer.innerHTML = renderAgent(findAgent(id));
  }

  function closeDrawer() {
    openAgentId = null;
    const drawer = document.getElementById("fb-drawer");
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.hidden = true;
    document.getElementById("fb-app").inert = false;
    const top = document.querySelector("header");
    if (top) top.inert = false;
    drawer.innerHTML = "";
    if (returnFocus?.isConnected !== false && returnFocus?.focus) returnFocus.focus();
    else if (returnFocus?.getAttribute && document.querySelectorAll) {
      const id = returnFocus.getAttribute('data-agent');
      const replacement = Array.from(document.querySelectorAll('[data-agent]')).find(el => el.getAttribute('data-agent') === id);
      if (replacement) replacement.focus();
    }
  }

  function openAgent(id) {
    if (!id) return;
    returnFocus = document.activeElement;
    openAgentId = id;
    fillDrawer(id);
    const close = document.querySelector("#fb-drawer [data-action='close']");
    if (close) close.focus();
  }

  function markNav(view) {
    document.querySelectorAll(".fb-views a").forEach((link) => {
      const on = link.getAttribute("data-nav") === view;
      link.classList.toggle("is-on", on);
      if (on) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  function syncStamp(route) {
    const age = ageMs();
    const state = staleState(viewSources(route), age, routeFailed(failures, route));
    const ago = document.getElementById("fb-ago");
    const label = document.getElementById("fb-stamp-label");
    const stamp = document.getElementById("fb-stamp");
    if (ago) ago.textContent = updatedLabel(age);
    if (label) label.hidden = age == null;
    if (stamp) stamp.classList.toggle("is-stale", state.stale);
    const banner = document.getElementById("fb-stale");
    if (banner) {
      banner.hidden = !state.stale;
      banner.textContent = staleMessage(state);
    }
  }

  function preserveFocusedRow(element, index) {
    if (index < 0 || !element?.closest) return;
    const row = element.closest('.fb-card, tr');
    const parent = row?.parentElement;
    if (!parent) return;
    const peers = Array.from(parent.children).filter(el => el !== row);
    parent.insertBefore(row, peers[Math.min(index, peers.length)] || null);
  }

  function paint() {
    try { paintView(); }
    catch (error) {
      const live = document.getElementById('fb-status');
      if (live) live.textContent = 'Display update failed. Retrying on next refresh.';
      console.error('Fleet Board display update failed', error);
    }
  }

  function paintView() {
    const app = document.getElementById("fb-app");
    if (!app) return;
    const route = parseRoute(location.hash || "#/home");
    const expandedSources = new Set(Array.from(app.querySelectorAll ? app.querySelectorAll('details[open] summary[data-focus-key]') : []).map(el => el.getAttribute('data-focus-key')));
    const focused = document.activeElement;
    const focusId = focused && focused.id;
    const focusKey = focused?.getAttribute && focused.getAttribute('data-focus-key');
    const focusedRow = focused?.closest?.('.fb-card, tr');
    const focusedIndex = focusedRow?.parentElement ? Array.from(focusedRow.parentElement.children).indexOf(focusedRow) : -1;
    const focusAgent = focused?.getAttribute && focused.getAttribute("data-agent");
    const focusRetry = focused?.getAttribute && focused.getAttribute("data-retry");
    const focusFilter = focused?.getAttribute && focused.getAttribute("data-filter");
    const focusHref = focused?.getAttribute && focused.getAttribute("href");
    const drafting = document.activeElement && document.activeElement.id === "fb-search";
    const draft = drafting ? document.activeElement.value : null;
    const selection = drafting ? document.activeElement.selectionStart : null;
    const selectionEnd = drafting ? document.activeElement.selectionEnd : null;
    const y = window.scrollY;
    const options = {
      ageMs: ageMs(),
      failed: routeFailed(failures, route),
      agentsFailed: !!failures.agents,
    };
    let html;
    if (route.view === "epic") {
      const data = snapshot.epic && snapshot.epic.data;
      const id = data && data.epic;
      const matches = snapshot.epicId === route.epicId && snapshot.epic && (id === route.epicId || data === null);
      const registered = reads.registry?.body?.streams.find(s => s.stream_id === route.epicId || s.stream_name === route.epicId);
      if (registered) {
        html = `<p class="fb-crumbs"><a href="#/home">Home</a> / stream</p><h2>${esc(registered.title || registered.stream_id)}</h2>` +
          readPanel('registry', 'Selected session-store stream', reads, Date.now(), () => registryRows({streams:[registered]}, reads, Date.now()));
        if (matches && data) html += renderEpic(snapshot.epic, snapshot.agents, options);
        else html += '<p>Optional board detail unavailable. Registry lease evidence is separate from current activity. <a href="#/prs">PR pipeline</a></p>';
      }
      else if (matches) html = renderEpic(snapshot.epic, snapshot.agents, options);
      else if (failed && snapshot.epicId === route.epicId) html = `<p class="fb-empty">The board could not be read.</p>`;
      else html = `<p class="fb-empty">Loading the board…</p>`;
    } else {
      reads.epics = { body: snapshot.epics, fetchedAt: freshAt.epics };
      html = renderOperator(reads, route, Date.now());
      if (route.view === "home") {
        const model = homeModel(snapshot.now, snapshot.epics);
        html += renderHome(model, route.params, options);
      }
    }
    const statusText = Object.entries(reads).filter(([key]) => READS[key]).map(([key,e]) => key + ': ' + (e.error || (e.pending ? 'loading' : 'observed'))).join('; ');
    const live = document.getElementById('fb-status');
    if (live && live.textContent !== statusText) live.textContent = statusText;
    app.innerHTML = html;
    if (app.querySelectorAll) app.querySelectorAll('details summary[data-focus-key]').forEach(summary => {
      if (expandedSources.has(summary.getAttribute('data-focus-key'))) summary.parentElement.open = true;
    });
    markNav(route.view);
    syncStamp(route);
    if (focusId || focusKey || focusAgent || focusRetry || focusFilter || focusHref) {
      // Match attributes directly; untrusted identities never enter a CSS selector.
      const candidates = Array.from(app.querySelectorAll ? app.querySelectorAll('a, button, input, select, summary') : []);
      const replacement = candidates.find(el => focusId ? el.id === focusId : focusKey ? el.getAttribute("data-focus-key") === focusKey : focusAgent ? el.getAttribute('data-agent') === focusAgent : focusRetry ? el.getAttribute('data-retry') === focusRetry : focusFilter ? el.getAttribute('data-filter') === focusFilter : el.getAttribute('href') === focusHref);
      if (replacement) { preserveFocusedRow(replacement, focusedIndex); replacement.focus(); }
    }
    if (draft != null) {
      const field = document.getElementById("fb-search");
      if (field) {
        field.value = draft;
        field.focus();
        const pos = selection == null ? draft.length : selection;
        if (field.setSelectionRange) field.setSelectionRange(pos, selectionEnd ?? pos);
      }
    }
    window.scrollTo(0, y);
    if (openAgentId && !(document.getElementById("fb-drawer")?.contains?.(document.activeElement))) fillDrawer(openAgentId);
  }

  async function fetchJson(path, detailed) {
    const result = (body, error) => detailed ? { body, error } : body;
    if (!isFleetPath(path) && !Object.values(READS).includes(path)) return result(null, 'Read path refused');
    try {
      const init = {
        headers: { Accept: "application/json" },
        cache: "no-store",
      };
      if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
        init.signal = AbortSignal.timeout(20000);
      }
      const response = await fetch(path, init);
      let body = null;
      try {
        body = await response.json();
      } catch (error) {
        return result(null, 'JSON parse failed');
      }
      if (!response.ok && !(response.status === 404 && path.startsWith("/api/fleet/v1/epics/"))) return result(null, 'HTTP ' + response.status);
      if (!record(body)) return result(null, 'Malformed success response');
      if (path.startsWith('/api/fleet/v1/') && !Object.values(READS).includes(path)) {
        const slot = path.includes('/epics/') ? 'epic' : path.endsWith('/agents') ? 'agents' : path.endsWith('/epics') ? 'epics' : 'now';
        if (!Array.isArray(body.sources) || !body.sources.every(record) || body.schema !== 'fleet.v1.' + slot) return result(null, 'Malformed success response');
        const epicRow = row => record(row) && text(row.epic) && (!('workers' in row) || Array.isArray(row.workers) && row.workers.every(record));
        if (slot === 'epic') { if (body.data !== null && !epicRow(body.data)) return result(null, 'Malformed success response'); }
        else {
          const data = body.data, rows = data?.[slot === 'now' ? 'attention' : slot];
          if (!record(data) || !Array.isArray(rows) || !rows.every(slot === 'epics' ? epicRow : record)) return result(null, 'Malformed success response');
          if (slot === 'now' && (!Array.isArray(data.epics) || !data.epics.every(epicRow))) return result(null, 'Malformed success response');
        }
      }
      return result(body, '');
    } catch (error) {
      return result(null, 'Request failed');
    }
  }

  function schedulePaint() {
    if (paintQueued) return;
    paintQueued = true;
    Promise.resolve().then(() => { paintQueued = false; paint(); });
  }

  async function refreshRead(key) {
    const gen = (readGeneration[key] || 0) + 1;
    readGeneration[key] = gen;
    reads[key] = Object.assign({}, reads[key], { pending: true });
    schedulePaint();
    const result = await fetchJson(READS[key], true);
    if (readGeneration[key] !== gen) return;
    reads[key] = readResult(key, result.body, result.error, reads[key], Date.now());
    schedulePaint();
  }

  async function refresh() {
    if (refreshRunning) { pendingRefresh = true; return; }
    refreshRunning = true;
    const extraReads = Promise.all(Object.keys(READS).map(refreshRead));
    const generation = ++refreshGen;
    const route = parseRoute(location.hash || "#/home");
    const ticket = { generation, key: routeKey(route) };
    const incoming = {};
    try {
      if (route.view === "epic" && route.epicId) {
        const epicPath = identifierHref("/api/fleet/v1/epics/", route.epicId);
        const [epicBody, agentsBody] = await Promise.all([
          epicPath === null ? Promise.resolve(null) : fetchJson(epicPath),
          fetchJson("/api/fleet/v1/agents"),
        ]);
        incoming.epic = epicBody;
        incoming.agents = agentsBody;
      } else {
        const [nowBody, epicsBody] = await Promise.all([
          fetchJson("/api/fleet/v1/now"),
          fetchJson("/api/fleet/v1/epics"),
        ]);
        incoming.now = nowBody;
        incoming.epics = epicsBody;
      }
    } finally {
      try {
        const current = parseRoute(location.hash || "#/home");
        if (responseCurrent(ticket, refreshGen, current)) {
          const committed = commitBoard(
            { generation: refreshGen, route: current, snapshot, freshAt, failures },
            ticket,
            incoming,
            Date.now(),
          );
          Object.keys(snapshot).forEach((key) => {
            snapshot[key] = committed.snapshot[key];
          });
          Object.keys(freshAt).forEach((key) => {
            freshAt[key] = committed.freshAt[key] || 0;
          });
          Object.keys(failures).forEach((key) => {
            failures[key] = !!committed.failures[key];
          });
          const slots = routeSlots(current);
          const anyBody = slots.some((slot) => incoming[slot]);
          const anyShown = slots.some((slot) => snapshot[slot]);
          failed = !anyBody && !anyShown;
          appliedKey = ticket.key;
          paint();
        }
        await extraReads;
      } finally {
        refreshRunning = false;
        if (pendingRefresh) { pendingRefresh = false; refresh(); }
      }
    }
  }

  function openHelp() {
    const help = document.getElementById("fb-help-modal");
    if (!help) return;
    returnFocus = document.activeElement;
    help.hidden = false;
    document.getElementById("fb-app").inert = true;
    const top = document.querySelector("header");
    if (top) top.inert = true;
    const close = document.getElementById("fb-help-close");
    if (close) close.focus();
  }

  function closeHelp() {
    const help = document.getElementById("fb-help-modal");
    if (help) help.hidden = true;
    document.getElementById("fb-app").inert = false;
    const top = document.querySelector("header");
    if (top) top.inert = false;
    if (returnFocus?.isConnected !== false && returnFocus?.focus) returnFocus.focus();
  }

  function setTheme(theme) {
    const next = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("fleet-board-theme", next);
    } catch (error) {
      /* the toggle still applies for this view */
    }
  }

  function focusSearch() {
    const route = parseRoute(location.hash || "#/home");
    if (route.view !== "home") {
      location.hash = "#/home";
      window.setTimeout(() => {
        const field = document.getElementById("fb-search");
        if (field) field.focus();
      }, 50);
      return;
    }
    const field = document.getElementById("fb-search");
    if (field) field.focus();
  }

  function moveCard(delta) {
    const cards = Array.prototype.slice.call(document.querySelectorAll(".fb-card"));
    if (!cards.length) return;
    const index = cards.indexOf(document.activeElement);
    const next = cards[Math.max(0, Math.min(cards.length - 1, (index === -1 ? (delta > 0 ? -1 : 0) : index) + delta))];
    if (next) next.focus();
  }

  function boot() {
    const app = document.getElementById("fb-app");
    if (!app || app.dataset.booted === "1") return;
    app.dataset.booted = "1";
    if (!location.hash) history.replaceState(null, "", "#/home");

    app.addEventListener("change", (event) => {
      const key = event.target.getAttribute && event.target.getAttribute("data-filter");
      if (!key) return;
      history.replaceState(null, "", withParams(location.hash || "#/home", { [key]: event.target.value }));
      paint();
    });
    app.addEventListener("input", (event) => {
      if (!event.target || event.target.id !== "fb-search") return;
      const value = event.target.value;
      const version = ++searchVersion;
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(() => {
        searchTimer = 0;
        if (version !== searchVersion) return;
        history.replaceState(null, "", withParams(location.hash || "#/home", { q: value.trim() ? value : "" }));
        paint();
      }, 250);
    });
    app.addEventListener("click", (event) => {
      const retry = event.target.closest && event.target.closest('[data-retry]');
      if (retry && READS[retry.getAttribute('data-retry')]) { refreshRead(retry.getAttribute('data-retry')); return; }
      const button = event.target.closest && event.target.closest("[data-agent]");
      if (!button) return;
      event.preventDefault();
      openAgent(button.getAttribute("data-agent"));
    });

    const drawer = document.getElementById("fb-drawer");
    if (drawer) {
      drawer.addEventListener("click", (event) => {
        if (event.target.closest && event.target.closest("[data-action='close']")) closeDrawer();
      });
    }
    const theme = document.getElementById("fb-theme");
    if (theme) {
      theme.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        setTheme(current === "dark" ? "light" : "dark");
      });
    }
    const help = document.getElementById("fb-help");
    if (help) help.addEventListener("click", openHelp);
    const helpClose = document.getElementById("fb-help-close");
    if (helpClose) helpClose.addEventListener("click", closeHelp);
    const modal = document.getElementById("fb-help-modal");
    if (modal) {
      modal.addEventListener("click", (event) => {
        if (event.target === modal) closeHelp();
      });
    }

    document.addEventListener("keydown", (event) => {
      const help = document.getElementById('fb-help-modal');
      const drawer = document.getElementById('fb-drawer');
      const dialog = help && !help.hidden ? help : drawer && !drawer.hidden ? drawer : null;
      if (dialog) {
        if (event.key === 'Escape') { event.preventDefault(); if (dialog === help) closeHelp(); else closeDrawer(); return; }
        if (event.key === 'Tab' && dialog.querySelectorAll) {
          const items = Array.from(dialog.querySelectorAll('a[href], button:not([disabled]), input, select, [tabindex="0"]'));
          const first = items[0], last = items[items.length - 1];
          if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
          else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        }
        return;
      }
      const tag = event.target && event.target.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") {
        if (event.key === "Escape") event.target.blur();
        return;
      }
      if (chord) {
        chord = false;
        if (event.key === "h") location.hash = "#/home";
        if (event.key === "p") location.hash = "#/prs";
        return;
      }
      if (event.key === "g") {
        chord = true;
        window.setTimeout(() => { chord = false; }, 800);
        return;
      }
      if (event.key === "/") {
        event.preventDefault();
        focusSearch();
      } else if (event.key === "t") {
        const current = document.documentElement.getAttribute("data-theme");
        setTheme(current === "dark" ? "light" : "dark");
      } else if (event.key === "?") {
        openHelp();
      } else if (event.key === "Escape") {
        closeHelp();
        closeDrawer();
      } else if (event.key === "r") {
        refresh();
      } else if (event.key === "j" || event.key === "k") {
        moveCard(event.key === "j" ? 1 : -1);
      }
    });

    window.addEventListener("hashchange", () => {
      searchVersion++;
      window.clearTimeout(searchTimer);
      searchTimer = 0;
      const route = parseRoute(location.hash || "#/home");
      paint();
      if (routeKey(route) !== appliedKey) refresh();
    });

    paint();
    refresh();
    window.setInterval(refresh, REFRESH_MS);
    window.setInterval(() => syncStamp(parseRoute(location.hash || "#/home")), 1000);
  }

  if (document.getElementById("fb-app")) boot();
  else document.addEventListener("DOMContentLoaded", boot);
})(typeof globalThis !== "undefined" ? globalThis : this);
