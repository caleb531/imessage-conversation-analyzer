import js from '@eslint/js';
import prettier from 'eslint-config-prettier';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';

/** @type {import('eslint').Linter.Config[]} */
// Flat ESLint configuration for TypeScript, Svelte, and formatting compatibility.
export default [
    js.configs.recommended,
    ...ts.configs.recommended,
    ...svelte.configs['flat/recommended'],
    prettier,
    ...svelte.configs['flat/prettier'],
    {
        // Svelte files use the TypeScript parser for script blocks.
        files: ['**/*.svelte', '**/*.svelte.ts'],
        languageOptions: {
            parserOptions: {
                parser: ts.parser
            }
        }
    },
    {
        // Shared browser/node globals and baseline lint rules.
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.node
            }
        },
        rules: {
            'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
            '@typescript-eslint/no-unused-vars': [
                'warn',
                {
                    argsIgnorePattern: '^_',
                    varsIgnorePattern: '^_',
                    caughtErrorsIgnorePattern: '^_'
                }
            ]
        }
    },
    {
        // Ignore generated assets and dependency lock files.
        ignores: [
            '.DS_Store',
            'node_modules',
            'build',
            'src-tauri',
            '.svelte-kit',
            '.vercel',
            'package',
            '.env',
            '.env.*',
            '!.env.example',
            'pnpm-lock.yaml',
            'package-lock.json',
            'yarn.lock'
        ]
    }
];
