from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig
import imaplib
import jwt
import requests
from datetime import datetime, timezone, time
import pytz
import aiohttp
import httpx

class RainReport:
    @staticmethod
    def generate_jwt_token(sub, kid, private_key):

        payload = {
            'iat': int(datetime.now(timezone.utc).timestamp()) - 30,
            'exp': int(datetime.now(timezone.utc).timestamp()) + 900,
            'sub': sub
        }
        headers = {
            'kid': kid
        }

        # Generate JWT
        encoded_jwt = jwt.encode(payload, private_key, algorithm='EdDSA', headers=headers)
        return encoded_jwt

    @staticmethod
    def grid_weather_24h(api_host, location, encoded_jwt):
        # 调用和风天气API请求天气
        url = f"https://{api_host}/v7/grid-weather/24h"
        # 定义查询地点
        params = {"location": location}
        headers = {
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept-Encoding": "gzip, deflate, br"  # 对应 --compressed 参数
        }

        response = requests.get(
            url,
            params=params,
            headers=headers
        )

        # 检查响应状态
        if response.status_code == 200:
            control_log=f"位置 {location} 的天气请求成功！"
        else:
            control_log=f"位置 {location} 的天气请求失败，状态码: {response.status_code}。错误信息:{response.text}"
        return response.json(), control_log

    @staticmethod
    def extract_weather_data_json(json_respond):
        """
        从JSON数据中提取天气数据

        Args:
            json_respond: JSON数据

        Returns:
            dict: 以"xx时"为键，包含temp、icon和text的字典
        """

        # 提取hourly数据
        control_log="开始整理气象数据"
        hourly_data = json_respond.get('hourly', [])

        # 创建结果字典
        result_dict = {}

        # 处理每小时的数据
        for item in hourly_data:
            # 获取时间
            fx_time = item.get('fxTime', '')
            # 获取温度、图标和天气描述
            temp = item.get('temp', '')
            icon = item.get('icon', '')
            text = item.get('text', '')

            # 将UTC时间转换为北京时间并格式化为"xx时"
            try:
                # 解析时间字符串
                time_part = fx_time.split('+')[0]
                dt = datetime.fromisoformat(time_part)

                # 转换为北京时间 (UTC+8)
                utc_tz = pytz.utc
                beijing_tz = pytz.timezone('Asia/Shanghai')
                utc_dt = utc_tz.localize(dt)
                beijing_dt = utc_dt.astimezone(beijing_tz)

                # 格式化为"xx时"
                time_key = f"{beijing_dt.hour}时"

                # 存储数据
                result_dict[time_key] = {
                    'temp': temp,
                    'icon': icon,
                    'text': text
                }
            except Exception as e:
                control_log = f"时间转换错误: {e}"
                continue
        return result_dict, control_log

    @staticmethod
    def check_single_location_rain(weather_data):
        """
        检查单个坐标点的降雨情况

        Args:
            weather_data: 天气数据字典

        Returns:
            tuple: (上午有雨, 下午有雨) 的布尔值
        """
        # 检查上午(8点到13点)是否有雨
        morning_hours = ['8时', '9时', '10时', '11时', '12时', '13时']
        morning_rain = False

        for hour in morning_hours:
            if hour in weather_data and 'text' in weather_data[hour]:
                if '雨' in weather_data[hour]['text']:
                    morning_rain = True
                    break

        # 检查下午(14点到18点)是否有雨
        afternoon_hours = ['14时', '15时', '16时', '17时', '18时']
        afternoon_rain = False

        for hour in afternoon_hours:
            if hour in weather_data and 'text' in weather_data[hour]:
                if '雨' in weather_data[hour]['text']:
                    afternoon_rain = True
                    break

        return morning_rain, afternoon_rain

