# Pika Data Collection Environment (Ubuntu20.04 + ROS1 Noetic)

このリポジトリは、ホストPCでデバイス認識(udev)を設定してから Docker コンテナでデータ収集を行うサンプル環境を提供するものです。
ホストPC要件：
- Ubuntu （ネイティブ環境） 22.04 にて動作確認済
- Docker

その他、Pika使用要件に準拠

## 全体フロー

1. ホストPCで共通 udev rules を登録（Vive / RealSense）
2. ホストPCで Pika デバイスごとの udev rules を自動生成・適用
3. Docker コンテナを起動
4. 生成済みのデバイスパスを使って収集を実行

---

## 1) ホストPCで共通 rules を登録

以下の rules を `/etc/udev/rules.d/` に配置してください。

```bash
cd device_setup
sudo cp 81-vive.rules /etc/udev/rules.d/
sudo cp 99-realsense-libusb.rules /etc/udev/rules.d/
```

---

## 2) ホストPCで Pika デバイスの rules を自動生成

特に2つ以上のPikaデバイスを同時に使いたい場合は、次の操作を行ってください。

```bash
cd device_setup
python3 setup_device.py
```
生成される起動スクリプトは `noetic_ws/user_code/start_*.bash` に出力され、
Docker コンテナ内では `/home/agilex/user_code/start_*.bash` として利用できます。

## 3) Docker 環境の起動

あらかじめDockerをインストールしてください。

その上で、以下を実行しておきます。
```
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl enable docker
sudo systemctl start docker
```

`Dockerfile`, `docker-compose.yml`のあるこのディレクトリで以下を実行：

```bash
docker-compose up --build -d # 初回：　環境により、10分以上かかる可能性あり
docker-compose up -d # 2回目以降
```

一例として、VSCodeのDev Container拡張機能を利用する方法：
- VSCodeにDev Container拡張機能をインストール。
- `Ctrl+Shift+P` を押す
- `Dev Containers: Reopen in Container`

あるいは、新しいウインドウから、左下隅の「リモート画面を開く」印をクリックし、
`Attach to Running Container...` を選択、対象のコンテナを選択してコンテナ環境に入ることもできます。


コンテナ内から以下のディレクトリに保存した内容は、ホストPCに保存されます。

- `/home/agilex/user_code`（ホストの `/user_code`）
- `/home/agilex/user_data`（ホストの `/user_data`）

コンテナの停止:

```bash
docker-compose down
```

---

## 4) コンテナ内で行うこと

本リリースでは、Pika Sense 1機あるいは2機でのデータ収集をガイドしています。
それぞれ、

- /dev_memo/sense_data_single.md
- /dev_memo/sense_data_double.md

を参照してください。



## サンプルデータ

少量のサンプルデータは https://huggingface.co/datasets/techshare-corp/pika_data_example から入手できます。

```
cd user_data/ts-example
git clone https://huggingface.co/datasets/techshare-corp/pika_data_example/single_pika_sense # 70.1MB
```

あるいは

```
cd user_data/ts-example
git clone https://huggingface.co/datasets/techshare-corp/pika_data_example/multi_pika_sense # 149MB
```


## クレジット

TechShare株式会社　技術部　AgileX製品担当  agilex@techshare.co.jp