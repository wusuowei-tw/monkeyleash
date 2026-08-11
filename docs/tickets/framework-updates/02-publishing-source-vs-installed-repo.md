# 02 — 發布來源沒有安裝產物,四條框架測試因此永遠紅

## 事實

在 `agent-gates` 跑 `pytest`:**4 failed, 301 passed**。
在淨室安裝出來的 repo 跑同一批:**305 passed**。

四條全部依賴 `.agents/legacy-no-redlight.txt`,而那份清單標記是 `generate` ——
由安裝器在**目標 repo** 產生。**發布來源本來就沒有它**,依設計如此。

```
TestLegacyNoRedlightList::test_the_list_is_what_the_generator_would_produce
TestTheListItselfIsGuarded::test_an_entry_absent_from_the_go_live_tree_is_a_violation
TestTheListItselfIsGuarded::test_the_shipped_list_is_clean
TestGoLiveShaTravelsWithTheList::test_the_shipped_list_carries_its_own_sha
```

## 為什麼要修

**這是 F-031 的形狀**:任何人打開 agent-gates 跑一次測試就看到四個紅,
而那四個紅與他做的事無關。他學到的是「這套測試本來就紅」,
之後真正的紅也會被同一個習慣濾掉。**壞掉的訊號會訓練人忽略訊號。**

而 agent-gates 是**別人第一個會打開的 repo** —— 汙染的是第一印象。

## 不能用的做法

「檔案不存在就 skip」——**那是自我服務的豁免**:刪掉 legacy 清單就能讓
R6 的測試整組消失。正是 F-022 的形狀(豁免條件必須無法自我服務)。

## 可能的方向(未裁決)

1. **明確的角色宣告**:repo 根目錄放一個 `PUBLISHING-SOURCE` 標記檔,
   測試看它決定 skip。安裝器**永不產生**這個檔,所以裝出來的 repo 不可能有它 ——
   宣告來源是「這個檔案存在」,而它在目標 repo 側造不出來(裝的時候不會被複製)。
   要驗證這一點:標記檔必須標記為**不可攜**(`skip`),而那件事有測試可以守。
2. **發布來源也自己安裝一次**:agent-gates 自己跑 install,產生 legacy 清單。
   但那與 ADR 0010 的 B(不自管)衝突,要一起重議。
3. **把那四條測試移出框架測試集**:改成只在 verify-gates 的淨室階段跑。
   缺點是它們不再隨框架走,新專案拿不到那層保護。

## 怎樣算做完

- agent-gates 跑 pytest 全綠,而且**不是靠自我服務的 skip**
- 淨室 repo 那 305 條一條都沒少
- 要實際製造一次:把 skip 條件偽造出來看看擋不擋得住
