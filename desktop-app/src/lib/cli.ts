import Papa from 'papaparse';
import { parseArgsStringToArgv } from 'string-argv';
import { getSelectedContacts } from './contacts.svelte';
import { runIcaSidecar, type SidecarResult } from './sidecar';

const FORMAT_FLAGS = new Set(['--format', '-f']);
const OUTPUT_FLAGS = new Set(['--output', '-o']);
const CONTACT_FLAGS = new Set(['--contact', '-c']);
const COMBINED_SHORT_FLAGS = new Set(['-c', '-f', '-o']);
const COMBINED_LONG_FLAGS = new Set(['--contact', '--format', '--output']);

export class MissingContactError extends Error {
    constructor(message = 'No contacts selected. Choose at least one contact before running the analyzer.') {
        super(message);
        this.name = 'MissingContactError';
    }
}

export interface IcaCsvHeader {
    original: string;
    id: string;
}

export interface IcaCsvResult {
    code: SidecarResult['code'];
    signal: SidecarResult['signal'];
    rows: Record<string, unknown>[];
    headers: IcaCsvHeader[];
    stderr: string;
    rawCsv: string;
    args: string[];
}

export interface IcaCommandResult {
    code: SidecarResult['code'];
    signal: SidecarResult['signal'];
    stderr: string;
    stdout: string;
    args: string[];
}

function toCamelCase(header: string, headerIndex: number): string {
    const cleaned = header.replace(/[^0-9A-Za-z]+/g, ' ').trim();
    if (!cleaned) {
        return `column${headerIndex}`;
    }
    const parts = cleaned.split(/\s+/);
    return parts
        .map((part, partIndex) => {
            const lower = part.toLowerCase();
            if (partIndex === 0) {
                return lower;
            }
            return lower.charAt(0).toUpperCase() + lower.slice(1);
        })
        .join('');
}

function expandKnownCombinedArgs(args: string[]): string[] {
    const expanded: string[] = [];
    for (const arg of args) {
        if (arg.startsWith('--')) {
            const eqIndex = arg.indexOf('=');
            if (eqIndex > 0) {
                const flag = arg.slice(0, eqIndex);
                const value = arg.slice(eqIndex + 1);
                if (COMBINED_LONG_FLAGS.has(flag)) {
                    expanded.push(flag, value);
                    continue;
                }
            }
        } else if (arg.startsWith('-') && !arg.startsWith('--')) {
            const flag = arg.slice(0, 2);
            let value = arg.slice(2);
            if (COMBINED_SHORT_FLAGS.has(flag) && value) {
                if (value.startsWith('=')) {
                    value = value.slice(1);
                }
                expanded.push(flag, value);
                continue;
            }
        }
        expanded.push(arg);
    }
    return expanded;
}

function removeOption(args: string[], flags: Set<string>): string[] {
    const result: string[] = [];
    for (let index = 0; index < args.length; index += 1) {
        const entry = args[index];
        if (flags.has(entry)) {
            index += 1;
            continue;
        }
        result.push(entry);
    }
    return result;
}

function hasFlag(args: string[], flags: Set<string>): boolean {
    return args.some((arg) => flags.has(arg));
}

function parseArgInput(args: string | string[]): string[] {
    if (Array.isArray(args)) {
        return [...args];
    }
    const trimmed = args.trim();
    if (!trimmed) {
        return [];
    }
    return parseArgsStringToArgv(trimmed);
}

async function addContactArgument(args: string[]): Promise<string[]> {
    if (hasFlag(args, CONTACT_FLAGS)) {
        return args;
    }
    const contacts = await getSelectedContacts();
    if (contacts.length === 0) {
        throw new MissingContactError();
    }
    return [...args, ...contacts.flatMap((contact) => ['--contact', contact])];
}

function ensureCsvFormat(args: string[]): string[] {
    const withoutFormat = removeOption(args, FORMAT_FLAGS);
    return [...withoutFormat, '--format', 'csv'];
}

function ensureOutputPath(args: string[], outputPath: string): string[] {
    const withoutOutput = removeOption(args, OUTPUT_FLAGS);
    return [...withoutOutput, '--output', outputPath];
}

