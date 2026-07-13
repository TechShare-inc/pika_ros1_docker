# Pika sense 1機でデータ収集を行う方法

Pikaデバイスが１つの場合、`setup_device.py`を行わなくとも、
Dockerコンテナ環境内で以下の手順を行うことでデータ収集が可能です。

## 準備

### Terminal 1
```
roscore
```
ずっと起動したままにする。

### Terminal 2
```
bash $HOME/pika_ros/scripts/calibration.bash
```
Errorが小さくなれば、`Ctrl+C`を２回押して停止してOK

### Terminal 3
```
roslaunch sensor_tools open_single_sensor.launch fisheye_port:=6 camera_fps:=15
```
実行後、ターミナルはそのまま閉じずにおいておく。

### Terminal 4
データ収集を行う前に、topic状態を確認しておくとよい。
```
rostopic list # トピック名一覧
rostopic list | wc -l # トピックの数を調べる。
rostopic list | grep camera # cameraという文字列を含むトピックを表示する
rostopic hz /pika_pose # 出力頻度(/秒)を調べる
rostopic echo /pika_pose # トピックの内容を表示する
```

## データ収集

次のコマンドを実行。

```
roslaunch data_tools run_data_capture.launch type:=single_pika datasetDir:=$HOME/user_data/single_pika timeout:=3 episodeIndex:=0
```

データ保存先、最大データ取得時間（timeout）、エピソード番号を適宜設定する。

Senseをダブルクリックすることでデータ収集を開始したい場合は、`useService:=true` を追加。

保存したエピソード内のディレクトリに各トピックのデータが保存される。 `statistic.txt` にデータ取得状況の概要が出力されている。

## データ同期

```
roslaunch data_tools run_data_sync.launch type:=single_pika datasetDir:=$HOME/user_data/single_pika episodeIndex:=-1
```
実行すると、各トピックデータの階層に`sync.txt`が生成される。

## データのHDF5形式への変換

```
cd $HOME/pika_ros/scripts && python3 data_to_hdf5.py --type single_pika --datasetDir $HOME/user_data/single_pika
```

## データ再生

以下のコマンドで、取得済みのデータをROS上でtopicとして再生することができます。

`sync.txt`を生成済みの場合
```
roslaunch data_tools run_data_publish.launch type:=single_pika datasetDir:=$HOME/user_data/single_pika episodeIndex:=0
```

HDF5ファイルを生成済みの場合
```
cd $HOME/pika_ros/scripts && python3 data_publish.py --type single_pika --datasetDir $HOME/user_data/single_pika episodeIndex 0
```

## データ読み込みテスト

取得したデータ（hdf5形式）を機械学習モデルに接続するためのデータローダのサンプルです。

```
pip3 install torch IPython
```

```
cd $HOME/pika_ros/scripts && python3 load_data_example.py --datasetDir $HOME/user_data/single_pika
```

## クレジット

TechShare株式会社 技術部 agilex@techshare.co.jp