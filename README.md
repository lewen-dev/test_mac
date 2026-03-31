# SDCard resource integrity tool #

### 1. 创建虚拟环境

py -m venv venv

### 2. 激活虚拟环境

* Windows:

venv\Scripts\activate

* Linux/Mac:

source venv/bin/activate

### 3. 安装依赖

pip install --upgrade pip

pip install -r requirements.txt

### 4. 安装pyinstaller

pip install pyinstaller

### 5. 编译项目

py build.py

### 6. 打包程序

运行完编译脚本后，dist目录下生成对应版本的文件夹，包含了可执行文件和必要配置文件，整个文件夹压缩打包即可。