function parseCsvOutput(
    rawCsv: string,
    finalArgs: string[]
): { headers: IcaCsvHeader[]; rows: Record<string, unknown>[] } {
    const headers: IcaCsvHeader[] = [];
    const headersByIndex = new Map<number, IcaCsvHeader>();
    const usedIds = new Set<string>();

    function ensureUniqueId(baseId: string): string {
        let candidate = baseId;
        let suffix = 1;
        while (usedIds.has(candidate)) {
            candidate = `${baseId}${suffix}`;
            suffix += 1;
        }
        usedIds.add(candidate);
        return candidate;
    }

    const parseResult = Papa.parse<Record<string, unknown>>(rawCsv, {
        header: true,
        skipEmptyLines: true,
        dynamicTyping: true,
        transformHeader(header: string, headerIndex: number) {
            const baseId = toCamelCase(header, headerIndex);
            const uniqueId = ensureUniqueId(baseId);
            const existing = headersByIndex.get(headerIndex);
            if (existing) {
                existing.id = uniqueId;
            } else {
                const entry: IcaCsvHeader = { original: header, id: uniqueId };
                headers.push(entry);
                headersByIndex.set(headerIndex, entry);
            }
            return uniqueId;
        }
    });

    if (parseResult.errors.length > 0) {
        const [firstError] = parseResult.errors;
        throw new Error(
            `Failed to parse CSV output from ICA (row ${firstError.row}): ${firstError.message}`
        );
    }

    const headersByOriginal = new Map<string, IcaCsvHeader[]>();
    const originalOrder: string[] = [];

    headers.forEach((header) => {
        const normalizedOriginal = header.original.trim().toLowerCase();
        const key = normalizedOriginal || `__empty__${header.id}`;
        if (!headersByOriginal.has(key)) {
            headersByOriginal.set(key, []);
            originalOrder.push(key);
        }
        headersByOriginal.get(key)?.push(header);
    });

    const filteredHeaders: IcaCsvHeader[] = [];
    const duplicateIds: string[] = [];

    for (const key of originalOrder) {
        const candidates = headersByOriginal.get(key) ?? [];
        if (candidates.length === 0) {
            continue;
        }

        const selected =
            candidates.find((candidate) =>
                parseResult.data.some((row) => {
                    const value = row[candidate.id];
                    return value !== undefined && value !== null && value !== '';
                })
            ) ?? candidates[0];

        filteredHeaders.push(selected);

        for (const candidate of candidates) {
            if (candidate.id !== selected.id) {
                duplicateIds.push(candidate.id);
            }
        }
    }

    if (duplicateIds.length > 0) {
        for (const row of parseResult.data) {
            for (const duplicateId of duplicateIds) {
                delete row[duplicateId];
            }
        }
    }

    if (filteredHeaders.length === 0 && parseResult.data.length === 0) {
        throw new Error(`ICA command produced no CSV data. Args: ${finalArgs.join(' ')}`);
    }

    return { headers: filteredHeaders, rows: parseResult.data };
}

export async function invokeIcaCsv(args: string | string[]): Promise<IcaCsvResult> {
    const parsedArgs = parseArgInput(args);
    const expandedArgs = expandKnownCombinedArgs(parsedArgs);
    const argsWithContact = await addContactArgument(expandedArgs);
    const finalArgs = ensureCsvFormat(argsWithContact);

    const result = await runIcaSidecar(finalArgs);
    const rawCsv = result.stdout.trim();

    if (!rawCsv) {
        throw new Error('ICA returned no CSV output.');
    }

    const parsedCsv = parseCsvOutput(rawCsv, finalArgs);

    return {
        code: result.code,
        signal: result.signal,
        rows: parsedCsv.rows,
        headers: parsedCsv.headers,
        stderr: result.stderr.trim(),
        rawCsv,
        args: finalArgs
    };
}

export async function invokeIcaCsvToFile(
    args: string | string[],
    outputPath: string
): Promise<IcaCommandResult> {
    const parsedArgs = parseArgInput(args);
    const expandedArgs = expandKnownCombinedArgs(parsedArgs);
    const argsWithContact = await addContactArgument(expandedArgs);
    const csvArgs = ensureCsvFormat(argsWithContact);
    const finalArgs = ensureOutputPath(csvArgs, outputPath);

    const result = await runIcaSidecar(finalArgs);
    const stderr = result.stderr.trim();
    const stdout = result.stdout.trim();

    if (result.code !== 0) {
        throw new Error(stderr || stdout || `ICA exited with code ${result.code ?? 'unknown'}.`);
    }

    return {
        code: result.code,
        signal: result.signal,
        stderr,
        stdout,
        args: finalArgs
    };
}

export async function runMessageTotals(): Promise<IcaCsvResult> {
    return invokeIcaCsv(['message_totals']);
}
