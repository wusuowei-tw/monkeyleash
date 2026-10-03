# 票 145 Station 5f 獨立審查報告

審查者:獨立、無記憶的審查者(未參與任何實作;未讀任何本機對話紀錄)。
全文以 `<TARGET>` 代表 `ad14418d903b26212dc9e98754f44aaa894375c8`。行號一律為 TARGET 上的行號。
pytest / pluggy 引用寫 `_pytest/<檔名>:<行號>`;Python 標準庫引用寫 `Lib/<檔名>:<行號>`(本機 Python 3.11 安裝,不照錄絕對路徑)。

## 0. 身分(S5f-0、TARGET、包 blob、包 SHA-256 —— 第 0 步原文)

- S5f-0 = `695909f2f22ec17f97d4609f3fd28a5d146f252d`
- TARGET = `ad14418d903b26212dc9e98754f44aaa894375c8`
- 審查包 = `docs/audits/2026-10-03-m1a-station5f-review-package.md`

第 0 步原文(各自單獨執行):

```
$ git status --porcelain
(無輸出)

$ cat .dev/pipeline.json
{
  "current_stage": "review",
  "feature": "framework-updates",
  "ticket_id": "145",
  "updated": "2026-10-02"
}

$ git rev-parse 695909f2f22ec17f97d4609f3fd28a5d146f252d:docs/audits/2026-10-03-m1a-station5f-review-package.md
a5821b099b8b8d0c6c626297348ecc8682255150

$ git hash-object docs/audits/2026-10-03-m1a-station5f-review-package.md
a5821b099b8b8d0c6c626297348ecc8682255150

$ sha256sum docs/audits/2026-10-03-m1a-station5f-review-package.md
f254a9d7278e1cbdfb50d67443ac1014bdaa5094d0db000e2d5e9b2eb6e5c385 *docs/audits/2026-10-03-m1a-station5f-review-package.md
```

判定:五項全部相符(工作樹乾淨;`current_stage = review`、`ticket_id = "145"`;blob 兩者皆 `a5821b09…8255150`;SHA-256 `f254a9d7…6e5c385`)。

## 1. 判決

**PASS**

- 阻擋 0 項
- 非阻擋 3 項(S5f-F1、S5f-F2、S5f-F3)
- **附帶聲明**:S5f-F1(logging 擷取選項 `--log-level` / `--log-disable` 等不在合約內)我判為非阻擋,理由是 TARGET 目前已提交的設定下,它能翻盤的情形全部落在已裁決的 scope 外 S-3。**但它與 (xvi) pytest `-W` 的納入理由同形**(3e-0 的 O-3 以「已提交設定若有 `error::X`,CLI 會蓋過它」納入合約,即使本 repo 當時實際能翻的也只有 S-3 類)。若裁決者以 O-3 / (xvi) 的同一標準看待它(與 S5e-F1 以 (xvii) 標準看待 `--pdb` 同型),本判決應改為 **FAIL**。判斷依據寫在 S5f-F1 的「為什麼判非阻擋」。

## 2. 必答題 G1–G12

### G1 (xix) usepdb 的強制、型別檢查、唯一 "true" 出口、usepdb_cls —— **成立**

**強制位置(TARGET)**
- 收集:`<TARGET>:.claude/hooks/redlight.py:462-467`(`COMPLETENESS_OPTIONS` 末項 `"usepdb"`,第 467 行);producer 依此逐鍵讀 `config.option`:`<TARGET>:tests/conftest.py:369-370`(`_plain(getattr(option, k, None))`,屬性不存在 ⇒ `None`)。
- 型別:`<TARGET>:.claude/hooks/redlight.py:716-717`(`options` 缺任何 `COMPLETENESS_OPTIONS` 鍵 ⇒ problem);`:752-755`(`runxfail` / `trace` / `usepdb` 必須 `isinstance(..., bool)`)。
- 判定:`<TARGET>:.claude/hooks/redlight.py:787-788`(有 problem ⇒ `"unknown"`);`:812-813`(`options["usepdb"] is not False` ⇒ `"unknown"`)。

**型別檢查逐項推演(全部在 `_completeness_problems` 內 fail-closed)**

| 輸入 | producer 落帳 | `:752-755` | 結果 |
|---|---|---|---|
| 缺欄(option 無 `usepdb` 屬性) | `None`(`conftest.py:369-370`;`_plain(None)` 回 None,`:312-313`) | `isinstance(None, bool)` 假 ⇒ problem | `:787-788` unknown |
| `None` | `None` | 同上 | unknown |
| 字串 `"False"` | `"False"`(`_plain` 原樣,`:312-313`) | 非 bool ⇒ problem | unknown |
| int `0` / `1` | `0` / `1` | `isinstance(0, bool)` 為假 ⇒ problem | unknown |
| 手寫 dict 缺 `usepdb` 鍵 | — | `:716-717` 先命中;`:753-755` `options.get` 回 None 再命中 | unknown |
| `True` | `True` | 通過 | `:812-813` unknown |
| `False` | `False` | 通過 | 繼續往下 |

附註:R2 的兩個破壞組(`[missing]`、`[str]`)即使型別檢查只寫在 verdict 層(`is not False`)也會通過,因此 R2 無法區分「型別防線在 problems 層」或「只在 verdict 層」。這不是缺陷 —— TARGET 兩層都有(`:752-755` 與 `:812-813`),兩種寫法也都 fail-closed。

**唯一 "true" 出口**:對 `.claude/` 全部 `*.py` Grep `return "true"` 只命中 `<TARGET>:.claude/hooks/redlight.py:833`。`file_coverage` 只在 `:443-444` 經 `_completeness_verdict` 回傳;status 的退紅 / orphan / green 只在 `rl.file_coverage(run, f) == "true"` 時進行(`<TARGET>:.claude/portable/status.py:456-458`)。(xix) 位於 `:812-813`,在 `:833` 之前,沒有繞過路徑。

**usepdb_cls(pytest 9.1.1 原始碼)**
- `--pdbcls` 的 dest 為 `usepdb_cls`(`_pytest/debugging.py:49-56`),型別轉換只做字串切分、**不 import**(`_pytest/debugging.py:30-38`)。
- `pytest_configure` 只在 `trace` 為真時註冊 `PdbTrace`、只在 `usepdb` 為真時註冊 `PdbInvoke`(`_pytest/debugging.py:68-71`);`usepdb_cls` 不參與。
- `usepdb_cls` 唯一的讀取點是 `_import_pdb_cls`(`_pytest/debugging.py:117`),它只被 `_init_pdb` 呼叫(`:272`)。`_init_pdb` 的呼叫者只有三個:
  1. `pytestPDB.set_trace`(`:279-283`)—— 只有在**被執行的程式碼**呼叫 `pdb.set_trace()` / `breakpoint()` 時才會到(`:76` 把 `pdb.set_trace` 換成它)⇒ 屬 H 段 P-1 殘餘「被執行的程式碼自己叫出 debugger」。
  2. `wrap_pytest_function_for_tracing`(`:316`)—— 由 `PdbTrace`(只在 trace 時註冊,`:68-69`)或 `maybe_wrap_pytest_function_for_tracing`(`:330-334`,以 `trace` 為閘;呼叫點 `_pytest/unittest.py:382-387`)觸發。
  3. `post_mortem`(`:399-404`)—— 由 `_enter_pdb`(`:364`)與 `PdbInvoke.pytest_internalerror`(`:299-301`)觸發,兩者都屬於只在 `usepdb` 時註冊的 `PdbInvoke`。
