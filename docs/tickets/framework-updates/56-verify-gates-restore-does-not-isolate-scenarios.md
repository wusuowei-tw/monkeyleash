# 票 56:verify_gates 的 restore() 不隔離情境,而它的註解說它會

**狀態**:實作中
**發現於**:2026-08-17,B 案第 0 步的補查輪(唯讀盤點 verify_gates 這一層時)
**前置**:票 54(裝 CI)、票 45(規則清冊)

---

## 頭條:`restore()` 清不掉自己宣稱要清的東西

`scenario_r4` 刪掉 `target/.claude/skills/tdd/SKILL.md` 來製造 R4 違規。
`restore()` 是:

```python
    sh(["git", "reset", "-q", "--hard", "HEAD"], target)
    sh(["git", "clean", "-qfd"], target)
```

鏡像目錄被 `.gitignore` 忽略 ⇒ `git reset --hard` 不管它、`git clean -fd`(不帶 `-x`)
也不管它 ⇒ **那個刪除永久留著**。

而該函式自己的註解寫的是:

> `git clean -fd` 不帶 -x:鏡像目錄被 .gitignore 忽略,帶了 -x 會把它們清掉,
> 下一條規則就在一個殘缺的 repo 上跑 —— 那會讓失敗的原因變成上一條情境。

註解防住了「鏡像被**整個**清掉」那一種殘缺,**漏掉了「鏡像**內**被刪一個檔」那一種**
—— 而那正是 `scenario_r4` 自己造的。這是 F-036 那一族:**註解描述了一個機制沒有的性質。**

## 證據(2026-08-17 唯讀實測)

全新安裝、單次執行,跑到 R5 那一步時 commit 的輸出:

```
[六站閘門/pre-commit] commit 已擋下,1 項違規:
  [R4][enforce] 鏡像缺少 .claude/skills/tdd/SKILL.md —— 正典有而鏡像沒有。
```

那筆 R4 違規的來源只可能是**同一次執行裡前一步的 `scenario_r4`**。

## 後果:連言退化成單言

`run_scenario` 的判定是一個連言(verify_gates.py:164):

```python
    blocked = rc != 0 and ("[%s]" % code in out or "[%s/" % code in out)
```

`scenario_r4` 之後的每一條走 commit 的情境(R5 / R6 / R8),
**`rc != 0` 那一半由殘留白送** —— 真正在做事的只剩 `"[Rx]" in out`。

**目前不產生錯判**(第二個連言項救了它),但這是「讀起來在驗兩件事、實際只驗一件」
的形狀,而本專案已經為這個形狀付過三次錢。已偵測到的洞擱置就是留在原地(docs/adr/0003)。

## 要做什麼(四筆 commit)

| # | 內容 |
|---|---|
| C1 | 本票立案 + 回歸測試紅燈先行 |
| C2 | 修 `restore()` |
| C3 | verify_gates 接進 CI 全套 + 落差表加一列 + CI 接線斷言 |
| C4 | R7 heredoc 那筆 friction(單獨一筆,不與測試混批) |

C2 原本還要把 `.claude/portable/verify_gates.py` 移出 legacy 豁免清單。
**已裁決不做** —— 理由見下面「紅燈途中發現的另一件事」。

### C2 的兩個條件(裁決給定,缺一不可)

1. **不得用 `git clean -x`** —— 註解已明說那會把鏡像整個清掉,那是換一個**更大**的殘缺。
   要用**重建**:`install.build_mirrors(target)`(它 rmtree + copytree,兩個鏡像一起重建)。
2. **必配回歸測試**,斷言「`scenario_r4` 跑完 target 是乾淨的」。
   不配的話同一件事會再長回來。

### C3 為什麼要加 `test_verify_gates_is_wired_into_ci`

那個 CI 步驟日後被拿掉**不會有東西叫**。不加的話,本票做的事本身就是同一個
缺陷家族的**第四個實例** —— 前三個是:verify_gates 不在 CI、
mutation_check 不指閘門、內層 hook 不進版控。

## 紅燈途中發現的另一件事:排水那條路在機制上是關著的

本票的紅燈順帶產出一筆**對既有檔案合格**的紅燈紀錄
(`impl_exists: true`,`impl_hash` 與 HEAD 逐字相同)。照 gate.py 寫的出口
「補測試 → 從清單移除」,`verify_gates.py` 這時應該可以退出豁免清單。**實測不行。**

兩條測試都用 `redlight_missing(stem)` 呼叫,**沒傳 `impl_rel`**,
於是 gate.py 的 `head = head_content_hash(impl_rel) if impl_rel else None` 讓
HEAD 錨點分支永遠走不到 —— 對既有檔案而言,它們只認得 `impl_exists: false` 的紀錄,
而既有檔案照定義產不出那種紀錄。方向相反地把出口堵死:

| 測試 | 後果 |
|---|---|
| `test_no_entry_still_holds_a_qualifying_redlight_record` | 看不見排水 ⇒ 不會逼人移除 |
| `test_the_list_is_what_the_generator_would_produce` | 移除後判成「沒有合格紅燈可以解釋」⇒ 轉紅,禁止移除 |

實測(帶不帶 `impl_rel` 的差別):

```
redlight_missing('verify_gates')                                    -> 有執行紀錄,但沒有任何一筆…(不合格)
redlight_missing('verify_gates', impl_rel='.claude/portable/verify_gates.py') -> None(合格)
```

附帶:前者那條測試的 docstring 說走不通的理由是「檔案還在就產不出那種紀錄」——
**那個理由現在是假的**,`impl_hash` 錨點分支存在的目的正是讓既有檔案排得了水。
docstring 描述的是那次修復之前的世界,誤診了自己的缺陷。

**閘門本身沒事**:`check()` 呼叫時**有**傳 `impl_rel`,所以就算移除清單那行,
R3 也判得出合格紅燈,不會把檔案鎖死。堵路的純粹是那兩條測試。

**本票不修它。** 這是一個獨立缺陷(偵測器的呼叫點關掉了自己一半的判斷),
有自己的紅燈需求,混進本票會讓一組紅綠燈同時服務兩個缺陷。
**已登記,處置另裁。**

## 驗收

- [ ] `tests/test_verify_gates.py` 先紅後綠,紅燈留在歷史上
- [ ] `restore()` 不含 `git clean -x`
- [ ] `scenario_r4` 跑完,鏡像檔回得來
- [ ] CI 跑 verify_gates 全套,且有測試守住那個步驟還在
- [ ] 票 54 的落差表多一列,並註明由本票加入

## 本票不做的事

- **不接「只跑規則驗證那 9 秒」的省時版**。那 70 秒的巢狀 pytest 驗的是
  「安裝後的形態也綠」,與 CI 現有的「原始碼形態」是不同維度、不重複。
  退路寫下但現在不做(痛點出現才加機制):時間變痛點就拆兩個 job,
  規則驗證每次跑、巢狀 pytest 只在 push to master 跑。
- **不補 R1/R5/load_stage 的正對照**。那些屬 B 案,順位在後,不混進本票。
- **不動票 55**。指標移開、票檔還在,本票收尾後指回去。
- **不修排水盲點,也不移除 legacy 清單那一行**。見上一節;已登記,處置另裁。
