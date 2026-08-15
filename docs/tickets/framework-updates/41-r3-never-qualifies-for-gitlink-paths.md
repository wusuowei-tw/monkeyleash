# 41 — R3 對 gitlink 路徑永遠給不出合格紅燈

**排程**:立即。station-④ TDD,紅燈先行。

**來源**:下游(量化)實測回報。`data_collector` 是 submodule(gitlink,mode `160000`)。

## 現象

`head_blob()` 只問 parent 的物件庫:

```
git cat-file blob HEAD:data_collector/<檔>   →  fatal(gitlink 那一格存的是 commit id,不是子樹)
```

於是 `head_content_hash()` 回 `None`,而 `redlight_missing()` 的兩個合格出口是:

| 出口 | 條件 | gitlink 底下 |
|---|---|---|
| 新檔案 | `impl_exists is False` | 檔案已存在 → 走不到 |
| 既有檔案 | `impl_hash == head` | `head is None` → 走不到 |

兩個都走不到 ⇒ **submodule 底下任何既有檔案永遠拿不到合格紅燈**。
出口只剩 legacy 豁免清單(只減不增,而且清單的入場券綁 parent 的 go-live 樹),
也就是沒有出口。

**該處只因影子模式開著才沒被擋。** 影子一晉升,submodule 底下每一次合法修改當場全擋 ——
方向是 fail-closed,擋的卻是做對事的人,而那種規則最後會被整條關掉(F-031 的形狀)。

## 根因

F-0013 把判準錨在 HEAD 是對的(時點不變),但它假設
**`git show HEAD:<路徑>` 對任何受版控的路徑都讀得到**。
gitlink 不成立:parent 的樹在那一格存的是一個 commit id,`HEAD:sub/foo.py` 沒有這個物件。
「讀不到」在 `head_blob` 裡與「不在 HEAD(新建未提交)」共用同一個回傳值 `None`,
所以這個缺席**完全無聲** —— 規則看起來還在,實際上對整個 submodule 失效。

## 修

偵測到路徑落在 gitlink 前綴底下就**委派**:`git -C <submodule> cat-file blob HEAD:<相對路徑>`。

判定 gitlink 用 **tree 的 mode 欄**(`git ls-tree HEAD -- <前綴>` 首欄 `== "160000"`),
不讀 `.gitmodules`:mode 是 git 自己的權威,`.gitmodules` 可能缺、可能過期。
**檔案模式位元是封閉集合**(`100644` / `100755` / `120000` / `040000` / `160000`)——
枚舉,不做 pattern 比對(CLAUDE.md 常駐檢查項、F-087)。

**委派的 HEAD 是 submodule 自己的 HEAD**,不是 parent 記錄的那個 gitlink sha。
理由:紅燈紀錄的 `impl_hash` 取自工作樹,而工作樹的內容跟著 submodule 的 HEAD 走;
parent 的指標只在有人 bump 時才動,拿它當錨會讓「submodule 內已提交、parent 還沒 bump」
這個**最常見的中間狀態**永遠對不上 —— 那正是本票要修掉的失效。

## 紅燈計畫

| # | 紅燈 | 守什麼 |
|---|---|---|
| 1 | `head_blob("sub/thing.py")` 取得 submodule 已提交的內容 | 委派存在 |
| 2 | submodule 內既有檔案取得**合格紅燈**(`redlight_missing` 回 `None`) | 本票主張(正控) |
| 3 | **負控**:委派後仍讀不到(檔案不在 submodule 的 HEAD)→ 照擋 | 「讀不到」不得變放行 |
| 4 | **負控**:submodule 的 `.git` 壞掉/不見 → 照擋 | 同上,fail-closed 不靠運氣 |
| 5 | **負控**:紅燈對著改動**後**的內容 → 照擋 | 自我服務路徑仍關著 |
| 6 | **回歸**:一般目錄(mode `040000`)不得被當成 gitlink | 枚舉只認 160000 |

