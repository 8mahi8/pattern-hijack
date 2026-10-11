# PATTERN HIJACK — v1.1 Stability

弾幕へ近づくことで共通FLOWを貯め、最後に狙った色の弾幕をHIJACKする、短編ブラウザアクションゲームです。

## 操作

- WASD / 矢印キー：移動
- 画面ドラッグ：移動（対応ブラウザ）
- 射撃とHIJACKは自動。FLOWが満タンになると対象の色を奪う
- 4 WaveでEMITTERを破壊 → build選択 → 3色Bossを攻略

## 起動

`index.html` をPCブラウザで開くか、静的Webサーバーに配置します。外部API・ログイン・Firebaseは不要です。

## GitHub Pages

専用のリポジトリを作成し、`index.html` / `README.md` / `tests/` / `.github/` を配置します。
GitHub上の `Settings → Pages` から `Deploy from a branch`、`main`・`/(root)` を選んで公開できます。公開はユーザーの判断で行ってください。

## v1.1 の変更

- 最終EMITTER撃破時の弾配列再代入を廃止。衝突処理との競合を防止
- Wave終了から強化選択へタイマー依存でなくゲームループ内で遷移
- 弾上限の実効性強化（friendlyのみで上限超過も防止）
- 描画内のHUD要素照会をキャッシュ
- RESTART時のキー入力状態・ドラッグ状態を確実にリセット
- 再START後に古いチュートリアルが割り込むのを防止
- FLOW/HIJACK/CHAIN/build効果は既存v1.0から変更せず、プレイ感を保護

## 品質と限界

自動ブラウザテストは起動・Wave移行・Bossクリア・RESTART/負荷条件を検査します。実プレイの面白さ、端末操作性、公開品質は自動テストだけでは保証できません。仮Web Audioは品質不足のため引き続きHOLDです。

## 権利

ゲームのコード・素材に第三者の画像や音源は同梱していません。再配布・ライセンス条件は所有者が決めるまで未設定です。