- 其他看 debugger 狀態的點只讀 `usepdb`、不讀 `usepdb_cls`:`_pytest/runner.py:265`、`_pytest/unittest.py:402`、`_pytest/doctest.py:415`。
- ⇒ `usepdb=False`、`trace=False` 時,`usepdb_cls` 無法單獨啟動 debugger,也不改變執行;只會影響「被執行的程式碼自己叫出的 debugger 用哪個類別」(P-1)。〈四十一〉41.1 第 1 點的裁決理由成立。R5(`<TARGET>:tests/test_redlight.py:1991-2001`)鎖住這個語意。

### G2 防錯欄位 —— **成立**

- R3(`<TARGET>:tests/test_redlight.py:1960-1975`)與 R4(`:1977-1989`):option 來自 `_f_parse` = `pytestconfig._parser.parse_known_args(list(args))`(`:1889-1891`);`Parser.parse_known_args` 回傳真實 argparse namespace(`_pytest/config/argparsing.py:145-154, 156-179`)。namespace 交給 `_e_run`(`:1609-1621`)→ `_d_drive`(`:1243-` 起)→ `_isolated_conftest`(`:290-`)載入**真實** `tests/conftest.py`(`:177-182`,`spec_from_file_location(ROOT / "tests" / "conftest.py")`)→ 真實 `pytest_sessionfinish` / `_completeness_of`(`<TARGET>:tests/conftest.py:226-254, 345-389`)寫帳本。
- S2(`<TARGET>:tests/test_status.py:2794-2811`):`pytestconfig._parser.parse_known_args([u"--strict-markers", u"--pdb"])`(`:2801`)並斷言 `option.usepdb is True`(`:2802`);經 `_e_red_then`(`:2638-2645`)→ `_e_drive` → `_chain_conftest`(載入真實 conftest)→ `_t_drive`,再由 status 讀回。
- **欄位名寫錯而測試仍過?** 逐一推演三種錯法:
  1. `COMPLETENESS_OPTIONS` 寫成錯名(例 `use_pdb`):producer 對 `_COption` 與真實 namespace 都 `getattr` 不到 ⇒ `None` ⇒ `:752-755` problem ⇒ 所有 session unknown ⇒ R1 / R4 的對照組 `== "true"`(`test_redlight.py:1939, 1988`)失敗;R3 斷言持久化鍵 `usepdb` 為 True / False(`:1974-1975`)也失敗。
  2. `COMPLETENESS_OPTIONS` 正確、problems 檢查寫錯名:錯名的 `options.get` 回 None ⇒ 永遠 problem ⇒ 同上,對照組失敗。
  3. verdict 寫錯名(`options["use_pdb"]`):`KeyError` 從 `file_coverage` 拋出 ⇒ 測試以例外失敗。
  ⇒ 不存在「欄位名寫錯、這些測試仍全部通過」的情形。真實 dest 由 pytest 自己的 parser 決定,`usepdb` 的拼法由 R3 / R4 / S2 的 namespace 與 R3 的持久化斷言共同鎖住。

### G3 S5e-F2(乙):override value 的越界基準 —— **成立**(含一項非阻擋,見 S5f-F3)

- **一律以 root 為基準**:`<TARGET>:.claude/hooks/redlight.py:662-665`。
  - 非絕對值:`_root_relative(val, root)`(`:664`,不傳 base ⇒ `:565` `start = root`)。
  - 絕對值:`_root_relative(val, root, base)`(`:663`)雖傳 base,但 `_root_relative` 只有在「非本機絕對」時才用 base(`:566`),而「任一平台絕對、但非本機絕對」在 `:562-563` 已直接回 `<outside>`。⇒ 絕對值的結果與 base 無關。
  - ⇒ 「conftest 仍把 invocation dir 傳給 `normalize_overrides`(`<TARGET>:tests/conftest.py:378-379`)但結果與 base 無關」的說法**成立**。附帶觀察:Windows 上無磁碟代號的根相對路徑(例 `\x`)在 `:568` 的 `relpath` 內由 `abspath` 以**行程目前的磁碟**補全,這與 base 無關,也不會產生 root 相對以外的落帳(不是 `<outside>` 就是 root 相對路徑)。
- **與 pytest 9.1.1 的基準比較**:
  - `cache_dir`:`resolve_from_str(config.getini("cache_dir"), config.rootpath)`(`_pytest/cacheprovider.py:135-141`)⇒ rootpath。一致。
  - `paths` 型 ini:以 `self.inipath.parent` 為基準(無 inipath 時才用 invocation dir)(`_pytest/config/__init__.py:1786-1793, 1848-1853`)。能得 `"true"` 的 run 必須 `inipath == "pyproject.toml"`((x),`<TARGET>:.claude/hooks/redlight.py:799-800`),即 inipath.parent = root。一致。
  - 不一致的反例:`log_file`(ini / `-o`)以**行程 cwd** 解析(`_pytest/logging.py:683-692`,`os.path.abspath(log_file)`)。這使 docstring「pytest 解析 ini 的路徑值也不用 invocation dir」(`<TARGET>:.claude/hooks/redlight.py:653-655`)過度概括。判定與隱私皆不受影響,另列 S5f-F3(非阻擋)。
  - (1) 類維持以 invocation dir 解析:`inifilename`(`<TARGET>:tests/conftest.py:380-381` 傳 `inv_dir`)、`invocation.args`(`<TARGET>:.claude/hooks/redlight.py:214` 傳 `invocation_dir`)。與 41.1 第 3 點一致。
- **「正規化後恰好等於常數」而得 "true" 的輸入**:不存在。推演:
  1. (viii) 比較的是整個清單(`<TARGET>:.claude/hooks/redlight.py:795`),正規化逐項 1:1 映射(`:659-666`),不會增刪項目。
  2. 已提交 addopts 的 `--strict-markers`(`pyproject.toml:72`)是 `OverrideIniAction`(`_pytest/main.py:83-89`),addopts 在第二次解析前被併入 args(`_pytest/config/__init__.py:1559-1566`)⇒ 清單第一項恆為 `strict_markers=true`。任何 CLI / `PYTEST_ADDOPTS` 的 `-o` 都是**追加**一項 ⇒ 長度 ≥ 2 ⇒ 不等。
  3. 唯一能把 addopts 那一項拿掉的途徑是 `-o addopts=…`(`getini("addopts")` 會吃 override)—— 但那個 `-o` 自己就成為清單的一項(`addopts=…`)⇒ 不等;改 pyproject ⇒ (xi);`-c` ⇒ (ix)。
  4. 因此只有「清單恰為那一項、值為 `true`」才相等,而那就是固定全套本身。例:`-o strict_markers=<root>/true`(絕對路徑,正規化後為 `true`)只能**追加**,得 `["strict_markers=true", "strict_markers=true"]`,長度 2 ⇒ unknown。

### G4 S5e-F3:兩平台逐項推演 —— **成立**(含一項非阻擋,見 S5f-F2)

