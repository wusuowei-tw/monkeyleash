# 票 100:`status` 在 idle 時對 `test-runs` 行印出**錯的宣稱**;Sync Health 的「末筆」不是水位線

**狀態**:**implement**(2026-09-02 落地,見第十一節;裁決乙有半句未實作,見十一之三)
~~**狀態**:**candidate**(2026-09-02 立案)~~(F-036 體例:舊行不刪)

**立案**:票 99 收票後的唯讀偵察(2026-09-02)。兩件都在 `status.py`,兩件都不是「算不出來」,
而是**算出了一個東西然後貼上一個它配不上的標籤**。

**來源票根**:本 repo `50251de`(偵察時的 HEAD,工作樹乾淨)

---

## 一、缺陷 / 動機

兩件,分甲乙。**共同形狀:判準 4(「算不出寫未記錄」)在這兩處失守,而失守的方式不是印錯值,
是印了一個正確的數字配一個錯的名字。**

| | 一句話 | 為什麼比「印不出來」糟 |
|---|---|---|
| **甲** | `pipeline.json` 沒有當前票時,`test-runs` 行把**整本 7956 行帳本**每個檔的最新一筆算進去,然後標成「**本票**(每檔最新一筆)red N / green M」 | 「未記錄」讀的人會去查;**一個帶著票面語氣的數字,讀的人會直接引用**。而 `status` 的用途正是給沒看過這個 repo 的人貼 |
| **乙** | Sync Health 的 `upstream commit` 取 `.dev/provenance.jsonl` 的 `recs[-1]` —— **檔案位置上的最後一行**,而憑證是**逐檔發**的:一次同步會寫入 N 筆,不同 path 可以帶不同 commit。末筆只代表「最後一個被寫進去的 path」 | `behind` 那一格由它推導。**一個由單一 path 決定的距離,被印成整個 repo 的落後量** |

**兩件都通過現有全部測試。** 這不是測試寫壞了 —— 是**沒有任何一支測試站在這兩個位置上**(見第八節)。

---

## 二、甲的根因(逐字)

**守衛短路。** `.claude/portable/status.py:271-285`:

```
def _latest_per_file(runs, ticket):
    """這張票底下,**每個測試檔的最新一筆**。回傳 `{檔: 紀錄}`。
    ...
    """
    out = {}
    for rec in runs or []:
        if ticket and rec.get("ticket_id") != ticket:
            continue
        f = rec.get("test_file")
        if f:
            out[f] = rec
    return out
```

`if ticket and ...` —— **`ticket` 是 falsy 的時候整個 `continue` 分支永遠不會執行**,
於是「這張票底下」變成「全部」,而函式名與 docstring 都還宣稱前者。

**同一支檔案裡,同一個問題有兩式並存。** 這是本票最要緊的一句:

| 位置 | 守衛 | idle 時印什麼 |
|---|---|---|
| `_evidence` `:434-453` | `if runs is None:` | 全帳本的數字,標籤寫**「本票(每檔最新一筆)red N / green M」** |
| `_derived` `:605-618` | `if runs is None or not ticket:` | `未記錄`,而且欄名也改成 `tests red under ticket 未記錄` |

`_evidence` 那段原文:

```
    run_log = _p(gate, "RUN_LOG")
    runs = _read_jsonl(run_log) if run_log else None
    if runs is None:
        val = UNRECORDED
    else:
        latest = _latest_per_file(runs, ticket)
        red = len([r for r in latest.values() if r.get("result") == "red"])
        green = len([r for r in latest.values() if r.get("result") == "green"])
        last = runs[-1] if runs else None
        tail = (u"最後一筆 %s=%s @ %s" % (_field(last, "test_file"),
                                          _field(last, "result"),
                                          _field(last, "time"))
                if last else UNRECORDED)
        val = u"本票(每檔最新一筆)red %d / green %d;%s;全套結果:%s(帳本不記全套)" % (
            red, green, tail, UNRECORDED)
```

`_derived` 那段原文:

```
    run_log = _p(gate, "RUN_LOG")
    runs = _read_jsonl(run_log) if run_log else None
    if runs is None or not ticket:
        red = green = UNRECORDED
    else:
        latest = _latest_per_file(runs, ticket)
        ...
    out.append(_line(u"tests red under ticket %s" % (ticket or UNRECORDED), red, src))
    out.append(_line(u"tests green under ticket %s" % (ticket or UNRECORDED), green, src))
```

