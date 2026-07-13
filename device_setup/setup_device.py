#!/usr/bin/env python3

import subprocess
import re
import os
import cv2
import time


def msg(zh, en):
    """Return a bilingual message (Chinese / English)."""
    return f"{zh}\n{en}"


def say(zh, en):
    """Print a bilingual message."""
    print(msg(zh, en))


def prompt(zh, en):
    """Return a bilingual input prompt."""
    return msg(zh, en)


def run_command(command):
    """コマンドを実行して出力を返す"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"コマンド実行中にエラーが発生しました: {str(e)}")
        return None


def get_device_info():
    """デバイス情報を取得"""
    rs_output = run_command("rs-enumerate-devices -s")
    if not rs_output:
       print("深度カメラのデータを取得できませんでした")
       return None, None

    serial_match = re.search(r'Intel RealSense D405\s+(\d+)', rs_output)
    if not serial_match:
       print("深度カメラのデータを取得できませんでした")
       return None, None
    serial_number = serial_match.group(1)

    ls_output = run_command("ls /dev | grep ttyUSB | grep -v ttyUSB50 | grep -v ttyUSB51 | grep -v ttyUSB60 | grep -v ttyUSB61")
    count = ls_output.count("tty")
    if count > 1:
       print("コントローラーに接続されているUSBシリアルデバイスは1つのみにしてください")
       return None, None
    udev_output = run_command(f"udevadm info /dev/{ls_output} | grep DEVPATH")
    if not udev_output:
       print("シリアルポートのデータを取得できませんでした")
       return None, None

    usb_path = udev_output[:udev_output.find(ls_output)][:-1]
    usb_path = usb_path[usb_path.rfind("/")+1:]
    print("魚眼カメラをスキャン中...")
    video_path = None
    cv2.setLogLevel(0)
    temp_dir = "/tmp/pika_camera_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    captured_devices = []
    for i in range(50):
       cap = cv2.VideoCapture(i)
       if cap.isOpened():
           fourcc = cv2.VideoWriter_fourcc(*'MJPG')
           cap.set(cv2.CAP_PROP_FOURCC, fourcc)
           cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
           cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
           cap.set(cv2.CAP_PROP_FPS, 30)
           ret, frame = cap.read()
           if ret and frame is not None:
               frame_path = os.path.join(temp_dir, f"video{i}.jpg")
               cv2.imwrite(frame_path, frame)
               captured_devices.append((i, frame_path))
           cap.release()
    
    if not captured_devices:
       print("魚眼カメラのデータを取得できませんでした")
       return None, None
    
    print(f"\n{len(captured_devices)}個のカメラを検出しました")
    print("各カメラの画像は以下に保存されています：")
    for idx, (device_id, frame_path) in enumerate(captured_devices):
       print(f"  番号 {idx}: /dev/video{device_id}")
       print(f"            → 画像: {frame_path}")
    
    print("\n保存された画像を確認する方法:")
    print(f"  $ eog /tmp/pika_camera_frames/video*.jpg  # 画像ビューアで開く")
    print()
    
    while True:
       try:
           choice = input(f"魚眼カメラの番号を入力してください（0-{len(captured_devices)-1}）: ")
           choice_idx = int(choice)
           if 0 <= choice_idx < len(captured_devices):
               video_path = 'video' + str(captured_devices[choice_idx][0])
               break
           else:
               print(f"入力が無効です。0～{len(captured_devices)-1}の範囲で入力してください。")
       except ValueError:
           print("有効な数字を入力してください")
    
    if video_path is None:
       print("魚眼カメラのデータを取得できませんでした")
       return None, None
    udev_output = run_command(f"udevadm info /dev/{video_path} | grep DEVPATH")
    video_path = udev_output[:udev_output.find("video")][:-1]
    video_path = video_path[video_path.rfind("/")+1:]

    return serial_number, usb_path, video_path


def generate_setup_bash(left_info, right_info, select):
    """setup.bashファイルを生成"""
    if select == "1":
        path = "setup_multi_sensor.bash"
        usb_num1 = 50
        usb_num2 = 51
        name1 = "sensor_"
        name2 = "sensor_"
        to1 = ">"
        to2 = ">>"
    if select == "2":
        path = "setup_multi_gripper.bash"
        usb_num1 = 60
        usb_num2 = 61
        name1 = "gripper_"
        name2 = "gripper_"
        to1 = ">"
        to2 = ">>"
    if select == "3":
        path = "setup_sensor_gripper.bash"
        usb_num1 = 50
        usb_num2 = 60
        name1 = "sensor_"
        name2 = "gripper_"
        to1 = ">"
        to2 = ">"
    content = f"""
