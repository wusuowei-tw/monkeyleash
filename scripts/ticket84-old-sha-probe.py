# -*- coding: utf-8 -*-
"""票 84 §4-12 第 1 / 1' 條:舊 sha 存活探針。唯讀,只發 GET。

用法:
    python scripts/ticket84-old-sha-probe.py --mode auth --shas all   # 第 0 步 a 組
    python scripts/ticket84-old-sha-probe.py --mode anon --shas root  # 第 2a 步 秒級絆線
    python scripts/ticket84-old-sha-probe.py --mode anon --shas all --slice 1-55   # 4a' 第 1 批

**當天不得臨場改寫這支腳本。** 它進版控的理由就是這一句
(2026-08-30 乾跑:臨場把 `gh api` 換成直連 API 才把 236 條壓到 131s,
 而那種改寫發生在窗口開著的時候是最不該做的事)。

★ 端點選擇 —— 用 /commits/,不要用 /git/commits/(2026-08-30 實測):

    /repos/{o}/{r}/commits/{sha}       200 提交在
                                       422 repo 讀得到而提交不在   <- 要的是這個
                                       404 repo 讀不到 / 不存在
    /repos/{o}/{r}/git/commits/{sha}   404 提交不在
                                       404 repo 讀不到            <- 同碼,分不出來

「舊 sha 全 404」那個原始寫法與 /git/commits/ 的行為一致,而在 /commits/ 上
404 的意思是【repo 讀不到】—— 照原寫法跑會把「讀不到」讀成「通過」(F-134)。
"""
import argparse, collections, io, os, re, subprocess, sys, time
import urllib.request, urllib.error

REPO = "wusuowei-tw/monkeyleash"
ROOT = "45a8d16437cefe5c571b7cf3896937d3f083b458"   # 舊根,必含
CTRL = "91335c8e212d21230b03bd26acc04a7e87590f3c"   # 對應新 sha,正控
MAP  = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                    "docs", "audits", "2026-08-27-identity-rewrite-commit-map.txt")

THROTTLE  = 0.05
RETRY_MAX = 2
PROGRESS  = 60          # 每 60 條印一行 —— 2 分 12 秒沒有輸出時看起來像卡住,
                        # 而那是最容易手癢中斷的時刻(2026-08-30 乾跑發現)


def old_shas():
    rows = []
    for line in io.open(MAP, encoding="utf-8"):
        m = re.match(r"^([0-9a-f]{40}) ([0-9a-f]{40})$", line)
        if m:
            rows.append((m.group(1), m.group(2)))
    olds = [o for o, _ in rows]
    news = [n for _, n in rows]
    assert len(rows) == 236, "commit-map 資料列 %d != 236" % len(rows)
    assert len(set(olds)) == 236, "舊欄有重複"
    assert not [o for o, n in rows if o == n], "舊欄 == 新欄 出現了,期望要拆兩組"
    assert not (set(olds) & set(news)), "舊欄 ∩ 新欄 出現了(跨列碰撞),期望要拆兩組"
    assert ROOT in olds, "舊根不在舊欄裡"
    return olds