**差一個 `or not ticket`。** 兩處的 `ticket` 同源 —— `render()` 裡 `stage, ticket = _stage_of(gate)`,
同一個值分別傳給 `_evidence(root, gate, ticket)` 與 `_derived(root, gate, stage, ticket)`。

**修在哪一層要先講清楚,因為這決定它會不會再犯**:
`_derived` 是**呼叫端**擋住的,`_latest_per_file` 自己沒有立場。
於是**下一個呼叫它的人會再踩一次**,而那個人不會知道要補守衛 ——
函式的名字與 docstring 都在跟他保證已經篩過了。

**本票的現況**:`pipeline.json` 現在就是這個狀態(`"current_stage": "idle"`、`"ticket_id":null`),
所以這個缺陷**此刻正在發生**,不是假設。

---

## 三、帳本裡「空票號」的四種形態(數字表)

`.dev/test-runs.jsonl`,全帳本,未抽樣:

| 形態 | 寫法 | 行數 |
|---|---|---|
| 空字串 | `"ticket_id": ""` | **1** |
| **字串** `null` | `"ticket_id": "null"` | **65** |
| JSON 空值 | `"ticket_id": null` | **364** |
| **欄位不存在** | (整行沒有 `ticket_id`) | **191** |
| | **小計** | **621** |

交叉數(**一份清單不會帶著它自己的長度**,所以把總和寫出來):

```
grep -c '"ticket_id"'      .dev/test-runs.jsonl   =  7765 行
grep -c -v '"ticket_id"'   .dev/test-runs.jsonl   =   191 行
wc -l <                    .dev/test-runs.jsonl   =  7956 行
grep -c '^$'               .dev/test-runs.jsonl   =     0 行
```

**7765 + 191 = 7956 ✓**(單位是**行**,一行一筆 JSON;`grep -c` 數的是行不是筆)。
有值的票號 50 個,7765 − 1 − 65 − 364 = **7335 行**帶真票號。

**這四種形態對甲的修法沒有影響**:`rec.get("ticket_id") != ticket` 在**有票**時對四者一律不相等,
行為一致;問題全部出在**無票**那條路上。四形態本身是另一件事,列在第七節「不做」。

---

## 四、乙的根因(逐字)

**憑證是逐檔發的,而 `recs[-1]` 是位置不是時間。**

`sync.py:556-592`,`write_provenance` 一次迴圈寫 N 筆,每筆四個欄位:

```
        out.append({
            "path": rel,
            "upstream_path": rel,
            "upstream_commit": commit,
            "content_hash": file_hash(os.path.join(src, rel.replace("/", os.sep))),
        })
```

**四個欄位裡沒有 `time`,沒有批次號,沒有 `sync` 版本。** 追加寫入:

```
    with io.open(p, "a", encoding="utf-8", newline="\n") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
```

`status.py:677-681` 取末筆:

```
        prov = os.path.join(down, ".dev", "provenance.jsonl")
        recs = _read_jsonl(prov)
        sha = _field(recs[-1], "upstream_commit") if recs else UNRECORDED
        out.append(_line(u"%s upstream commit" % tag, sha,
                         u"%s 末筆" % prov.replace("\\", "/")))
```

**來源欄寫的是「末筆」,不是「最新」—— 那一格是誠實的,本票不指控它。**
問題在**下一行**:`behind` 由這個 sha 推導,而那個數字被讀成整個下游的落後量。

`sync.py` 一側同時要記的兩件事:

1. **`write_provenance` 只對 `in_commit(src, commit, rel)` 為真的檔案發證**,
   所以同一批裡有些 path 會被跳過 —— **N 筆不等於這一輪同步的檔案數**。
2. `status.py` 對 `.dev/provenance.jsonl` **只讀不寫**(判準:對下游零寫入),
   本票的修法必須維持這一點。

**現有測試為什麼接不住**:`tests/test_status.py:526` 的 `TestSyncHealth._pair` fixture
**只寫一筆** provenance:

```
            ".dev/provenance.jsonl": json.dumps(
                {"path": "x", "upstream_path": "x",
                 "upstream_commit": sha or head, "content_hash": "z"}) + "\n",
```

