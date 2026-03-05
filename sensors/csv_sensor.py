import pandas as pd
from config.pollutants import COLUMN_ALIASES, META_COLUMNS
from sensors.base import BaseSensor

class CSVSensor(BaseSensor):
    def _find_column(self, df, candidates):
        for name in candidates:
            if name in df.columns:
                return name
        return None

    def _extract_row(self, df, row):
        sensors = {}
        for pollutant, aliases in COLUMN_ALIASES.items():
            col = self._find_column(df, aliases)
            if col and pd.notna(row[col]):
                sensors[pollutant] = float(row[col])
        meta = {}
        for field in META_COLUMNS:
            if field in df.columns and pd.notna(row[field]):
                meta[field.capitalize()] = row[field]
        sensors["_meta"] = meta
        return sensors

    def read(self, source, row_index=-1):
        df = pd.read_csv(source)
        if df.empty:
            raise ValueError(f"Empty dataset: {source}")
        return self._extract_row(df, df.iloc[row_index])

    def read_all(self, source):
        df = pd.read_csv(source)
        results = []
        for idx in range(len(df)):
            snap = self._extract_row(df, df.iloc[idx])
            if any(not k.startswith("_") for k in snap):
                results.append(snap)
        return results