def get(url, token):
    hdr = {"Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    for attempt in range(RETRY_MAX + 1):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=hdr), timeout=20) as r:
                return r.status, {}
        except urllib.error.HTTPError as e:
            code, h = e.code, dict(e.headers)
        except Exception as e:
            code, h = "TIMEOUT/" + type(e).__name__, {}
        transient = (code == 429 or (isinstance(code, int) and 500 <= code < 600)
                     or isinstance(code, str))
        if transient and attempt < RETRY_MAX:
            time.sleep(2 ** attempt)
            continue
        return code, {k: v for k, v in h.items()
                      if k.lower().startswith(("x-ratelimit", "retry-after"))}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["auth", "anon"], required=True)
    ap.add_argument("--shas", choices=["all", "root"], required=True)
    ap.add_argument("--slice", dest="rng", default=None, metavar="N-M",
                    help="只取舊欄第 N 到第 M 條(1 起算,含兩端)。"
                         "依【檔案出現順序】切,不排序、不隨機、不去重、不挑選 —— "
                         "順序來自檔案本身,不來自跑的人。只對 --shas all 有效。")
    ap.add_argument("--head", default=None,
                    help="auth 模式的端點活性控:從 GitHub UI 手抄的 HEAD(F-152)")
    a = ap.parse_args(argv)

    token = None
    if a.mode == "auth":
        token = subprocess.run(["gh", "auth", "token"],
                               capture_output=True).stdout.decode().strip()
        if not token:
            print("!! 取不到 token"); return 2

    base = "https://api.github.com/repos/%s/commits/" % REPO

    # ---- 正控:不過就不准讀結果 ----
    print("== 正控 (%s) ==" % a.mode)
    ctrls = [("內容存活控 (map 新 sha)", CTRL)]
    if a.mode == "auth":
        if not a.head:
            print("!! auth 模式必須給 --head(從 GitHub UI 手抄,不得用 git rev-parse)")
            return 2
        ctrls.insert(0, ("端點活性控 (UI 手抄 HEAD)", a.head))
    for label, sha in ctrls:
        code, _ = get(base + sha, token)
        print("   %-28s %s -> %s" % (label, sha[:12] + "...", code))
        if code != 200:
            print("!! 正控不過 => 這次檢查【無效】,不得讀下面的結果。")
            return 2

    targets = old_shas() if a.shas == "all" else [ROOT]
    if a.rng:
        if a.shas != "all":
            print("!! --slice 只對 --shas all 有效"); return 2
        try:
            lo, hi = [int(x) for x in a.rng.split("-", 1)]
        except Exception:
            print("!! --slice 格式是 N-M(例:1-55)"); return 2
        if not (1 <= lo <= hi <= len(targets)):
            print("!! --slice 超出範圍:清單共 %d 條,收到 %s" % (len(targets), a.rng))
            return 2
        targets = targets[lo - 1:hi]          # 1 起算,含兩端
        print("== 批次 %d-%d,共 %d 條(依檔案出現順序,未排序未挑選) ==" % (lo, hi, len(targets)))
    print("== 探測 %d 條 (%s) ==" % (len(targets), a.mode))

    res, notes, t0 = {}, [], time.time()
    for n, sha in enumerate(targets, 1):
        code, h = get(base + sha, token)
        res[sha] = code
        if h:
            notes.append((sha, code, h))
        time.sleep(THROTTLE)
        if n % PROGRESS == 0 or n == len(targets):
            sys.stderr.write("   ... %d/%d  (%.0fs)\n" % (n, len(targets), time.time() - t0))

    dist = collections.Counter(res.values())
    el = time.time() - t0
    print("耗時 %.1fs (%.2fs/call)" % (el, el / len(targets)))
    print("狀態碼分佈:", dict(dist))
    print("舊根 %s -> %s" % (ROOT[:12] + "...", res.get(ROOT, "(未測)")))

    alive = sorted(s for s, c in res.items() if c == 200)
    unread = sorted(s for s, c in res.items() if c == 404)
    other = sorted((s, c) for s, c in res.items() if c not in (200, 404, 422))

    # ---- 三態判定 ----
    if unread or other:
        print("\n!! 整輪【無效】,不是通過也不是失敗 —— 重跑。")
        if unread:
            print("   404 = repo 讀不到,%d 條。**不得計入通過。**" % len(unread))
        if other:
            print("   403/429/5xx/逾時 %d 條:%s" % (len(other), other[:5]))
        if notes:
            print("   回應標頭:", notes[:3])
        return 2
    if alive:
        print("\n!! 【失敗】%d 條舊 sha 仍解得開(200):" % len(alive))
        for s in alive[:10]:
            print("     ", s)
        return 1
    print("\n== 通過:%d / %d = 422 (repo 讀得到,而提交不在) ==" % (dist[422], len(targets)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
