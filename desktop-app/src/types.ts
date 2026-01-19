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
