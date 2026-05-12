import pandas as pd
import json
from pathlib import Path

csv = Path("app/data/processed/competitive_data.csv")
df  = pd.read_csv(csv, encoding="utf-8-sig")

print(f"Total registros: {len(df)}")
print(f"Plataformas:")
for p, n in df["platform"].value_counts().items():
    print(f"  {p}: {n}")
print(f"Zonas: {df['zone'].value_counts().to_dict()}")
print(f"Productos unicos: {df['product'].nunique()}")
print()
print(df.groupby("platform").agg(
    avg_precio_final=("final_price", "mean"),
    avg_delivery_fee=("delivery_fee", "mean"),
    avg_eta_min=("eta_min", "mean"),
    pct_promo=("discount", lambda x: (x > 0).mean() * 100),
).round(2))

ins = json.loads(Path("app/data/processed/insights.json").read_text(encoding="utf-8"))
print(f"\nInsights generados: {len(ins)}")
for i in ins:
    print(f"  [{i['priority']}] {i['id']} - {i['title'][:65]}")
