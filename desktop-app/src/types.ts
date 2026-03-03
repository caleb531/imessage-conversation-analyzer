export interface GridColumn {
    id: string;
    header: string;
    width?: number;
    flexgrow?: number;
}

export interface DataPoint {
    key: string;
    value: number;
}

// Represents a contact fetched from the native macOS contacts framework.
export interface Contact {
    id: string;
    firstName?: string;
    lastName?: string;
    companyName?: string;
    phone?: string;
    email?: string;
}

// Holds optional controls for contact label formatting.
export interface ContactLabelOptions {
    includeDisambiguation?: boolean;
}

// Returns the preferred base name for a contact using first+last, then first, then company.
export function getContactBaseName(contact: Contact): string {
    const trimmedFirstName = contact.firstName?.trim() ?? '';
    const trimmedLastName = contact.lastName?.trim() ?? '';
    const trimmedCompanyName = contact.companyName?.trim() ?? '';

    if (trimmedFirstName && trimmedLastName) {
        return `${trimmedFirstName} ${trimmedLastName}`;
    }
    if (trimmedFirstName) {
        return trimmedFirstName;
    }
    if (trimmedCompanyName) {
        return trimmedCompanyName;
    }
    return 'Unknown contact';
}

// Returns the preferred value to disambiguate duplicate contact labels.
export function getContactDisambiguator(contact: Contact): string {
    const trimmedPhone = contact.phone?.trim() ?? '';
    const trimmedEmail = contact.email?.trim() ?? '';
    const trimmedId = contact.id.trim();

    if (trimmedPhone) {
        return trimmedPhone;
    }
    if (trimmedEmail) {
        return trimmedEmail;
    }
    return trimmedId;
}

// Builds the display label shown in UI surfaces.
export function getContactDisplayLabel(
    contact: Contact,
    options: ContactLabelOptions = {}
): string {
    const baseName = getContactBaseName(contact);
    if (!options.includeDisambiguation) {
        return baseName;
    }

    const disambiguator = getContactDisambiguator(contact);
    if (!disambiguator) {
        return baseName;
    }

    return `${baseName} (${disambiguator})`;
}

// Returns the selector value accepted by the ICA CLI for --contact.
export function getContactCliSelector(contact: Contact): string {
    const trimmedPhone = contact.phone?.trim() ?? '';
    const trimmedEmail = contact.email?.trim() ?? '';
    const baseName = getContactBaseName(contact);
    const trimmedId = contact.id.trim();

    if (trimmedPhone) {
        return trimmedPhone;
    }
    if (trimmedEmail) {
        return trimmedEmail;
    }
    if (baseName !== 'Unknown contact') {
        return baseName;
    }
    return trimmedId;
}
