# Python版本独立管理方案

为了解决airtest与Python 3.14的兼容性问题，我们需要为项目创建一个完全独立的Python环境，包括特定版本的Python解释器。以下是使用pyenv-win进行Python版本管理的详细方案。

## 1. 安装pyenv-win

pyenv-win是Windows系统下的Python版本管理工具，类似于Linux/macOS下的pyenv，可以帮助我们安装和管理多个Python版本。

### 安装步骤

1. **下载安装包**：
   - 访问 https://github.com/pyenv-win/pyenv-win/releases
   - 下载最新版本的`pyenv-win-x.y.z.zip`文件

2. **解压安装**：
   - 将下载的zip文件解压到`C:\pyenv-win`目录
   - 或使用PowerShell安装：
     ```powershell
     Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "install-pyenv-win.ps1"
     .\install-pyenv-win.ps1
     ```

3. **配置环境变量**：
   - 确保以下环境变量已添加到系统PATH中：
     - `C:\pyenv-win\bin`
     - `C:\pyenv-win\shims`

4. **验证安装**：
   ```powershell
   pyenv --version
   ```

## 2. 安装指定版本的Python

使用pyenv-win安装airtest支持的Python 3.9版本：

```powershell
# 查看可用的Python 3.9版本
pyenv install --list | grep 3.9

# 安装Python 3.9.13（airtest支持的稳定版本）
pyenv install 3.9.13

# 设置全局默认Python版本
pyenv global 3.9.13

# 或仅为当前目录设置Python版本
pyenv local 3.9.13

# 验证安装结果
python --version
# 预期输出：Python 3.9.13
```

## 3. 基于指定Python版本创建虚拟环境

```powershell
# 使用Python 3.9.13创建虚拟环境
python -m venv "e:\My_plugins\Game_script\venv_39"

# 激活虚拟环境
"e:\My_plugins\Game_script\venv_39\Scripts\Activate.ps1"

# 验证Python版本
python --version
# 预期输出：Python 3.9.13
```

## 4. 安装项目依赖

```powershell
# 升级pip
pip install --upgrade pip

# 安装numpy 1.26.4（airtest兼容版本）
pip install numpy==1.26.4

# 安装airtest及其它必要依赖
pip install airtest pywin32 psutil pywinauto==0.6.3 opencv-contrib-python<=4.6.0.66 requests six==1.16.0 mss==6.1.0 Jinja2 Pillow packaging filelock

# 验证安装结果
python -c "from airtest.core.api import *; print('Airtest导入成功')"
# 预期输出：Airtest导入成功
```

## 5. 生成依赖文件

```powershell
# 生成requirements.txt
pip freeze > "e:\My_plugins\Game_script\requirements_39.txt"
```

## 6. 运行项目脚本

```powershell
# 激活虚拟环境
"e:\My_plugins\Game_script\venv_39\Scripts\Activate.ps1"

# 运行脚本
python "e:\My_plugins\Game_script\twinkle_starknightsX\daily\daily.py"
```

## 7. 其他Python版本管理方案

### 7.1 使用Anaconda/Miniconda

```powershell
# 下载Miniconda：https://docs.conda.io/en/latest/miniconda.html

# 创建conda环境
conda create -n game_script python=3.9.13

# 激活环境
conda activate game_script

# 安装依赖
pip install -r requirements_39.txt
```

### 7.2 使用Docker

```dockerfile
# 创建Dockerfile
FROM python:3.9.13-slim

WORKDIR /app

COPY requirements_39.txt .

RUN pip install --no-cache-dir -r requirements_39.txt

COPY . .

CMD ["python", "twinkle_starknightsX/daily/daily.py"]
```

```powershell
# 构建镜像
docker build -t game_script .

# 运行容器
docker run -it --rm game_script
```

## 8. 切换Python版本

### 使用pyenv-win切换版本

```powershell
# 查看已安装的Python版本
pyenv versions

# 切换到Python 3.9.13
pyenv local 3.9.13

# 切换到系统Python
pyenv local system
```

### 切换虚拟环境

```powershell
# 停用当前虚拟环境
deactivate

# 激活Python 3.9的虚拟环境
"e:\My_plugins\Game_script\venv_39\Scripts\Activate.ps1"

# 或激活Python 3.14的虚拟环境
"e:\My_plugins\Game_script\venv\Scripts\Activate.ps1"
```

## 9. 优势与建议

### 优势

- **完全隔离**：不同Python版本之间完全隔离，避免版本冲突
- **灵活切换**：可以轻松在不同Python版本之间切换
- **环境一致性**：确保项目在不同机器上使用相同的Python版本
- **支持airtest**：使用Python 3.9可以完美兼容airtest

### 建议

1. **推荐使用pyenv-win**：对于Windows系统，pyenv-win是管理Python版本的轻量级解决方案
2. **保留多版本虚拟环境**：可以同时保留Python 3.14和3.9的虚拟环境，根据需要切换
3. **定期更新依赖**：定期更新requirements.txt文件，确保依赖版本最新
4. **使用.gitignore**：将虚拟环境目录添加到.gitignore中，避免提交到版本控制

通过以上方案，我们可以为项目创建一个完全独立的Python环境，包括特定版本的Python解释器，解决airtest与Python 3.14的兼容性问题。