class EmailInboxChecker:
    def __init__(self, server, port, username, password, use_ssl=True):
        """
        初始化邮箱连接参数
        :param server: 邮件服务器地址
        :param port: 邮件服务器端口
        :param username: 邮箱地址
        :param password: 邮箱密码/授权码
        :param use_ssl: 是否使用SSL加密连接
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.connection = None

    def connect(self):
        """建立与邮件服务器的连接"""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                self.connection = imaplib.IMAP4(self.server, self.port)

            # 登录邮箱
            self.connection.login(self.username, self.password)
            logger.info("成功连接到邮箱服务器")
            return True
        except Exception as e:
            logger.info(f"连接失败: {str(e)}")
            return False

    def get_unread_count(self, mailbox='INBOX'):
        """
        获取指定邮箱的未读邮件数量
        :param mailbox: 邮箱文件夹，默认为收件箱(INBOX)
        :return: 未读邮件数量，连接失败返回-1
        """
        if not self.connection:
            if not self.connect():
                return -1

        try:
            # 选择邮箱文件夹
            self.connection.select(mailbox)

            # 搜索未读邮件
            result, data = self.connection.search(None, 'UNSEEN')

            if result == 'OK':
                # 获取未读邮件编号列表
                unread_msgs = data[0].split()
                unread_count = len(unread_msgs)
                return unread_count
            else:
                logger.info("搜索未读邮件失败")
                return 0

        except Exception as e:
            logger.info(f"获取未读邮件数量时出错: {str(e)}")
            return -1

    def close_connection(self):
        """关闭连接"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("连接已关闭")
            except:
                pass
            finally:
                self.connection = None

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close_connection()

