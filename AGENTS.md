# AGENTS.md

> Greenfield repo — 目前僅有 `LICENSE`（AGPLv3）+ Python `.gitignore`，尚無程式碼、README、套件管理檔、CI 或工具鏈設定（2026-10-06）。若目錄結構已有變化，以實際為準。

- 所有回應一律使用繁體中文。
- 專案程式語言為 Python。
- 使用 conda 管理 Python 套件，環境名稱為 `iem_python`（例如：`conda activate iem_python`、`conda install ...`）。不要改用 pip / venv / poetry，除非使用者明確指示。
- 授權為 AGPLv3（`LICENSE`），新增程式碼須保持相容；除非專案後續採用表頭慣例，否則不加授權表頭。
- 首批程式碼／工具鏈落地時，請在此補上：確切的環境建立指令、單一測試執行方式、lint／typecheck 順序與進入點，省略通用建議。
