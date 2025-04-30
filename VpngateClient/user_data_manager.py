#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台文件存储管理器
用于处理三种类型的文件:
1. 临时文件：使用后立即删除
2. 缓存文件：保存一段时间
3. 配置文件：长期保存和读写
"""

import os
import stat
import tempfile
import platform
import shutil
import contextlib
import atexit
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserDataManager:
    """管理不同类型文件的存储位置和操作"""

    def __init__(self, app_name="my_app"):
        """
        初始化文件存储管理器

        参数:
            app_name (str): 应用程序名称，用于创建目录名
        """
        self.app_name = app_name
        self.system = platform.system()

        # 初始化各类型目录路径
        self.temp_dir = self._get_temp_directory()
        self.cache_dir = self._get_cache_directory()
        self.config_dir = self._get_config_directory()

        # 确保所有目录存在
        self._ensure_directories()

        # 注册退出时清理临时文件
        atexit.register(self.cleanup_temp_files)

    def _get_temp_directory(self):
        """获取适合当前平台的临时目录"""
        temp_base = (
            tempfile.gettempdir()
        )  # 跨平台临时目录 :contentReference[oaicite:3]{index=3}
        # 检查 /tmp sticky bit & 可写
        if platform.system() == "Linux":
            # Ubuntu 25特殊处理
            if self._is_ubuntu_25():
                # 在用户主目录下创建隐藏的临时目录
                home = os.path.expanduser("~")
                return os.path.join(home, f".{self.app_name}", "temp")

        return os.path.join(temp_base, self.app_name)

    def _get_cache_directory(self):
        """获取适合当前平台的缓存目录"""
        if self.system == "Windows":
            # Windows的标准缓存位置
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                return os.path.join(local_app_data, self.app_name, "Cache")
            else:
                # 回退方案
                user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
                return os.path.join(
                    user_profile, "AppData", "Local", self.app_name, "Cache"
                )

        elif self.system == "Darwin":  # macOS
            home = os.path.expanduser("~")
            return os.path.join(home, "Library", "Caches", self.app_name)

        else:  # Linux和其他类Unix系统
            # 遵循XDG规范
            xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
            if xdg_cache_home:
                return os.path.join(xdg_cache_home, self.app_name)
            else:
                home = os.path.expanduser("~")
                return os.path.join(home, ".cache", self.app_name)

    def _get_config_directory(self):
        """获取适合当前平台的配置目录"""
        if self.system == "Windows":
            # Windows的标准配置位置
            app_data = os.environ.get("APPDATA")
            if app_data:
                return os.path.join(app_data, self.app_name)
            else:
                # 回退方案
                user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
                return os.path.join(user_profile, "AppData", "Roaming", self.app_name)

        elif self.system == "Darwin":  # macOS
            home = os.path.expanduser("~")
            return os.path.join(home, "Library", "Application Support", self.app_name)

        else:  # Linux和其他类Unix系统
            # 遵循XDG规范
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                return os.path.join(xdg_config_home, self.app_name)
            else:
                home = os.path.expanduser("~")
                return os.path.join(home, ".config", self.app_name)

    def _is_ubuntu_25(self):
        """检测是否为Ubuntu 25系统"""
        try:
            if self.system != "Linux":
                return False

            # 检查/etc/os-release文件
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    content = f.read()
                    if "Ubuntu" in content:
                        # 寻找版本号
                        for line in content.split("\n"):
                            if line.startswith("VERSION_ID="):
                                version = line.split("=")[1].strip('"').strip("'")
                                return version.startswith("25")
        except Exception as e:
            logger.warning(f"检查Ubuntu版本时出错: {e}")

        return False

    def _ensure_directories(self):
        """确保所有需要的目录存在并具有正确权限"""
        for directory in [self.temp_dir, self.cache_dir, self.config_dir]:
            try:
                os.makedirs(directory, exist_ok=True)

                # 在类Unix系统上设置权限
                if self.system != "Windows":
                    # 设置700权限 (只有用户自己可读写执行)
                    os.chmod(directory, stat.S_IRWXU)
            except Exception as e:
                logger.error(f"创建目录失败 {directory}: {e}")

    @contextlib.contextmanager
    def temp_file(self, filename=None, suffix=None):
        """
        创建一个临时文件的上下文管理器，退出上下文时自动删除

        参数:
            filename (str, optional): 文件名。如果为None，将生成随机名称
            suffix (str, optional): 文件扩展名

        用法:
            with file_manager.temp_file("myfile.txt") as temp_path:
                # 使用临时文件
                with open(temp_path, 'w') as f:
                    f.write("some data")
        """
        if filename is None:
            # 生成随机文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            random_part = os.urandom(4).hex()
            filename = f"temp_{timestamp}_{random_part}"

        if suffix and not filename.endswith(suffix):
            filename = f"{filename}{suffix}"

        temp_path = os.path.join(self.temp_dir, filename)

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            # 创建空文件
            with open(temp_path, "a"):
                pass

            # 在非Windows系统上设置权限
            if self.system != "Windows":
                os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)  # 600权限

            yield temp_path

        finally:
            # 删除临时文件
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"无法删除临时文件 {temp_path}: {e}")

    def get_cache_file_path(self, filename):
        """
        获取缓存文件的完整路径

        参数:
            filename (str): 缓存文件名

        返回:
            str: 缓存文件的完整路径
        """
        return os.path.join(self.cache_dir, filename)

    def write_cache_file(self, filename, data, mode="w"):
        """
        写入数据到缓存文件

        参数:
            filename (str): 缓存文件名
            data (str or bytes): 要写入的数据
            mode (str): 打开文件的模式，默认为'w'（文本写入）

        返回:
            str: 缓存文件的完整路径
        """
        cache_path = self.get_cache_file_path(filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        # 写入数据
        with open(cache_path, mode) as f:
            f.write(data)

        # 在非Windows系统上设置权限
        if self.system != "Windows":
            os.chmod(cache_path, stat.S_IRUSR | stat.S_IWUSR)  # 600权限

        return cache_path

    def read_cache_file(self, filename, mode="r"):
        """
        读取缓存文件内容

        参数:
            filename (str): 缓存文件名
            mode (str): 打开文件的模式，默认为'r'（文本读取）

        返回:
            str or bytes: 文件内容

        异常:
            FileNotFoundError: 文件不存在时抛出
        """
        cache_path = self.get_cache_file_path(filename)

        with open(cache_path, mode) as f:
            return f.read()

    def delete_cache_file(self, filename):
        """
        删除缓存文件

        参数:
            filename (str): 缓存文件名

        返回:
            bool: 是否成功删除
        """
        cache_path = self.get_cache_file_path(filename)

        try:
            if os.path.exists(cache_path):
                os.unlink(cache_path)
                return True
        except Exception as e:
            logger.warning(f"删除缓存文件失败 {cache_path}: {e}")

        return False

    def clear_old_cache(self, max_age_days=30):
        """
        清理超过指定天数的缓存文件

        参数:
            max_age_days (int): 最大保留天数，默认30天

        返回:
            int: 删除的文件数量
        """
        if not os.path.exists(self.cache_dir):
            return 0

        now = datetime.now()
        deleted_count = 0

        for root, dirs, files in os.walk(self.cache_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_days = (now - mtime).days

                    if age_days > max_age_days:
                        os.unlink(file_path)
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"处理缓存文件时出错 {file_path}: {e}")

        return deleted_count

    def get_config_file_path(self, filename):
        """
        获取配置文件的完整路径

        参数:
            filename (str): 配置文件名

        返回:
            str: 配置文件的完整路径
        """
        return os.path.join(self.config_dir, filename)

    def write_config_file(self, filename, data, mode="w"):
        """
        写入数据到配置文件

        参数:
            filename (str): 配置文件名
            data (str or bytes): 要写入的数据
            mode (str): 打开文件的模式，默认为'w'（文本写入）

        返回:
            str: 配置文件的完整路径
        """
        config_path = self.get_config_file_path(filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # 写入数据
        with open(config_path, mode) as f:
            f.write(data)

        # 在非Windows系统上设置权限
        if self.system != "Windows":
            os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)  # 600权限

        return config_path

    def read_config_file(self, filename, mode="r"):
        """
        读取配置文件内容

        参数:
            filename (str): 配置文件名
            mode (str): 打开文件的模式，默认为'r'（文本读取）

        返回:
            str or bytes: 文件内容

        异常:
            FileNotFoundError: 文件不存在时抛出
        """
        config_path = self.get_config_file_path(filename)

        with open(config_path, mode) as f:
            return f.read()

    def config_file_exists(self, filename):
        """
        检查配置文件是否存在

        参数:
            filename (str): 配置文件名

        返回:
            bool: 文件是否存在
        """
        config_path = self.get_config_file_path(filename)
        return os.path.exists(config_path)

    def cleanup_temp_files(self):
        """清理所有临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                for item in os.listdir(self.temp_dir):
                    item_path = os.path.join(self.temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        logger.warning(f"清理临时文件时出错 {item_path}: {e}")
        except Exception as e:
            logger.error(f"清理临时目录时出错: {e}")


# 使用示例
if __name__ == "__main__":
    # 创建文件存储管理器实例
    fsm = UserDataManager("my_awesome_app")

    # 显示各类型目录的路径
    print(f"临时文件目录: {fsm.temp_dir}")
    print(f"缓存文件目录: {fsm.cache_dir}")
    print(f"配置文件目录: {fsm.config_dir}")

    # 使用临时文件
    with fsm.temp_file("test.txt") as temp_path:
        print(f"创建临时文件: {temp_path}")
        with open(temp_path, "w") as f:
            f.write("这是一个临时文件的内容")

    # 自动删除临时文件
    print(f"临时文件应该已被删除: {not os.path.exists(temp_path)}")

    # 写入缓存文件
    cache_path = fsm.write_cache_file("test_cache.txt", "这是缓存数据")
    print(f"缓存文件已写入: {cache_path}")

    # 读取缓存文件
    cache_data = fsm.read_cache_file("test_cache.txt")
    print(f"读取缓存数据: {cache_data}")

    # 写入配置文件
    config_path = fsm.write_config_file("settings.conf", "key=value\nlog_level=debug")
    print(f"配置文件已写入: {config_path}")

    # 读取配置文件
    config_data = fsm.read_config_file("settings.conf")
    print(f"读取配置数据: {config_data}")

    # 清理旧缓存
    deleted = fsm.clear_old_cache(max_age_days=0)  # 删除所有缓存用于测试
    print(f"清理了 {deleted} 个旧缓存文件")
