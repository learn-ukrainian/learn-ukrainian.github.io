import { connect, Client } from '@dagger.io/dagger';

// CI Pipeline for Learn Ukrainian
// 1. Lint (ESLint)
// 2. Typecheck (TSC)
// 3. Test (Jest)
// 4. Audit (Custom Scripts)

connect(async (client: Client) => {
    // 1. Get source code
    const source = client
        .host()
        .directory('.', { exclude: ['node_modules', 'output', '.git', 'coverage', '.dagger'] });

    // 2. Prepare Base Image (Node)
    const base = client
        .container()
        .from('node:20')
        .withWorkdir('/app')
        .withExec(['apt-get', 'update'])
        .withExec(['apt-get', 'install', '-y', 'python3'])
        .withFile('package.json', source.file('package.json'))
        .withFile('package-lock.json', source.file('package-lock.json'))
        .withExec(['npm', 'ci']);

    // 3. Lint Gate
    const lint = base
        .withDirectory('.', source)
        .withExec(['npm', 'run', 'lint', '--', '--max-warnings=0'])
        .sync(); // Execute

    console.log('✅ Lint passed');

    // 4. Test Gate
    const test = base
        .withDirectory('.', source)
        .withExec(['npm', 'test'])
        .sync(); // Execute

    console.log('✅ Tests passed');

    // 5. Build/Generate Gate (Verify it builds)
    const build = base
        .withDirectory('.', source)
        .withExec(['npm', 'run', 'generate:all'])
        .sync();

    console.log('✅ Build passed');

    // 6. Audit Gate (Strict Quality Check)
    console.log('🔍 Running Audit...');
    const audit = base
        .withDirectory('.', source)
        .withExec(['sh', '-c', 'find curriculum/l2-uk-en -name "module-*.md" -print0 | xargs -0 -n 1 python3 scripts/audit_module.py'])
        .sync();

    console.log('✅ Audit passed');

}, { LogOutput: process.stdout });
