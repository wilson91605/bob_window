# 開發日誌

## 在Jetson AGX 安裝 tensorflow 

原因：執行YOLOv5刷新率過低，延遲時間久。

狀態：尚未成功

日誌：同時安裝NVIDIA提供之tensorflow、pytorch、torch-vision，YOLOv5有抓到CUDA，但執行YOLOv5辨識時失敗。最後錯誤訊息與Kernel有關。

[在Jetson 安裝tensorflow](https://docs.nvidia.com/deeplearning/frameworks/install-tf-jetson-platform/index.html)
https://docs.nvidia.com/deeplearning/frameworks/install-pytorch-jetson-platform/index.html
https://docs.nvidia.com/deeplearning/frameworks/install-tf-jetson-platform/index.html
https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048

```shell=
$ sudo apt-get update
$ sudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran

$ sudo apt-get install python3-pip
$ sudo pip3 install -U pip testresources setuptools==49.6.0 

$ sudo pip3 install -U --no-deps numpy==1.19.4 future==0.18.2 mock==3.0.5 keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 protobuf pybind11 cython pkgconfig packaging
$ sudo env H5PY_SETUP_REQUIRES=0 pip3 install -U h5py==3.1.0

$ sudo pip3 install --pre --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v50 tensorflow

```

查看tensorflow版本
```shell=
pip3 list |grep "tensor"
tensorboard             2.8.0
tensorboard-data-server 0.6.1
tensorboard-plugin-wit  1.8.1
tensorflow              2.8.0+nv22.5
tensorflow-estimator    2.8.0
```

JP_VERSION=5.0.1 DP
TF_VERSION=2.8.0
NV_VERSION=22.5

將``$NV_VERSION``、``$TF_VERSION``換成上方版本號

進入虛擬環境後

```shell=
$ pip3 install -U numpy grpcio absl-py py-cpuinfo psutil portpicker six mock requests gast h5py astor termcolor protobuf keras-applications keras-preprocessing wrapt google-pasta setuptools testresources
$ pip3 install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v50 tensorflow==$TF_VERSION+nv$NV_VERSION
```




