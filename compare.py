from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "required_columns_output"
OUTPUT_DIR = BASE_DIR / "comparison_output"
MISSING_CODE_TEXT = "code is not mention"


ENTITY_CONFIG = {
    "state": {
        "key": "State Code",
        "name": "State Name",
        "mapping_columns": [],
        "required_columns": ["State Name", "State Code", "State Type"],
    },
    "district": {
        "key": "District Code",
        "name": "District Name",
        "mapping_columns": ["State Code"],
        "required_columns": ["State Code", "State Name", "District Code", "District Name"],
    },
    "subdistrict": {
        "key": "Sub District Code",
        "name": "Sub District Name",
        "mapping_columns": ["District Code"],
        "required_columns": [
            "Sub District Name",
            "Sub District Code",
            "District Code",
            "District Name",
            "State Name",
        ],
    },
    "village": {
        "key": "Village Code",
        "name": "Village Name",
        "mapping_columns": ["Village Census Code", "Sub District Code", "District Code"],
        "required_columns": [
            "Village Name",
            "Village Code",
            "Village Census Code",
            "Sub District Code",
            "Sub District Name",
            "District Code",
            "District Name",
            "State Name",
        ],
    },
}


def read_output(input_dir: Path, source_name: str, entity_name: str) -> pd.DataFrame:
    file_path = input_dir / source_name / f"{entity_name}.csv"
    return pd.read_csv(file_path, dtype="string").fillna("")


def output_exists(input_dir: Path, source_name: str, entity_name: str) -> bool:
    file_path = input_dir / source_name / f"{entity_name}.csv"
    return file_path.exists() and file_path.is_file()


def normalize_name(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .fillna("")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.casefold()
    )


def prepare_for_compare(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    prepared = df.copy()
    prepared[key_column] = prepared[key_column].astype("string").fillna("").str.strip()
    return prepared


def build_insert_file(ekcc_df: pd.DataFrame, lgd_df: pd.DataFrame, entity_name: str) -> pd.DataFrame:
    config = ENTITY_CONFIG[entity_name]
    key_column = config["key"]

    ekcc_keys = set(
        ekcc_df.loc[
            ekcc_df[key_column].ne("") & ekcc_df[key_column].ne(MISSING_CODE_TEXT),
            key_column,
        ]
    )

    insert_df = lgd_df.loc[
        lgd_df[key_column].eq(MISSING_CODE_TEXT) | ~lgd_df[key_column].isin(ekcc_keys),
        config["required_columns"],
    ].copy()

    insert_df = insert_df.drop_duplicates()
    insert_df.insert(0, "comparison", "Present in LGD but not in EKCC")
    return insert_df


def build_rename_file(ekcc_df: pd.DataFrame, lgd_df: pd.DataFrame, entity_name: str) -> pd.DataFrame:
    config = ENTITY_CONFIG[entity_name]
    key_column = config["key"]
    name_column = config["name"]

    shared = ekcc_df.merge(
        lgd_df,
        on=key_column,
        how="inner",
        suffixes=("_ekcc", "_lgd"),
    )
    shared = shared.loc[
        shared[key_column].ne("") & shared[key_column].ne(MISSING_CODE_TEXT)
    ].copy()

    rename_mask = normalize_name(shared[f"{name_column}_ekcc"]) != normalize_name(shared[f"{name_column}_lgd"])
    rename_df = shared.loc[rename_mask].copy()
    rename_df["comparison"] = (
        "Before: "
        + rename_df[f"{name_column}_ekcc"].astype("string").fillna("")
        + " | After: "
        + rename_df[f"{name_column}_lgd"].astype("string").fillna("")
    )

    result_columns = [key_column, f"{name_column}_ekcc", f"{name_column}_lgd", "comparison"]
    for mapping_column in config["mapping_columns"]:
        ekcc_column = f"{mapping_column}_ekcc"
        lgd_column = f"{mapping_column}_lgd"
        if ekcc_column in rename_df.columns and lgd_column in rename_df.columns:
            result_columns.extend([ekcc_column, lgd_column])

    return rename_df.loc[:, result_columns].drop_duplicates()


def build_update_file(ekcc_df: pd.DataFrame, lgd_df: pd.DataFrame, entity_name: str) -> pd.DataFrame:
    config = ENTITY_CONFIG[entity_name]
    key_column = config["key"]
    name_column = config["name"]
    mapping_columns = config["mapping_columns"]

    if not mapping_columns:
        return pd.DataFrame(columns=[key_column, name_column, "comparison"])

    shared = ekcc_df.merge(
        lgd_df,
        on=key_column,
        how="inner",
        suffixes=("_ekcc", "_lgd"),
    )
    shared = shared.loc[
        shared[key_column].ne("") & shared[key_column].ne(MISSING_CODE_TEXT)
    ].copy()

    difference_masks = []
    for mapping_column in mapping_columns:
        difference_masks.append(
            shared[f"{mapping_column}_ekcc"].astype("string").fillna("").str.strip()
            != shared[f"{mapping_column}_lgd"].astype("string").fillna("").str.strip()
        )

    update_mask = difference_masks[0]
    for mask in difference_masks[1:]:
        update_mask = update_mask | mask

    update_df = shared.loc[update_mask].copy()

    reasons = []
    for _, row in update_df.iterrows():
        changed_columns = []
        for mapping_column in mapping_columns:
            before_value = str(row[f"{mapping_column}_ekcc"]).strip()
            after_value = str(row[f"{mapping_column}_lgd"]).strip()
            if before_value != after_value:
                changed_columns.append(f"{mapping_column}: Before {before_value} -> After {after_value}")
        reasons.append(" | ".join(changed_columns))
    update_df["comparison"] = reasons

    result_columns = [key_column, f"{name_column}_ekcc", f"{name_column}_lgd"]
    for mapping_column in mapping_columns:
        result_columns.extend([f"{mapping_column}_ekcc", f"{mapping_column}_lgd"])
    result_columns.append("comparison")

    return update_df.loc[:, result_columns].drop_duplicates()


def write_comparison_files(
    input_dir: Path = INPUT_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, dict[str, pd.DataFrame]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing_file in output_dir.glob("*.csv"):
        existing_file.unlink()
    generated_outputs: dict[str, dict[str, pd.DataFrame]] = {}

    for entity_name, config in ENTITY_CONFIG.items():
        if not (
            output_exists(input_dir, "ekcc", entity_name)
            and output_exists(input_dir, "lgd", entity_name)
        ):
            continue

        ekcc_df = prepare_for_compare(read_output(input_dir, "ekcc", entity_name), config["key"])
        lgd_df = prepare_for_compare(read_output(input_dir, "lgd", entity_name), config["key"])

        insert_df = build_insert_file(ekcc_df, lgd_df, entity_name)
        rename_df = build_rename_file(ekcc_df, lgd_df, entity_name)
        update_df = build_update_file(ekcc_df, lgd_df, entity_name)

        insert_df.to_csv(output_dir / f"{entity_name}_insert.csv", index=False)
        rename_df.to_csv(output_dir / f"{entity_name}_rename.csv", index=False)
        update_df.to_csv(output_dir / f"{entity_name}_update.csv", index=False)
        generated_outputs[entity_name] = {
            "insert": insert_df,
            "rename": rename_df,
            "update": update_df,
        }

        print(f"{entity_name}_insert.csv -> {insert_df.shape}")
        print(f"{entity_name}_rename.csv -> {rename_df.shape}")
        print(f"{entity_name}_update.csv -> {update_df.shape}")

    return generated_outputs


if __name__ == "__main__":
    write_comparison_files(INPUT_DIR, OUTPUT_DIR)
