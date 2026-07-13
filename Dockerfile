FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# Set the locale: Ubuntuはasciiしか知らないので、UTF-8を使えるようにする
# en_US.UTF-8で、日本語なども表示できる。
# ROS, pythonなどもUTF-8を前提にしており、設定しないとエラーや文字化けでログの可視性が悪くなる
RUN apt-get update && apt-get install -y locales && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# timezoneを日本に設定
ENV TZ=Asia/Tokyo
RUN apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 基本的なツールとPython環境をインストール
RUN apt-get update && apt-get install -y \
    sudo \
    curl \
    git \
    wget \
    unzip \
    usbutils \
    lsb-release \
    build-essential \
    python3.8 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*


RUN curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc \
    | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" \
    > /etc/apt/sources.list.d/ros1.list

# install pika_ros relevant packages: took about 300s
RUN apt-get update && apt-get install -y \
    libjsoncpp-dev \
    ros-noetic-ddynamic-reconfigure \
    ros-noetic-ros-control \
    ros-noetic-controller-manager \
    ros-noetic-ros-numpy \
    ros-noetic-serial \
    ros-noetic-librealsense2 \
    python3-pcl \
    libqt5serialport5-dev \
    zlib1g-dev \
    libx11-dev \
    libusb-1.0-0-dev \
    freeglut3-dev \
    liblapacke-dev libopenblas-dev libatlas-base-dev \
    cmake libssl-dev pkg-config libgtk-3-dev \
    libglfw3-dev libgl1-mesa-dev \
    libglu1-mesa-dev g++ libopenvr-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip && \
    pip3 install opencv-python

RUN useradd -m agilex
ENV HOME=/home/agilex

# clone pika_ros repository: took about 20 minutes (depends on network speed)
USER agilex
WORKDIR ${HOME}
RUN git clone https://github.com/agilexrobotics/pika_ros.git && \
    cd pika_ros && \
    git submodule update --init --recursive

# unpack and install librealsense, realsense-viewwer: took about 7 minutes (depends on CPU speed)
WORKDIR ${HOME}/pika_ros/source
USER root
RUN unzip librealsense-2.55.1.zip -d . && \
    rm librealsense-2.55.1.zip && echo "Unzipped librealsense" && \
    tar -xzf curl-7.75.0.tar.gz -C . && \
    rm curl-7.75.0.tar.gz && echo "Unzipped curl" && \
    cd librealsense && \
    # fix path in CMake/external_libcurl.cmake to point to the correct location of curl-7.75.0 (unpacked in the same directory as librealsense)
    # 特定の行を置換
    sed -i 's|URL "/home/agilex/curl-7.75.0"|URL "/home/agilex/pika_ros/source/curl-7.75.0"|g' CMake/external_libcurl.cmake && \
    bash install.bash && echo "Installed librealsense"

# build pika_ros packages
WORKDIR ${HOME}/pika_ros
RUN unzip source/install.zip -d . && \
    rm source/install.zip && \
    dpkg -i source/ros-noetic-ddynamic-reconfigure*.deb || true && \
    apt-get update && apt-get install -f -y
# 必要なファイルに対して適切な権限を設定する。
RUN chmod -R a+rX -R install/ && \
    chmod -R a+rX -R scripts/ && \
    # echo "source ${HOME}/pika_ros/install/setup.bash" >> ~/.bashrc && \
    echo "agilex ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Ensure full ROS desktop, rosdep and initialization so package dependencies can be resolved
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-desktop-full \
    python3-rosdep \
    python3-rosinstall-generator \
    python3-wstool \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && rosdep init || true \
    && rosdep update || true

USER root
# Install utilities and rviz; keep gazebo repo setup below where gazebo is installed
RUN apt-get update && apt-get install -y \
    ros-noetic-rviz \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# install packages for teleoperation
SHELL ["/bin/bash", "-c"]
WORKDIR ${HOME}/pika_ros/src
RUN git clone https://github.com/agilexrobotics/PikaAnyArm.git --depth 1 && \
    cd PikaAnyArm && \
    git submodule update --init --recursive

# ROS 依存パッケージの導入
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common curl gnupg lsb-release && \
    add-apt-repository universe && \
    # Add OSRF Gazebo repository and key for gazebo11
    curl -sSL https://packages.osrfoundation.org/gazebo.key | apt-key add - && \
    echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -sc) main" > /etc/apt/sources.list.d/gazebo-stable.list && \
    apt-get update && \
    apt-get install -y gazebo11 \
    ros-noetic-moveit \
    ros-noetic-moveit-visual-tools && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${HOME}/pika_ros
SHELL ["/bin/bash", "-c"]
RUN source /opt/ros/noetic/setup.bash && \
    export CMAKE_PREFIX_PATH=/opt/ros/noetic:${CMAKE_PREFIX_PATH} && \
    catkin_make install -DCATKIN_WHITELIST_PACKAGES=""

# conda利用のため、Miniforgeインストール
RUN apt-get update && apt-get install -y \
    bzip2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    wget -O /tmp/miniforge.sh \
    https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh && \
    bash /tmp/miniforge.sh -b -p /opt/conda && \
    rm /tmp/miniforge.sh
# PATH追加
ENV PATH=/opt/conda/bin:$PATH
        
# conda環境(pika)を作成しpiperテレオペに必要なパッケージをインストール
RUN conda create -y -n pika python=3.9 && \
    conda run -n pika conda install -y -c conda-forge \
        pinocchio=3.2.0 casadi=3.6.7 && \
    conda run -n pika pip install \
        meshcat rospkg pyyaml piper-sdk opencv-python netifaces ur-rtde
        
# その他便利ツール
RUN apt-get update && apt-get install -y \
    ethtool \
    can-utils \
    v4l-utils \
    ffmpeg \
    cheese \
    && rm -rf /var/lib/apt/lists/*

# bashrcにROS, condaの初期化を追加
RUN cat <<'EOF' >> ${HOME}/.bashrc

# ROS
source /opt/ros/noetic/setup.bash
source /home/agilex/pika_ros/install/setup.bash

# conda
__conda_setup="$('/opt/conda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
eval "$__conda_setup"
unset __conda_setup

# Path整理
PATH=$(echo $PATH | sed -e 's|/opt/conda/bin:||g')
export PATH=/usr/bin:$PATH
EOF

SHELL ["/bin/bash", "-c"]
RUN conda config --set auto_activate_base false

# Set execute permissions
RUN chmod -R +x /home/agilex/pika_ros/install/ && \
    chmod -R +x /home/agilex/pika_ros/scripts/

WORKDIR ${HOME}
CMD ["/bin/bash"]