推演依據:`<TARGET>:.claude/hooks/redlight.py:545-548`(`_is_abs_path`)、`:551-574`(`_root_relative`);Python 3.11 的 `ntpath.isabs` 對以 `\` 或 `/` 開頭、或 `X:\` 形狀的字串一律判絕對(`Lib/ntpath.py:98-103`;第 100 行自註 LEGACY BUG)。
以 `normalize_config_path(value, root, root)`((1) 類)為準;POSIX root `/home/u/repo`、Windows root `C:\r\repo`(與 R11 / R12 的 root 相同)。

| 輸入 | POSIX 推演 | POSIX 結果 | Windows 推演 | Windows 結果 |
|---|---|---|---|---|
| `C:\x` | `ntpath.isabs` 真、本機非絕對 ⇒ `:562-563` | `<outside>` | 本機絕對;relpath `..\..\x` ⇒ `:572` | `<outside>` |
| `C:/x` | 同上 | `<outside>` | 同上 | `<outside>` |
| `D:rel` | `_DRIVE_PREFIX` 命中、本機非絕對 ⇒ `:562-563` | `<outside>` | `ntpath.isabs("D:rel")` 假 ⇒ 本機非絕對,`_DRIVE_PREFIX` 命中 ⇒ `:562-563` | `<outside>` |
| `\\server\share\x` | `ntpath.isabs` 真 ⇒ `:562-563` | `<outside>` | 本機絕對;relpath 跨 mount ⇒ `ValueError` ⇒ `:569-570` | `<outside>` |
| `\\?\C:\x` | 同 UNC | `<outside>` | 本機絕對;`:564` 換成 `//?/C:/x` 後 normpath 為 `\\?\C:\x`,與 `C:` 不同 drive ⇒ `ValueError` | `<outside>` |
| `/etc/x` | 本機絕對;relpath `../../../etc/x` | `<outside>` | `ntpath.isabs("/etc/x")` 真(3.11)⇒ 本機絕對;`abspath` 補行程磁碟,relpath 以 `..` 開頭或跨磁碟 | `<outside>` |
| `../../x` | join + normpath `/home/x` ⇒ `../../x` | `<outside>` | 同理 | `<outside>` |
| `sub/x` | | `sub/x` | | `sub/x` |
| 混用、不越界 `sub\y/z` | `:564` 先換成 `sub/y/z` | `sub/y/z` | | `sub/y/z` |
| 混用、越界 `a\..\..\..\u\c` | 非絕對;`:564` ⇒ `a/../../../u/c` ⇒ normpath `/home/u/c`… relpath `../../u/c` | `<outside>` | `ntpath` 原本就認 `\`;同結果 | `<outside>` |
| 跨磁碟 `D:\x` | 同 `C:\x` | `<outside>` | relpath `ValueError` | `<outside>` |
| root 內絕對 | `/home/u/repo/sub/x` ⇒ `sub/x` | `sub/x` | `C:\r\repo\sub\x`(大小寫不敏感)⇒ `sub/x` | `sub/x` |

- **兩平台是否一致**:除「本機才可能在 root 內的絕對路徑」(先天依平台而異)外,同一輸入在兩平台結果相同;越界值兩平台都是 `<outside>`,不再出現 S5e-F3 的分歧。
- **反斜線替換的位置是否改變「他平台絕對」判定**:不改變。`:561-563` 以**原字串**判定,`:564` 才替換。替換後才可能變成 POSIX 絕對的字串只有「以 `\` 開頭」者,而它們在 3.11 的 `ntpath.isabs` 已為真(`Lib/ntpath.py:101`),早在 `:562-563` 回 `<outside>`。
- **非阻擋發現**:`:564` 只換**值**、不換 **root**(`:568` 的 `os.fspath(root)` 未替換)。POSIX 上 root 路徑本身含 `\` 時,固定全套的 inipath 與 root conftest 都被判成 `<outside>` ⇒ 永遠 unknown。見 S5f-F2。
- **未證明**:`ntpath.isabs` 在 3.11 以外版本的行為我沒有讀原始碼。在 `KNOWN_PYTHON_VERSIONS` 之外的直譯器上,(xviii) 會讓判定為 unknown(`:808-809`),但正規化(隱私)不受 (xviii) 管;那些版本上的落帳形狀未推演。
- 參考:C.3 的 POSIX 外部驗證(22 個案例 passed)與上表一致,但本題結論以上面的紙上推演為據。

### G5 S5e-F4:`_IDENTIFIER` 整串比對 —— **成立**

- `<TARGET>:.claude/hooks/redlight.py:542`:`re.compile(r"[A-Za-z0-9_.\-]+")`;`:587`:`_IDENTIFIER.fullmatch(name)`。`fullmatch` 要求整串符合,`"abc\n"` 不符 ⇒ `:589` `<non-identifier>`;`"abc"` 原樣;數字 id 原樣;空字串因 `+` 不符 ⇒ `<non-identifier>`(與修正前相同)。
- **kind 判定不受影響**:`classify_plugins` 以原始名稱判 `is_path`(`:609`)、以 plugin 物件判 dist 配對(`:611-613`)與定義模組(`:617-620`);`shown`(`:610`)只寫進落帳的 `name`(`:621`)。
- **(vii)** 只看 `kind`(`:789-790`);**(xii)** 只看 `comp["blocked"]` 是否非空(`:791`),而 `blocked_plugins` 是逐項映射、長度不變(`:633-634`)。⇒ 對 (vii) / (xii) 無影響。

### G6 測試沒有被放寬 —— **成立**

- `git diff --stat <S3F2> <TARGET>`:測試檔只有 `tests/test_redlight.py | 1 +`、`tests/test_status.py | 6 ++-`。
- `git diff -U0 <S3F2> <TARGET> -- tests/test_redlight.py tests/test_status.py` 恰為 4 個 hunk(原文見第 5 節):
  1. `@@ -772,0 +773 @@ _C_OPTION_DEFAULTS`:`+ "usepdb": False,` ⇒ `<TARGET>:tests/test_redlight.py:773`
  2. `@@ -587 +587,2 @@`(`TestTestsUnderTicketUsesTheLatestRecordPerFile` 的手寫 completeness)⇒ `<TARGET>:tests/test_status.py:587-588`
  3. `@@ -1360 +1361 @@`(`TestOrphans` 的手寫 completeness)⇒ `<TARGET>:tests/test_status.py:1361`
  4. `@@ -1896,0 +1898 @@ _S_OPTION_DEFAULTS`:`+ "usepdb": False,` ⇒ `<TARGET>:tests/test_status.py:1898`
  與〈四十一〉41.1 第 6 點的授權逐項相符(兩個預設 dict 各一鍵、兩支手寫 dict 測試各補 `u"usepdb": False`),沒有任何 assertion、docstring、test identity 改動。
- **3f 新增的 36 支未改**:上述 4 個 hunk 都不在 3f 區段(`test_redlight.py` 3f 區段起於 `:1854`;`test_status.py` 起於 `:2736`)。另核:`git diff --stat <S3F1> <S3F2>` 只有 docs;`git diff --stat <5E_TARGET> <S3F1> -- tests .claude` 為 `418 insertions(+)`、0 刪除 ⇒ 3f 只新增測試。

### G7 13 支 behavior-red「為對的理由」轉綠 —— **成立**

| # | nodeid(簡) | TARGET 上讓它通過的條件 |
|---|---|---|
| R1 | `TestDebuggerModeCoverage::test_f3p_pdb_alone_is_not_full_coverage` | 破壞組 `usepdb=True` 型別合格 ⇒ `redlight.py:812-813` unknown;對照組全部條件成立 ⇒ `:833` |
| R2[missing] | `…::test_f3p_a_missing_or_malformed_usepdb_fact…[missing]` | producer 記 `None`(`conftest.py:369-370`)⇒ `redlight.py:753-755` problem ⇒ `:787-788` |
| R2[str] | `…[str]` | `"False"` 非 bool ⇒ `:753-755` ⇒ `:787-788` |
| R3 | `…::test_f3p_the_producer_records_usepdb_from_the_pytest_parser` | `COMPLETENESS_OPTIONS` 含 `usepdb`(`redlight.py:467`)⇒ producer 照 namespace 記 True / False(`conftest.py:369-370`) |
| R4 | `…::test_f3p_pdb_parsed_by_pytest_is_not_full_coverage` | 同 R1,經 pytest parser namespace;`:812-813` |
| R6 | `TestOverrideBaseCoverage::test_f3o_an_invocation_dir_outside…` | `true` 非絕對 ⇒ `redlight.py:664` 以 root 為基準 ⇒ `root/true` 在 root 內 ⇒ 原樣 |
| R7 | `…::test_f3o_the_fixed_command_from_the_parent_dir_is_full_coverage` | R6 + `_normalize_arg(<root 名>, root, 上一層)` ⇒ `.`(`redlight.py:196-205`)⇒ `:441` covering ⇒ `:795` 相等 ⇒ `:833` |
| R9 | `TestPlatformIndependentNormalization::…posix_semantics[override]` | `:564` 先換分隔符 ⇒ posixpath normpath 收合 `..` ⇒ `:572-573` `<outside>` ⇒ `:664-665` |
| R10 | `…posix_semantics[config-file]` | 同 R9 的 `_root_relative`(`:643` 經 `:564`、`:572-573`) |
| R14 | `TestIdentifierFullMatch::…trailing_newline…` | `:587` `fullmatch` 不符 ⇒ `:589` |
| S1 | `TestDebuggerModeChain::test_f3p_pdb_pass_does_not_retire_a_known_red` | R2 run `:812-813` unknown ⇒ `status.py:456-458` 不退紅、不 green |
| S2 | `…::test_f3p_pdb_parsed_by_pytest_does_not_retire_a_known_red` | 同 S1,namespace 來自 parser |
| S3 | `TestOverrideBaseChain::test_f3o_the_fixed_command_from_the_parent_dir_retires_the_red` | 同 R6 / R7 ⇒ `"true"` ⇒ `status.py:459-475` 退紅、green |

補充(非發現):S2 本身沒有同一支測試內的對照組;它「為對的理由」通過的證明來自紙上推演 —— parser namespace 含全部 `COMPLETENESS_OPTIONS` 鍵(`maxfail` 預設 0,`_pytest/main.py:67-75`;`pythonwarnings` 為 `append` 無預設 ⇒ None,`:122-127`;`lf` / `stepwise` 等由 cacheprovider / stepwise 註冊)、`override_ini == ["strict_markers=true"]`,其餘事實由 `_TConfig` / `_t_plugins` / `_t_committed` 給齊 ⇒ 唯一擋下條件是 `:812-813`。R4 以同一種 namespace 的對照組得 `"true"`(`test_redlight.py:1985, 1988`)佐證了這一點。

### G8 S5c-F2 同類關切:有沒有 `!= "true"` 的既有測試只靠 (xix) 通過 —— **無**

- 對 `tests/` Grep `usepdb`:把 `usepdb` 設為非 False 的只有 3f 測試(`test_redlight.py:1938, 1953, 1955, 1969, 1987`;`test_status.py:2786, 2801`)。
- 3c / 3d / 3e 的 producer 驅動測試,option 一律來自 `_COption`(`test_redlight.py:777-788`,預設含 `"usepdb": False`,`:773`)或 `_CompletenessOption`(`test_status.py:1902-1910`,預設 `:1898`);`_d_option` / `_e_option` / `_t_option` 都經這兩個類別(`test_redlight.py:1235-1240, 1602-1606`;`test_status.py:2455-2458, 2621-2625`)⇒ `usepdb` 為 False ⇒ `redlight.py:812` 不成立 ⇒ (xix) 不擋任何一支。
- 不帶完整 option 的 3b 舊型 helper(`_Option`,`test_redlight.py:436`;`_ChainOption`,`test_status.py:1476`)與手寫 `_c_all_off()` 都同時缺多個 4d / 4e 欄位(例:`optimize`、`python_version`、`override_ini`),`_completeness_problems` 在 `:716-717, 731-751` 就有多條 problem,少一個 `usepdb` 不是唯一理由。
- 與 F.1 5f 節的「論證一」一致;本題結論以上述行號推演為據。

### G9 執行模式盤點(重點題)—— **有一項新觀點(S5f-F1,非阻擋 / 請裁決);沒有找到合約內的新 false-green**

盤點方式:以 Grep 列出 `_pytest/` 全部 `addoption` / `_addoption` / `add_option_ini`,逐項問兩個問題:(1) 能否讓人或模式本身在執行途中改變行程狀態;(2) 能否讓一個在固定全套下失敗的斷言變成 passed,而 TARGET 仍判 `"true"`。對照 3e-0(`<TARGET>:docs/audits/2026-10-03-m1a-station3e-redlight-plan.md:89-149`)與 3f-0 複查(`<TARGET>:docs/audits/2026-10-03-m1a-station3f-redlight-plan.md:100-138`)的結論,但不沿用其理由,逐項重推。

**A. 會翻盤、且 TARGET 判 "true" 的選項**

| 選項 | 機制(pytest 9.1.1) | 現行歸屬 | 我的判斷 |
|---|---|---|---|
| `--log-level` / `--log-disable` / `--log-cli-level` / `--log-file-level` | `--log-level` 設 caplog handler 的層級(`_pytest/logging.py:673, 828-843, 349-352`),低於它的紀錄不交給 handler(`Lib/logging/__init__.py:1705`);`--log-disable` 直接 `logger.disabled = True`(`_pytest/logging.py:724, 726-732`);`--log-cli-level` / `--log-file-level` 把 root logger 調低(`:367-371, 793-795, 814-816`),原本被濾掉的 INFO / DEBUG 進入 caplog。四者都不是 `OverrideIniAction`(`:239-243, 245-332`),也不在 `COMPLETENESS_OPTIONS`(`redlight.py:462-467`) | O-17 ⇒ S-3(scope 外,〈三十五〉35.1 第 6 點) | **S-3 的前提(「依賴環境預設值」)只在已提交設定沒有 `log_level` 時成立,而 TARGET 沒有機制守住這個前提**;與 (xvi) 的納入理由同形。見 **S5f-F1** |
| `-s` / `--capture=no` | 預設 `fd` 擷取時 `sys.stdin` 為 `DontReadFromInput`,讀取即拋 `OSError`(`_pytest/capture.py:222-231, 369-371, 488-490, 712-714`);`-s` 時 `in_=None`(`:59-65, 717-718`),stdin 是真的終端機 ⇒ 被執行的程式碼呼叫 `input()` 時,人可以在執行中輸入答案,讓固定全套下會拋錯的測試通過 | 3f-0 已複查(`3f-redlight-plan.md:114`),歸 P-1(H 段) | 同意歸 P-1(觸發途徑只有被執行的程式碼自己讀 stdin)。不另列 |
| `--import-mode` / `PYTHONPATH` / `-P` 等 | 改變受測模組的解析來源(`_pytest/main.py:217-224`) | I-9 / I-6 族(41.1 第 5 點,H 段) | 同意。不另列 |
| `-p <模組>`(模組自改 `__name__ = "_pytest.x"`) | `_defining_module` 看模組 `__name__`(`redlight.py:524-531, 617-620`) | S5c-F4(P-1,H 段) | 現況未變。不另列 |
| `--ff` / `--nf` | 只重排(`_pytest/cacheprovider.py:485-500`);依測試間狀態洩漏才可能翻盤 | 3e-0 C-3 | 屬 S-2 / S-3 類(順序相依是測試實作品質);且位置參數的順序本來就不受合約約束(`redlight.py:432-442` 只問是否涵蓋)。不另列 |

**B. 已由合約鎖住、我重推後成立的**
- `--pdb`:(xix) `redlight.py:812-813`(見 G1)。`--trace`:(xvii) `:810-811`;unittest 路徑也以 `trace` 為閘(`_pytest/debugging.py:330-334`;`_pytest/unittest.py:382-387`)。
- `--pdbcls`:單獨無效(見 G1)。
- `--runxfail`(xv)、`-W`(xvi)、`-o` / `--strict*` / `-c` / 設定檔(viii)–(xi)、`-p no:`(xii)、pytest 版本(xiii)、`-O` / `PYTHONOPTIMIZE`(xiv)。
- `--sw-reset`:`pytest_configure` 把 `stepwise` 設為 True(`_pytest/stepwise.py:42-50, 53-56`)⇒ (ii) `redlight.py:816-818`。
- `-x` / `--maxfail`(預設 0,`_pytest/main.py:59-75`)⇒ (iii) `:819-821`。`--co` / `--setup-only` / `--setup-plan` ⇒ (iii)(vi)。
- `--max-warnings`:只會以錯誤結束(`_pytest/main.py:128-136`),不會讓失敗變通過。
- `--disable-plugin-autoload`:只會少掉 anyio,只會更嚴。
- `--confcutdir` / `--noconftest`:root conftest 不載入 ⇒ producer 不寫 run 事實 ⇒ 不退紅。

**C. 結論**:除 `--pdb`、`--trace` 外,能在合約內讓失敗變 passed 而 TARGET 判 `"true"` 的選項,全部落在已裁決的殘餘(P-1、I-9 / I-6、S-2、S-3)。唯一我認為裁決理由有缺口的是 logging 族:S-3 的理由在 TARGET 現行設定下成立,但它的前提沒有機制守住,且與 (xvi) 的納入標準不一致 —— 列為 S5f-F1。

### G10 scope 邊界 —— **成立**

- 未新增 assertmode 條件:`redlight.py` 中 `assertmode` 只出現在 docstring(`:776`);`_completeness_verdict`(`:786-833`)沒有對應判斷。
- 未帶入 `sys.warnoptions`:對 `redlight.py`、`tests/conftest.py` Grep `warnoptions` 無命中。
- `validate_session` 未改:`git diff --stat <5E_TARGET> <TARGET> -- .claude/hooks/redlight.py` 為 `21 insertions(+), 8 deletions(-)`,與 E.3 的 4f hunk 相同;各 hunk 位於 `:462`、`:535`、`:554`、`:584`、`:646 / :661`、`:750`、`:774`、`:809`,都不在 `validate_session`(`:297-360`)。
- `usepdb_cls` 未納入:`COMPLETENESS_OPTIONS`(`:462-467`)沒有它;理由成立(見 G1)。
- I-9 / I-6 族未半套處理:TARGET 沒有任何受測物件來源 / provenance 欄位(`_completeness_of` 的鍵見 `conftest.py:368-387`)。
- S5e-F6 未半套處理:override 的 key 仍原樣(`redlight.py:660, 666`);`pythonwarnings` 仍原樣(`conftest.py:309-316, 369-370`)。

### G11 隱私與欄位邊界 —— **成立**

- 新欄位 `options.usepdb` 只能是 bool / None / 型別名字串(`conftest.py:309-316`),不帶路徑。
- 正規化後欄位((1) 類 inipath / inifilename / conftest 名稱;名稱欄位 plugins[].name / blocked[];(2) 類 override value)只可能是 root 相對 posix 路徑、`<outside>`、`<non-identifier>`、或原樣的非路徑 / root 內相對值(`redlight.py:551-574, 582-589, 637-643, 646-667`)。絕對值一律轉成 root 相對或 `<outside>`。
- (2) 類非絕對值:以 root 為基準越界 ⇒ `<outside>`;不越界則原樣保留。保留下來的是使用者輸入的相對字串,不含絕對路徑。
- 獨立核對(以 Read / Grep 唯讀,材料不取自 4f 報告):
  - 以本機使用者名稱(遮為 `<user>`)對 `.dev/test-*.jsonl` 做不分大小寫 Grep count ⇒ `No matches found`、`Found 0 total occurrences across 0 files.`
  - `"usepdb": (true|false)` 只在帳本第 21 行出現,值為 `false`。
  - 第 17–21 行的 `override_ini` 皆為 `["strict_markers=true"]`、`inifilename` 皆為 `null`、`inipath` 皆為 `"pyproject.toml"`、`blocked` 皆為 `[]`;全帳本沒有 `"kind": "other"`。
- 〈二十五〉裁決 1 的 (2) 類(nodeid 等身分)不在本次改動範圍,未變。
- 殘餘:S5e-F6(key、`pythonwarnings`)依 H 段不重列。

### G12 既往修正未退步 —— **成立**

先確認範圍:`<5E_TARGET>..<TARGET>` 之間,`status.py` 與 `tests/conftest.py` 無差異(`git diff --stat` 無輸出);`redlight.py` 只有 4f 的 hunk,且刪掉的 8 行全是被取代的行(`COMPLETENESS_OPTIONS` 的結尾、註解、`_IDENTIFIER`、`.match`、docstring、`elif`、`for key in`),沒有移除任何判定條件。

| 既往缺陷 | TARGET 上仍成立的證據 |
|---|---|
| Station 5 F1(schema fail-closed) | `redlight.py:297-360`;status 不合格即 return(`status.py:429-431`) |
| F2(D 無退紅權) | `redlight.py:384-385`;`status.py:456` 的 `state == u"D"` |
| F3(coverage authority) | `redlight.py:395-447`;唯一 `"true"` 在 `:833` |
| F4(串接) | `status.py:456-475` 只在 `file_coverage == "true"` 時退紅 / orphan / green |
| S5b-F1(選擇 / 執行完整性) | (ii) `:816-818`、(v) `:826-828`、(vi) `:829-832`;縮小前快照 `conftest.py:295-306` |
| S5c-F1(收集定義被單次覆寫) | (viii) `:795-796`、(ix) `:797-798`、(x) `:799-800`、(xi) `:801-804`;producer `conftest.py:378-383` |
| S5d-F1 / S5d-X1(assert 未執行) | (xiv) `:806-807`;producer 在呼叫當下讀 `sys.flags.optimize`(`conftest.py:319-326, 385`);型別 `:748-749` |
| S5e-F1(`--pdb`) | (xix) `:812-813`、`:752-755`、`:467` |
| S5e-F2 | `:664` |
| S5e-F3 | `:564` |
| S5e-F4 | `:542`、`:587` |

## 3. 發現清單

### S5f-F1【非阻擋(請裁決)】logging 擷取選項(`--log-level` / `--log-disable` / `--log-cli-level` / `--log-file-level`)能讓失敗的斷言變成 passed,TARGET 仍判 `"true"`;歸 S-3 的前提沒有機制守住,且與 (xvi) 的納入標準不一致

**證據行**
- `<TARGET>:.claude/hooks/redlight.py:462-467`:`COMPLETENESS_OPTIONS` 沒有 `log_level`、`logger_disable`、`log_cli_level`、`log_file_level`。
- `<TARGET>:.claude/hooks/redlight.py:786-833`:verdict 沒有對應條件 ⇒ 其他條件成立時 `:833` 回 `"true"`。
- `<TARGET>:pyproject.toml:70-80`:已提交的 `[tool.pytest.ini_options]` 沒有 `log_level`(只有 `testpaths`、`addopts`、`markers`、`filterwarnings`)。
- `<TARGET>:docs/audits/2026-10-03-m1a-station3e-redlight-plan.md:109`(O-17)與 `:148`(S-3 明列「斷言 `caplog` 為空」);`:95`(O-3:`-W` 因「已提交設定若有 `error::X`(下游 repo 常見)」而判 B,並註明「TARGET 已提交的 filter 只有 `ignore::DeprecationWarning`,本 repo 實際能翻的只有 S-3 類」)。
- `<TARGET>:docs/audits/2026-10-03-m1a-station3f-redlight-plan.md:129`:3f-0 複查 O-17,結論「成立;只影響依賴環境的斷言(S-3)」,沒有討論已提交 `log_level` 的情形。
- pytest 9.1.1:
  - `_pytest/logging.py:239-243, 245-255`:`--log-level` 是一般 `store` 選項(dest `log_level`),同時註冊同名 ini;不是 `OverrideIniAction` ⇒ 不進 `override_ini`。
  - `_pytest/logging.py:627-633`:`get_log_level_for_setting` **先讀 CLI 值**(`config.getoption`),為 None 才讀 ini ⇒ CLI 會蓋過已提交的 `log_level`。
  - `_pytest/logging.py:673, 828-843`:caplog handler 在每個測試階段以 `level=self.log_level` 進入 `catching_logs`;`:349-352` 設定 handler 層級。
  - `Lib/logging/__init__.py:1705`:`if record.levelno >= hdlr.level:` 才交給 handler。
  - `_pytest/logging.py:326-332, 724, 726-732`:`--log-disable=<name>` ⇒ `logging.getLogger(name).disabled = True`,整個 session 有效(`Lib/logging/__init__.py:1738`)。
  - `_pytest/logging.py:367-371`:`catching_logs` 把 root logger 調到 `min(原層級, level)`;`--log-cli-level` / `--log-file-level` 在 `runtestloop` 期間包住全部測試(`:814-816`)⇒ 原本被 root WARNING 濾掉的 INFO / DEBUG 進入 caplog。

**紙上推演(情境一:現行設定,S-3 類)**
1. `tests/test_x.py::test_quiet(caplog)`:呼叫 `impl.run()`(內含 `logging.getLogger("impl").warning("deprecated path")`),斷言 `caplog.records == []`。
2. R1 固定全套 `python -X utf8 -m pytest -q`:`log_level` 為 None ⇒ `catching_logs(..., level=None)` 不改 handler 層級(`:351`)⇒ WARNING 紀錄被擷取 ⇒ 斷言失敗 ⇒ 已知紅。
3. R2 `python -X utf8 -m pytest -q --log-level=ERROR`:handler 層級 40(`:673, 351-352`)⇒ 30 < 40,不交給 handler(`Lib/logging/__init__.py:1705`)⇒ `caplog.records == []` ⇒ **passed**。
4. 完整性事實:`override_ini == ["strict_markers=true"]`、plugins 全是 builtin / root_conftest / anyio(logging plugin 定義在 `_pytest.logging`)、optimize 0、3.11、runxfail / trace / usepdb False、pythonwarnings None、其餘選項關閉 ⇒ `redlight.py:833` **`"true"`** ⇒ `status.py:459-475` 退紅並 green。
5. 同一結果也可由 `--log-disable=impl` 達成;反方向(斷言某個 INFO 紀錄**存在**,固定全套下因 root WARNING 而失敗)可由 `--log-cli-level=INFO` 或 `--log-level=INFO` 翻成 passed。

**紙上推演(情境二:已提交 `log_level`,不在 S-3 的理由內)**
- 若 `pyproject.toml` 提交 `log_level = "INFO"`(例:之後某一票要讓 caplog 擷取 INFO),上面的 `test_quiet` 在固定全套下依**已提交設定**失敗。`--log-level=ERROR` 經 `:627-633` 蓋過已提交的 ini,而它既不在 `override_ini`((viii) 看不到),也不在 `COMPLETENESS_OPTIONS` ⇒ `"true"`。
- 這與 O-3 / (xvi) 是同一種形狀:**CLI 選項蓋過已提交的 ini 設定,讓「依已提交設定會失敗」的測試通過**。差別只在 (xvi) 被納入合約,logging 族沒有。
- (xi) 只要求工作樹 = HEAD(`redlight.py:801-804`),所以「提交 `log_level`」這個變更本身不會觸發任何重新盤點;(viii) 有鎖步測試對照 addopts(`<TARGET>:tests/test_redlight.py` 的 `test_d4_…`),`log_level` 沒有。

**預期 vs 實際**
- 預期(依〈三十五〉35.1 第 2 點「passed 未因 pytest execution mode 失去通常的 pass 語意」,以及 (xvi) 的同一標準):改變擷取層級的 run 不得退紅。
- 實際:情境一、二都判 `"true"` 並退紅。

**為什麼判非阻擋**
- TARGET 符合已裁決的合約:〈三十五〉35.1 第 6 點把 S-3 列為 scope 外,而 3e-0 的 S-3 明列「斷言 `caplog` 為空」。在 TARGET 已提交的設定下(沒有 `log_level`),所有能翻盤的情形都是情境一,屬 S-3。
- 情境二需要先提交一個 `log_level`,TARGET 現在不存在這個狀態。
- 依 CLAUDE.md 的分流判準(「不改會不會讓別的規則失效」):現在不改,沒有任何現行規則失效;但情境二出現時,(xvi) 守的那一類輸入會從 logging 這個旁門繞過。

**要裁決的事(三個選項)**
- **A(建議)**:納入 M1-a。新增 (xx):`log_level`、`log_cli_level`、`log_file_level` 為 None,且 `logger_disable` 為空 list(缺欄或型別錯 ⇒ 不得為 `"true"`)。producer 讀得到(`config.option` 的四個 dest),成本與 (xix) 相同。代價:再走一輪 3g / 4g / 5g;用 `--log-cli-level` 除錯的 run 也不能退紅。選 A ⇒ 本判決改為 **FAIL**。
- **B**:維持 S-3,但把前提變成機制:新增一支鎖步測試,讀 `git show HEAD:pyproject.toml`,斷言 `[tool.pytest.ini_options]` 沒有 `log_level` / `log_cli_level` / `log_file_level`(做法同 D4)。代價:一支測試;提交 `log_level` 時會紅並逼出重新盤點。不改產品碼。本判決維持 PASS(B 可在追蹤票做)。
- **C**:只記追蹤票,不加機制。代價:情境二發生時沒有任何東西會出聲(CLAUDE.md「祈使句沒有主詞」那一型)。本判決維持 PASS。

**未證明**:純紙上推演,沒有實際執行。「下游 repo 常提交 `log_level`」我沒有查證,不據以判斷。

### S5f-F2【非阻擋】POSIX 上 root 路徑本身含 `\` 時,固定全套永遠 unknown(4f 引入;與 4f 報告第 7 節第 3 點「判定不受影響」的敘述不符)

**證據行**
- `<TARGET>:.claude/hooks/redlight.py:564`:只把**值**的 `\` 換成 `/`。
- `<TARGET>:.claude/hooks/redlight.py:568`:`os.path.relpath(os.path.normpath(full), os.path.normpath(os.fspath(root)))` —— root **沒有**替換。
- `<TARGET>:.claude/hooks/redlight.py:572-573`:結果以 `../` 開頭 ⇒ `<outside>`。
- 受影響的呼叫點(都把含 root 的絕對路徑交給 `_root_relative`):
  - inipath:`<TARGET>:tests/conftest.py:382`(`normalize_config_path(cfg.inipath, _ROOT)`)⇒ (x) `redlight.py:799-800`。
  - root conftest 的註冊名稱:`<TARGET>:.claude/hooks/redlight.py:614-615`(`_plugin_path_name` ⇒ `:577-579`)⇒ kind `other` ⇒ (vii) `:789-790`。
- `_ROOT` 取自 conftest 自己的位置(`<TARGET>:tests/conftest.py:130`),含 root 路徑上的原字元。

**具體輸入與推演**
- POSIX,repo 放在 `/home/u/a\b/`(目錄名 `a\b`,POSIX 合法)。執行固定全套。
- inipath = `/home/u/a\b/pyproject.toml`:`:561` 本機絕對;`:564` ⇒ `/home/u/a/b/pyproject.toml`;`:568` relpath 對 `/home/u/a\b` ⇒ 共同前綴 `/home/u` ⇒ `../a/b/pyproject.toml` ⇒ `:572-573` `<outside>`。
- root conftest 名稱 `/home/u/a\b/tests/conftest.py` 同理 ⇒ `<outside>` ≠ `tests/conftest.py` ⇒ kind `other`。
- ⇒ `:789-790` 先命中 ⇒ `"unknown"`;固定全套在這台機器上永遠無法退紅。

**預期 vs 實際**
- 預期(5E_TARGET 的行為,也是 4f 以前):沒有 `:564` 這一行,relpath 直接得 `pyproject.toml` 與 `tests/conftest.py` ⇒ 其他條件成立時 `"true"`。
- 實際:`"unknown"`。
- 4f 報告第 7 節第 3 點(本包 H.1)寫「POSIX 上檔名本身含 `\` 的合法路徑會被當成 `/` 分隔落帳。判定不受影響:`-c` 由 (ix)、override 由 (viii) 一律 unknown」。這只涵蓋「值」含 `\`;**root 路徑含 `\` 時,判定受影響的是固定全套本身**((vii)、(x)),不是 `-c` 或 override。

**影響與判定**
- 方向是 fail-closed(只會無法退紅,不會假綠);隱私不受影響(落帳是 `<outside>`)。
- 觸發需要 repo 位於名稱含 `\` 的 POSIX 目錄,極少見。判非阻擋。
- 建議追蹤:對 root 做同樣的替換(或 root 與值都不替換、改在 relpath 之後再以 `posixpath.normpath` 收合),並更正 4f 報告該點的敘述(依 F-036 慣例在新紀錄更正,不回寫)。

**未證明**:純紙上推演,沒有實際執行。

### S5f-F3【非阻擋】`normalize_overrides` 的 docstring 對 pytest 的敘述過度概括:「pytest 解析 ini 的路徑值也不用 invocation dir」

**證據行**
- `<TARGET>:.claude/hooks/redlight.py:653-655`:「pytest 解析 ini 的路徑值也不用 invocation dir(`cache_dir` 用 rootpath)」。
- 反例 `_pytest/logging.py:683-692`:`log_file`(ini 或 `-o log_file=…`)以 `os.path.abspath(log_file)` 解析,基準是**行程 cwd**(= invocation dir)。
- 正例(敘述成立的部分):`_pytest/cacheprovider.py:135-141`(`cache_dir` 用 rootpath);`_pytest/config/__init__.py:1786-1793`(`paths` 型用 inipath 所在目錄)。

**具體輸入**:從 root 的上一層執行 `pytest -q agent-gates -o log_file=agent-gates/../x.log`。
- TARGET:以 root 為基準 ⇒ `root/agent-gates/../x.log` = `root/x.log`,在 root 內 ⇒ 原樣落帳 `log_file=agent-gates/../x.log`(`redlight.py:664`)。
- pytest:以 cwd 為基準 ⇒ 寫到 `root/x.log`(同一個位置,本例一致);若值為 `../x.log`,TARGET 判 `<outside>`,pytest 寫到 cwd 的上一層 —— 兩者基準不同。

**影響**:沒有判定影響(多一個 override ⇒ (viii) 必為 unknown,`redlight.py:795-796`);沒有隱私影響(保留下來的是使用者輸入的相對字串,不含絕對路徑)。屬註解準確度。建議改為「`cache_dir` 用 rootpath、`paths` 型用 inipath 所在目錄;其他字串型(例 `log_file`)以 cwd 為準,但它們一律被 (viii) 判 unknown,這裡只管隱私」。

## 4. 對 H 段已知例外的意見

沒有我認為應改為阻擋的項目。

說明:S5f-F1 涉及 H 段的「scope 外 S-3」。我**沒有**主張把 S-3 本身改為阻擋 —— 情境一確實符合 S-3 的理由。S5f-F1 指出的是 S-3 理由之外的情境二(已提交 `log_level` 被 CLI 蓋過),以及它與 (xvi) 納入標準的不一致;是否因此改判,依第 1 節的附帶聲明由裁決者決定。

## 5. 審查過程紀錄

**讀過的內容**
- 審查包全文 7100 行(分段讀完:A–D、E.1 全部、E.2、E.3、F.1、F.2、G、H)。
- TARGET 範圍檔(先以 `git diff --stat <TARGET> <S5f-0> -- <五檔>` 確認無差異、`git rev-parse HEAD` = S5f-0,再用 Read 讀工作樹,行號即 TARGET 行號):
  - `.claude/hooks/redlight.py:140-834`
  - `tests/conftest.py` 全檔
  - `.claude/portable/status.py:425-494`
  - `tests/test_redlight.py`:`:177-182, 290-296, 760-800, 1140-1260, 1560-1640, 1850-2145`
  - `tests/test_status.py`:`:1891-1916, 2415-2480, 2621-2645, 2680-2859`
- `pyproject.toml`(`git show <TARGET>:pyproject.toml`;並確認 TARGET 與 S5f-0 之間無差異)。
- `docs/audits/2026-10-03-m1a-station3e-redlight-plan.md:86-149`、`docs/audits/2026-10-03-m1a-station3f-redlight-plan.md:100-138`(先確認兩檔在 TARGET 與 S5f-0 之間無差異);以 Grep 查 `docs/` 中 `__name__` / 冒充 / stdin / log 相關段落(用來確認 S5c-F4、O-16、O-17 是否已裁決,避免重報)。
- pytest 9.1.1(Read / Grep):`_pytest/debugging.py:1-405`、`_pytest/runner.py:240-284`、`_pytest/main.py:50-299`、`_pytest/logging.py:225-345, 344-388, 388-490, 620-880`、`_pytest/stepwise.py:1-90`、`_pytest/capture.py:48-72, 215-254, 362-386, 464-503`(另 Grep)、`_pytest/config/argparsing.py:121-180`、`_pytest/config/__init__.py:1512-1581, 1760-1859`(另 Grep)、`_pytest/cacheprovider.py`(Grep)、`_pytest/` 全目錄 `addoption` Grep。pluggy:未讀(本次判斷用不到)。
- Python 3.11 標準庫:`Lib/ntpath.py:87-103`(另 Grep)、`Lib/logging/__init__.py`(Grep `:1690, 1705, 1734, 1738`)。
- 帳本(唯讀 Grep,不寫入):`.dev/test-*.jsonl` 的使用者名稱計數;`.dev/test-sessions.jsonl` 的 `usepdb`、`override_ini`、`inifilename`、`inipath`、`blocked`、`"kind": "other"`。

**執行過的指令(依序;每條單獨送出)**
```
git status --porcelain
cat .dev/pipeline.json
git rev-parse 695909f2f22ec17f97d4609f3fd28a5d146f252d:docs/audits/2026-10-03-m1a-station5f-review-package.md
git hash-object docs/audits/2026-10-03-m1a-station5f-review-package.md
sha256sum docs/audits/2026-10-03-m1a-station5f-review-package.md
python -m pip show pytest
python -m pip show pluggy
git diff --stat ad14418d903b26212dc9e98754f44aaa894375c8 695909f2f22ec17f97d4609f3fd28a5d146f252d -- .claude/hooks/redlight.py .claude/portable/status.py tests/conftest.py tests/test_redlight.py tests/test_status.py
git rev-parse HEAD
git diff --stat 2f6743fff2f13170b27c52c3390a69cc361dfe26 ad14418d903b26212dc9e98754f44aaa894375c8
git diff -U0 2f6743fff2f13170b27c52c3390a69cc361dfe26 ad14418d903b26212dc9e98754f44aaa894375c8 -- tests/test_redlight.py tests/test_status.py
git diff --stat 229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5 2f6743fff2f13170b27c52c3390a69cc361dfe26
git diff --stat 0139a7e803fc2d41eb354f1196a6206cfe304701 229b5e762f087193e138c7c8d0f0d0b0f3e5cbb5 -- tests .claude
git diff --stat 0139a7e803fc2d41eb354f1196a6206cfe304701 ad14418d903b26212dc9e98754f44aaa894375c8 -- .claude/portable/status.py tests/conftest.py
git diff --stat 0139a7e803fc2d41eb354f1196a6206cfe304701 ad14418d903b26212dc9e98754f44aaa894375c8 -- .claude/hooks/redlight.py
git show ad14418d903b26212dc9e98754f44aaa894375c8:pyproject.toml
git diff --stat ad14418d903b26212dc9e98754f44aaa894375c8 695909f2f22ec17f97d4609f3fd28a5d146f252d -- pyproject.toml
git diff --stat ad14418d903b26212dc9e98754f44aaa894375c8 695909f2f22ec17f97d4609f3fd28a5d146f252d -- docs/audits/2026-10-03-m1a-station3e-redlight-plan.md docs/audits/2026-10-02-m1a-station5c-independent-review-fail.md
```

關鍵輸出(原文):
```
$ python -m pip show pytest
Name: pytest
Version: 9.1.1
…
Location: C:\Users\<user>\AppData\Local\Programs\Python\Python311\Lib\site-packages
…
$ python -m pip show pluggy
Name: pluggy
Version: 1.6.0
…
(Location 同上,已遮罩;其餘欄位省略 —— 以上兩段不是逐字全文)