**單筆時「末筆」與「水位線」恰好同義,分不出差別。**
六支 `TestSyncHealth` 測試全部建立在這個 fixture 上。

---

## 五、裁決甲

三件一起,缺一件就還是會再犯:

1. **`_latest_per_file(runs, ticket)` 在 `ticket` 為 falsy 時回 `{}`**(fail-closed)。
   修在**函式自己**,不是修在呼叫端 —— 呼叫端的守衛救不了下一個呼叫者,
   而函式的名字會繼續對他撒謊。
2. **`_evidence` 的守衛改成與 `_derived` 同式**(`if runs is None or not ticket:`)。
   兩式並存本身就是缺陷:**同一個問題在同一支檔案裡有兩種答案時,
   讀的人會以為那是刻意的區別。**
3. **無票時 `test-runs` 行的值印「未記錄(無當前票)」,且值裡不得出現「本票」二字。**
   括號裡那句是**判準 4 的完整形態**:不只說「我算不出」,還說「為什麼算不出」——
   前者讀的人會去查檔案在不在,後者他直接知道要去切票號。

**`(1)` 與 `(2)` 不是同一件事的兩種寫法**:`(1)` 之後 `_evidence` 拿到的會是空 dict,
`red = green = 0`,於是它會印「本票…red 0 / green 0」—— **一個看起來像全綠的謊**。
所以 `(2)` `(3)` 必須同輪落地。

---

## 六、裁決乙

**保留現有的「末筆」行,不刪。** 它是一個誠實的觀測,而刪掉一個觀測換一個新的,
會讓「本來印什麼」在事後查不到。**加一行**,不是換一行。

新的 `waterline` 行,規則:

1. **每個 `path` 取它最新的一筆憑證**(同 path 後寫的蓋前寫的,與 `_latest_per_file` 同一個
   「追加式帳本問最新」的形狀),再把這些憑證的 `upstream_commit` **去重**,得到 N。
2. **N == 1** ⇒ `waterline` 印那個 sha;**`behind` 用它算**。
3. **N > 1** ⇒ `waterline` 印那 N 個 sha;**`behind` 印「未記錄(N 個不同 commit,未收齊)」**。
   —— **不挑一個。** 挑哪一個都是猜,而猜出來的距離長得跟量出來的一模一樣。
4. **N == 0**(讀不到 / 空檔)⇒ 沿用現有的 `未記錄`。
5. **`DEAD_SHA` 的判定對 `waterline` 做**,不對末筆做 —— 現有那行
   `_git(upstream, ["cat-file", "-e", "%s^{commit}" % sha])` 的對象換成 waterline 的 sha。
   N > 1 時逐個判,**任一個死掉就印死** —— 票 59 講的正是「一批一起死」。

**為什麼 N > 1 不是異常而是常態的可能形狀**:憑證逐檔發、追加不覆蓋,
下游若曾經**部分同步**(有些檔案 `ask` 桶要人決定、有些檔案上游未提交而被跳過),
帳本裡就會同時躺著兩個以上的 commit,**而那正是「這個下游同步到哪」答不出來的真實狀態**。
印 N 個 sha 是**把那個狀態說出來**,不是拒絕回答。

---

## 七、**不做**

| | 不做的事 | 為什麼 / 去哪 |
|---|---|---|
| **B** | **四種空票號形態的收斂**(寫入端 `conftest` 統一寫法 + 既有 7956 行帳本回填) | 體積是另一張票:要動寫入端**與**既有資料,而既有資料一動就要面對「追加式帳本可不可以改寫」。**轉 candidate,另立票** |
| | 票 59 的 (c)(`sync.py` 發證前先驗上一批還查得到) | **本票不碰 `sync.py` 的寫入端。** 乙只加讀取側的 waterline;票 59 管的是寫入側會不會出聲,兩者不互相取代 |
| | 下游 `.dev/provenance.jsonl` 的既有內容處置 | 票 59 已明寫「另裁」 |

### ⚠ 一則已作廢的證據,明寫

影音輪曾經有一則觀察:「`gate.py` 的錨點比末筆早 **12 刀**」。
**那則證據作廢** —— 它建立在「雜湊命中的那一刀就是持有該內容的那一刀」,
而 `git log -- <file>` 只列**改動該檔的刀**,命中的是**引入**該內容的那一刀;
內容會一直持續到下一次改動,所以命中的其實是一個**區間**,不是一個點。
**由「引入刀」與「末筆刀」相減得到的差值沒有意義。**

