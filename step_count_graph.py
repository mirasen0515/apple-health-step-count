"""
Apple Health の export.xml から歩数（StepCount）を抽出し、
日別の合計をグラフで表示するスクリプト。
"""

from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# 同じフォルダにある export.xml を読み込む
XML_PATH = Path(__file__).parent / "export.xml"
STEP_COUNT_TYPE = "HKQuantityTypeIdentifierStepCount"


def load_step_records(xml_path: Path) -> pd.DataFrame:
    """export.xml から StepCount レコードだけを抽出する。"""
    if not xml_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    records = []
    for record in root.iter("Record"):
        if record.get("type") != STEP_COUNT_TYPE:
            continue

        value = record.get("value")
        start_date = record.get("startDate")
        if value is None or start_date is None:
            continue

        records.append(
            {
                "startDate": start_date,
                "steps": float(value),
            }
        )

    if not records:
        raise ValueError("StepCount のデータが見つかりませんでした。")

    df = pd.DataFrame(records)
    # Apple Health の日時形式: "2018-08-20 16:45:57 +1200"
    df["datetime"] = pd.to_datetime(df["startDate"], format="%Y-%m-%d %H:%M:%S %z")
    df["date"] = df["datetime"].dt.date
    return df


def aggregate_daily_steps(df: pd.DataFrame) -> pd.DataFrame:
    """日別の歩数合計を計算する。"""
    daily = (
        df.groupby("date", as_index=False)["steps"]
        .sum()
        .rename(columns={"steps": "total_steps"})
        .sort_values("date")
    )
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def plot_daily_steps(daily: pd.DataFrame) -> None:
    """日別歩数の棒グラフを表示する。"""
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(daily["date"], daily["total_steps"], width=0.8, color="#4C9AFF", edgecolor="none")

    ax.set_title("日別の歩数合計", fontsize=16, pad=12)
    ax.set_xlabel("日付", fontsize=12)
    ax.set_ylabel("歩数", fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=45, ha="right")

    avg_steps = daily["total_steps"].mean()
    ax.axhline(avg_steps, color="#FF6B6B", linestyle="--", linewidth=1.5, label=f"平均: {avg_steps:,.0f} 歩")
    ax.legend()

    plt.tight_layout()
    plt.show()


def main() -> None:
    print(f"読み込み中: {XML_PATH}")
    df = load_step_records(XML_PATH)
    daily = aggregate_daily_steps(df)

    print(f"StepCount レコード数: {len(df):,} 件")
    print(f"集計日数: {len(daily):,} 日")
    print(f"期間: {daily['date'].min().date()} ～ {daily['date'].max().date()}")
    print(f"1日あたり平均: {daily['total_steps'].mean():,.0f} 歩")

    plot_daily_steps(daily)


if __name__ == "__main__":
    main()