$ git diff --stat ad14418d… 695909f2… -- <五檔>
(無輸出)
$ git rev-parse HEAD
695909f2f22ec17f97d4609f3fd28a5d146f252d

$ git diff --stat 2f6743ff… ad14418d…
 .claude/hooks/redlight.py                          | 29 +++++++---
 .../145-m1a-run-level-evidence-correctness.md      | 62 ++++++++++++++++++++--
 tests/test_redlight.py                             |  1 +
 tests/test_status.py                               |  6 ++-
 4 files changed, 85 insertions(+), 13 deletions(-)

$ git diff -U0 2f6743ff… ad14418d… -- tests/test_redlight.py tests/test_status.py
diff --git a/tests/test_redlight.py b/tests/test_redlight.py
index bb8bab9..877b131 100644
--- a/tests/test_redlight.py
+++ b/tests/test_redlight.py
@@ -772,0 +773 @@ _C_OPTION_DEFAULTS = {
+    "usepdb": False,
diff --git a/tests/test_status.py b/tests/test_status.py
index 74c986d..05e0c67 100644
--- a/tests/test_status.py
+++ b/tests/test_status.py
@@ -587 +587,2 @@ class TestTestsUnderTicketUsesTheLatestRecordPerFile:
-                             u"runxfail": False, u"pythonwarnings": None, u"trace": False},
+                             u"runxfail": False, u"pythonwarnings": None, u"trace": False,
+                             u"usepdb": False},
@@ -1360 +1361 @@ class TestOrphans:
-                                                 u"trace": False},
+                                                 u"trace": False, u"usepdb": False},
@@ -1896,0 +1898 @@ _S_OPTION_DEFAULTS = {
+    "usepdb": False,

$ git diff --stat 229b5e76… 2f6743ff…
 docs/audits/2026-10-03-m1a-station3f-redlight.md   | 234 +++++++++++++++++++++
 .../145-m1a-run-level-evidence-correctness.md      |  28 ++-
 2 files changed, 259 insertions(+), 3 deletions(-)

$ git diff --stat 0139a7e8… 229b5e76… -- tests .claude
 tests/test_redlight.py | 293 +++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_status.py   | 125 +++++++++++++++++++++
 2 files changed, 418 insertions(+)

$ git diff --stat 0139a7e8… ad14418d… -- .claude/portable/status.py tests/conftest.py
(無輸出)

$ git diff --stat 0139a7e8… ad14418d… -- .claude/hooks/redlight.py
 .claude/hooks/redlight.py | 29 +++++++++++++++++++++--------
 1 file changed, 21 insertions(+), 8 deletions(-)

$ git diff --stat ad14418d… 695909f2… -- pyproject.toml
(無輸出)
$ git diff --stat ad14418d… 695909f2… -- <兩份 docs>
(無輸出)
```
(上段指令中以 `…` 縮寫的 SHA 是本報告的排版縮寫;實際執行的指令一律用完整 SHA,見上方指令清單。)

**規則遵守與偏離(照實記錄)**
- **偏離一**:`python -m pip show pytest` 與 `python -m pip show pluggy` 兩條指令在同一回合**平行送出**,違反「不得平行送出」。兩條都是唯讀查詢,輸出不受彼此影響;之後所有指令都逐條送出。
- **說明二**:執行了一次 `git rev-parse HEAD`,用途只是確認工作樹的 HEAD 就是 S5f-0,以便用 Read 讀工作樹並引用 TARGET 行號;所有證據查詢仍以完整 SHA 為錨點。
- 未執行 pytest(含 `--collect-only`、`--version`);未用 `python -c`、heredoc、或任何把程式碼放進指令字串的寫法;未用 Bash 寫任何檔案。
- 未修改 repo 內任何檔案、未 commit、未 push、未改 `.dev/pipeline.json`。唯一寫入的檔案是本報告(以 Write 工具寫到 `.scratch/m1a-s5f/review-report.md`)。
- 未讀任何本機對話紀錄(transcript)。
- 沒有被任何閘門擋下。
- 照錄的路徑已把本機使用者名稱遮成 `<user>`。