#/bin/bash

sudo sh -c 'echo "ACTION==\\"add\\", KERNELS==\\"{left_info[1]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{usb_num1}\\"" {to1} /etc/udev/rules.d/{name1}serial.rules'
sudo sh -c 'echo "ACTION==\\"add\\", KERNELS==\\"{right_info[1]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{usb_num2}\\"" {to2} /etc/udev/rules.d/{name2}serial.rules'

sudo sh -c 'echo "ACTION==\\"add\\", KERNEL==\\"video[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48]*\\", KERNELS==\\"{left_info[2]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{usb_num1}\\"" {to1} /etc/udev/rules.d/{name1}fisheye.rules'
sudo sh -c 'echo "ACTION==\\"add\\", KERNEL==\\"video[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48]*\\", KERNELS==\\"{right_info[2]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{usb_num2}\\"" {to2} /etc/udev/rules.d/{name2}fisheye.rules'

sudo udevadm control --reload-rules && sudo service udev restart && sudo udevadm trigger
               """
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def generate_start_bash(left_info, right_info, select):
    if select == "1":
        path = "start_multi_sensor.bash"
        usb_num1 = 50
        usb_num2 = 51
        content = f"""
camera_fps=30
camera_width=640
camera_height=480
l_depth_camera_no={left_info[0]}
r_depth_camera_no={right_info[0]}

l_serial_port=/dev/ttyUSB{usb_num1}
r_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port={usb_num1}
r_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/noetic/setup.bash && cd $HOME/pika_ros/install/share/sensor_tools/scripts && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_multi_sensor.launch l_depth_camera_no:=$l_depth_camera_no r_depth_camera_no:=$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height name:=$1 name_index:=$1_
else
    source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_multi_sensor.launch l_depth_camera_no:=$l_depth_camera_no r_depth_camera_no:=$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height
fi
                """
    if select == "2":
        path = "start_multi_gripper.bash"
        usb_num1 = 60
        usb_num2 = 61
        content = f"""
camera_fps=30
camera_width=640
camera_height=480
l_depth_camera_no={left_info[0]}
r_depth_camera_no={right_info[0]}

l_serial_port=/dev/ttyUSB{usb_num1}
r_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port={usb_num1}
r_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/noetic/setup.bash && cd $HOME/pika_ros/install/share/sensor_tools/scripts && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_multi_gripper.launch l_depth_camera_no:=$l_depth_camera_no r_depth_camera_no:=$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height name:=$1 name_index:=$1_
else
    source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_multi_gripper.launch l_depth_camera_no:=$l_depth_camera_no r_depth_camera_no:=$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height
fi
                """
    if select == "3":
        path = "start_sensor_gripper.bash"
        usb_num1 = 50
        usb_num2 = 60
        content = f"""
camera_fps=30
camera_width=640
camera_height=480
sensor_depth_camera_no={left_info[0]}
gripper_depth_camera_no={right_info[0]}

