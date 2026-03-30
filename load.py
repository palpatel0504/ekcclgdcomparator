from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

FILE_MAP = {
    "ekcc_state_df": DATA_DIR / "ekcc" / "ekcc_state.csv",
    "ekcc_district_df": DATA_DIR / "ekcc" / "ekcc_district.csv",
    "ekcc_subdistrict_df": DATA_DIR / "ekcc" / "ekcc_subdistrict.csv",
    "ekcc_village_df": DATA_DIR / "ekcc" / "ekcc_village.csv",
    "lgd_state_df": DATA_DIR / "lgd" / "lgd_state.csv",
    "lgd_district_df": DATA_DIR / "lgd" / "lgd_district.csv",
    "lgd_subdistrict_df": DATA_DIR / "lgd" / "lgd_subdistrict.csv",
    "lgd_village_df": DATA_DIR / "lgd" / "lgd_village.csv",
}


def _read_file(file_path: Path) -> pd.DataFrame:
    # LGD files are Excel workbooks saved with a .csv extension.
    if file_path.parent.name == "lgd":
        return pd.read_excel(
            BytesIO(file_path.read_bytes()),
            engine="openpyxl",
            header=1,
        )
    return pd.read_csv(file_path, encoding="latin1", low_memory=False)


def load_all_dataframes() -> dict[str, pd.DataFrame]:
    dataframes: dict[str, pd.DataFrame] = {}

    for dataframe_name, file_path in FILE_MAP.items():
        dataframes[dataframe_name] = _read_file(file_path)

    return dataframes


if __name__ == "__main__":
    dataframes = load_all_dataframes()

    ekcc_state_df = dataframes["ekcc_state_df"]
    ekcc_district_df = dataframes["ekcc_district_df"]
    ekcc_subdistrict_df = dataframes["ekcc_subdistrict_df"]
    ekcc_village_df = dataframes["ekcc_village_df"]

    lgd_state_df = dataframes["lgd_state_df"]
    lgd_district_df = dataframes["lgd_district_df"]
    lgd_subdistrict_df = dataframes["lgd_subdistrict_df"]
    lgd_village_df = dataframes["lgd_village_df"]

    for name, df in dataframes.items():
        print(f"{name}: {df.shape}")
