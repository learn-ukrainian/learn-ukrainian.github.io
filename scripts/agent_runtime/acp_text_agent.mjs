#!/usr/bin/env node

/**
 * Text-only ACP server for fleet CLIs that do not expose a suitably confined
 * native ACP endpoint.
 *
 * The server accepts exactly one text prompt per ACP session and returns one
 * text response. Provider CLIs run in a fresh temporary directory with no
 * repository files. AGY uses plan+sandbox mode without permission bypasses;
 * Hermes uses an isolated config with an explicit empty CLI toolset, no
 * fallbacks, no MCP, no plugins, and no injected project rules.
 */

import * as acp from '@agentclientprotocol/sdk';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, rm, symlink, writeFile } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import { Readable, Writable } from 'node:stream';

const MAX_PROMPT_BYTES = 512 * 1024;
const MAX_OUTPUT_BYTES = 2 * 1024 * 1024;
const CHILD_TIMEOUT_MS = 270_000;
const FORCE_KILL_GRACE_MS = 1_000;
const CHILD_ENV_KEYS = [
  'HOME',
  'LANG',
  'LC_ALL',
  'NODE_EXTRA_CA_CERTS',
  'PATH',
  'SSL_CERT_DIR',
  'SSL_CERT_FILE',
  'TMPDIR',
];
const CONFINEMENT_NOTICE = [
  'This is a bounded text-only advisory turn.',
  'Do not invoke tools, inspect files, browse, execute commands, or modify state.',
  'Answer only from the text in this prompt.',
].join(' ');

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith('--') || value == null) {
      throw new Error('usage: acp_text_agent.mjs --provider NAME --model MODEL --binary PATH');
    }
    values[flag.slice(2)] = value;
  }
  if (!['agy', 'deepseek'].includes(values.provider)) {
    throw new Error(`unsupported provider ${JSON.stringify(values.provider)}`);
  }
  if (!values.model || !values.binary) {
    throw new Error('--model and --binary are required');
  }
  return values;
}

function textPrompt(blocks) {
  if (!Array.isArray(blocks) || blocks.length === 0) {
    throw new Error('a non-empty text prompt is required');
  }
  if (blocks.some((block) => block?.type !== 'text' || typeof block.text !== 'string')) {
    throw new Error('this ACP adapter accepts text content blocks only');
  }
  const prompt = blocks
    .map((block) => block.text)
    .join('\n')
    .trim();
  if (!prompt) {
    throw new Error('a non-empty text prompt is required');
  }
  if (Buffer.byteLength(prompt, 'utf8') > MAX_PROMPT_BYTES) {
    throw new Error(`prompt exceeds the ${MAX_PROMPT_BYTES}-byte limit`);
  }
  return `${CONFINEMENT_NOTICE}\n\n${prompt}`;
}