sensor_serial_port=/dev/ttyUSB{usb_num1}
gripper_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
sensor_fisheye_port={usb_num1}
gripper_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/noetic/setup.bash && cd $HOME/pika_ros/install/share/sensor_tools/scripts && chmod 777 usb_camera.py
source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_sensor_gripper.launch sensor_depth_camera_no:=$sensor_depth_camera_no gripper_depth_camera_no:=$gripper_depth_camera_no sensor_serial_port:=$sensor_serial_port gripper_serial_port:=$gripper_serial_port sensor_fisheye_port:=$sensor_fisheye_port gripper_fisheye_port:=$gripper_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height
                """
    script_dir = os.path.join(os.path.dirname(__file__), "..", "user_code")
    os.makedirs(script_dir, exist_ok=True)
    script_path = os.path.join(script_dir, path)
    with open(script_path, "w") as f:
        f.write(content)
    os.chmod(script_path, 0o755)


def main():
    print("=== Pikaデバイスセットアップツール ===")
    select = None
    while True:
        print("\nバインディングモードを選択してください：")
        print("1. 2つのpikaセンサー（ハンドヘルドグリッパー）")
        print("2. 2つのpikaグリッパー（アーム搭載グリッパー）")
        print("3. 1つのpikaセンサーと1つのpikaグリッパー")
        select = input("選択を入力してください（1-3）: ")
        
        if select == "1":
            device1 = "左"
            device2 = "右"
            break
        elif select == "2":
            device1 = "左"
            device2 = "右"
            break
        elif select == "3":
            device1 = "センサー"
            device2 = "グリッパー"
            break
        else:
            print("1、2、または3を入力してください")
            continue

    print(f"\n{device1}デバイスを接続して、Enterキーを押してください...")
    input()
    print(f"{device1}デバイス情報を取得中...")
    while True:
        left_info = get_device_info()
        if not left_info[0]:
            print(f"{device1}デバイス情報を取得できませんでした。接続を確認して、Enterキーを押してください...")
            input()
        else:
            break
    print(f"{device1}デバイス情報: {left_info[0]} {left_info[1]} {left_info[2]}")

    print(f"\n{device1}デバイスを取り外し、{device2}デバイスを接続してください")
    print("（注：異なるUSBポートを使用し、セットアップ完了後はポートを変更しないでください）")
    print("Enterキーを押して続行...")
    input()
    print(f"{device2}デバイス情報を取得中...")
    while True:
        right_info = get_device_info()
        if not right_info[0]:
            print(f"{device2}デバイス情報を取得できませんでした。接続を確認して、Enterキーを押してください...")
            input()
        else:
            break
    print(f"{device2}デバイス情報: {right_info[0]} {right_info[1]} {right_info[2]}")

    print("\n設定ファイルを生成中...")
    generate_setup_bash(left_info, right_info, select)
    generate_start_bash(left_info, right_info, select)
    setup_path = "setup_multi_sensor.bash" if select=="1" else ("setup_multi_gripper.bash" if select=="2" else "setup_sensor_gripper.bash")
    start_path = "start_multi_sensor.bash" if select=="1" else ("start_multi_gripper.bash" if select=="2" else "start_sensor_gripper.bash")
    print("\nセットアップ完了！以下のファイルが生成されました：")
    print(f"1. {setup_path}")
    print(f"2. {start_path}")
    print(f"\n{setup_path}を実行中...")
    run_command(f"bash {setup_path}")
    print("実行完了しました。")
    
    while True:
        print("\nデバイスを再接続してください")
        print("（注：以前バインドしたのと同じUSBポートを使用してください）")
        print("Enterキーを押してバインディングの成功を確認...")
        input()
        print("待機中...")
        time.sleep(5)
        video_list = run_command("ls /dev | grep video")
        usb_list = run_command("ls /dev | grep ttyUSB")
        
        if (select == "1" or select == "3") and video_list.find("50") < 0:
            print("センサー（左）のフィッシュアイカメラが見つかりません")
            continue
        if (select == "1") and video_list.find("51") < 0:
            print("センサー（右）のフィッシュアイカメラが見つかりません")
            continue
        if (select == "2" or select == "3") and video_list.find("60") < 0:
            print("グリッパー（左）のフィッシュアイカメラが見つかりません")
            continue
        if (select == "2") and video_list.find("61") < 0:
            print("グリッパー（右）のフィッシュアイカメラが見つかりません")
            continue
        if (select == "1" or select == "3") and usb_list.find("50") < 0:
            print("センサー（左）のシリアルポートが見つかりません")
            continue
        if (select == "1") and usb_list.find("51") < 0:
            print("センサー（右）のシリアルポートが見つかりません")
            continue
        if (select == "2" or select == "3") and usb_list.find("60") < 0:
            print("グリッパー（左）のシリアルポートが見つかりません")
            continue
        if (select == "2") and usb_list.find("61") < 0:
            print("グリッパー（右）のシリアルポートが見つかりません")
            continue
        break
    
    print("\nバインディング成功！デバイス起動方法：")
    print(f"bash {start_path}")


if __name__ == "__main__":
    main()
