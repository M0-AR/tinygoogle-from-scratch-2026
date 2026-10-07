# Demo GIF script (regenerable — keeps README visuals fresh)
# Requires: vhs (https://github.com/charmbracelet/vhs) + ttyd + ffmpeg
# Run: vhs docs/demo.tape   → renders docs/demo.gif (keep under 8 MB)
Output docs/demo.gif
Set FontSize 18
Set Width 900
Set Height 520
Set Framerate 12
Hide
Type "python3 -m experiments.benchmark --live" Enter
Sleep 2s
Show
Type "# 12-17kx scan-vs-index, BM25 order, PageRank r=0.50" Sleep 1s Enter
Type "python3 -m src.server &" Enter Sleep 1s
Type "curl -s 'http://localhost:8000/?q=web+crawler' | head -c 400" Enter
Sleep 3s
