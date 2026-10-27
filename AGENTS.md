# AGENTS.md

> 目前包含 Python 桌面自動化程式與 unittest 測試；尚無套件管理檔、CI 或 lint/typecheck 工具鏈（2026-10-27）。若目錄結構已有變化，以實際為準。

- 所有回應一律使用繁體中文。
- 專案程式語言為 Python。
- 使用 conda 管理 Python 套件，環境名稱為 `iem_python`（例如：`conda activate iem_python`、`conda install ...`）。不要改用 pip / venv / poetry，除非使用者明確指示。
- 授權為 AGPLv3（`LICENSE`），新增程式碼須保持相容；除非專案後續採用表頭慣例，否則不加授權表頭。
- 首批程式碼／工具鏈落地時，請在此補上：確切的環境建立指令、單一測試執行方式、lint／typecheck 順序與進入點，省略通用建議。
- Dino 自動跳躍程式進入點：`python dino_bot.py`（或相容啟動器 `python ff.py`）；依賴安裝：`conda install -n iem_python -c conda-forge pyautogui`。啟動後把滑鼠放在希望跳躍的位置，5 秒後固定該座標，預設在右側 60 像素處以小區域畫面偵測；可用 `--lookahead` 調整距離。偵測會補償全畫面日夜色偏，並支援 `(83,83,83)`、`(172,172,172)` 附近障礙色。
- 建立環境：`conda create -n iem_python -c conda-forge python=3.12 pyautogui`；既有環境只需執行前述 `conda install`。
- 單一測試命令：`python -m unittest discover -s tests -v`。
- 驗證順序：目前未設定 lint/typecheck 工具，故不執行；先執行上述 unittest。加入工具設定後，依序執行 lint、typecheck、unittest。
