import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import prettierFn from 'eslint-config-prettier';
import jsdoc from 'eslint-plugin-jsdoc';

export default tseslint.config(
    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    {
        ignores: ['node_modules/', 'output/', 'coverage/', 'dist/'],
    },
    {
        files: ['scripts/**/*.ts'],
        plugins: {
            jsdoc,
        },
        rules: {
            ...prettierFn.rules,
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
            'complexity': ['warn', 15],
            'jsdoc/require-description': 'warn',
            'jsdoc/require-jsdoc': [
                'warn',
                {
                    require: {
                        FunctionDeclaration: true,
                        MethodDefinition: true,
                        ClassDeclaration: true,
                    },
                },
            ],
        },
    },
);