@register("astrbot_plugin_online_assistant", "thegeminisky", "在线小助理太一", "0.2.1")
class OnlineAS(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self._load_config()

    def _load_config(self):
        """加载并初始化插件配置"""
        # 钉钉自定义机器人
        dingtalk_notify_api = self.config.get("dingtalk_notify", {})
        self.dingtalk_notify_access_token = dingtalk_notify_api.get("access_token")
        self.dingtalk_notify_secret = dingtalk_notify_api.get("secret")

        # LLM服务商余额查询
        self.balance_check_api = self.config.get("balance_check", {})

        # 和风天气
        self.rain_report_api = self.config.get("rain_report", {})

        # 邮箱IMAP
        self.email_monitor = self.config.get("email_monitor", {})

    @filter.command_group("助手")
    def online_assistant(self):
        pass

    # 注册指令的装饰器。指令名为'邮箱'。注册成功后，发送 `/助手 邮箱` 就会触发这个指令。
    @filter.permission_type(filter.PermissionType.ADMIN)
    @online_assistant.command("邮箱")
    async def online_assistant_email_check(self, event: AstrMessageEvent):
        """这是一个未读邮件查询指令"""
        user_name = event.get_sender_name()
        logger.info(f"{user_name}发起邮箱查询")

        # 读取查询配置
        checker = EmailInboxChecker(
            server=self.email_monitor.get("url"),
            port=self.email_monitor.get("port"),
            username=self.email_monitor.get("username"),
            password=self.email_monitor.get("password")
        )

        # 发起查询
        count = checker.get_unread_count()
        checker.close_connection()
        yield event.plain_result(f"未读邮件: {count}封") # 发送一条纯文本消息

    # 注册指令的装饰器。指令名为'天气'。注册成功后，发送 `/助手 天气` 就会触发这个指令。
    @filter.permission_type(filter.PermissionType.ADMIN)
    @online_assistant.command("天气")
    async def online_assistant_weather_check(self, event: AstrMessageEvent):
        """这是一个天气查询指令"""
        user_name = event.get_sender_name()
        logger.info(f"{user_name}发起天气查询")

        # 生成鉴权密钥
        encoded_jwt = RainReport.generate_jwt_token(
            self.rain_report_api.get("sub"),
            self.rain_report_api.get("kid"),
            self.rain_report_api.get("private_key")
        )

        # 检查所有坐标点的降雨情况
        morning_rain_anywhere = False
        afternoon_rain_anywhere = False
        for location in self.rain_report_api.get("location_list"):
            try:
                # 获取天气数据
                weather_condition, control_log = RainReport.grid_weather_24h(self.rain_report_api.get("api_host"), location, encoded_jwt)
                logger.info(control_log)
                weather_dict, control_log = RainReport.extract_weather_data_json(weather_condition)
                logger.info(control_log)

                # 检查当前坐标点的降雨情况
                morning_rain, afternoon_rain = RainReport.check_single_location_rain(weather_dict)

                # 更新总体降雨状态（只要有一个地方有雨就为True）
                if morning_rain:
                    morning_rain_anywhere = True
                    logger.info(f"位置 {location} 上午有雨")

                if afternoon_rain:
                    afternoon_rain_anywhere = True
                    logger.info(f"位置 {location} 下午有雨")

            except Exception as e:
                logger.info(f"处理位置 {location} 时出错: {e}")
                continue

        # 设置北京时区
        beijing_tz = pytz.timezone('Asia/Shanghai')

        # 获取当前北京时间的日期和时间
        now_beijing = datetime.now(beijing_tz)
        current_time = now_beijing.time()

        # 定义时间范围
        start_time_morning = time(6, 0, 0)
        end_time_morning = time(9, 0, 0)
        start_time_afternoon = time(12, 0, 0)
        end_time_afternoon = time(15, 0, 0)

        # 检查时间并完成推送
        if start_time_morning <= current_time < end_time_morning and morning_rain_anywhere:
            yield event.plain_result("上午可能有雨") # 发送一条纯文本消息
        elif start_time_afternoon <= current_time < end_time_afternoon and afternoon_rain_anywhere:
            yield event.plain_result("下午可能有雨") # 发送一条纯文本消息
        elif morning_rain_anywhere + afternoon_rain_anywhere == 0:
            yield event.plain_result("无雨") # 发送一条纯文本消息
        else:
            yield event.plain_result("请在6-9点或12-15点发起查询")  # 发送一条纯文本消息

    # 注册指令的装饰器。指令名为'余额'。注册成功后，发送 `/助手 余额` 就会触发这个指令。
    @filter.permission_type(filter.PermissionType.ADMIN)
    @online_assistant.command("余额")
    async def online_assistant_balance_check(self, event: AstrMessageEvent):
        """查询硅基流动平台余额信息"""
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.balance_check_api.get('provider_key_1')}",
            "Content-Type": "application/json"
        }
        # 发起请求
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://api.siliconflow.cn/v1/user/info", headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data.get('status') and data.get('data'):
                        balance_info = data['data']
                        result = (
                            f"{self.balance_check_api.get('provider_name_1')}账户余额信息:\n"
                            f"赠费余额: {balance_info['balance']}\n"
                            f"充值余额: {balance_info['chargeBalance']}\n"
                            f"总余额: {balance_info['totalBalance']}\n"
                        )
                        yield event.plain_result(result)
                    else:
                        yield event.plain_result("获取硅基流动余额失败：" + data.get('message', '未知错误'))
            except aiohttp.ClientError as e:
                yield event.plain_result(f"请求错误: {e}")

    # 注册指令的装饰器。指令名为'新闻'。注册成功后，发送 `/助手 新闻` 就会触发这个指令。
    @filter.permission_type(filter.PermissionType.ADMIN)
    @online_assistant.command("新闻")
    async def online_assistant_news(self, event: AstrMessageEvent):
        """获取当天的每天60秒读懂世界"""
        # 构建请求链接
        url = f"https://{self.config.get('news_host')}/v2/60s?encoding=text"
        # 发起请求
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()  # 检查请求是否成功
                yield event.plain_result(response.text)
            except httpx.HTTPError as e:
                yield event.plain_result(f"HTTP错误: {e}")
            except Exception as e:
                yield event.plain_result(f"其他错误: {e}")