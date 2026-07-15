# PDF Overlay Editor

既存PDFへ文字・画像をオーバーレイして保存する Windows 11向けGUIアプリです。初期実装では設計書の Phase 1〜3（表示、ページ切替、ズーム、文字・画像の追加と移動、Undo/Redo、安全な保存）を実装しています。

## セットアップ

Python 3.11以降で次を実行します。

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 実行

```powershell
python main.py
```

PDFを開き、「文字追加」または「画像追加」で要素を中央へ配置します。配置・編集した要素を右クリックして「すべてのページに適用」を選ぶと、同じ位置と設定で他ページへ複製できます。「ページ番号追加」では現在ページに番号を挿入し、位置を決めてから右クリックで全ページへ連番を展開できます。要素はドラッグ移動できます。画像を右クリックして「画像サイズを編集」を選ぶと、幅・高さと縦横比の維持を設定できます。Ctrl+Z/Ctrl+Yで取り消し・やり直し、Ctrl+Sで上書き保存できます。上書き時は同じフォルダーの一時PDFへ保存した後、元ファイルを置換します。

日本語文字は Windows の游ゴシック、メイリオ、MSゴシックの順で自動検出します。見つからない環境では英数字用の組込みフォントが使われます。

## テスト

```powershell
pytest -q
```

## 配布用EXE

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name PDFOverlayEditor main.py
```

成果物は `dist\PDFOverlayEditor\` に生成されます。

## 初期実装の制限

- 画像サイズは右クリックメニューから数値編集できます。キャンバス上のリサイズハンドルと右側プロパティペインは未実装です。
- ページ範囲を指定した一括適用と、フッター書式の詳細設定は未実装です。
- 編集内容はPDFへ保存するまで元PDFには反映されません。
