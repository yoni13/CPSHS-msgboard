# 竹北軟研留言板

## Setup
Check [setup.md](setup.md)

## 系統

#### *多模組設計*
 - api
 - frontend
 - moderation
 - static_files

#### *管理*
- 留言管理
- 回覆管理
- 使用者管理(WIP)
- 管理員管理

#### *DB儲存的資料*
##### *使用者註冊時*
- 使用者名稱
- 電子郵件
- 密碼
- 註冊時間
- 最後登入時間
- 權限
- 帳號狀態
##### *留言時*
- 留言內容
- 留言時間
- 留言者
- 是否被管理員設定隱藏或標記

#### *使用者權限*
- 最高管理員(3)，可以隱藏、標記所有使用者、留言、回覆
- 一般管理員(2)，可以標記所有留言、回覆
- 一般使用者(1)，可以留言、回覆

## 開發rules
- CSS/JS使用絕對路徑(ex: `/static/css/main.css`)
- 別把key放在程式碼裡