**本票的依據不是那則。** 乙的依據是**機制**:`write_provenance` 逐檔發證、
追加不覆蓋、四欄無時間戳 —— 這三件事在原始碼裡讀得到,不依賴任何一次量測。

(**記這一段的理由**:一則被推翻的證據若只是不再被提起,
下一個人會在別處重新引用它,而**它讀起來仍然像一個量出來的數字**。)

---

## 八、紅燈形狀(全部在 `tests/test_status.py`)

**三支,兩支帶負控。** 負控不是湊數:一支「永遠回未記錄」的實作在紅燈上長得跟正確的一樣。

### 甲-1 —— idle 時 `test-runs` 行不得帶票面語氣

- **佈置**:`pipeline.json` 為 `"current_stage": "idle"` / `"ticket_id": null`,
  `.dev/test-runs.jsonl` 裡放數筆帶真票號的紀錄(讓「不篩就會算到」成立)
- **斷言**:`render(root)` 的 `test-runs` 行,值**以「未記錄」開頭**,
  且值裡**不含「本票」**二字
- **為什麼要斷言「不含本票」而不只斷言「以未記錄開頭」**:
  只斷言開頭的話,一個印成「未記錄;本票 red 0 / green 0」的實作會過關

### 甲-2 —— `_latest_per_file` 自己就要 fail-closed

- **斷言**:`_latest_per_file(runs, None) == {}`
- **負控**:`_latest_per_file(runs, "99")` 的行為**不變** ——
  與現有 `TestTestsUnderTicketUsesTheLatestRecordPerFile` 同一組資料,
  紅轉綠的檔仍然算綠。**這一支是防止「修法把有票那條路一起關掉」**

### 乙-1 —— waterline 要能說出「未收齊」

- **佈置**:下游 `.dev/provenance.jsonl` 寫**兩筆、兩個不同 `path`、兩個不同 `upstream_commit`**
  (兩個都是上游真實存在的 commit,否則測到的是 `DEAD_SHA` 那條路)
- **斷言**:`waterline` 行印出 **2 個 sha**;`behind` 行印
  「未記錄(2 個不同 commit,未收齊)」
- **負控**:**兩筆、兩個不同 `path`、同一個 `upstream_commit`** ⇒
  `waterline` 印**那一個 sha**、`behind` 印**刀數**
- **為什麼負控在這裡是必須的**:沒有它的話,一個「永遠印未收齊」的實作會讓甲支測試綠,
  而那個實作把 Sync Health 整段變成裝飾

**現有測試的處置**:`TestSyncHealth._pair` 的單筆 fixture **不改**(六支現有測試靠它),
新增的兩個情境**自己造 fixture**。理由是票 99 十一之四那一族:
**改一個被六支測試共用的 fixture,受影響的不只是你正在看的那一支。**

---

## 九、時鐘

**MCP 前置。** 本票不做 MCP,但本票修的兩行是 MCP 會端出去的東西 ——
**一個會被機器讀走的錯宣稱,比一個給人讀的錯宣稱擴散得快**。

**「欄位兩週不動」的起算日 = 本票落地日。** 起算日寫在這裡,不靠記性:
沒有起算日的「兩週」是一句祈使句,而**祈使句沒有主詞**。

---

## 十、紅燈紀律

- **本票的紅燈記在本票號下** —— `.dev/test-runs.jsonl` 的 `ticket_id` 要是 `"100"`。
  票 99 第一節第二個標本就是這一格記錯的後果(章蓋在 82,而當時在做 98),
  而**本票的甲正是「那個欄位空著會怎樣」**。在這張票上把號蓋錯,
  等於在講這件事的同一份文件裡再犯一次。
- **動工前 `pipeline.json` 由 Jeff 切**(`current_stage` 與 `ticket_id`)。
  agent 不得自己改流程狀態檔 —— 那是被擋時的繞道動作之一。
- 本票在 `pipeline.json` 切好之前**只有這一個檔案落地**,不動任何原始碼。

---

## 十一、落地(2026-09-02)

**狀態改為 implement → 本節記實際發生的事。** `pipeline.json` 由 Jeff 切成
`("implement", "100")`,經 `gate.load_stage()` 驗讀確認(不自己 parse 那個檔:
自己 parse 讀到的是「我對那個檔的理解」,不是閘門看到的東西)。

