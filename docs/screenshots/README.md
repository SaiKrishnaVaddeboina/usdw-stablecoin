# Screenshots

The README references four PNG files in this directory:

| File | What to capture |
|---|---|
| `dashboard.png` | The **📊 Dashboard** tab after running the **Happy Path** scenario — should show the reserves-vs-supply chart, balance distribution, and transfer-volume timeline |
| `transfer.png` | The **💸 Mint & Transfer** tab with a transfer receipt visible (the JSON event + the green "PQC signature ✅ verified" badge) |
| `audit.png` | The **📜 Audit Log** tab showing the events table with the type filter and search box visible |
| `scenarios.png` | The **🎬 Scenarios** tab showing all five scenario cards |

## How to capture

1. Open the [live demo](https://usdw-stablecoin.streamlit.app) (or run locally: `streamlit run ui/app.py`)
2. Run the **Happy Path** scenario first to populate state
3. Set your browser to ~1400px wide for clean screenshots
4. Take a screenshot of each tab (macOS: `Cmd+Shift+4` then space then click the window)
5. Save into this directory using the exact filenames above
6. Commit and push — they'll automatically appear in the main README

## Tips for good screenshots

- **Light theme** (the deployed app uses light by default — looks cleaner in READMEs)
- **Hide the sidebar** for the wider tab screenshots, or include it for the dashboard shot to show the live metrics
- **PNG, not JPG** — UI screenshots compress better as PNG and stay sharp
- Keep file sizes under ~500 KB each (Streamlit's UI is mostly flat colors, so PNGs stay small naturally)
