from pathlib import Path

from modules.graph_visualizer import build_premium_graph


suspect = "0x1111111111111111111111111111111111111111"

transactions = [
    {
        "from": suspect,
        "to": "0x2222222222222222222222222222222222222222",
        "value": "2400000000000000000",
    },
    {
        "from": "0x2222222222222222222222222222222222222222",
        "to": "0x3333333333333333333333333333333333333333",
        "value": "1800000000000000000",
    },
    {
        "from": "0x3333333333333333333333333333333333333333",
        "to": "0x4444444444444444444444444444444444444444",
        "value": "1200000000000000000",
    },
]


html = build_premium_graph(
    transactions,
    suspect,
)

Path("test_graph.html").write_text(
    html,
    encoding="utf-8",
)

print("Premium graph generated successfully.")