### 十一之一、兩刀

| 刀 | sha | 內容 |
|---|---|---|
| 紅燈先行 | `c9a0992` | 只含 `tests/test_status.py`(+150 行,5 支測試) |
| 落地 | (本刀) | `status.py` + 本票面 |

**紅燈那一刀的實作雜湊逐字留存**,證明當時實作未動:

```
git show HEAD:.claude/portable/status.py | sha256sum
  = 2df2e6d2e44e998d9f9358f6739e3099b5aedb35838e0495a7b456c21a02bc32
```

`.dev/test-runs.jsonl` 裡 `"ticket_id": "100"` 的那筆紅燈,`impl_hash` 是**同一個值**。

紅燈實測 **4 failed / 1 passed**(1 passed 是甲-2 的負控,測現行行為,本輪不得改壞)。

### 十一之二、全套

| | 數字 |
|---|---|
| 基線(`7c7e22e`) | 1194 passed / 3 skipped / 3 xfailed |
| 本輪 | **1199 passed / 3 skipped / 3 xfailed** |
| 差 | **+5 passed** |

**差額說得出是哪五條**:本票新增的 5 支,逐名 ——
`test_idle_prints_unrecorded_not_this_ticket`、`test_no_ticket_returns_empty`、
`test_with_ticket_still_filters`、`test_two_commits_print_count_and_unrecorded_behind`、
`test_one_commit_prints_sha_and_behind`。

**基線與本輪之間只隔一刀 `50251de`,而那一刀 `--stat` 只動了一個 markdown 票檔
(43 insertions / 8 deletions,0 支測試)** —— 所以 +5 全部落在本票,沒有殘差。
(基準與被對的 commit 不同就先重算再談差異:這裡重算過了。)

### 十一之三、⚠ 裁決乙有**半句沒有實作**,明寫

第六節第 5 條的後半句「**N > 1 時逐個判,任一個死掉就印死**」——**未實作**。

現行行為:`N > 1` 直接印 `未記錄(N 個不同 commit,未收齊)`,
**不對那 N 個 sha 做 `cat-file -e`**。`DEAD_SHA` 只在 `N == 1` 這條路上判。

- **為什麼沒做**:本輪的實作規格明文寫的是「`N>1` 印未收齊」,而
  **沒有任何一支紅燈覆蓋「N>1 且其中一個死掉」**。
  沒有紅燈的行為寫進去,綠了也證不出它在做事。
- **代價**:一個「兩批未收齊、其中一批已被上游改寫掉」的下游,
  現在只會被告知「未收齊」,**不會被告知那批已經死了** —— 而票 59 講的正是那件事。
- **處置**:留給票 59 的 (c) 那一輪一起做(它本來就要處理「上一批還查得到嗎」),
  或另立票。**兩者都不做的話,這半句會停在票面上而沒有東西在管它。**

### 十一之四、登記:R7 把票面 markdown 切成寫入目標(**不主張嚴重度**)

立案那一輪用 `cat > <票檔> <<'EOF'` 寫票面,被 R7 擋下。擋下訊息列出的「寫入目標」是:

```
docs/tickets/framework-updates/100-status-lies-when-idle-and-sync-waterline.md、(引號或跳脫使目標無法可靠切分)、1**、1、`
```

後三個 —— **`1**`、`1`、`` ` `` —— 不是路徑,是票面內文裡的 markdown 粗體與反引號
被當成寫入目標解析出來的。

**這不是誤判,是照設計的動作。** 同一則擋下訊息自己寫著:

> **切分不認引號,也不認 heredoc 內文**:`<<'EOF'` 到 `EOF` 之間、
> 以及引號裡的每一個 `;` / `&&` / `||`,一樣會被切成一段。

以及:

> 從指令字串解析『寫到哪』解不完,而半套的解析器比零涵蓋更危險
> —— 零涵蓋你知道它是零。

**記在這裡的理由**:那句自承是一個一般命題,而這是它的一個現成標本。
出口(「內文用 Write 寫成檔案,再 `git commit -F`」)寫在擋下訊息裡,
本票兩刀都照走。攔截紀錄在 `.dev/intercepts-2026-09.jsonl`。

**不主張嚴重度,也不提出修法** —— 收窄那個解析器正是那句自承說不划算的事。
