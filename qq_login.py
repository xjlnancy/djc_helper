# Generated by Selenium IDE
import subprocess

import win32api
import win32con
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from config import *
from data_struct import Object
from log import logger


class LoginResult(Object):
    def __init__(self, uin="", skey=""):
        super().__init__()
        self.uin = uin
        self.skey = skey


class QQLogin():
    bandizip_executable_path = os.path.realpath("./bandizip_portable/bz.exe")
    chrome_driver_executable_path = os.path.realpath("./chromedriver_85.0.4183.87.exe")
    chrome_binary_7z = os.path.realpath("./chrome_portable_85.0.4183.59.7z")
    chrome_binary_directory = os.path.realpath("./chrome_portable_85.0.4183.59")
    chrome_binary_location = os.path.realpath("./chrome_portable_85.0.4183.59/chrome.exe")

    def __init__(self, common_config):
        self.cfg = common_config  # type: CommonConfig

        caps = DesiredCapabilities().CHROME
        # caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
        caps["pageLoadStrategy"] = "none"  # Do not wait for full page load

        options = Options()
        if not self.cfg._debug_show_chrome_logs:
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

        inited = False

        try:
            if not self.cfg.force_use_portable_chrome:
                # 如果未强制使用便携版chrome，则首先尝试使用系统安装的chrome85
                self.driver = webdriver.Chrome(executable_path="./chromedriver_85.0.4183.87.exe", desired_capabilities=caps, options=options)
                logger.info("使用自带chrome")
                inited = True
        except:
            pass

        if not inited:
            # 如果找不到，则尝试使用打包的便携版chrome85
            # 先判定是否是下载的无附带浏览器的小包
            if not os.path.isfile(self.chrome_binary_7z):
                msg = (
                    "当前电脑未发现合适版本chrome85版本，且当前目录无便携版chrome的压缩包，因此猜测你下载的是未附带浏览器的小包\n"
                    "请采取下列措施之一\n"
                    "\t1. 去蓝奏云网盘下载chrome85离线安装包.exe，并安装，从而系统有合适版本的chrome浏览器\n"
                    "\t2. 去蓝奏云网盘下载完整版的本工具压缩包，也就是大概是95MB的最新的压缩包\n"
                    "\n"
                    "请进行上述操作后再尝试~\n"
                )
                win32api.MessageBox(0, msg, "出错啦", win32con.MB_ICONERROR)
                exit(-1)

            # 先判断便携版chrome是否已解压
            if not os.path.isdir(self.chrome_binary_directory):
                logger.info("自动解压便携版chrome到当前目录")
                subprocess.call('{} x -target:auto {}'.format(self.bandizip_executable_path, self.chrome_binary_7z))

            # 然后使用本地的chrome来初始化driver对象
            options.binary_location = self.chrome_binary_location
            # you may need some other options
            options.add_argument('--no-sandbox')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--no-first-run')
            self.driver = webdriver.Chrome(executable_path=self.chrome_driver_executable_path, desired_capabilities=caps, options=options)
            logger.info("使用便携版chrome")

    def login(self, account, password):
        """
        自动登录指定账号，并返回登陆后的cookie中包含的uin、skey数据
        :param account: 账号
        :param password: 密码
        :rtype: LoginResult
        """
        logger.info("即将开始自动登录，无需任何手动操作，等待其完成即可")
        logger.info("如果出现报错，可以尝试调高相关超时时间然后重新执行脚本")

        def login_with_account_and_password():
            # 选择密码登录
            self.driver.find_element(By.ID, "switcher_plogin").click()
            # 输入账号
            self.driver.find_element(By.ID, "u").send_keys(account)
            # 输入密码
            self.driver.find_element(By.ID, "p").send_keys(password)
            # 发送登录请求
            self.driver.find_element(By.ID, "login_button").click()

        return self._login(login_with_account_and_password)

    def qr_login(self):
        """
        二维码登录，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """
        logger.info("即将开始扫码登录，请在弹出的网页中扫码登录~")
        return self._login()

    def _login(self, login_action_fn=None):
        """
        通用登录逻辑，并返回登陆后的cookie中包含的uin、skey数据
        :rtype: LoginResult
        """
        # 打开活动界面
        self.driver.get("https://dnf.qq.com/lbact/a20200716wgmhz/index.html")
        # 浏览器设为最大
        self.driver.set_window_size(1936, 1056)
        # 等待登录按钮出来，确保加载完成
        WebDriverWait(self.driver, self.cfg.login_timeouts.load_page).until(expected_conditions.visibility_of_element_located((By.ID, "dologin")))
        # 点击登录按钮
        self.driver.find_element(By.ID, "dologin").click()
        # 等待iframe显示出来
        try:
            WebDriverWait(self.driver, self.cfg.login_timeouts.load_login_iframe).until(
                expected_conditions.visibility_of_element_located((By.XPATH, '//*[@id="switcher_plogin"]'))
            )
        except:
            pass
        # 切换登录iframe
        self.driver.switch_to.frame(0)

        logger.info("请在{}s内完成登录操作".format(self.cfg.login_timeouts.login))

        # 实际登录的逻辑，不同方式的处理不同，这里调用外部传入的函数
        if login_action_fn is not None:
            login_action_fn()

        # 等待登录完成（也就是登录框消失）
        WebDriverWait(self.driver, self.cfg.login_timeouts.login).until(expected_conditions.invisibility_of_element_located((By.ID, "login")))
        # 回到主iframe
        self.driver.switch_to.default_content()
        # 等待活动已结束的弹窗出来，说明已经登录完成了
        WebDriverWait(self.driver, self.cfg.login_timeouts.login_finished).until(expected_conditions.visibility_of_element_located((By.ID, "showAlertContent")))

        # 从cookie中获取uin和skey
        loginResult = LoginResult(self.get_cookie("uin"), self.get_cookie("skey"))

        # 最小化网页
        self.driver.minimize_window()
        self.driver.quit()

        return loginResult

    def get_cookie(self, name):
        return self.driver.get_cookie(name)['value']


if __name__ == '__main__':
    # 读取配置信息
    load_config("config.toml", "config.toml.local")
    cfg = config()

    ql = QQLogin(cfg.common)
    # lr = ql.login("1234567", "xxxxxxxxxx")
    lr = ql.qr_login()
    print(lr)
