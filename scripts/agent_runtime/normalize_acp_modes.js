const fs = require('fs');
const path = require('path');

const targetDir = 'node_modules/@agentclientprotocol/claude-agent-acp';
const packagePath = path.resolve(process.cwd(), targetDir);

try {
    if (!fs.existsSync(packagePath)) {
        console.log(`Package ${targetDir} is absent, skipping normalization.`);
        process.exit(0);
    }

    const realPackagePath = fs.realpathSync(packagePath);
    if (realPackagePath !== packagePath) {
        console.error(`Error: Package root ${targetDir} is a symlink or resolves outside. Refusing to normalize.`);
        process.exit(1);
    }
} catch (e) {
    if (e.code === 'ENOENT') {
        console.log(`Package ${targetDir} is absent, skipping normalization.`);
        process.exit(0);
    }
    console.error(`Error resolving ${targetDir}: ${e.message}`);
    process.exit(1);
}

function normalizeDir(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        let stat;
        try {
            stat = fs.lstatSync(fullPath);
        } catch (e) {
            console.error(`Error statting ${fullPath}: ${e.message}`);
            process.exit(1);
        }

        if (stat.isSymbolicLink()) {
            console.error(`Error: Symlink found at ${fullPath}. Refusing to normalize.`);
            process.exit(1);
        }

        if (!stat.isDirectory() && !stat.isFile()) {
            continue;
        }

        if (stat.isFile() && stat.nlink > 1) {
            continue;
        }

        try {
            const newMode = stat.mode & ~(0o022);
            if (newMode !== stat.mode) {
                fs.chmodSync(fullPath, newMode);
            }
        } catch (e) {
            console.error(`Error chmodding ${fullPath}: ${e.message}`);
            process.exit(1);
        }

        if (stat.isDirectory()) {
            normalizeDir(fullPath);
        }
    }
}

try {
    const rootStat = fs.lstatSync(packagePath);
    const newMode = rootStat.mode & ~(0o022);
    if (newMode !== rootStat.mode) {
        fs.chmodSync(packagePath, newMode);
    }
    normalizeDir(packagePath);
} catch (e) {
    console.error(`Error during normalization: ${e.message}`);
    process.exit(1);
}