async function linkIfPresent(source, destination) {
  try {
    await symlink(source, destination);
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
}

function childBaseEnv() {
  const env = {};
  for (const name of CHILD_ENV_KEYS) {
    if (process.env[name] != null) env[name] = process.env[name];
  }
  return env;
}

function signalProcessTree(child, signal) {
  try {
    if (process.platform !== 'win32' && child.pid != null) {
      process.kill(-child.pid, signal);
    } else {
      child.kill(signal);
    }
  } catch (error) {
    if (error?.code !== 'ESRCH') throw error;
  }
}

function boundedAppend(current, chunk) {
  const next = current + chunk.toString('utf8');
  if (Buffer.byteLength(next, 'utf8') > MAX_OUTPUT_BYTES) {
    throw new Error(`provider output exceeds the ${MAX_OUTPUT_BYTES}-byte limit`);
  }
  return next;
}

function runChild(binary, args, { cwd, env, session }) {
  return new Promise((resolve, reject) => {
    const child = spawn(binary, args, {
      cwd,
      env,
      detached: process.platform !== 'win32',
      shell: false,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    session.child = child;
    let stdout = '';
    let stderr = '';
    let settled = false;
    let terminalError = null;
    let forceKillTimer = null;
    let timeoutTimer = null;

    const finish = (callback) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutTimer);
      clearTimeout(forceKillTimer);
      session.child = null;
      session.terminate = null;
      callback();
    };
    const terminate = (error) => {
      if (settled) return;
      terminalError ??= error;
      signalProcessTree(child, 'SIGTERM');
      forceKillTimer ??= setTimeout(() => {
        signalProcessTree(child, 'SIGKILL');
      }, FORCE_KILL_GRACE_MS);
    };
    session.terminate = terminate;
    timeoutTimer = setTimeout(() => {
      terminate(new Error(`provider exceeded ${CHILD_TIMEOUT_MS}ms`));
    }, CHILD_TIMEOUT_MS);

    child.stdout.on('data', (chunk) => {
      try {
        stdout = boundedAppend(stdout, chunk);
      } catch (error) {
        terminate(error);
      }
    });
    child.stderr.on('data', (chunk) => {
      try {
        stderr = boundedAppend(stderr, chunk);
      } catch (error) {
        terminate(error);
      }
    });
    child.on('error', (error) => finish(() => reject(error)));
    child.on('close', (code, signal) => {
      finish(() => {
        if (terminalError != null) {
          reject(terminalError);
          return;
        }
        const response = stdout.trim();
        if (code === 0 && response) {
          resolve(response);
          return;
        }
        const detail = stderr.trim().slice(-500);
        reject(
          new Error(
            `provider exited without a usable response (code=${code}, signal=${signal ?? 'none'})` +
              (detail ? `: ${detail}` : ''),
          ),
        );
      });
    });
  });
}

async function runAgy(options, prompt, session, workRoot) {
  const appData = join(workRoot, 'agy-data');
  await mkdir(appData, { recursive: true });
  return runChild(
    options.binary,
    [
      '-p',
      prompt,
      '--mode',
      'plan',
      '--sandbox',
      '--disable-slash-commands',
      '--print-timeout',
      '5m',
      '--output-format',
      'text',
      '--model',
      options.model,
      '--log-file',
      join(workRoot, 'agy.log'),
    ],
    {
      cwd: workRoot,
      env: { ...childBaseEnv(), AGY_APP_DATA_DIR: appData },
      session,
    },
  );
}

async function runDeepSeek(options, prompt, session, workRoot) {
  const hermesHome = join(workRoot, 'hermes-home');
  await mkdir(hermesHome, { recursive: true });
  await writeFile(
    join(hermesHome, 'config.yaml'),
    [
      'model:',
      '  provider: deepseek',
      `  default: ${options.model}`,
      'platform_toolsets:',
      '  cli: []',
      'fallback_providers: []',
      'mcp_servers: {}',
      'plugins:',
      '  enabled: []',
      '  disabled: []',
      'hooks: []',
      '',
    ].join('\n'),
    { encoding: 'utf8', mode: 0o600 },
  );

  const sourceHome = join(homedir(), '.hermes');
  for (const name of ['.env', 'auth.json', 'auth.lock']) {
    await linkIfPresent(join(sourceHome, name), join(hermesHome, name));
  }

  return runChild(
    options.binary,
    ['--ignore-rules', '-z', prompt, '-m', options.model, '--provider', 'deepseek'],
    {
      cwd: workRoot,
      env: {
        ...childBaseEnv(),
        HERMES_HOME: hermesHome,
        HERMES_SAFE_MODE: '1',
        HERMES_IGNORE_RULES: '1',
      },
      session,
    },
  );
}

const options = parseArgs(process.argv.slice(2));
const sessions = new Map();

const input = Writable.toWeb(process.stdout);
const output = Readable.toWeb(process.stdin);
const stream = acp.ndJsonStream(input, output);

acp
  .agent({ name: `learn-ukrainian-${options.provider}-text-agent` })
  .onRequest(acp.methods.agent.initialize, () => ({
    protocolVersion: acp.PROTOCOL_VERSION,
    agentCapabilities: { loadSession: false },
  }))
  .onRequest(acp.methods.agent.session.new, () => {
    const sessionId = globalThis.crypto.randomUUID();
    sessions.set(sessionId, { child: null, prompted: false });
    return { sessionId };
  })
  .onRequest(acp.methods.agent.authenticate, () => ({}))
  .onRequest(acp.methods.agent.session.setMode, () => ({}))
  .onRequest(acp.methods.agent.session.prompt, async (context) => {
    const session = sessions.get(context.params.sessionId);
    if (!session) throw new Error('unknown ACP session');
    if (session.prompted) throw new Error('this text-only ACP session accepts one prompt');
    session.prompted = true;
    const prompt = textPrompt(context.params.prompt);
    const workRoot = await mkdtemp(join(tmpdir(), `lu-acp-${options.provider}-`));
    try {
      const response =
        options.provider === 'agy'
          ? await runAgy(options, prompt, session, workRoot)
          : await runDeepSeek(options, prompt, session, workRoot);
      await context.client.notify(acp.methods.client.session.update, {
        sessionId: context.params.sessionId,
        update: {
          sessionUpdate: 'agent_message_chunk',
          content: { type: 'text', text: response },
        },
      });
      return { stopReason: 'end_turn' };
    } finally {
      await rm(workRoot, { recursive: true, force: true });
    }
  })
  .onNotification(acp.methods.agent.session.cancel, (context) => {
    sessions
      .get(context.params.sessionId)
      ?.terminate?.(new Error('provider cancelled by ACP client'));
  })
  .connect(stream);