第 3、4 條是本票最重要的部分:**修法本身是「多一條讀取路徑」,
而多一條路徑最便宜的寫法就是失敗時放行。** 少了這兩條,本票會把一個
「永遠擋」的缺陷換成一個「永遠放行」的缺陷,而後者測試全綠、訊息什麼都不說。

## 註記(**不在本票範圍**)

**權威層對 submodule 內 staged 檔案零涵蓋**:parent 的 pre-commit hook 看不到
submodule 內的 staged 檔案(它只列 parent 的索引),而 submodule 自己的 hook
目前只跑 `leak_scan`。所以本票修好之後,submodule 底下的 R3 仍然**只有前哨**這一層。

這是下游 `data-collector-full-gate` 票的完成定義缺口,不是本票的。
寫在這裡是為了讓它有出處 —— **「沒有入口」與「我沒去造入口」是兩件事**,
這一條屬於後者:可以做,本票刻意沒做,理由是範圍。

## 怎樣算做完

- 上表六條各有測試;**1、2 先紅**(那是本票要修的東西)
- 3–6 修法前就是綠的 —— 現行實作對整個 submodule 一律擋,負控當然過。
  **綠不等於它們沒有用**:它們守的是「修法被寫成失敗時放行」那個方向,
  所以要用一次**故意寫錯的修法**確認它們會紅,否則這四條只是裝飾
- `head_blob` 的委派是**唯一**新增的讀取路徑,失敗一律回 `None`
- friction 記一則 `F-088`:F-0013 假設 `git show HEAD:` 必定讀得到,未預期 gitlink
- ADR `F-0013` 原地加註,指向本票

## 落地紀錄(2026-08-15)

**紅燈先行**:`TestGitlinkPathsCanReachAQualifyingRedlight`,
紅燈紀錄 `ticket_id: "41"`、`impl_hash: 856fdfd0…`,與 `.claude/hooks/gate.py`
在 HEAD 的內容雜湊相同(即紅燈發生在改動之前)。

```
2 failed, 4 passed        ← 修法前(紅 1、紅 2)
6 passed                  ← 修法後
760 passed / 0 failed / 3 skipped / 3 xfailed   ← 全套
```

### 負控真的會咬 —— 用故意寫錯的修法量過

把委派失敗那一行暫時改成「退回讀工作樹」(最便宜、最可能被寫出來的錯):

```
FAILED …::test_a_file_absent_from_the_submodule_head_is_still_blocked
FAILED …::test_a_broken_submodule_does_not_open_the_gate
2 failed, 4 passed
```

改回 fail-closed 後 6 passed。**沒有這一步的話,3–6 一路綠著,
而「它們會不會咬」與「它們是裝飾」在測試輸出上長得一模一樣。**

### 判定用 mode 枚舉,不讀 `.gitmodules`

`GITLINK_MODE = "160000"`,`is_gitlink()` 比對 `git ls-tree HEAD -- <前綴>` 的首欄。
tree mode 是封閉集合(`040000` / `100644` / `100755` / `120000` / `160000`),
所以枚舉;`.gitmodules` 可能缺席、可能過期,拿它當來源就是
**以錯的來源決定可見範圍**(F-019 的形狀)。

### fixture 的兩個坑,寫下來

1. **不用 `git submodule add`**:git 2.38+ 預設擋 file:// submodule
   (`protocol.file.allow`),那條限制與本票無關卻會讓 fixture 因為別的理由壞掉。
   改用 `git update-index --add --cacheinfo 160000,<sha>,sub` 直接種一格,
   產出的 mode 與 `submodule add` 相同。fixture 自己斷言那一格真的是 `160000` ——
   **fixture 壞掉要當場出聲**,否則「測試綠了」可能只代表它測了一個沒有 gitlink 的 repo。
2. **不用 `shutil.rmtree` 砍 `.git`**:Windows 上 git 的物件檔唯讀,
   直接 `PermissionError`(實測)。改成 `os.rename` —— 而且那更像真實情形:
   **未 init 的 submodule 就是「目錄在、工作樹在、`.git` 不在」**。
   紅得不對的測試等於沒有測試。
